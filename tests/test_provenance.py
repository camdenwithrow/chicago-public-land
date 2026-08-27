from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from pipeline.provenance import ProvenanceStore, latest_runs_by_source, load_ingestion_runs
from pipeline.source_registry import load_source_registry


def test_response_and_run_metadata_are_persisted_immutably(tmp_path: Path) -> None:
    source = load_source_registry().by_key("chicago_city_owned_land")
    store = ProvenanceStore(tmp_path / "raw", tmp_path / "runs")
    fetched_at = datetime(2026, 8, 27, 15, 30, tzinfo=UTC)
    source_updated_at = datetime(2026, 8, 26, 12, tzinfo=UTC)

    first = store.record_response(
        source=source,
        response=b'[{"id":"1"}]',
        row_count=1,
        source_updated_at=source_updated_at,
        fetched_at=fetched_at,
        pipeline_version="v1.0.0",
        run_id="00000000-0000-4000-8000-000000000001",
    )
    second = store.record_response(
        source=source,
        response=b'[{"id":"1"}]',
        row_count=1,
        source_updated_at=source_updated_at,
        fetched_at=fetched_at + timedelta(hours=1),
        pipeline_version="v1.0.0",
        run_id="00000000-0000-4000-8000-000000000002",
    )

    assert first.response_checksum.startswith("sha256:")
    assert first.snapshot_path == second.snapshot_path
    assert Path(first.snapshot_path).read_bytes() == b'[{"id":"1"}]'
    runs = load_ingestion_runs(tmp_path / "runs")
    assert len(runs) == 2
    assert latest_runs_by_source(runs)[source.key].run_id == second.run_id


def test_run_metadata_rejects_naive_timestamps(tmp_path: Path) -> None:
    source = load_source_registry().by_key("chicago_city_owned_land")
    store = ProvenanceStore(tmp_path / "raw", tmp_path / "runs")

    with pytest.raises(ValueError, match="timezone"):
        store.record_response(
            source=source,
            response=b"[]",
            row_count=0,
            fetched_at=datetime(2026, 8, 27),
            pipeline_version="v1.0.0",
        )
