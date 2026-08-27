from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class QualitySummary:
    source_key: str
    run_id: str
    rows_read: int
    rows_written: int
    missing_ids: int
    missing_geometry: int
    invalid_geometry: int
    repaired_geometry: int
    duplicates: int
    unmatched_joins: int
    previous_row_count: int | None
    row_count_change_ratio: float | None
    major_count_change: bool

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True) + "\n"


def count_change(
    current: int, previous: int | None, *, threshold: float = 0.2
) -> tuple[float | None, bool]:
    if previous is None or previous == 0:
        return None, False
    ratio = (current - previous) / previous
    return ratio, abs(ratio) > threshold


def write_quality_summary(summary: QualitySummary, root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{summary.run_id}.json"
    with path.open("x", encoding="utf-8") as summary_file:
        summary_file.write(summary.to_json())
    return path


def write_quarantine(records: list[dict[str, object]], run_id: str, root: Path) -> Path | None:
    if not records:
        return None
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{run_id}.jsonl"
    with path.open("x", encoding="utf-8") as quarantine_file:
        for record in records:
            quarantine_file.write(json.dumps(record, sort_keys=True, default=str) + "\n")
    return path
