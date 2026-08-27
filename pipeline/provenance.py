from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from pipeline.source_registry import Source

SAFE_EXTENSION = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


@dataclass(frozen=True)
class IngestionRun:
    run_id: str
    source_key: str
    source_name: str
    source_url: str
    source_updated_at: datetime | None
    fetched_at: datetime
    row_count: int
    response_checksum: str
    pipeline_version: str
    snapshot_path: str

    def to_json(self) -> str:
        record = asdict(self)
        record["source_updated_at"] = (
            self.source_updated_at.isoformat() if self.source_updated_at else None
        )
        record["fetched_at"] = self.fetched_at.isoformat()
        return json.dumps(record, indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_json(cls, value: str) -> IngestionRun:
        record = json.loads(value)
        return cls(
            run_id=record["run_id"],
            source_key=record["source_key"],
            source_name=record["source_name"],
            source_url=record["source_url"],
            source_updated_at=(
                datetime.fromisoformat(record["source_updated_at"])
                if record["source_updated_at"]
                else None
            ),
            fetched_at=datetime.fromisoformat(record["fetched_at"]),
            row_count=record["row_count"],
            response_checksum=record["response_checksum"],
            pipeline_version=record["pipeline_version"],
            snapshot_path=record["snapshot_path"],
        )


def _require_aware(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")


class ProvenanceStore:
    """Persist immutable source bytes and one audit manifest for every fetch."""

    def __init__(self, raw_root: Path, runs_root: Path) -> None:
        self.raw_root = raw_root
        self.runs_root = runs_root

    def record_response(
        self,
        *,
        source: Source,
        response: bytes,
        row_count: int,
        pipeline_version: str,
        source_updated_at: datetime | None = None,
        fetched_at: datetime | None = None,
        extension: str = "json",
        run_id: str | None = None,
    ) -> IngestionRun:
        if row_count < 0:
            raise ValueError("row_count cannot be negative")
        if not pipeline_version.strip():
            raise ValueError("pipeline_version cannot be empty")
        if not SAFE_EXTENSION.fullmatch(extension):
            raise ValueError("extension contains unsafe characters")
        if source_updated_at is not None:
            _require_aware(source_updated_at, "source_updated_at")

        fetched = fetched_at or datetime.now(UTC)
        _require_aware(fetched, "fetched_at")
        identifier = run_id or str(uuid.uuid4())
        uuid.UUID(identifier)

        digest = hashlib.sha256(response).hexdigest()
        checksum = f"sha256:{digest}"
        snapshot_path = self.raw_root / source.key / digest[:2] / f"{digest}.{extension}"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with snapshot_path.open("xb") as snapshot_file:
                snapshot_file.write(response)
        except FileExistsError:
            if hashlib.sha256(snapshot_path.read_bytes()).hexdigest() != digest:
                raise RuntimeError(
                    f"immutable snapshot checksum conflict: {snapshot_path}"
                ) from None

        run = IngestionRun(
            run_id=identifier,
            source_key=source.key,
            source_name=source.name,
            source_url=source.fetch_url or source.landing_url,
            source_updated_at=source_updated_at,
            fetched_at=fetched,
            row_count=row_count,
            response_checksum=checksum,
            pipeline_version=pipeline_version,
            snapshot_path=str(snapshot_path),
        )
        self.runs_root.mkdir(parents=True, exist_ok=True)
        manifest_path = self.runs_root / f"{identifier}.json"
        with manifest_path.open("x", encoding="utf-8") as manifest_file:
            manifest_file.write(run.to_json())
        return run


def load_ingestion_runs(runs_root: Path) -> tuple[IngestionRun, ...]:
    if not runs_root.exists():
        return ()
    return tuple(
        IngestionRun.from_json(path.read_text(encoding="utf-8"))
        for path in sorted(runs_root.glob("*.json"))
    )


def latest_runs_by_source(runs: tuple[IngestionRun, ...]) -> dict[str, IngestionRun]:
    latest: dict[str, IngestionRun] = {}
    for run in runs:
        current = latest.get(run.source_key)
        if current is None or run.fetched_at > current.fetched_at:
            latest[run.source_key] = run
    return latest
