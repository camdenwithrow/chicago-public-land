import json

from shapely.geometry import Polygon

from pipeline.geometry import parse_geometry, validate_and_project


def test_geometry_parses_geojson_wkt_and_coordinates() -> None:
    geojson = json.dumps({"type": "Point", "coordinates": [-87.63, 41.88]})

    assert parse_geometry(geojson).geom_type == "Point"
    assert parse_geometry("POINT (-87.63 41.88)").geom_type == "Point"
    assert parse_geometry(latitude="41.88", longitude="-87.63").geom_type == "Point"


def test_invalid_polygon_is_repaired_and_projected() -> None:
    bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])

    result = validate_and_project(bowtie, expected="polygon")

    assert result.error is None
    assert result.repaired is True
    assert result.geometry_4326 is not None and result.geometry_4326.is_valid
    assert result.geometry_3435 is not None


def test_unexpected_geometry_type_is_quarantinable() -> None:
    result = validate_and_project(parse_geometry("POINT (0 0)"), expected="polygon")

    assert result.error == "unexpected_geometry_type:Point"
