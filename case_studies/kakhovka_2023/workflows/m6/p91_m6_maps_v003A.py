# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Figures only; reads finished runs, changes nothing.
"""P91 -- maps and training curves for the v003_A arms (and the v002-trained U2 next to them).

Per frame (B1, B2), downsampled by DS for the PNG:
  <F>_flood_maps.png      one panel per run: predicted flood at that run's frozen validation threshold, over the
                          v003_A reference context (REFERENCE_WATER hatched grey, no S1 event = white).
  <F>_flood_state_<run>.png  composite flood-state map for one run: EVENT_FLOOD predicted / predicted on REFERENCE_WATER
                          (temporal-attribution candidate) / REFERENCE_WATER not predicted / dry / no S1 event; TEST
                          blocks outlined.
  <F>_score_<run>.png     the continuous score (single-hue sequential), nodata white.
training_curves.png       train loss and validation patch-F1 per epoch, one line per run (two panels, one axis each).

Every map shows AGREEMENT WITH WEAK REFERENCE LABELS, not flood-mapping accuracy (see runs/*/config.json:meaning).
Output: <case_study>/figures/m6_v003A/
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd, rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib.patches import Patch, Rectangle
from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = CFG.BULK_ROOT / "frames10"
FIG = ROOT / "figures" / "m6_v003A"
FRAMES = ("B1", "B2")
DS = 4
# fixed categorical assignment (never cycled): one colour per run, one per state
RUN_COLOR = {"U2_B1B2_v1": "#eb6834", "U0d_B1B2_v003A": "#1baf7a", "U2_B1B2_v003A": "#2a78d6", "U2b_B1B2_v003A": "#4a3aa7"}
STATE = {  # value: (name, colour)
    0: ("no S1 event / outside frame", "#ffffff"),
    1: ("dry (not predicted)", "#efece6"),
    2: ("REFERENCE_WATER, not predicted", "#b9c7d6"),
    3: ("predicted on REFERENCE_WATER (attribution candidate)", "#eda100"),
    4: ("predicted flood on EVENT_FLOOD label", "#2a78d6"),
    5: ("predicted flood elsewhere (unlabelled / LAND)", "#7fb3e6"),
}
SEQ = LinearSegmentedColormap.from_list("score", ["#f4f8fc", "#2a78d6", "#0b2a5c"])


def ds(a):
    return a[::DS, ::DS]


def load(fid):
    with rasterio.open(OUT / fid / "s1_change.tif") as s:
        d = list(s.descriptions); ne = s.read(d.index("n_valid_event") + 1); d0 = s.read(1)
        T = s.transform
    has = (ne > 0) & (d0 != -32768)
    with rasterio.open(OUT / fid / "m6_labels_v003_A.tif") as s:
        ont = s.read(1)
    with rasterio.open(OUT / fid / "m6_split_v1_role.tif") as s:
        role = s.read(1)
    ext = [T.c, T.c + T.a * has.shape[1], T.f + T.e * has.shape[0], T.f]      # (left, right, bottom, top), metres
    return dict(has=ds(has), ont=ds(ont), role=ds(role), ext=[e / 1000 for e in ext])


def score(fid, run):
    arm, suffix = run.split("_B1B2_")
    name = f"{arm}_score.tif" if suffix == "v1" else f"{arm}_{suffix}_score.tif"
    with rasterio.open(OUT / fid / "m6" / name) as s:
        q = s.read(1)
    thr = json.loads((ROOT / "runs" / run / "validation_threshold.json").read_text())["threshold"]
    return ds(np.where(q == 65535, np.nan, q / 1e4).astype("f4")), thr


def test_outline(ax, role, ext):
    """Outline the TEST blocks (role 3) so the reader knows where the numbers come from."""
    ny, nx = role.shape
    dx, dy = (ext[1] - ext[0]) / nx, (ext[3] - ext[2]) / ny
    from scipy import ndimage
    lab, n = ndimage.label(role == 3)
    for k in range(1, n + 1):
        rr, cc = np.nonzero(lab == k)
        ax.add_patch(Rectangle((ext[0] + cc.min() * dx, ext[3] - (rr.max() + 1) * dy), (cc.max() - cc.min() + 1) * dx,
                               (rr.max() - rr.min() + 1) * dy, fill=False, ec="#0b0b0b", lw=0.6, ls="--"))


def style(ax, ext, title):
    ax.set_title(title, fontsize=9, loc="left"); ax.set_xlabel("UTM 36N easting, km", fontsize=7)
    ax.set_ylabel("northing, km", fontsize=7); ax.tick_params(labelsize=6)
    for sp in ax.spines.values():
        sp.set_color("#c3c2b7")
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal")


def flood_maps(fid, L, runs):
    fig, axs = plt.subplots(1, len(runs), figsize=(4.2 * len(runs), 4.2 * L["has"].shape[0] / L["has"].shape[1] + 1.4),
                            constrained_layout=True)
    base = np.where(L["has"], 1, 0); base[(L["ont"] == 2) & L["has"]] = 2
    cm = ListedColormap(["#ffffff", "#efece6", "#b9c7d6"])
    for ax, run in zip(np.atleast_1d(axs), runs):
        sc, thr = score(fid, run)
        ax.imshow(base, cmap=cm, vmin=0, vmax=2, extent=L["ext"], interpolation="nearest")
        pred = np.ma.masked_where(~(sc >= thr), np.ones_like(sc))
        ax.imshow(pred, cmap=ListedColormap([RUN_COLOR[run]]), extent=L["ext"], interpolation="nearest")
        test_outline(ax, L["role"], L["ext"])
        km2 = float(np.nansum((sc >= thr) & L["has"])) * 1e-4 * DS * DS
        style(ax, L["ext"], f"{run}  thr {thr:.2f}\npredicted flood {km2:,.0f} km² (whole frame)")
    fig.legend(handles=[Patch(fc="#efece6", label="S1 event observed, not predicted"),
                        Patch(fc="#b9c7d6", label="REFERENCE_WATER (v003_A, recurrent May water)"),
                        Patch(fc="#ffffff", ec="#c3c2b7", label="no S1 event"),
                        Patch(fc="none", ec="#0b0b0b", ls="--", label="TEST blocks")],
               loc="lower center", ncol=4, fontsize=7, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(f"{fid}: predicted flood per arm at its frozen validation threshold "
                 "(agreement with weak labels, not flood accuracy)", fontsize=10)
    fig.savefig(FIG / f"{fid}_flood_maps.png", dpi=110, bbox_inches="tight"); plt.close(fig)


def flood_state(fid, L, run):
    sc, thr = score(fid, run); pred = sc >= thr
    st = np.zeros(sc.shape, "u1"); st[L["has"]] = 1
    st[L["has"] & (L["ont"] == 2)] = 2
    st[pred & L["has"]] = 5
    st[pred & (L["ont"] == 1)] = 4
    st[pred & (L["ont"] == 2)] = 3
    cm = ListedColormap([c for _, c in STATE.values()])
    h = L["has"].shape[0] / L["has"].shape[1]
    fig, ax = plt.subplots(figsize=(7, 7 * h + 1.6), constrained_layout=True)
    ax.imshow(st, cmap=cm, vmin=-0.5, vmax=5.5, extent=L["ext"], interpolation="nearest")
    test_outline(ax, L["role"], L["ext"])
    a = lambda v: float((st == v).sum()) * 1e-4 * DS * DS
    style(ax, L["ext"], f"{fid} flood state -- {run} (thr {thr:.2f})\n"
                        f"predicted on EVENT_FLOOD label {a(4):,.0f} km² · on REFERENCE_WATER {a(3):,.0f} km² · "
                        f"elsewhere {a(5):,.0f} km²")
    ax.legend(handles=[Patch(fc=c, ec="#c3c2b7", label=n) for n, c in STATE.values()], loc="upper center",
              bbox_to_anchor=(0.5, -0.08), ncol=2, fontsize=7, frameon=False)
    fig.savefig(FIG / f"{fid}_flood_state_{run}.png", dpi=110, bbox_inches="tight"); plt.close(fig)


def score_map(fid, L, run):
    sc, thr = score(fid, run)
    h = L["has"].shape[0] / L["has"].shape[1]
    fig, ax = plt.subplots(figsize=(7, 7 * h + 1.0), constrained_layout=True)
    im = ax.imshow(sc, cmap=SEQ, vmin=0, vmax=1, extent=L["ext"], interpolation="nearest")
    ax.imshow(np.ma.masked_where(L["has"], np.ones_like(sc)), cmap=ListedColormap(["#ffffff"]), extent=L["ext"])
    test_outline(ax, L["role"], L["ext"])
    style(ax, L["ext"], f"{fid} continuous score -- {run} (threshold {thr:.2f} drawn on the bar)")
    cb = fig.colorbar(im, ax=ax, shrink=0.6, pad=0.02); cb.ax.tick_params(labelsize=7)
    cb.ax.axhline(thr, color="#0b0b0b", lw=1.2); cb.set_label("U-Net score (weak-label agreement)", fontsize=7)
    fig.savefig(FIG / f"{fid}_score_{run}.png", dpi=110, bbox_inches="tight"); plt.close(fig)


def curves(runs):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6), constrained_layout=True)
    for run in runs:
        h = pd.read_csv(ROOT / "runs" / run / "training_history.csv")
        a1.plot(h.epoch, h.train_loss, color=RUN_COLOR[run], lw=2, label=run)
        a2.plot(h.epoch, h.val_patch_F1_at_0p5, color=RUN_COLOR[run], lw=2, label=run)
        a2.annotate(f"{h.val_patch_F1_at_0p5.max():.3f}", (h.epoch.iloc[-1], h.val_patch_F1_at_0p5.iloc[-1]),
                    fontsize=7, color="#52514e", xytext=(3, 0), textcoords="offset points")
    for ax, t in ((a1, "train loss (masked BCE + Dice)"), (a2, "validation patch F1 @ 0.5")):
        ax.set_title(t, fontsize=9, loc="left"); ax.set_xlabel("epoch", fontsize=8); ax.tick_params(labelsize=7)
        ax.grid(color="#efece6", lw=0.8); ax.spines[["top", "right"]].set_visible(False)
    a1.legend(fontsize=7, frameon=False)
    fig.suptitle("M6 arms on m6_split_v1 -- same recipe, seed and blocks; only inputs / labels differ", fontsize=10)
    fig.savefig(FIG / "training_curves.png", dpi=120, bbox_inches="tight"); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", default=["U2_B1B2_v1", "U0d_B1B2_v003A", "U2_B1B2_v003A", "U2b_B1B2_v003A"])
    ap.add_argument("--state-runs", nargs="+", default=["U2_B1B2_v003A", "U2b_B1B2_v003A"])
    a = ap.parse_args()
    FIG.mkdir(parents=True, exist_ok=True)
    curves([r for r in a.runs if (ROOT / "runs" / r / "training_history.csv").exists()])
    for fid in FRAMES:
        L = load(fid)
        flood_maps(fid, L, a.runs)
        for run in a.state_runs:
            flood_state(fid, L, run); score_map(fid, L, run)
        print(fid, "done", flush=True)
    print(f"-> {FIG.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
