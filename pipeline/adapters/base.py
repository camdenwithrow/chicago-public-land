from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pipeline.socrata import SocrataResult


@dataclass(frozen=True)
class AdapterResult[RecordT]:
    source_result: SocrataResult
    records: tuple[RecordT, ...]
    quarantined: tuple[dict[str, object], ...]
    missing_ids: int
    missing_geometry: int
    invalid_geometry: int
    repaired_geometry: int
    duplicates: int
    unmatched_joins: int = 0


class SourceAdapter[RecordT](Protocol):
    async def extract(self) -> AdapterResult[RecordT]: ...
