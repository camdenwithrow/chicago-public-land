from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from pyproj import Transformer
from shapely import from_geojson, from_wkt, make_valid
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

GeometryFamily = Literal["point", "polygon", "line"]

TO_3435 = Transformer.from_crs(4326, 3435, always_xy=True)


@dataclass(frozen=True)
class GeometryResult:
    geometry_4326: BaseGeometry | None
    geometry_3435: BaseGeometry | None
    repaired: bool
    error: str | None


def parse_geometry(
    value: Any = None, *, latitude: Any = None, longitude: Any = None
) -> BaseGeometry | None:
    if value is not None:
        if isinstance(value, BaseGeometry):
            return value
        if isinstance(value, dict):
            return shape(value)
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            if stripped.startswith(("{", "[")):
                parsed = json.loads(stripped)
                return from_geojson(json.dumps(parsed))
            return from_wkt(stripped)
        raise ValueError(f"unsupported geometry value: {type(value).__name__}")
    if latitude is None or longitude is None:
        return None
    return Point(float(longitude), float(latitude))


def _matches_family(geometry: BaseGeometry, expected: GeometryFamily) -> bool:
    families = {
        "point": {"Point", "MultiPoint"},
        "polygon": {"Polygon", "MultiPolygon"},
        "line": {"LineString", "MultiLineString"},
    }
    return geometry.geom_type in families[expected]


def validate_and_project(
    geometry: BaseGeometry | None, *, expected: GeometryFamily
) -> GeometryResult:
    if geometry is None or geometry.is_empty:
        return GeometryResult(None, None, False, "missing_geometry")
    if not _matches_family(geometry, expected):
        return GeometryResult(None, None, False, f"unexpected_geometry_type:{geometry.geom_type}")

    repaired = False
    candidate = geometry
    if not candidate.is_valid:
        candidate = make_valid(candidate)
        repaired = True
    if candidate.is_empty or not candidate.is_valid or not _matches_family(candidate, expected):
        return GeometryResult(None, None, repaired, "unrepairable_geometry")

    projected = transform(TO_3435.transform, candidate)
    return GeometryResult(candidate, projected, repaired, None)
