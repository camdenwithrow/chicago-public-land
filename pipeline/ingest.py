from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

from sqlalchemy import create_engine

from pipeline.adapters.city_owned_land import CityOwnedLandAdapter
from pipeline.config import PipelineSettings
from pipeline.postgis import PostGISPublisher
from pipeline.provenance import ProvenanceStore, latest_runs_by_source, load_ingestion_runs
from pipeline.quality import QualitySummary, count_change, write_quality_summary, write_quarantine
from pipeline.socrata import SocrataClient
from pipeline.source_registry import load_source_registry

LOGGER = logging.getLogger(__name__)


class IngestionQualityError(RuntimeError):
    """Raised after audit artifacts are saved but before an unsafe release is published."""


@dataclass(frozen=True)
class IngestionOutcome:
    run_id: str
    rows_read: int
    rows_written: int
    published: bool
    quality_summary: QualitySummary


async def ingest_city_owned_land(
    settings: PipelineSettings, *, publish: bool = True, page_size: int = 10_000
) -> IngestionOutcome:
    registry = load_source_registry()
    source = registry.by_key("chicago_city_owned_land")
    domain = urlparse(source.fetch_url).netloc
    if not domain:
        raise ValueError(f"source has no fetch domain: {source.key}")

    runs_root = settings.processed_data_dir / "provenance" / "runs"
    previous_runs = latest_runs_by_source(load_ingestion_runs(runs_root))
    previous = previous_runs.get(source.key)
    app_token = (
        settings.socrata_app_token.get_secret_value() if settings.socrata_app_token else None
    )
    async with SocrataClient(domain, app_token=app_token) as client:
        adapter_result = await CityOwnedLandAdapter(source, client, page_size=page_size).extract()

    store = ProvenanceStore(settings.raw_data_dir, runs_root)
    run = store.record_response(
        source=source,
        response=adapter_result.source_result.raw_snapshot,
        row_count=len(adapter_result.source_result.records),
        pipeline_version=settings.pipeline_version,
        source_updated_at=adapter_result.source_result.source_updated_at,
        extension="jsonl",
    )
    change_ratio, major_change = count_change(
        len(adapter_result.source_result.records),
        previous.row_count if previous else None,
        threshold=settings.major_count_change_threshold,
    )
    summary = QualitySummary(
        source_key=source.key,
        run_id=run.run_id,
        rows_read=len(adapter_result.source_result.records),
        rows_written=len(adapter_result.records),
        missing_ids=adapter_result.missing_ids,
        missing_geometry=adapter_result.missing_geometry,
        invalid_geometry=adapter_result.invalid_geometry,
        repaired_geometry=adapter_result.repaired_geometry,
        duplicates=adapter_result.duplicates,
        unmatched_joins=adapter_result.unmatched_joins,
        previous_row_count=previous.row_count if previous else None,
        row_count_change_ratio=change_ratio,
        major_count_change=major_change,
    )
    write_quality_summary(summary, settings.processed_data_dir / "quality")
    write_quarantine(
        list(adapter_result.quarantined),
        run.run_id,
        settings.processed_data_dir / "quarantine" / source.key,
    )

    if summary.rows_read == 0:
        raise IngestionQualityError("source returned zero rows; release was not published")
    if summary.major_count_change:
        raise IngestionQualityError(
            f"source row count changed by {summary.row_count_change_ratio:.1%}; "
            "release was not published"
        )
    if not adapter_result.records:
        raise IngestionQualityError("no valid records remained; release was not published")

    published = False
    if publish:
        engine = create_engine(settings.database_url)
        try:
            PostGISPublisher(engine).publish_city_owned_land(adapter_result.records, run)
        finally:
            engine.dispose()
        published = True

    LOGGER.info(
        "ingestion complete source=%s run=%s read=%d written=%d published=%s",
        source.key,
        run.run_id,
        summary.rows_read,
        summary.rows_written,
        published,
    )
    return IngestionOutcome(
        run_id=run.run_id,
        rows_read=summary.rows_read,
        rows_written=summary.rows_written,
        published=published,
        quality_summary=summary,
    )
