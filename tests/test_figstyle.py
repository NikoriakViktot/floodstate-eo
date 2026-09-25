"""figstyle: imports, palette fixed, map furniture draws on a metric axis, save writes png + pdf."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from floodstate_eo.visualization import figstyle as FS


def test_palette_is_fixed():
    assert FS.PALETTE["terrain"] == "#2a78d6" and FS.PALETTE["s1"] == "#eb6834" and FS.PALETTE["unet"] == "#4a3aa7"


def test_furniture_and_save(tmp_path):
    FS.use_style()
    fig, ax = plt.subplots(figsize=(3, 3))
    ax.imshow(np.zeros((10, 10)), extent=[440_000, 480_000, 5_140_000, 5_180_000])
    FS.scale_bar(ax, 10_000); FS.north_arrow(ax); FS.graticule(ax, "EPSG:32636"); FS.panel_label(ax, "a")
    out = FS.save(fig, "t", tmp_path)
    assert [p.suffix for p in out] == [".png", ".pdf"] and all(p.stat().st_size > 1000 for p in out)


def test_stats_helpers():
    x = np.array([1.0, 1.1, 0.9, 1.05, 0.95, 10.0])
    assert 0.05 < FS.nmad(x) < 0.2
    lo, hi = FS.bootstrap_ci(x, n=200)
    assert lo <= np.median(x) <= hi


def test_forest_and_band():
    fig, (a, b) = plt.subplots(1, 2)
    FS.forest(a, ["u", "v"], [0.1, -0.2], [0.0, -0.5], [0.3, 0.1])
    FS.band(b, np.arange(3), [0, 1, 2], [1, 2, 3])
    plt.close(fig)
