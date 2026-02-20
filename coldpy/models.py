from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "1.0"
HEAVY_IMPORT_NOTE = "Heavy import; consider lazy loading or reducing transitive dependencies."


@dataclass
class ModuleResult:
    name: str
    file: str
    import_time_ms: float | None
    memory_mb: float | None
    status: str
    error: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScanSettings:
    threshold_ms: float
    threshold_mb: float
    exclusions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScanSummary:
    total_modules: int
    scanned_modules: int
    failed_modules: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScanPayload:
    project_root: str
    settings: ScanSettings
    summary: ScanSummary
    modules: list[ModuleResult]
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "project_root": self.project_root,
            "settings": self.settings.to_dict(),
            "summary": self.summary.to_dict(),
            "modules": [module.to_dict() for module in self.modules],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ScanPayload":
        settings = ScanSettings(**payload["settings"])
        summary = ScanSummary(**payload["summary"])
        modules = [ModuleResult(**module) for module in payload["modules"]]
        return cls(
            schema_version=payload.get("schema_version", SCHEMA_VERSION),
            generated_at=payload.get("generated_at", datetime.now(timezone.utc).isoformat()),
            project_root=payload["project_root"],
            settings=settings,
            summary=summary,
            modules=modules,
        )
