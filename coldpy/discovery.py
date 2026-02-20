from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

EXCLUDED_DIRS = {
    ".venv",
    "venv",
    "env",
    "site-packages",
    "__pycache__",
    ".git",
    "build",
    "dist",
    "tests",
}

DEFAULT_EXCLUDE_PATTERNS = [
    "alembic/**",
    "migrations/**",
    "**/alembic/**",
    "**/migrations/**",
]

EXCLUSION_LABELS = sorted(EXCLUDED_DIRS) + ["hidden.*", "test_*.py", "*_test.py"] + DEFAULT_EXCLUDE_PATTERNS


@dataclass(frozen=True)
class ModuleTarget:
    name: str
    file: Path


def _is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def _is_excluded_file(path: Path) -> bool:
    name = path.name
    return name.startswith("test_") or name.endswith("_test.py")


def _to_module_name(scan_root: Path, file_path: Path) -> str:
    relative = file_path.relative_to(scan_root)
    parts = list(relative.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = Path(parts[-1]).stem
    return ".".join(parts)


def _matches_exclude_patterns(relative_path: Path, exclude_patterns: list[str]) -> bool:
    path_str = str(relative_path)
    for pattern in exclude_patterns:
        if relative_path.match(pattern) or path_str.startswith(pattern.rstrip("/*")):
            return True
    return False


def discover_modules(
    scan_path: Path,
    exclude_patterns: list[str] | None = None,
    return_excluded_count: bool = False,
) -> list[ModuleTarget] | tuple[list[ModuleTarget], int]:
    if not scan_path.exists() or not scan_path.is_dir():
        raise ValueError(f"Invalid scan path: {scan_path}")

    module_targets: list[ModuleTarget] = []
    excluded_count = 0
    effective_patterns = exclude_patterns or DEFAULT_EXCLUDE_PATTERNS
    for file_path in sorted(scan_path.rglob("*.py")):
        relative = file_path.relative_to(scan_path)

        if _is_hidden(relative):
            excluded_count += 1
            continue

        if any(part in EXCLUDED_DIRS for part in relative.parts[:-1]):
            excluded_count += 1
            continue

        if _is_excluded_file(file_path):
            excluded_count += 1
            continue

        if _matches_exclude_patterns(relative, effective_patterns):
            excluded_count += 1
            continue

        module_name = _to_module_name(scan_path, file_path)
        if not module_name:
            continue

        module_targets.append(ModuleTarget(name=module_name, file=file_path))

    if return_excluded_count:
        return module_targets, excluded_count

    return module_targets
