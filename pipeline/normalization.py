from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any


def normalize_null(value: Any, *, null_tokens: frozenset[str] = frozenset()) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped.casefold() in null_tokens:
            return None
        return stripped
    return value


def normalize_column_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    if not normalized:
        raise ValueError("column name cannot normalize to empty")
    return normalized


def normalize_pin(value: Any) -> str | None:
    normalized = normalize_null(value)
    if normalized is None:
        return None
    digits = re.sub(r"\D", "", str(normalized))
    return digits or None


def normalize_boolean(value: Any) -> bool | None:
    normalized = normalize_null(value)
    if normalized is None:
        return None
    if isinstance(normalized, bool):
        return normalized
    if isinstance(normalized, int) and normalized in (0, 1):
        return bool(normalized)
    text = str(normalized).casefold()
    if text in {"true", "t", "yes", "y", "1"}:
        return True
    if text in {"false", "f", "no", "n", "0"}:
        return False
    raise ValueError(f"cannot normalize boolean: {value!r}")


def normalize_datetime(value: Any) -> datetime | None:
    normalized = normalize_null(value)
    if normalized is None:
        return None
    if isinstance(normalized, datetime):
        parsed = normalized
    else:
        parsed = datetime.fromisoformat(str(normalized).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def normalize_owner(value: Any) -> tuple[str | None, str | None]:
    original = normalize_null(value)
    if original is None:
        return None, None
    original_text = str(original)
    canonical = " ".join(re.sub(r"[^A-Z0-9]+", " ", original_text.upper()).split())
    return canonical or None, original_text


def normalize_mapping(record: dict[str, Any]) -> dict[str, Any]:
    return {normalize_column_name(key): normalize_null(value) for key, value in record.items()}
