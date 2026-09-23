# Provenance: ported (not a verbatim copy) from SWOT-DNIPRO src/swot_dnipro/spatial_domains.py
# source_repo=SWOT-DNIPRO source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766 copy_date=2026-09-23
# sha256_of_source=71fa5348ef42a6aa53e018c395bcc888249ccf533a8a586ed8ce946d28077e3a (full source file, before the
# extract below; see provenance/MIGRATION_MANIFEST.csv)
#
# SCOPED EXTRACT, PER THE MIGRATION MANIFEST: the source module mixed a generic YAML-driven geometry
# registry pattern with event-specific loader functions (named zone and reservoir polygons) and a hard-coded
# path to the source repo's own domain registry YAML. Only the generic, event-agnostic mechanics are ported
# here: build_grid(), assert_covers(), assert_projected_32636(), DomainTruncationError, geom_hash(), and a
# load()/as_bbox() pair that takes an injected loaders dict instead of a hard-coded per-event registry. The
# event-specific loaders themselves are NOT ported -- see a case study's own study_area.yaml and
# provenance/UNRESOLVED_DEPENDENCIES.md for what still depends on them (sentinel_preprocess.zone_grid, several
# migrated case-study scripts).
"""Event-agnostic geometry registry mechanics: named domains, grid-building, and CRS/coverage guards.

This is infrastructure, not data. A case study supplies its own named domains (a dict of
``name -> callable() -> shapely geometry in EPSG:4326``, or a YAML file plus loaders) and calls
``load(name, loaders)`` / ``as_bbox(name, loaders)``; nothing here knows what a "reservoir" or a "zone" is.

``build_grid`` is the only sanctioned way to turn a domain geometry into an analysis grid: it verifies the
result actually covers the geometry before returning, so a truncated grid cannot silently leave this function.
That single defect (three independently hand-written bbox literals in different scripts, three different wrong
extents for the same real-world object) is the reason this module exists at all in the source repository.
"""
from __future__ import annotations

import hashlib
from typing import Any, Callable

import numpy as np
import pyproj
import shapely
from shapely.ops import transform as shp_transform


def geom_hash(geom: "shapely.Geometry") -> str:
    """Short, stable content hash of a geometry's WKB -- provenance tag for a derived product."""
    return hashlib.sha256(shapely.to_wkb(geom, output_dimension=2)).hexdigest()[:16]


def load(name: str, loaders: dict[str, Callable[[], Any]]) -> "shapely.Geometry":
    """Return the named domain (EPSG:4326) from an injected loaders dict.

    Raises ``KeyError`` for anything not in ``loaders`` -- a typo must fail loudly, never fall through to a
    silent default extent. A loader may itself raise to mark a domain as deliberately unresolved.
    """
    if name not in loaders:
        raise KeyError(f"{name!r} is not a registered spatial domain. Known: {sorted(loaders)}.")
    return loaders[name]()


def as_bbox(name: str, loaders: dict[str, Callable[[], Any]]) -> tuple[float, float, float, float]:
    """(lon_min, lat_min, lon_max, lat_max), derived programmatically -- never hand-typed."""
    return tuple(round(v, 6) for v in load(name, loaders).bounds)  # type: ignore[return-value]


def to_utm(geom: "shapely.Geometry", crs_metric: str) -> "shapely.Geometry":
    """Reproject an EPSG:4326 domain geometry to the study's metric CRS for quantitative work."""
    tf = pyproj.Transformer.from_crs("EPSG:4326", crs_metric, always_xy=True).transform
    return shp_transform(tf, geom)


CANONICAL_CRS_DEFAULT = "EPSG:32636"


def assert_projected(obj, crs_metric: str = CANONICAL_CRS_DEFAULT, label: str = "geometry") -> None:
    """Fail fast before any distance/buffer/area/raster operation on a non-metric CRS.

    Accepts a GeoDataFrame/GeoSeries (checks .crs) or a pyproj/rasterio CRS object directly.
    """
    crs = getattr(obj, "crs", obj)
    if crs is None:
        raise ValueError(f"{label}: CRS is missing -- must be {crs_metric}")
    crs_str = crs.to_string() if hasattr(crs, "to_string") else str(crs)
    epsg = crs.to_epsg() if hasattr(crs, "to_epsg") else None
    if epsg == 4326 or "4326" in crs_str:
        raise ValueError(f"{label}: CRS is geographic (EPSG:4326, degrees) -- reproject to {crs_metric} "
                         f"BEFORE any distance/buffer/area/raster operation, do not mix degrees and metres.")
    want_epsg = int(crs_metric.split(":")[-1])
    if epsg != want_epsg:
        raise ValueError(f"{label}: CRS is {crs_str!r}, expected {crs_metric}. Reproject explicitly at ingestion.")


class DomainTruncationError(RuntimeError):
    """A grid or raster does not cover the authoritative domain it claims to represent.

    A legacy surface may still be READ as a covariate. It may never define an output grid --
    ``build_grid()`` is the only sanctioned way to make one.
    """


def assert_covers(geom, gx, gy, *, what: str = "grid", cell: float | None = None) -> None:
    """Raise unless the grid spans the geometry's bounds.

    ``cell`` lets the last grid line sit one cell short of the bound, which is correct for cell-centre
    coordinates; without it the check is exact.
    """
    gx = np.asarray(gx, float)
    gy = np.asarray(gy, float)
    x0, y0, x1, y1 = geom.bounds
    pad = float(cell) if cell else 0.0
    short = []
    if gx.min() > x0 + 1e-6:
        short.append(f"west by {gx.min() - x0:,.0f} m")
    if gx.max() + pad < x1 - 1e-6:
        short.append(f"EAST by {x1 - gx.max():,.0f} m")
    if gy.min() > y0 + 1e-6:
        short.append(f"south by {gy.min() - y0:,.0f} m")
    if gy.max() + pad < y1 - 1e-6:
        short.append(f"north by {y1 - gy.max():,.0f} m")
    if short:
        raise DomainTruncationError(
            f"{what} is truncated: {', '.join(short)}. The domain spans E {x0:,.0f}..{x1:,.0f}, "
            f"N {y0:,.0f}..{y1:,.0f}; the grid spans E {gx.min():,.0f}..{gx.max():,.0f}, "
            f"N {gy.min():,.0f}..{gy.max():,.0f}. Build the grid from the registry with build_grid(), "
            f"never from a precomputed surface file.")


def build_grid(geom, cell: float, *, what: str = "grid") -> dict:
    """The only sanctioned way to build an analysis grid from a domain geometry.

    Takes its extent from the geometry and verifies the result, so a truncated grid cannot leave this
    function. Returns cell-centre coordinate vectors ``gx``/``gy``, the flat indices of cells inside the
    geometry, and the grid shape.
    """
    import shapely as _shp
    x0, y0, x1, y1 = geom.bounds
    if abs(x0) <= 180.0 and abs(y0) <= 90.0:
        raise ValueError(f"{what}: bounds {geom.bounds} look like degrees; reproject to a metric CRS "
                         f"before building a metric grid")
    gx = np.arange(np.floor(x0 / cell) * cell, np.ceil(x1 / cell) * cell + cell, cell)
    gy = np.arange(np.floor(y0 / cell) * cell, np.ceil(y1 / cell) * cell + cell, cell)
    GX, GY = np.meshgrid(gx, gy)
    ins = np.where(_shp.contains_xy(geom, GX.ravel(), GY.ravel()))[0]
    assert_covers(geom, gx, gy, what=what, cell=cell)
    return {"gx": gx, "gy": gy, "nx": len(gx), "ny": len(gy),
            "ins_idx": ins, "cell_m": float(cell),
            "x": GX.ravel()[ins], "y": GY.ravel()[ins]}
