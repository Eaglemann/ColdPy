from pathlib import Path

import pytest

from coldpy.cache import CacheError, read_cache, write_cache
from coldpy.discovery import discover_modules
from coldpy.scanner import scan_modules


FIXTURE = Path(__file__).parent / "fixtures" / "sample_project"


def test_write_and_read_cache_round_trip(tmp_path: Path) -> None:
    payload = scan_modules(FIXTURE, discover_modules(FIXTURE))
    written = write_cache(payload, base_dir=tmp_path)
    assert written.exists()

    loaded = read_cache(base_dir=tmp_path)
    assert loaded.schema_version == "1.0"
    assert loaded.summary.total_modules == payload.summary.total_modules


def test_read_cache_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(CacheError) as exc:
        read_cache(base_dir=tmp_path)

    assert "Run `coldpy scan <path>` first" in str(exc.value)
