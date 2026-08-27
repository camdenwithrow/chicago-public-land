from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

SourceStatus = Literal["selected", "provisional", "gap", "basemap_only"]

REGISTRY_PATH = Path(__file__).with_name("sources.toml")
REQUIRED_SOURCE_FIELDS = {
    "key",
    "name",
    "publisher",
    "kind",
    "status",
    "dataset_id",
    "landing_url",
    "fetch_url",
    "fetch_method",
    "license",
    "update_frequency",
    "contact",
    "geometry",
    "join_keys",
    "expected_fields",
    "limitations",
}
VALID_STATUSES: set[SourceStatus] = {"selected", "provisional", "gap", "basemap_only"}


@dataclass(frozen=True)
class Source:
    key: str
    name: str
    publisher: str
    kind: str
    status: SourceStatus
    dataset_id: str
    landing_url: str
    fetch_url: str
    fetch_method: str
    license: str
    update_frequency: str
    contact: str
    geometry: str
    join_keys: tuple[str, ...]
    expected_fields: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class SourceRegistry:
    version: str
    reviewed_at: str
    sources: tuple[Source, ...]

    def by_key(self, key: str) -> Source:
        try:
            return next(source for source in self.sources if source.key == key)
        except StopIteration as error:
            raise KeyError(key) from error


def _require_string(record: dict[str, Any], field: str, *, allow_empty: bool = False) -> str:
    value = record[field]
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ValueError(f"source {record.get('key', '<unknown>')}: {field} must be a string")
    return value


def _require_string_list(record: dict[str, Any], field: str) -> tuple[str, ...]:
    value = record[field]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"source {record.get('key', '<unknown>')}: {field} must be a string list")
    return tuple(value)


def _validate_url(value: str, field: str, key: str, *, allow_empty: bool = False) -> None:
    if allow_empty and not value:
        return
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"source {key}: {field} must be an HTTPS URL")


def _parse_source(record: dict[str, Any]) -> Source:
    missing = REQUIRED_SOURCE_FIELDS - record.keys()
    if missing:
        raise ValueError(f"source {record.get('key', '<unknown>')}: missing {sorted(missing)}")

    key = _require_string(record, "key")
    status_value = _require_string(record, "status")
    if status_value not in VALID_STATUSES:
        raise ValueError(f"source {key}: invalid status {status_value}")
    status: SourceStatus = status_value
    landing_url = _require_string(record, "landing_url")
    fetch_url = _require_string(record, "fetch_url", allow_empty=True)
    _validate_url(landing_url, "landing_url", key)
    _validate_url(fetch_url, "fetch_url", key, allow_empty=True)

    limitations = _require_string_list(record, "limitations")
    if not limitations:
        raise ValueError(f"source {key}: at least one limitation is required")

    return Source(
        key=key,
        name=_require_string(record, "name"),
        publisher=_require_string(record, "publisher"),
        kind=_require_string(record, "kind"),
        status=status,
        dataset_id=_require_string(record, "dataset_id", allow_empty=True),
        landing_url=landing_url,
        fetch_url=fetch_url,
        fetch_method=_require_string(record, "fetch_method"),
        license=_require_string(record, "license"),
        update_frequency=_require_string(record, "update_frequency"),
        contact=_require_string(record, "contact"),
        geometry=_require_string(record, "geometry"),
        join_keys=_require_string_list(record, "join_keys"),
        expected_fields=_require_string_list(record, "expected_fields"),
        limitations=limitations,
    )


def load_source_registry(path: Path = REGISTRY_PATH) -> SourceRegistry:
    with path.open("rb") as registry_file:
        document = tomllib.load(registry_file)

    version = document.get("registry_version")
    reviewed_at = document.get("reviewed_at")
    records = document.get("sources")
    if not isinstance(version, str) or not version:
        raise ValueError("registry_version must be a non-empty string")
    if not isinstance(reviewed_at, str) or not reviewed_at:
        raise ValueError("reviewed_at must be a non-empty string")
    if not isinstance(records, list):
        raise ValueError("sources must be a list")

    sources = tuple(_parse_source(record) for record in records)
    keys = [source.key for source in sources]
    if len(keys) != len(set(keys)):
        raise ValueError("source keys must be unique")
    return SourceRegistry(version=version, reviewed_at=reviewed_at, sources=sources)
