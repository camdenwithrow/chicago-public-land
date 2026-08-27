import asyncio
import json
from datetime import UTC, datetime
from typing import Any

from pipeline.adapters.city_owned_land import CityOwnedLandAdapter
from pipeline.socrata import SocrataResult
from pipeline.source_registry import load_source_registry


class StubSocrataClient:
    def __init__(self, result: SocrataResult) -> None:
        self.result = result
        self.dataset_id: str | None = None
        self.query: object | None = None

    async def fetch(self, dataset_id: str, query: object) -> SocrataResult:
        self.dataset_id = dataset_id
        self.query = query
        return self.result


def test_adapter_preserves_lineage_and_quarantines_bad_records() -> None:
    source = load_source_registry().by_key("chicago_city_owned_land")
    valid = {
        "id": "source-1",
        "pin": "12-34-567-890-0000",
        "address": "100 TEST ST",
        "managing_organization": "City of Chicago – DPD",
        "property_status": "Available",
        "date_of_acquisition": "2020-01-01T00:00:00.000",
        "latitude": "41.88",
        "longitude": "-87.63",
    }
    records: list[dict[str, Any]] = [
        valid,
        {**valid, "id": "source-1"},
        {**valid, "id": "source-2", "latitude": "not-a-number"},
        {**valid, "id": "source-3", "latitude": None, "longitude": None},
        {**valid, "id": ""},
    ]
    schema = {
        field: "text"
        for field in ("id", "pin", "managing_organization", "property_status", "last_update")
    }
    result = SocrataResult(
        records=tuple(records),
        raw_pages=(json.dumps(records).encode(),),
        observed_schema=schema,
        source_updated_at=datetime(2026, 8, 27, tzinfo=UTC),
    )
    client = StubSocrataClient(result)

    adapter_result = asyncio.run(CityOwnedLandAdapter(source, client, page_size=2).extract())  # type: ignore[arg-type]

    assert len(adapter_result.records) == 2
    record = adapter_result.records[0]
    assert record.source_record_id == "source-1"
    assert record.pin == "12345678900000"
    assert record.original_owner == "City of Chicago – DPD"
    assert record.owner_name == "CITY OF CHICAGO DPD"
    assert record.geometry_4326.geom_type == "Point"
    assert adapter_result.duplicates == 1
    assert adapter_result.invalid_geometry == 1
    assert adapter_result.missing_geometry == 1
    assert adapter_result.missing_ids == 1
    assert len(adapter_result.quarantined) == 3
    assert adapter_result.records[1].geometry_4326 is None
    assert client.dataset_id == "aksk-kvfp"
