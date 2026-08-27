from pathlib import Path

import pytest

from pipeline.source_registry import load_source_registry


def test_source_registry_is_valid_and_unique() -> None:
    registry = load_source_registry()

    assert registry.version == "1.0.0"
    assert len(registry.sources) >= 10
    assert len({source.key for source in registry.sources}) == len(registry.sources)
    assert registry.by_key("chicago_city_owned_land").dataset_id == "aksk-kvfp"


def test_source_registry_requires_limitations(tmp_path: Path) -> None:
    invalid_registry = tmp_path / "sources.toml"
    invalid_registry.write_text(
        'registry_version = "1"\nreviewed_at = "2026-08-27"\n[[sources]]\nkey = "bad"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing"):
        load_source_registry(invalid_registry)
