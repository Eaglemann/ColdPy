from __future__ import annotations

import os
import sys
from pathlib import Path

DEFAULT_ENV_FILES = (".env", ".env.local")


def _absolute_no_symlink(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_absolute():
        return Path(os.path.abspath(str(expanded)))
    return Path(os.path.abspath(str(Path.cwd() / expanded)))


def resolve_python_executable(project_root: Path, requested_python: Path | None = None) -> Path:
    if requested_python is not None:
        candidate = _absolute_no_symlink(requested_python)
        if not candidate.exists() or not candidate.is_file():
            raise ValueError(f"Invalid python executable: {candidate}")
        return candidate

    candidates = [
        project_root / ".venv" / "bin" / "python",
        project_root / "venv" / "bin" / "python",
        project_root / "env" / "bin" / "python",
        project_root / ".venv" / "Scripts" / "python.exe",
        project_root / "venv" / "Scripts" / "python.exe",
        project_root / "env" / "Scripts" / "python.exe",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return _absolute_no_symlink(candidate)

    return _absolute_no_symlink(Path(sys.executable))


def _strip_wrapping_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_dotenv_file(path: Path) -> dict[str, str]:
    env_values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export ") :]

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue

        parsed_value = _strip_wrapping_quotes(value.strip())
        env_values[key] = parsed_value

    return env_values


def load_project_env(project_root: Path, env_file: Path | None = None) -> tuple[dict[str, str], Path | None]:
    if env_file is not None:
        resolved = env_file.resolve()
        if not resolved.exists() or not resolved.is_file():
            raise ValueError(f"Invalid env file: {resolved}")
        return parse_dotenv_file(resolved), resolved

    for name in DEFAULT_ENV_FILES:
        candidate = project_root / name
        if candidate.exists() and candidate.is_file():
            return parse_dotenv_file(candidate), candidate

    return {}, None


def build_scan_environment(extra_env: dict[str, str] | None = None) -> dict[str, str]:
    merged = os.environ.copy()
    if extra_env:
        merged.update(extra_env)
    return merged
