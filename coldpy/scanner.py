from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from coldpy.discovery import ModuleTarget
from coldpy.models import HEAVY_IMPORT_NOTE, ModuleResult, ScanPayload, ScanSettings, ScanSummary

DEFAULT_THRESHOLD_MS = 100.0
DEFAULT_THRESHOLD_MB = 50.0


def _measure_module(
    module_name: str,
    project_root: Path,
    python_executable: Path | None = None,
    scan_env: dict[str, str] | None = None,
) -> dict[str, object]:
    probe_code = r'''
import importlib
import json
import sys
import time
import tracemalloc

module_name = sys.argv[1]
project_root = sys.argv[2]

sys.path.insert(0, project_root)
tracemalloc.start()
start = time.perf_counter()

try:
    importlib.import_module(module_name)
    elapsed_ms = (time.perf_counter() - start) * 1000
    current, peak = tracemalloc.get_traced_memory()
    output = {
        "status": "ok",
        "import_time_ms": elapsed_ms,
        "memory_mb": peak / (1024 * 1024),
    }
except Exception as exc:
    output = {
        "status": "error",
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }
finally:
    tracemalloc.stop()

print(json.dumps(output))
'''

    executable = str(python_executable or Path(sys.executable))
    completed = subprocess.run(
        [executable, "-c", probe_code, module_name, str(project_root)],
        text=True,
        capture_output=True,
        check=False,
        cwd=str(project_root),
        env=scan_env,
    )

    if completed.returncode != 0 and not completed.stdout.strip():
        return {
            "status": "error",
            "error_type": "SubprocessError",
            "error_message": completed.stderr.strip() or "Child process exited unexpectedly.",
        }

    stdout = completed.stdout.strip().splitlines()
    if not stdout:
        return {
            "status": "error",
            "error_type": "ParseError",
            "error_message": "No scanner output received from child process.",
        }

    try:
        return json.loads(stdout[-1])
    except json.JSONDecodeError:
        return {
            "status": "error",
            "error_type": "ParseError",
            "error_message": f"Invalid scanner output: {stdout[-1]}",
        }


def scan_modules(
    project_root: Path,
    module_targets: list[ModuleTarget],
    threshold_ms: float = DEFAULT_THRESHOLD_MS,
    threshold_mb: float = DEFAULT_THRESHOLD_MB,
    exclusions: list[str] | None = None,
    python_executable: Path | None = None,
    scan_env: dict[str, str] | None = None,
) -> ScanPayload:
    modules: list[ModuleResult] = []

    for target in module_targets:
        result = _measure_module(
            target.name,
            project_root,
            python_executable=python_executable,
            scan_env=scan_env,
        )
        if result.get("status") == "ok":
            import_time_ms = float(result["import_time_ms"])
            memory_mb = float(result["memory_mb"])
            notes: list[str] = []
            if import_time_ms > threshold_ms or memory_mb > threshold_mb:
                notes.append(HEAVY_IMPORT_NOTE)

            modules.append(
                ModuleResult(
                    name=target.name,
                    file=str(target.file),
                    import_time_ms=round(import_time_ms, 3),
                    memory_mb=round(memory_mb, 3),
                    status="ok",
                    notes=notes,
                )
            )
        else:
            error_type = result.get("error_type", "ImportError")
            error_message = result.get("error_message", "Unknown import error")
            modules.append(
                ModuleResult(
                    name=target.name,
                    file=str(target.file),
                    import_time_ms=None,
                    memory_mb=None,
                    status="error",
                    error=f"{error_type}: {error_message}",
                    notes=[],
                )
            )

    scanned_modules = sum(1 for module in modules if module.status == "ok")
    failed_modules = len(modules) - scanned_modules
    summary = ScanSummary(
        total_modules=len(module_targets),
        scanned_modules=scanned_modules,
        failed_modules=failed_modules,
    )

    settings = ScanSettings(
        threshold_ms=threshold_ms,
        threshold_mb=threshold_mb,
        exclusions=exclusions or [],
    )

    return ScanPayload(
        project_root=str(project_root),
        settings=settings,
        summary=summary,
        modules=modules,
    )
