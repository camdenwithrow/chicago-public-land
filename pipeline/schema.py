from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from pipeline.source_registry import Source


class SchemaDriftError(RuntimeError):
    """Raised when a publisher's observed schema violates a source contract."""


@dataclass(frozen=True)
class SchemaContract:
    source_key: str
    required_fields: frozenset[str]
    field_types: Mapping[str, str]

    @classmethod
    def for_source(
        cls, source: Source, *, field_types: Mapping[str, str] | None = None
    ) -> SchemaContract:
        expected_types = dict(field_types or {})
        unknown_fields = expected_types.keys() - set(source.expected_fields)
        if unknown_fields:
            raise ValueError(f"type contracts are not required fields: {sorted(unknown_fields)}")
        return cls(
            source_key=source.key,
            required_fields=frozenset(source.expected_fields),
            field_types=MappingProxyType(expected_types),
        )

    def validate(self, observed_fields: Mapping[str, str]) -> None:
        missing = sorted(self.required_fields - observed_fields.keys())
        mismatches = sorted(
            (field, expected, observed_fields[field])
            for field, expected in self.field_types.items()
            if field in observed_fields and observed_fields[field] != expected
        )
        if not missing and not mismatches:
            return

        details: list[str] = []
        if missing:
            details.append(f"missing required fields: {', '.join(missing)}")
        if mismatches:
            formatted = ", ".join(
                f"{field} expected {expected}, observed {observed}"
                for field, expected, observed in mismatches
            )
            details.append(f"type changes: {formatted}")
        raise SchemaDriftError(f"schema drift for {self.source_key}: {'; '.join(details)}")
