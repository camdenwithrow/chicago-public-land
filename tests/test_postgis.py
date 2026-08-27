from datetime import UTC, datetime
from unittest.mock import MagicMock

from pyproj import Transformer
from shapely.geometry import Point
from shapely.ops import transform

from pipeline.adapters.city_owned_land import CityOwnedLandRecord
from pipeline.postgis import PostGISPublisher
from pipeline.provenance import IngestionRun


def test_postgis_publication_uses_one_transaction_and_atomic_replace() -> None:
    transformer = Transformer.from_crs(4326, 3435, always_xy=True)
    point = Point(-87.63, 41.88)
    record = CityOwnedLandRecord(
        source_key="chicago_city_owned_land",
        source_record_id="source-1",
        pin="12345678900000",
        owner_name="CITY OF CHICAGO",
        original_owner="City of Chicago",
        address="100 TEST ST",
        property_status="Available",
        acquired_at=None,
        disposed_at=None,
        geometry_4326=point,
        geometry_3435=transform(transformer.transform, point),
        properties={"id": "source-1"},
    )
    run = IngestionRun(
        run_id="00000000-0000-4000-8000-000000000001",
        source_key="chicago_city_owned_land",
        source_name="City-Owned Land Inventory",
        source_url="https://example.test/source",
        source_updated_at=datetime(2026, 8, 26, tzinfo=UTC),
        fetched_at=datetime(2026, 8, 27, tzinfo=UTC),
        row_count=1,
        response_checksum="sha256:abc",
        pipeline_version="v1.0.0",
        snapshot_path="data/raw/example.json",
    )
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value
    count_result = MagicMock()
    count_result.scalar_one.return_value = 1
    connection.execute.side_effect = [
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        count_result,
        MagicMock(),
        MagicMock(),
    ]

    written = PostGISPublisher(engine).publish_city_owned_land([record], run)

    assert written == 1
    engine.begin.assert_called_once_with()
    statements = [str(call.args[0]) for call in connection.execute.call_args_list]
    assert any("TEMP TABLE public_land_inventory_staging" in sql for sql in statements)
    assert any("DELETE FROM raw.public_land_inventory" in sql for sql in statements)
    assert "ST_GeomFromWKB" in statements[-1]
