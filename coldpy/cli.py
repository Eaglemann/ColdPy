from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from coldpy.cache import CacheError, read_cache, write_cache
from coldpy.discovery import EXCLUSION_LABELS, discover_modules
from coldpy.models import ModuleResult, ScanPayload
from coldpy.reporter import print_summary, render_modules_table, write_json_report
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
    path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    json_output: Path | None = typer.Option(None, "--json", help="Write JSON report to file."),
    threshold_ms: float = typer.Option(DEFAULT_THRESHOLD_MS, "--threshold-ms"),
    threshold_mb: float = typer.Option(DEFAULT_THRESHOLD_MB, "--threshold-mb"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Do not write .coldpy/cache.json"),
) -> None:
    """Scan a Python project for import time and memory cost."""
    if threshold_ms < 0 or threshold_mb < 0:
        raise typer.BadParameter("Threshold values must be >= 0")

    project_root = path.resolve()

    try:
        module_targets = discover_modules(project_root)
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
        exclusions=EXCLUSION_LABELS,
    )

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
