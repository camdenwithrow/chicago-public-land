from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential

LOGGER = logging.getLogger(__name__)
DATASET_ID = re.compile(r"^[a-z0-9]{4}-[a-z0-9]{4}$")
FIELD_NAME = re.compile(r"^[A-Za-z_:@][A-Za-z0-9_:@.]*$")


@dataclass(frozen=True)
class SocrataQuery:
    select: tuple[str, ...]
    order_by: tuple[str, ...]
    where: str | None = None
    incremental_field: str | None = None
    incremental_value: str | datetime | None = None
    page_size: int = 10_000

    def __post_init__(self) -> None:
        if not self.select:
            raise ValueError("select cannot be empty")
        if not self.order_by:
            raise ValueError("deterministic order_by is required")
        if not 1 <= self.page_size <= 50_000:
            raise ValueError("page_size must be between 1 and 50,000")
        for field in (*self.select, *self.order_by):
            if not FIELD_NAME.fullmatch(field):
                raise ValueError(f"unsafe Socrata field name: {field}")
        if (self.incremental_field is None) != (self.incremental_value is None):
            raise ValueError("incremental_field and incremental_value must be supplied together")
        if self.incremental_field and not FIELD_NAME.fullmatch(self.incremental_field):
            raise ValueError(f"unsafe incremental field: {self.incremental_field}")

    def parameters(self, offset: int) -> dict[str, str | int]:
        conditions = [self.where] if self.where else []
        if self.incremental_field and self.incremental_value is not None:
            value = self.incremental_value
            if isinstance(value, datetime):
                if value.tzinfo is None or value.utcoffset() is None:
                    raise ValueError("incremental datetime must include a timezone")
                literal = value.astimezone(UTC).isoformat().replace("+00:00", "Z")
            else:
                literal = value
            escaped = literal.replace("'", "''")
            conditions.append(f"{self.incremental_field} > '{escaped}'")

        parameters: dict[str, str | int] = {
            "$select": ",".join(self.select),
            "$order": ",".join(self.order_by),
            "$limit": self.page_size,
            "$offset": offset,
        }
        if conditions:
            parameters["$where"] = " AND ".join(f"({condition})" for condition in conditions)
        return parameters


@dataclass(frozen=True)
class SocrataResult:
    records: tuple[dict[str, Any], ...]
    raw_pages: tuple[bytes, ...]
    observed_schema: dict[str, str]
    source_updated_at: datetime | None

    @property
    def raw_snapshot(self) -> bytes:
        return b"\n".join(self.raw_pages)


def _is_retryable(error: BaseException) -> bool:
    if isinstance(error, (httpx.TimeoutException, httpx.NetworkError)):
        return True
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code == 429 or error.response.status_code >= 500
    return False


class SocrataClient:
    def __init__(
        self,
        domain: str,
        *,
        app_token: str | None = None,
        client: httpx.AsyncClient | None = None,
        max_attempts: int = 4,
    ) -> None:
        self.domain = domain.removeprefix("https://").rstrip("/")
        self.app_token = app_token
        self.client = client or httpx.AsyncClient(timeout=30)
        self._owns_client = client is None
        self.max_attempts = max_attempts

    async def __aenter__(self) -> SocrataClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def _get(
        self, path: str, *, params: dict[str, str | int] | None = None
    ) -> httpx.Response:
        headers = {"X-App-Token": self.app_token} if self.app_token else {}
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(multiplier=0.25, min=0.25, max=4),
            retry=retry_if_exception(_is_retryable),
            reraise=True,
        ):
            with attempt:
                response = await self.client.get(
                    f"https://{self.domain}{path}", params=params, headers=headers
                )
                response.raise_for_status()
                return response
        raise RuntimeError("unreachable retry state")

    async def fetch(self, dataset_id: str, query: SocrataQuery) -> SocrataResult:
        if not DATASET_ID.fullmatch(dataset_id):
            raise ValueError(f"invalid Socrata dataset ID: {dataset_id}")

        metadata_response = await self._get(f"/api/views/{dataset_id}")
        metadata = metadata_response.json()
        observed_schema = {
            column["fieldName"]: column["dataTypeName"] for column in metadata.get("columns", [])
        }
        rows_updated_at = metadata.get("rowsUpdatedAt")
        source_updated_at = (
            datetime.fromtimestamp(rows_updated_at, tz=UTC)
            if isinstance(rows_updated_at, int | float)
            else None
        )
        LOGGER.info(
            "Socrata schema fetched dataset=%s fields=%d updated_at=%s",
            dataset_id,
            len(observed_schema),
            source_updated_at.isoformat() if source_updated_at else "unknown",
        )

        records: list[dict[str, Any]] = []
        raw_pages: list[bytes] = []
        offset = 0
        while True:
            response = await self._get(
                f"/resource/{dataset_id}.json", params=query.parameters(offset)
            )
            page = json.loads(response.content)
            if not isinstance(page, list) or not all(isinstance(item, dict) for item in page):
                raise ValueError(f"unexpected Socrata response shape for {dataset_id}")
            typed_page: list[dict[str, Any]] = page
            raw_pages.append(response.content)
            records.extend(typed_page)
            LOGGER.info(
                "Socrata page fetched dataset=%s offset=%d rows=%d",
                dataset_id,
                offset,
                len(typed_page),
            )
            if len(typed_page) < query.page_size:
                break
            offset += query.page_size

        return SocrataResult(
            records=tuple(records),
            raw_pages=tuple(raw_pages),
            observed_schema=observed_schema,
            source_updated_at=source_updated_at,
        )
