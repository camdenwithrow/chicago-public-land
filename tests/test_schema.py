import pytest

from pipeline.schema import SchemaContract, SchemaDriftError
from pipeline.source_registry import load_source_registry


def test_schema_contract_accepts_required_fields_and_types() -> None:
    source = load_source_registry().by_key("chicago_city_owned_land")
    contract = SchemaContract.for_source(source, field_types={"id": "text", "pin": "text"})

    contract.validate(
        {
            "id": "text",
            "pin": "text",
            "managing_organization": "text",
            "property_status": "text",
            "last_update": "text",
            "new_optional_field": "number",
        }
    )


def test_schema_contract_fails_loudly_on_missing_or_changed_fields() -> None:
    source = load_source_registry().by_key("chicago_city_owned_land")
    contract = SchemaContract.for_source(source, field_types={"id": "text", "pin": "text"})

    with pytest.raises(SchemaDriftError, match="missing required fields.*type changes"):
        contract.validate(
            {
                "id": "number",
                "pin": "text",
                "property_status": "text",
                "last_update": "text",
            }
        )
