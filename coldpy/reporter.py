from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from rich.console import Console
from rich.table import Table

from coldpy.models import ModuleResult, ScanPayload

console = Console()


def _format_value(value: float | None) -> str:
    return "-" if value is None else f"{value:.3f}"


def render_modules_table(modules: Iterable[ModuleResult], title: str = "ColdPy Report") -> None:
    table = Table(title=title)
    table.add_column("Module", justify="left")
    table.add_column("Import Time (ms)", justify="right")
    table.add_column("Memory (MB)", justify="right")
    table.add_column("Status", justify="left")
    table.add_column("Notes", justify="left")

    for module in modules:
        table.add_row(
            module.name,
            _format_value(module.import_time_ms),
            _format_value(module.memory_mb),
            module.status,
            "; ".join(module.notes) if module.notes else (module.error or ""),
        )

    console.print(table)


def print_summary(payload: ScanPayload) -> None:
    summary = payload.summary
    console.print(
        f"Scanned: {summary.scanned_modules}/{summary.total_modules} modules, "
        f"Failed: {summary.failed_modules}"
    )


def write_json_report(payload: ScanPayload, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(payload.to_dict(), indent=2), encoding="utf-8")
