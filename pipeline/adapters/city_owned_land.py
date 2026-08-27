from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from shapely.geometry.base import BaseGeometry

from pipeline.adapters.base import AdapterResult
from pipeline.geometry import parse_geometry, validate_and_project
from pipeline.normalization import (
    normalize_datetime,
    normalize_mapping,
    normalize_null,
    normalize_owner,
    normalize_pin,
)
from pipeline.schema import SchemaContract
from pipeline.socrata import SocrataClient, SocrataQuery
from pipeline.source_registry import Source


@dataclass(frozen=True)
class CityOwnedLandRecord:
    source_key: str
    source_record_id: str
    pin: str | None
    owner_name: str | None
    original_owner: str | None
    address: str | None
    property_status: str | None
    acquired_at: datetime | None
    disposed_at: datetime | None
    geometry_4326: BaseGeometry | None
    geometry_3435: BaseGeometry | None
    properties: dict[str, Any]


class CityOwnedLandAdapter:
    SELECT_FIELDS = (
        "id",
        "pin",
        "address",
        "managing_organization",
        "property_status",
        "date_of_acquisition",
        "date_of_disposition",
        "sq_ft",
        "square_footage_city_estimate",
        "zoning_classification",
        "community_area_number",
        "community_area_name",
        "last_update",
        "latitude",
        "longitude",
    )
    FIELD_TYPES = {
        "id": "text",
        "pin": "text",
        "managing_organization": "text",
        "property_status": "text",
        "last_update": "text",
    }

    def __init__(self, source: Source, client: SocrataClient, *, page_size: int = 10_000) -> None:
        if source.key != "chicago_city_owned_land":
            raise ValueError(f"unsupported source for CityOwnedLandAdapter: {source.key}")
        self.source = source
        self.client = client
        self.page_size = page_size

    async def extract(self) -> AdapterResult[CityOwnedLandRecord]:
        source_result = await self.client.fetch(
            self.source.dataset_id,
            SocrataQuery(
                select=self.SELECT_FIELDS,
                order_by=("id",),
                page_size=self.page_size,
            ),
        )
        SchemaContract.for_source(self.source, field_types=self.FIELD_TYPES).validate(
            source_result.observed_schema
        )

        records: list[CityOwnedLandRecord] = []
        quarantined: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        missing_ids = 0
        missing_geometry = 0
        invalid_geometry = 0
        repaired_geometry = 0
        duplicates = 0

        for raw_record in source_result.records:
            normalized = normalize_mapping(raw_record)
            source_id_value = normalize_null(normalized.get("id"))
            if source_id_value is None:
                missing_ids += 1
                quarantined.append({"reason": "missing_source_id", "record": raw_record})
                continue
            source_id = str(source_id_value)
            if source_id in seen_ids:
                duplicates += 1
                quarantined.append({"reason": "duplicate_source_id", "source_record_id": source_id})
                continue
            seen_ids.add(source_id)
            pin = normalize_pin(normalized.get("pin"))

            try:
                geometry = parse_geometry(
                    latitude=normalized.get("latitude"), longitude=normalized.get("longitude")
                )
                geometry_result = validate_and_project(geometry, expected="point")
            except (TypeError, ValueError) as error:
                invalid_geometry += 1
                quarantined.append(
                    {
                        "reason": f"geometry_parse_error:{error}",
                        "source_record_id": source_id,
                    }
                )
                continue
            if geometry_result.error:
                if geometry_result.error == "missing_geometry" and pin is not None:
                    missing_geometry += 1
                else:
                    invalid_geometry += 1
                    quarantined.append(
                        {
                            "reason": geometry_result.error,
                            "source_record_id": source_id,
                        }
                    )
                    continue
            repaired_geometry += int(geometry_result.repaired)
            if geometry_result.error is None and (
                geometry_result.geometry_4326 is None or geometry_result.geometry_3435 is None
            ):
                raise RuntimeError("validated geometry unexpectedly missing")

            owner_name, original_owner = normalize_owner(normalized.get("managing_organization"))
            try:
                acquired_at = normalize_datetime(normalized.get("date_of_acquisition"))
                disposed_at = normalize_datetime(normalized.get("date_of_disposition"))
            except ValueError as error:
                quarantined.append(
                    {
                        "reason": f"date_parse_error:{error}",
                        "source_record_id": source_id,
                    }
                )
                continue
            records.append(
                CityOwnedLandRecord(
                    source_key=self.source.key,
                    source_record_id=source_id,
                    pin=pin,
                    owner_name=owner_name,
                    original_owner=original_owner,
                    address=normalized.get("address"),
                    property_status=normalized.get("property_status"),
                    acquired_at=acquired_at,
                    disposed_at=disposed_at,
                    geometry_4326=geometry_result.geometry_4326,
                    geometry_3435=geometry_result.geometry_3435,
                    properties=normalized,
                )
            )

        return AdapterResult(
            source_result=source_result,
            records=tuple(records),
            quarantined=tuple(quarantined),
            missing_ids=missing_ids,
            missing_geometry=missing_geometry,
            invalid_geometry=invalid_geometry,
            repaired_geometry=repaired_geometry,
            duplicates=duplicates,
        )
