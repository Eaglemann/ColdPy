from __future__ import annotations

import json
from pathlib import Path

from coldpy.models import ScanPayload

CACHE_DIR_NAME = ".coldpy"
CACHE_FILE_NAME = "cache.json"


class CacheError(Exception):
    pass


def cache_path(base_dir: Path | None = None) -> Path:
    base = base_dir or Path.cwd()
    return base / CACHE_DIR_NAME / CACHE_FILE_NAME


def write_cache(payload: ScanPayload, base_dir: Path | None = None) -> Path:
    target = cache_path(base_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload.to_dict(), indent=2), encoding="utf-8")
    return target


def read_cache(base_dir: Path | None = None) -> ScanPayload:
    target = cache_path(base_dir)
    if not target.exists():
        raise CacheError("Cache not found. Run `coldpy scan <path>` first.")

    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CacheError(f"Cache file is not valid JSON: {target}") from exc

    try:
        return ScanPayload.from_dict(raw)
    except Exception as exc:  # pragma: no cover - defensive
        raise CacheError(f"Cache format is invalid: {target}") from exc
