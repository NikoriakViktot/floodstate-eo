# Provenance: SWOT-DNIPRO src/swot_dnipro/plotting/maps.py, source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766
# copy_date=2026-09-23. CORE_LIBRARY, per 19_MIGRATION_MANIFEST.csv row 29 (migration_phase=5).
#
# MIGRATION TODO / UNRESOLVED DEPENDENCY: the source file imports a sibling `plotting/style.py` module (scale
# bar, north arrow, a colour-name lookup `ST.C`) that is NOT in 19_MIGRATION_MANIFEST.csv and was therefore not
# copied (the manifest is the authoritative migration scope; pulling it in silently was avoided). The two call
# sites are wrapped so this module stays importable and usable without it: `finish()` already tolerated a
# missing/failing style backend in the source (try/except around the scale bar and north arrow) and that is
# unchanged; `zone_outline()`'s colour lookup now falls back to a literal default instead of importing `ST`.
# Logged in provenance/UNRESOLVED_DEPENDENCIES.md. `zone_outline()` and `fig_size()` also depend on the
# Kakhovka zone-geometry legacy shim (`_kakhovka_legacy_config`), same as `sentinel_preprocess.zone_grid`.
"""Shared map helpers for zone rasters -- the pieces every map script re-drew inline.

Every atlas map draws the authoritative domain outline the same way and every panel that shows the same
quantity uses the same colour scale (consistent colour bar across any multi-panel comparison of the same
quantity; scale bar, north arrow, legend, CRS, acquisition date, provenance on every map).

Nothing here computes anything: it draws what an upstream stage wrote.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .. import _kakhovka_legacy_config as CFG

#: Fixed display range per index. Chosen once, used everywhere, so a PRE and a
#: POST panel of the same index are directly comparable by eye.
INDEX_SCALE = {
    "NDVI":   dict(cmap="YlGn",     vmin=-0.2, vmax=0.9),
    "NDWI":   dict(cmap="RdBu",     vmin=-0.6, vmax=0.6),   # water > 0 -> blue
    "MNDWI":  dict(cmap="RdBu",     vmin=-0.6, vmax=0.6),
    "NDMI":   dict(cmap="BrBG",     vmin=-0.4, vmax=0.6),
    "BSI":    dict(cmap="PuOr_r",   vmin=-0.3, vmax=0.3),
    "AWEIsh": dict(cmap="RdBu",     vmin=-0.6, vmax=0.3),
    "NDTI":   dict(cmap="coolwarm", vmin=-0.3, vmax=0.3),
}

#: k10e physical classes -- colours fixed for the legend.
CLASS_COLORS = {
    0: ("INVALID", "#ffffff"), 1: ("OPEN_WATER", "#1b6ca8"), 2: ("SHALLOW_OR_MIXED_WATER", "#7fb3d5"),
    3: ("WET_SEDIMENT", "#8c6d31"), 4: ("DRY_BARE_SEDIMENT", "#d9c58b"), 5: ("SPARSE_HERBACEOUS", "#b8d98d"),
    6: ("DENSE_HERBACEOUS", "#4c9a2a"), 7: ("REED_OR_FLOODED_VEGETATION", "#1e6f3f"),
    8: ("BUILT_HARD_SURFACE", "#7d7d7d"), 9: ("AMBIGUOUS", "#e08214"),
}


def read_raster(path: Path, scale: float | None = None):
    """(array float32 with NaN nodata, extent for imshow, transform, tags)."""
    import rasterio
    with rasterio.open(path) as s:
        a = s.read(1).astype("f4")
        nd = s.nodata
        if nd is not None:
            a[a == nd] = np.nan
        if scale:
            a *= scale
        b = s.bounds
        return a, (b.left, b.right, b.bottom, b.top), s.transform, s.tags()


def zone_outline(ax, zone: str, **kw):
    """The authoritative registry outline, EPSG:32636, on every zone map."""
    from .. import _kakhovka_legacy_config as _LEGACY
    g = _LEGACY.load_utm(zone)
    polys = list(g.geoms) if hasattr(g, "geoms") else [g]
    style = dict(color="#7d3c98", lw=1.0, zorder=5)     # default; style.py's colour table was not migrated
    style.update(kw)
    for p in polys:
        x, y = p.exterior.xy
        ax.plot(x, y, **style)
        for r in p.interiors:
            xi, yi = r.xy
            ax.plot(xi, yi, **{**style, "lw": style["lw"] * 0.6})
    return g.bounds


def class_cmap():
    from matplotlib.colors import ListedColormap, BoundaryNorm
    cmap = ListedColormap([c for _, c in (CLASS_COLORS[k] for k in range(10))])
    norm = BoundaryNorm(np.arange(-0.5, 10.5, 1.0), cmap.N)
    return cmap, norm


def class_legend(ax, present: set[int] | None = None, **kw):
    """Legend OUTSIDE the axes by default: tall narrow frames make an inside legend cover the whole map."""
    from matplotlib.patches import Patch
    keys = [k for k in range(1, 10) if (present is None or k in present) and k != 8]
    handles = [Patch(facecolor=CLASS_COLORS[k][1], edgecolor="k", lw=0.3,
                     label=CLASS_COLORS[k][0].replace("_", " ").lower()) for k in keys]
    kw.setdefault("loc", "upper left")
    kw.setdefault("bbox_to_anchor", (1.02, 1.0))
    return ax.legend(handles=handles, fontsize=7, framealpha=0.95, borderaxespad=0, **kw)


def fig_size(zone: str, width_in: float = 6.0, extra_w: float = 0.0, cell: float = 20.0):
    """Figure size that respects the zone grid's aspect (tall zones stay tall)."""
    from ..optical import sentinel_preprocess as SP
    G = SP.zone_grid(zone, cell)
    aspect = G["ny"] / G["nx"]
    h = min(max(width_in * aspect, 4.0), 11.0)
    w = width_in * (h / (width_in * aspect)) if width_in * aspect > 11.0 else width_in
    return (w + extra_w, h + 0.8)


def draw_index(ax, path: Path, index: str, zone: str, add_cbar: bool = True):
    a, ext, _, tags = read_raster(path, scale=1.0 / 10000)
    sc = INDEX_SCALE[index]
    im = ax.imshow(a, extent=ext, origin="upper", cmap=sc["cmap"], vmin=sc["vmin"], vmax=sc["vmax"],
                   interpolation="nearest")
    zone_outline(ax, zone)
    ax.set_aspect("equal")
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    if add_cbar:
        import matplotlib.pyplot as plt
        plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02, label=index)
    return im, tags


def draw_class(ax, path: Path, zone: str):
    a, ext, _, tags = read_raster(path)
    cmap, norm = class_cmap()
    a = np.nan_to_num(a, nan=0)
    ax.imshow(a, extent=ext, origin="upper", cmap=cmap, norm=norm, interpolation="nearest")
    zone_outline(ax, zone)
    ax.set_aspect("equal"); ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    class_legend(ax, present=set(np.unique(a).astype(int)))
    return tags


def draw_uint8(ax, path: Path, zone: str, label: str, cmap="viridis", vmax=None):
    a, ext, _, tags = read_raster(path)
    import matplotlib.pyplot as plt
    im = ax.imshow(a, extent=ext, origin="upper", cmap=cmap, vmin=0, vmax=vmax, interpolation="nearest")
    zone_outline(ax, zone)
    ax.set_aspect("equal"); ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02, label=label)
    return tags


def finish(ax, title: str, caption: str):
    """Standard furniture: title, scale bar, north arrow, CRS/provenance caption, no ticks."""
    ax.set_title(title, fontsize=9)
    try:
        from .. import style as ST          # not migrated; see module header
        ST.scale_bar(ax)
        ST.north_arrow(ax)
    except Exception:
        pass
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(0.01, -0.02, caption, transform=ax.transAxes, fontsize=6, va="top", color="#444")


def caption_from_tags(tags: dict, extra: str = "") -> str:
    parts = [f"CRS {CFG.CRS_METRIC}"]
    for k in ("regime", "n_dates", "date", "cell_m"):
        if k in tags:
            parts.append(f"{k} {tags[k]}")
    if "dates" in tags:
        d = tags["dates"].split("|")
        parts.append(f"{d[0]}..{d[-1]}" if len(d) > 1 else d[0])
    if "producer" in tags:
        parts.append(tags["producer"])
    if extra:
        parts.append(extra)
    return " · ".join(parts)
