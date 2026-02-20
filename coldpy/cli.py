from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from coldpy.cache import CacheError, read_cache, write_cache
from coldpy.discovery import DEFAULT_EXCLUDE_PATTERNS, EXCLUSION_LABELS, discover_modules
from coldpy.models import ModuleResult, ScanPayload
from coldpy.reporter import print_summary, render_modules_table, write_json_report
from coldpy.runtime import build_scan_environment, load_project_env, resolve_python_executable
from coldpy.scanner import DEFAULT_THRESHOLD_MB, DEFAULT_THRESHOLD_MS, scan_modules

app = typer.Typer(help="ColdPy: Python import time + memory profiler")
console = Console()


class TopSort(str):
    TIME = "time"
    MEMORY = "memory"


def _sort_modules(modules: list[ModuleResult], sort_by: str) -> list[ModuleResult]:
    def sort_key(module: ModuleResult) -> float:
        if sort_by == TopSort.MEMORY:
            return module.memory_mb if module.memory_mb is not None else -1.0
        return module.import_time_ms if module.import_time_ms is not None else -1.0

    return sorted(modules, key=sort_key, reverse=True)


def _filter_successful(
    modules: list[ModuleResult], threshold_ms: float, threshold_mb: float
) -> list[ModuleResult]:
    filtered: list[ModuleResult] = []
    for module in modules:
        if module.status != "ok":
            continue

        time_val = module.import_time_ms or 0.0
        mem_val = module.memory_mb or 0.0
        if time_val >= threshold_ms or mem_val >= threshold_mb:
            filtered.append(module)

    return filtered


@app.command()
def scan(
    path: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Project path to scan (defaults to current directory).",
    ),
    json_output: Path | None = typer.Option(None, "--json", help="Write JSON report to file."),
    threshold_ms: float = typer.Option(DEFAULT_THRESHOLD_MS, "--threshold-ms"),
    threshold_mb: float = typer.Option(DEFAULT_THRESHOLD_MB, "--threshold-mb"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Do not write .coldpy/cache.json"),
    python_executable: Path | None = typer.Option(
        None,
        "--python",
        help="Python executable to use for module imports. Defaults to project venv if found.",
    ),
    env_file: Path | None = typer.Option(
        None,
        "--env-file",
        help="Path to .env file to load for scanned imports.",
    ),
    no_project_env: bool = typer.Option(
        False,
        "--no-project-env",
        help="Disable automatic loading of .env/.env.local from project path.",
    ),
    exclude: list[str] = typer.Option(
        [],
        "--exclude",
        help="Glob pattern to exclude files/modules from scan. Can be repeated.",
    ),
) -> None:
    """Scan a Python project for import time and memory cost."""
    if threshold_ms < 0 or threshold_mb < 0:
        raise typer.BadParameter("Threshold values must be >= 0")

    project_root = path.resolve()
    try:
        runtime_python = resolve_python_executable(project_root, requested_python=python_executable)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    extra_env: dict[str, str] = {}
    env_source: Path | None = None
    if not no_project_env or env_file is not None:
        try:
            extra_env, env_source = load_project_env(project_root, env_file=env_file)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc

    scan_env = build_scan_environment(extra_env)

    effective_exclusions = EXCLUSION_LABELS + [pattern for pattern in exclude if pattern not in EXCLUSION_LABELS]
    file_exclude_patterns = DEFAULT_EXCLUDE_PATTERNS + [
        pattern for pattern in exclude if pattern not in DEFAULT_EXCLUDE_PATTERNS
    ]

    try:
        module_targets, excluded_count = discover_modules(
            project_root,
            exclude_patterns=file_exclude_patterns,
            return_excluded_count=True,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if not module_targets:
        console.print("[red]No Python modules found for scanning.[/red]")
        raise typer.Exit(code=1)

    payload = scan_modules(
        project_root=project_root,
        module_targets=module_targets,
        threshold_ms=threshold_ms,
        threshold_mb=threshold_mb,
        exclusions=effective_exclusions,
        python_executable=runtime_python,
        scan_env=scan_env,
    )

    console.print(f"[dim]Runtime Python: {runtime_python}[/dim]")
    if env_source is not None:
        console.print(f"[dim]Loaded env vars from: {env_source}[/dim]")
    if excluded_count > 0:
        console.print(f"[dim]Excluded modules/files: {excluded_count} (patterns: {', '.join(file_exclude_patterns)})[/dim]")

    sorted_modules = _sort_modules(payload.modules, TopSort.TIME)
    render_modules_table(sorted_modules, title="ColdPy Scan Report")
    print_summary(payload)

    if not no_cache:
        write_cache(payload)

    if json_output is not None:
        try:
            write_json_report(payload, json_output)
        except OSError as exc:
            console.print(f"[red]Failed to write JSON report: {exc}[/red]")
            raise typer.Exit(code=1) from exc

    if payload.summary.scanned_modules == 0:
        raise typer.Exit(code=1)


@app.command()
def top(
    n: int = typer.Argument(10, min=1),
    sort: str = typer.Option(TopSort.TIME, "--sort", help="Sort by time or memory."),
    threshold_ms: float = typer.Option(DEFAULT_THRESHOLD_MS, "--threshold-ms"),
    threshold_mb: float = typer.Option(DEFAULT_THRESHOLD_MB, "--threshold-mb"),
) -> None:
    """Show top heavy imports from the latest cache."""
    if sort not in {TopSort.TIME, TopSort.MEMORY}:
        raise typer.BadParameter("Sort must be one of: time, memory")

    if threshold_ms < 0 or threshold_mb < 0:
        raise typer.BadParameter("Threshold values must be >= 0")

    try:
        payload: ScanPayload = read_cache()
    except CacheError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    filtered = _filter_successful(payload.modules, threshold_ms=threshold_ms, threshold_mb=threshold_mb)
    ranked = _sort_modules(filtered, sort)[:n]

    if not ranked:
        console.print("[yellow]No modules match the requested thresholds.[/yellow]")
        raise typer.Exit(code=0)

    render_modules_table(ranked, title="ColdPy Top Imports")
