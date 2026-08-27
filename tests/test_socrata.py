import asyncio
import json
import logging
from datetime import UTC, datetime

import httpx
import pytest

from pipeline.socrata import SocrataClient, SocrataQuery


def test_query_builds_deterministic_incremental_parameters() -> None:
    query = SocrataQuery(
        select=("id", "pin"),
        order_by=("id",),
        where="property_status = 'Available'",
        incremental_field="updated_at",
        incremental_value=datetime(2026, 8, 27, tzinfo=UTC),
        page_size=500,
    )

    assert query.parameters(1_000) == {
        "$select": "id,pin",
        "$order": "id",
        "$limit": 500,
        "$offset": 1_000,
        "$where": "(property_status = 'Available') AND (updated_at > '2026-08-27T00:00:00Z')",
    }


def test_client_paginates_and_never_logs_token(caplog: pytest.LogCaptureFixture) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/views/abcd-1234":
            return httpx.Response(
                200,
                json={
                    "rowsUpdatedAt": 1_787_827_200,
                    "columns": [
                        {"fieldName": "id", "dataTypeName": "text"},
                        {"fieldName": "pin", "dataTypeName": "text"},
                    ],
                },
            )
        offset = request.url.params["$offset"]
        page = [{"id": "1"}, {"id": "2"}] if offset == "0" else [{"id": "3"}]
        return httpx.Response(200, content=json.dumps(page).encode())

    async def fetch() -> object:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as http_client:
            client = SocrataClient("data.example.gov", app_token="secret-token", client=http_client)
            return await client.fetch(
                "abcd-1234",
                SocrataQuery(select=("id", "pin"), order_by=("id",), page_size=2),
            )

    with caplog.at_level(logging.INFO):
        result = asyncio.run(fetch())

    assert [record["id"] for record in result.records] == ["1", "2", "3"]
    assert len(result.raw_pages) == 2
    assert requests[1].url.params["$order"] == "id"
    assert requests[2].url.params["$offset"] == "2"
    assert all(request.headers["X-App-Token"] == "secret-token" for request in requests)
    assert "secret-token" not in caplog.text


def test_query_requires_deterministic_order() -> None:
    with pytest.raises(ValueError, match="order_by"):
        SocrataQuery(select=("id",), order_by=())


def test_client_retries_transient_server_errors() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        if request.url.path == "/api/views/abcd-1234":
            attempts += 1
            if attempts == 1:
                return httpx.Response(503, json={"error": "temporarily unavailable"})
            return httpx.Response(200, json={"columns": []})
        return httpx.Response(200, json=[])

    async def fetch() -> object:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as http_client:
            client = SocrataClient(
                "data.example.gov",
                client=http_client,
                max_attempts=2,
            )
            return await client.fetch(
                "abcd-1234",
                SocrataQuery(select=("id",), order_by=("id",)),
            )

    result = asyncio.run(fetch())

    assert attempts == 2
    assert result.records == ()
