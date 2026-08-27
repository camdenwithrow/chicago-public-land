from datetime import UTC, datetime

import pytest

from pipeline.normalization import (
    normalize_boolean,
    normalize_column_name,
    normalize_datetime,
    normalize_owner,
    normalize_pin,
)


def test_common_values_are_normalized() -> None:
    assert normalize_column_name("Property Status") == "property_status"
    assert normalize_pin("12-34-567-890-0000") == "12345678900000"
    assert normalize_boolean(" yes ") is True
    assert normalize_datetime("2026-08-27T12:00:00Z") == datetime(2026, 8, 27, 12, tzinfo=UTC)
    assert normalize_owner(" City of Chicago – DPD ") == (
        "CITY OF CHICAGO DPD",
        "City of Chicago – DPD",
    )


def test_invalid_boolean_fails() -> None:
    with pytest.raises(ValueError, match="boolean"):
        normalize_boolean("sometimes")
