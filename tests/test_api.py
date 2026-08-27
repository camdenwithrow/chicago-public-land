import asyncio
from pathlib import Path

from httpx import ASGITransport, AsyncClient, Response
from pytest import MonkeyPatch

from apps.api.app.main import app, settings


async def get_health() -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/health")


async def get_metadata() -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/meta")


def test_health() -> None:
    response = asyncio.run(get_health())

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Land to Homes API",
        "version": "0.1.0",
    }


def test_metadata_exposes_attribution_and_independent_dates(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "provenance_runs_dir", tmp_path / "runs")
    response = asyncio.run(get_metadata())

    assert response.status_code == 200
    payload = response.json()
    assert payload["methodology_version"] == "v1.0.0"
    assert payload["registry_version"] == "1.1.0"
    assert payload["tracker_processed_at"] is None
    city_land = next(
        source for source in payload["sources"] if source["key"] == "chicago_city_owned_land"
    )
    assert city_land == {
        "key": "chicago_city_owned_land",
        "name": "City-Owned Land Inventory",
        "publisher": "City of Chicago Department of Planning and Development",
        "source_url": "https://data.cityofchicago.org/d/aksk-kvfp",
        "license": "City of Chicago Data Portal Terms of Use",
        "status": "selected",
        "source_updated_at": None,
        "fetched_at": None,
    }
