from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from apps.api.app.config import get_settings
from pipeline.provenance import latest_runs_by_source, load_ingestion_runs
from pipeline.source_registry import load_source_registry


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


class SourceMetadataResponse(BaseModel):
    key: str
    name: str
    publisher: str
    source_url: str
    license: str
    status: str
    source_updated_at: datetime | None
    fetched_at: datetime | None


class MetadataResponse(BaseModel):
    methodology_version: str
    registry_version: str
    tracker_processed_at: datetime | None
    sources: list[SourceMetadataResponse]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    get_settings()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API for explainable screening of publicly owned Chicago land.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["operations"])
async def health() -> HealthResponse:
    """Return process health. Database readiness will be added with persistence."""

    return HealthResponse(status="ok", service=settings.app_name, version=app.version)


@app.get("/meta", response_model=MetadataResponse, tags=["operations"])
async def metadata() -> MetadataResponse:
    """Return source attribution and the independently tracked freshness dates."""

    registry = load_source_registry()
    runs = load_ingestion_runs(settings.provenance_runs_dir)
    latest = latest_runs_by_source(runs)
    processed_at = max((run.fetched_at for run in runs), default=None)
    sources = []
    for source in registry.sources:
        run = latest.get(source.key)
        sources.append(
            SourceMetadataResponse(
                key=source.key,
                name=source.name,
                publisher=source.publisher,
                source_url=source.landing_url,
                license=source.license,
                status=source.status,
                source_updated_at=run.source_updated_at if run else None,
                fetched_at=run.fetched_at if run else None,
            )
        )
    return MetadataResponse(
        methodology_version="v1.0.0",
        registry_version=registry.version,
        tracker_processed_at=processed_at,
        sources=sources,
    )
