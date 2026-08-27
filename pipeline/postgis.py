from __future__ import annotations

import json
from collections.abc import Sequence

from sqlalchemy import Engine, text

from pipeline.adapters.city_owned_land import CityOwnedLandRecord
from pipeline.provenance import IngestionRun

CREATE_SCHEMA = "CREATE SCHEMA IF NOT EXISTS raw"
CREATE_PUBLISHED = """
CREATE TABLE IF NOT EXISTS raw.public_land_inventory (
    source_key text NOT NULL,
    source_record_id text NOT NULL,
    pin text,
    owner_name text,
    original_owner text,
    address text,
    property_status text,
    acquired_at timestamptz,
    disposed_at timestamptz,
    properties jsonb NOT NULL,
    geom_4326 geometry(Geometry, 4326),
    geom_3435 geometry(Geometry, 3435),
    source_run_id uuid NOT NULL,
    source_updated_at timestamptz,
    fetched_at timestamptz NOT NULL,
    response_checksum text NOT NULL,
    PRIMARY KEY (source_key, source_record_id)
)
"""
CREATE_STAGING = """
CREATE TEMP TABLE public_land_inventory_staging (
    source_key text NOT NULL,
    source_record_id text NOT NULL,
    pin text,
    owner_name text,
    original_owner text,
    address text,
    property_status text,
    acquired_at timestamptz,
    disposed_at timestamptz,
    properties jsonb NOT NULL,
    geom_4326_wkb bytea,
    geom_3435_wkb bytea,
    source_run_id uuid NOT NULL,
    source_updated_at timestamptz,
    fetched_at timestamptz NOT NULL,
    response_checksum text NOT NULL
) ON COMMIT DROP
"""
INSERT_STAGING = """
INSERT INTO public_land_inventory_staging (
    source_key, source_record_id, pin, owner_name, original_owner, address,
    property_status, acquired_at, disposed_at, properties, geom_4326_wkb,
    geom_3435_wkb, source_run_id, source_updated_at, fetched_at, response_checksum
) VALUES (
    :source_key, :source_record_id, :pin, :owner_name, :original_owner, :address,
    :property_status, :acquired_at, :disposed_at, CAST(:properties AS jsonb),
    :geom_4326_wkb, :geom_3435_wkb, :source_run_id, :source_updated_at,
    :fetched_at, :response_checksum
)
"""
PUBLISH_STAGING = """
INSERT INTO raw.public_land_inventory (
    source_key, source_record_id, pin, owner_name, original_owner, address,
    property_status, acquired_at, disposed_at, properties, geom_4326, geom_3435,
    source_run_id, source_updated_at, fetched_at, response_checksum
)
SELECT
    source_key, source_record_id, pin, owner_name, original_owner, address,
    property_status, acquired_at, disposed_at, properties,
    CASE WHEN geom_4326_wkb IS NULL THEN NULL ELSE ST_GeomFromWKB(geom_4326_wkb, 4326) END,
    CASE WHEN geom_3435_wkb IS NULL THEN NULL ELSE ST_GeomFromWKB(geom_3435_wkb, 3435) END,
    source_run_id, source_updated_at, fetched_at, response_checksum
FROM public_land_inventory_staging
"""


class PostGISPublisher:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def publish_city_owned_land(
        self, records: Sequence[CityOwnedLandRecord], run: IngestionRun
    ) -> int:
        if not records:
            raise ValueError("refusing to publish an empty source release")
        source_keys = {record.source_key for record in records}
        if source_keys != {run.source_key}:
            raise ValueError("record source keys do not match the ingestion run")

        parameters = [
            {
                "source_key": record.source_key,
                "source_record_id": record.source_record_id,
                "pin": record.pin,
                "owner_name": record.owner_name,
                "original_owner": record.original_owner,
                "address": record.address,
                "property_status": record.property_status,
                "acquired_at": record.acquired_at,
                "disposed_at": record.disposed_at,
                "properties": json.dumps(record.properties, default=str, sort_keys=True),
                "geom_4326_wkb": record.geometry_4326.wkb if record.geometry_4326 else None,
                "geom_3435_wkb": record.geometry_3435.wkb if record.geometry_3435 else None,
                "source_run_id": run.run_id,
                "source_updated_at": run.source_updated_at,
                "fetched_at": run.fetched_at,
                "response_checksum": run.response_checksum,
            }
            for record in records
        ]

        with self.engine.begin() as connection:
            connection.execute(text(CREATE_SCHEMA))
            connection.execute(text(CREATE_PUBLISHED))
            connection.execute(text(CREATE_STAGING))
            connection.execute(text(INSERT_STAGING), parameters)
            staged_count = connection.execute(
                text("SELECT count(*) FROM public_land_inventory_staging")
            ).scalar_one()
            if staged_count != len(records):
                raise RuntimeError(
                    f"staging count mismatch: expected {len(records)}, observed {staged_count}"
                )
            connection.execute(
                text("DELETE FROM raw.public_land_inventory WHERE source_key = :source_key"),
                {"source_key": run.source_key},
            )
            connection.execute(text(PUBLISH_STAGING))
        return len(records)
