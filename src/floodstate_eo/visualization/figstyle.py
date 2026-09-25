# Provenance: adapted from SWOT-DNIPRO src/swot_dnipro/plotting/style.py (source_commit_sha=f3e3e1afe91902a82a73f3c09354d1f9eb847766),
# adaptation_date=2026-09-25. Changes: colour table replaced by the FloodState-EO evidence palette, dpi 300, helpers for
# date axes, uncertainty bands and forest plots added, no case-study literals (resolves provenance/UNRESOLVED_DEPENDENCIES.md #2).
"""Publication figure style for FloodState-EO: one palette, one font, PDF + PNG output, map furniture.

Colours follow the evidence hierarchy of the case-study papers (fixed assignment, never cycled):
    terrain reconstruction  #2a78d6   (independent physical evidence)
    Sentinel-1 observation  #eb6834   (cross-sensor observation)
    U-Net / weak labels     #4a3aa7   (weak-label agreement)
    RF surface context      #1baf7a   (contextual)
    gauge / in-situ         #52514e
Sequential score ramp: one hue (blue) light -> dark. Diverging: orange <-> blue through neutral grey.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle

PALETTE = {"terrain": "#2a78d6", "s1": "#eb6834", "unet": "#4a3aa7", "rf": "#1baf7a", "gauge": "#52514e", "s2": "#eda100",
           "muted": "#95a5a6", "grid": "#efece6", "ink": "#0b0b0b", "ink2": "#52514e", "band": "#2a78d6"}
STATE_COLOURS = {0: ("no observation", "#ffffff"), 1: ("dry", "#efece6"), 2: ("reference water", "#b9c7d6"),
                 3: ("flood on reference water", "#eda100"), 4: ("flood on labelled event flood", "#2a78d6"),
                 5: ("flood elsewhere", "#7fb3e6")}
AGREEMENT_COLOURS = {"A": ("both", "#1baf7a"), "B": ("terrain only", "#7fb3e6"), "C": ("sensor only", "#eb6834"), "N": ("neither", "#efece6")}
SEQ_SCORE = LinearSegmentedColormap.from_list("score", ["#f4f8fc", "#2a78d6", "#0b2a5c"])
SEQ_DEPTH = LinearSegmentedColormap.from_list("depth", ["#dbe9f8", "#2a78d6", "#0b2a5c"])
SEQ_DAYS = LinearSegmentedColormap.from_list("days", ["#f4f8fc", "#eda100", "#e34948", "#4a3aa7"])
DIVERGING = LinearSegmentedColormap.from_list("div", ["#eb6834", "#d8dbdd", "#2a78d6"])


def use_style(font_size: float = 8.5, dpi: int = 300) -> None:
    """DejaVu Sans, small ticks, recessive grid, editable fonts in PDF."""
    matplotlib.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": font_size, "axes.titlesize": font_size + 0.5, "axes.labelsize": font_size,
        "xtick.labelsize": font_size - 1, "ytick.labelsize": font_size - 1, "legend.fontsize": font_size - 1.5,
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8,
        "grid.color": PALETTE["grid"], "grid.linewidth": 0.8, "axes.grid": False, "legend.frameon": False,
        "savefig.dpi": dpi, "figure.dpi": 100, "pdf.fonttype": 42, "ps.fonttype": 42, "axes.prop_cycle": matplotlib.cycler(
            color=[PALETTE["terrain"], PALETTE["s1"], PALETTE["unet"], PALETTE["rf"], PALETTE["s2"], PALETTE["gauge"]])})


def save(fig, stem: str, outdir: Path, formats=("png", "pdf"), dpi: int = 300) -> list[Path]:
    """Write <outdir>/<stem>.png and .pdf (tight bbox); returns the paths."""
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True); out = []
    for ext in formats:
        p = outdir / f"{stem}.{ext}"; fig.savefig(p, dpi=dpi, bbox_inches="tight"); out.append(p)
    plt.close(fig)
    return out


def panel_label(ax, text: str, x: float = 0.01, y: float = 0.99, **kw) -> None:
    ax.text(x, y, text, transform=ax.transAxes, ha="left", va="top", fontsize=kw.pop("fontsize", 10), fontweight="bold",
            color=PALETTE["ink"], **kw)


def scale_bar(ax, length_m: float, x: float = 0.05, y: float = 0.05, units_per_m: float = 1.0, label: str | None = None) -> None:
    """Horizontal scale bar on a metric axis. `units_per_m` = axis units per metre (0.001 when the axis is in km)."""
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim(); L = length_m * units_per_m
    bx = x0 + x * (x1 - x0); by = y0 + y * (y1 - y0); h = 0.012 * (y1 - y0)
    ax.add_patch(Rectangle((bx, by), L, h, fc=PALETTE["ink"], ec=PALETTE["ink"], lw=0.5, zorder=20))
    ax.add_patch(Rectangle((bx, by), L / 2, h, fc="white", ec=PALETTE["ink"], lw=0.5, zorder=21))
    ax.text(bx + L / 2, by + 1.6 * h, label or (f"{length_m / 1000:g} km" if length_m >= 1000 else f"{length_m:g} m"),
            ha="center", va="bottom", fontsize=7, color=PALETTE["ink"], zorder=22)


def north_arrow(ax, x: float = 0.95, y: float = 0.12, size: float = 0.06) -> None:
    ax.annotate("N", xy=(x, y + size), xytext=(x, y), xycoords="axes fraction", textcoords="axes fraction", ha="center",
                va="center", fontsize=8, color=PALETTE["ink"],
                arrowprops={"arrowstyle": "-|>", "color": PALETTE["ink"], "lw": 1.0, "shrinkA": 0, "shrinkB": 0})


def graticule(ax, crs_metric: str, step_deg: float = 0.25, units_per_m: float = 1.0, color: str = "#b9c7d6") -> None:
    """Lon/lat lines and edge labels on an axis drawn in a projected CRS (axis units = metres x units_per_m)."""
    from pyproj import Transformer
    tf = Transformer.from_crs(crs_metric, "EPSG:4326", always_xy=True); inv = Transformer.from_crs("EPSG:4326", crs_metric, always_xy=True)
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    lon0, lat0 = tf.transform(x0 / units_per_m, y0 / units_per_m); lon1, lat1 = tf.transform(x1 / units_per_m, y1 / units_per_m)
    for lon in np.arange(np.floor(lon0 / step_deg) * step_deg, lon1 + step_deg, step_deg):
        lats = np.linspace(lat0 - 0.2, lat1 + 0.2, 50); xs, ys = inv.transform(np.full_like(lats, lon), lats)
        ax.plot(np.array(xs) * units_per_m, np.array(ys) * units_per_m, color=color, lw=0.4, ls=":", zorder=5)
        xi = np.interp(y0, np.array(ys) * units_per_m, np.array(xs) * units_per_m)
        if x0 <= xi <= x1:
            ax.text(xi, y0 + 0.012 * (y1 - y0), f"{lon:.2f}°E", ha="center", va="bottom", fontsize=5.5, color=PALETTE["ink2"], zorder=30)
    for lat in np.arange(np.floor(lat0 / step_deg) * step_deg, lat1 + step_deg, step_deg):
        lons = np.linspace(lon0 - 0.3, lon1 + 0.3, 50); xs, ys = inv.transform(lons, np.full_like(lons, lat))
        ax.plot(np.array(xs) * units_per_m, np.array(ys) * units_per_m, color=color, lw=0.4, ls=":", zorder=5)
        yi = np.interp(x0, np.array(xs) * units_per_m, np.array(ys) * units_per_m)
        if y0 <= yi <= y1:
            ax.text(x0 + 0.006 * (x1 - x0), yi, f"{lat:.2f}°N", ha="left", va="bottom", fontsize=5.5, color=PALETTE["ink2"], rotation=90, zorder=30)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)


def date_axis(ax, event_date=None, fmt: str = "%d %b", every_days: int = 7, label: str | None = None) -> None:
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=every_days)); ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
    ax.grid(axis="y", color=PALETTE["grid"], lw=0.8)
    if event_date is not None:
        ax.axvline(event_date, color="#e34948", lw=0.8, ls="--")
        if label:
            ax.text(event_date, ax.get_ylim()[1], f" {label}", fontsize=6.5, color="#e34948", va="top")


def band(ax, x, lo, hi, color: str | None = None, alpha: float = 0.18, label: str | None = None):
    return ax.fill_between(x, lo, hi, color=color or PALETTE["band"], alpha=alpha, lw=0, label=label)


def forest(ax, labels, median, lo, hi, color: str | None = None, zero: bool = True) -> None:
    """Horizontal forest plot of paired differences with intervals; the entity order is the label order."""
    y = np.arange(len(labels))[::-1]; c = color or PALETTE["unet"]
    ax.hlines(y, lo, hi, color=c, lw=1.6); ax.plot(median, y, "o", color=c, ms=5)
    ax.set_yticks(y); ax.set_yticklabels(labels)
    if zero:
        ax.axvline(0, color=PALETTE["ink2"], lw=0.8, ls=":")
    ax.grid(axis="x", color=PALETTE["grid"], lw=0.8)


def nmad(x) -> float:
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return float(1.4826 * np.median(np.abs(x - np.median(x)))) if x.size else float("nan")


def bootstrap_ci(x, stat=np.median, n: int = 2000, seed: int = 20260923, q=(2.5, 97.5)) -> tuple[float, float]:
    x = np.asarray(x, float); x = x[np.isfinite(x)]; rng = np.random.default_rng(seed)
    if x.size == 0:
        return float("nan"), float("nan")
    s = np.array([stat(x[rng.integers(0, x.size, x.size)]) for _ in range(n)])
    return float(np.percentile(s, q[0])), float(np.percentile(s, q[1]))
