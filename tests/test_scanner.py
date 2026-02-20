from pathlib import Path

from coldpy.discovery import discover_modules
from coldpy.scanner import scan_modules


FIXTURE = Path(__file__).parent / "fixtures" / "sample_project"


def test_scan_modules_collects_success_and_errors() -> None:
    targets = discover_modules(FIXTURE)
    payload = scan_modules(FIXTURE, targets, threshold_ms=1.0, threshold_mb=0.001)

    by_name = {module.name: module for module in payload.modules}

    assert payload.summary.total_modules == len(targets)
    assert payload.summary.scanned_modules >= 2
    assert payload.summary.failed_modules >= 1

    assert by_name["pkg.fast"].status == "ok"
    assert by_name["pkg.fast"].import_time_ms is not None
    assert by_name["pkg.fast"].memory_mb is not None

    assert by_name["pkg.broken"].status == "error"
    assert by_name["pkg.broken"].error


def test_scan_payload_schema_shape() -> None:
    targets = discover_modules(FIXTURE)
    payload = scan_modules(FIXTURE, targets)
    raw = payload.to_dict()

    assert raw["schema_version"] == "1.0"
    assert "generated_at" in raw
    assert "project_root" in raw
    assert set(raw["summary"].keys()) == {"total_modules", "scanned_modules", "failed_modules"}
    assert isinstance(raw["modules"], list)
