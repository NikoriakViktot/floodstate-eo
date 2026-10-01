# New in floodstate-eo, 2026-10-01 (maintainer: "before the event all the index classifications -- maps of the classified indices -- and
# after the event"; then "what is all this cloud": single dates replaced by cloud-free period composites, the peak mapped with Sentinel-1).
# STATUS: ACTIVE. Display classes only: nothing is fitted or re-classified.
"""P95zm -- cloud-free maps of the classified indices of the reed-bed zones before and after the breach: the map side of the seasonal
evidence of p95z (T12i, T12j).

Zones: the Kherson delta (ZONE_2, Sentinel-2 frame B2) and the floodway between the dam and Kherson (ZONE_4, frame B1, west of 538 km;
  east of it no frame). Mapped window = the reed beds, the optical water and the event extent of the zone plus 1.5 km, clipped to the
  frame; every sensor is shown on the same window, inside the reconstruction domain.
Sentinel-2: the seven p54a indices, per cell the MEDIAN OF THE CLEAR OBSERVATIONS of a period (20 m), classed with the display bins of
  the reservoir maps (p95h INDEX_BINS; not thresholds of any classifier):
    before  normal year 25 May - 30 June 2022 (same season); the last period before the breach -- delta February - March 2023 (no optical
            scene of the delta between 5 March and 5 June), floodway 15 April - 5 June 2023
    after   recession 16 - 30 June 2023; July 2023
  The peak (7 - 9 June) has no clear optical view of most of the reed beds (8 June: 26 % of the delta, 18 % of the floodway clear): it is
  mapped with Sentinel-1 instead. Grey = no clear observation in the whole period. A period whose clear share of the window is below the
  inventory gate (p95u MIN_SHARE, 50 %) is refused unless --allow-partial, and then labelled PARTIAL.
Sentinel-1: VV (dB) of the zone caches on the same orbit 14 (ascending, ~16 UTC): the median of the spring 2023 scenes before the breach,
  9 June (peak) and 21 June (recession), in display classes < -18 | -18..-14 | -14..-10 | -10..-6 | > -6 dB (dark = smooth open water;
  bright = double bounce of emergent vegetation standing in water, or buildings). Clouds do not matter.
k10e: the frozen SWOT-DNIPRO surface classes (zone_spectral, 20 m): the best-covered same-season date before the breach, the last date
  before it and the first dates after it with >= 60 % of the window observed (else the best covered).
Black line = the event extent on 7 June (ensemble P(water) >= 0.5).
Tables (per zone, period, stratum = the p95z strata and ALL = every domain cell of the window, layer, class): km2 and share of the
  observed cells. Outputs: figures/m6_v003A/p95zm_<zone>_<INDEX>.png (before | after), p95zm_<zone>_index_classes.png (all indices),
  p95zm_<zone>_s1_vv.png, p95zm_<zone>_k10e.png; tables/p95zm_index_classes.csv, p95zm_s1_classes.csv, p95zm_k10e_classes.csv
"""
from __future__ import annotations

import importlib.util
import time
import warnings
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PERIODS = {
    "delta": (("before", "normal year · 25 May – 30 Jun 2022", "2022-05-25", "2022-06-30"),
              ("before", "last before the breach · Feb – Mar 2023", "2023-02-01", "2023-03-31"),
              ("after", "recession · 16 – 30 Jun 2023", "2023-06-16", "2023-06-30"),
              ("after", "after the flood · Jul 2023", "2023-07-01", "2023-07-31")),
    "floodway": (("before", "normal year · 25 May – 30 Jun 2022", "2022-05-25", "2022-06-30"),
                 ("before", "spring before the breach · 15 Apr – 5 Jun 2023", "2023-04-15", "2023-06-05"),
                 ("after", "recession · 16 – 30 Jun 2023", "2023-06-16", "2023-06-30"),
                 ("after", "after the flood · Jul 2023", "2023-07-01", "2023-07-31"))}
S1_ROWS = (("before", "spring 2023 before the breach · orbit 14 median", "spring"), ("after", "9 June 2023 · peak · orbit 14", "2023-06-09_orb14_ASC"),
           ("after", "21 June 2023 · recession · orbit 14", "2023-06-21_orb14_ASC"))
S1_BINS = ([-18.0, -14.0, -10.0, -6.0], ["< −18 dB", "−18 – −14", "−14 – −10", "−10 – −6", "> −6 dB"], ["#08306b", "#6baed6", "#e6dcc3", "#74a65a", "#7b3294"])
BREACH = "2023-06-06"
GREY = "#d9d9d9"
MARGIN_M = 1500.0
MAX_PX = 1600                                                    # display decimation: longest panel side in pixels
K10E_MIN_COVER = 0.6


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def _counts(rows, base, cls, n_cls, labels, code, inwin, cell_km2, strata):
    """Area per stratum and class (observed cells only)."""
    for st_name, sel in [("ALL", inwin)] + [(nm, code == c) for c, nm in strata.items()]:
        cnt = np.bincount(cls[sel], minlength=256)[:n_cls + 1].astype(float) * cell_km2
        obs = cnt[1:].sum()
        if obs < 0.2:
            continue
        for k in range(1, n_cls + 1):
            rows.append(dict(base, cls=k, label=labels[k - 1], stratum=st_name, km2=round(float(cnt[k]), 3),
                             share_of_observed=round(float(cnt[k] / obs), 4), observed_km2=round(float(obs), 2)))


def _panel(ax, cls, outside, cols, event, title, dec):
    from matplotlib.colors import ListedColormap
    cm = ListedColormap([GREY] + list(cols)); cm.set_bad("white")
    ax.imshow(np.ma.masked_where(outside[dec], cls[dec]), cmap=cm, vmin=-0.5, vmax=len(cols) + 0.5, interpolation="nearest")
    if event.any():
        ax.contour(event[dec].astype("f4"), levels=[0.5], colors="k", linewidths=0.4)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title(title, fontsize=9)


def _legend(ax, labels, cols, ncol=3):
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label=lab) for c, lab in zip(cols, labels)] + [Patch(color=GREY, label="no clear observation")],
              loc="upper center", bbox_to_anchor=(0.5, -0.01), fontsize=8, ncol=ncol, frameon=False)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-partial", action="store_true", help="draw a period composite below the inventory gate (p95u MIN_SHARE) anyway")
    a = ap.parse_args(); t0 = time.time()
    import matplotlib
    import pandas as pd
    import rasterio
    from affine import Affine
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.warp import reproject
    from rasterio.windows import Window, from_bounds, intersection
    from rasterio.windows import transform as win_transform
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from floodstate_eo import _kakhovka_legacy_config as CFG
    Z = _ld("p95z", HERE / "p95z_delta_indices.py"); H = _ld("p95h", HERE / "p95h_reservoir_maps.py")
    U = _ld("p95u", HERE / "p95u_evidence_inventory.py"); GATE = {"normal_year": "normal_year", "last before": "pre_breach_2023", "spring": "spring_2023", "recession": "recession", "after the flood": "july"}
    TAB = ROOT / "tables"; FIG = ROOT / "figures" / "m6_v003A"; FIG.mkdir(parents=True, exist_ok=True)
    C = Z.strata_context(list(Z.ZONES)); tr, crs = C["tr"], C["crs"]; event = C["pw7"] >= 0.5
    print("context", round(time.time() - t0), "s", flush=True)

    def onto(a, dst_tr, dst_shape):
        out = np.zeros(dst_shape, "u1")
        reproject(a.astype("u1"), out, src_transform=tr, src_crs=crs, dst_transform=dst_tr, dst_crs=crs, resampling=Resampling.nearest)
        return out

    rows, srows, krows = [], [], []
    for zone, (zname, frame, caches) in Z.ZONES.items():
        zm, code = C["zm"][zone], C["code"][zone]
        idir = CFG.BULK_ROOT / "frames10" / frame / "indices"; alld = sorted(p.name[:10] for p in idir.glob("20*_valid.tif"))
        with rasterio.open(idir / f"{alld[0]}.tif") as s:
            t10, s10, fb = s.transform, s.shape, s.bounds
        focus = zm & (((code > 0) & (code < 6)) | event)
        r, c = np.nonzero(focus); x0, y1 = tr * (c.min(), r.min()); x1, y0 = tr * (c.max() + 1, r.max() + 1)
        bounds = (max(x0 - MARGIN_M, fb.left), max(y0 - MARGIN_M, fb.bottom), min(x1 + MARGIN_M, fb.right), min(y1 + MARGIN_M, fb.top))

        def on_grid(t_full, shape_full, step, bounds=bounds, zm=zm, code=code):
            """The mapped window on a sensor grid: window, transform and shape at the reading resolution, domain / strata / event."""
            w = intersection(from_bounds(*bounds, transform=t_full).round_offsets().round_lengths(), Window(0, 0, shape_full[1], shape_full[0]))
            w = Window(int(w.col_off), int(w.row_off), int(w.width), int(w.height))
            ts = win_transform(w, t_full) * Affine.scale(step); sh = (int(w.height // step), int(w.width // step))
            return w, ts, sh, onto(zm, ts, sh) > 0, onto(code, ts, sh), onto(event & zm, ts, sh) > 0

        # ---- Sentinel-2: per-cell median of the clear observations of each period, 20 m ----------------------------------------------
        win, _, sh, inwin, code_w, ev_w = on_grid(t10, s10, 2)
        dec = (slice(None, None, max(1, int(np.ceil(max(sh) / MAX_PX)))),) * 2; outside = ~inwin
        comp = {}
        for phase, label, d0, d1 in PERIODS[zone]:
            ds = [d for d in alld if d0 <= d <= d1]; stack = {ix: [] for ix in Z.INDICES}
            for d in ds:
                with rasterio.open(idir / f"{d}.tif") as s:
                    dsc = list(s.descriptions); nd = int(s.nodata)
                    arr = {ix: s.read(dsc.index(ix) + 1, window=win, out_shape=sh, resampling=Resampling.nearest) for ix in Z.INDICES}
                with rasterio.open(idir / f"{d}_valid.tif") as s:
                    v = s.read(1, window=win, out_shape=sh, resampling=Resampling.nearest) > 0
                for ix in Z.INDICES:
                    a = arr[ix].astype("i2"); a[~v] = nd; stack[ix].append(a)
            nobs = np.sum([x != nd for x in stack[Z.INDICES[0]]], axis=0) if ds else np.zeros(sh, int)
            cover = float(((nobs > 0) & inwin).sum() / inwin.sum())
            for ix in Z.INDICES:
                if ds:
                    st = np.stack(stack[ix]); x = st.astype("f4") / 1e4; x[st == nd] = np.nan
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", RuntimeWarning); med = np.nanmedian(x, axis=0)
                    del st, x
                else:
                    med = np.full(sh, np.nan, "f4")
                cls = H.classify_index(med, ix); _, labels, cols = H.INDEX_BINS[ix]
                comp[(label, ix)] = cls
                _counts(rows, dict(zone=zone, phase=phase, period=label, dates="|".join(ds), cover=round(cover, 3), layer=ix),
                        np.where(inwin, cls, 0).astype("u1"), len(labels), labels, code_w, inwin, 4e-4, Z.STRATA)
            comp[(label, "_cover")] = cover; comp[(label, "_dates")] = ds; del stack
            key = next((v for k, v in GATE.items() if label.startswith(k)), None)                 # the inventory gate (p95u)
            ok, inv_share, _ = U.check(zone, key, "S2") if key else (None, None, None)
            if ok is not None and abs(inv_share - cover) > 0.05:
                print(f"  NOTE {zone} {label}: clear share of the mapped window {cover:.2f} vs the inventory's zone domain {inv_share:.2f} (different windows; the gate uses the mapped window)", flush=True)
            if (ok is False or cover < U.MIN_SHARE) and not a.allow_partial:
                raise SystemExit(f"{zone} {label}: only {cover:.0%} of the window has a clear observation (inventory gate {U.MIN_SHARE:.0%}); "
                                 "pass --allow-partial to draw it, labelled PARTIAL")
            if cover < U.MIN_SHARE:
                comp[(label, "_partial")] = True
            print(f"  {zone} S2 {label}: {len(ds)} scenes, clear in the period {cover:.0%}, {round(time.time() - t0)} s", flush=True)
        per = PERIODS[zone]; bef = [p for p in per if p[0] == "before"]; aft = [p for p in per if p[0] == "after"]; nr = max(len(bef), len(aft))
        aspect = sh[0] / sh[1]
        for ix in Z.INDICES:                                             # one figure per index: BEFORE | AFTER
            _, labels, cols = H.INDEX_BINS[ix]
            fig, axs = plt.subplots(nr, 2, figsize=(16, 8 * aspect * nr + 1.6), constrained_layout=True, squeeze=False)
            for col, group in ((0, bef), (1, aft)):
                for i in range(nr):
                    if i >= len(group):
                        axs[i, col].axis("off"); continue
                    phase, label, _, _ = group[i]
                    _panel(axs[i, col], comp[(label, ix)], outside, cols, ev_w,
                           f"{phase.upper()} · {label} · {len(comp[(label, '_dates')])} scenes · clear {comp[(label, '_cover')]:.0%}"
                           + (" · PARTIAL" if comp.get((label, '_partial')) else ""), dec)
            _legend(axs[-1, 0], labels, cols); _legend(axs[-1, 1], labels, cols)
            fig.suptitle(f"P95zm {zname} · {ix} in display classes (p95h bins), per-cell median of the clear Sentinel-2 observations of each period "
                         f"(frame {frame}, 20 m). Black line = event extent 7 June. The peak is mapped with Sentinel-1 (p95zm_{zone}_s1_vv.png).", fontsize=10)
            fig.savefig(FIG / f"p95zm_{zone}_{ix}.png", dpi=90); plt.close(fig)
        fig, axs = plt.subplots(len(per), len(Z.INDICES), figsize=(3.2 * len(Z.INDICES), 3.2 * aspect * len(per) + 1.4), constrained_layout=True, squeeze=False)
        for i, (phase, label, _, _) in enumerate(per):                  # overview: every index
            for j, ix in enumerate(Z.INDICES):
                _, labels, cols = H.INDEX_BINS[ix]
                _panel(axs[i, j], comp[(label, ix)], outside, cols, ev_w, ix if i == 0 else "", dec)
                if j == 0:
                    axs[i, j].set_ylabel(f"{phase.upper()}\n{label}\nclear {comp[(label, '_cover')]:.0%}" + ("\nPARTIAL" if comp.get((label, '_partial')) else ""), fontsize=8)
        for j, ix in enumerate(Z.INDICES):
            _, labels, cols = H.INDEX_BINS[ix]; _legend(axs[-1, j], labels, cols, ncol=1)
        fig.suptitle(f"P95zm {zname}: every Sentinel-2 index in display classes, cloud-free period composites before and after the breach "
                     "(per-cell median of clear observations); black line = event extent 7 June.", fontsize=10)
        fig.savefig(FIG / f"p95zm_{zone}_index_classes.png", dpi=90); plt.close(fig)
        del comp

        # ---- Sentinel-1 VV, same orbit 14: spring median, peak, recession ----------------------------------------------------------
        s1 = {}; grids = set()
        for cname in caches:
            cdir = CFG.S1_CACHE / cname; zz = np.load(cdir / "per_scene_water.npz", allow_pickle=True)
            grids.add((float(zz["x0"]), float(zz["y1"]), float(zz["cell"]), tuple(int(v) for v in zz["shape"])))
            for p in sorted(cdir.glob("2023-*_orb14_ASC.npz")):
                s1.setdefault(p.stem, cdir)
        assert len(grids) == 1, grids
        gx0, gy1, gcell, gshape = next(iter(grids)); tS = from_origin(gx0, gy1, gcell, gcell)
        winS, _, shs, inS, codeS, evS = on_grid(tS, gshape, 1)
        cutS = (slice(winS.row_off, winS.row_off + winS.height), slice(winS.col_off, winS.col_off + winS.width))
        decS = (slice(None, None, max(1, int(np.ceil(max(shs) / MAX_PX)))),) * 2

        def vv_db(stem, s1=s1, cutS=cutS, shs=shs):
            with np.load(s1[stem] / f"{stem}.npz") as b:
                vv, cov = b["vv"][cutS], b["cov"][cutS]
            x = np.where(cov & (vv > 0), 10 * np.log10(np.maximum(vv, 1e-6)), np.nan).astype("f4")
            return x[:shs[0], :shs[1]]

        spring = [k for k in sorted(s1) if "2023-04-15" <= k[:10] < BREACH]
        fig, axs = plt.subplots(1, len(S1_ROWS), figsize=(7 * len(S1_ROWS), 7 * shs[0] / shs[1] + 1.6), constrained_layout=True, squeeze=False)
        for j, (phase, label, key) in enumerate(S1_ROWS):
            if key == "spring":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning); x = np.nanmedian(np.stack([vv_db(k) for k in spring]), axis=0)
                used = spring
            else:
                x = vv_db(key) if key in s1 else np.full(shs, np.nan, "f4"); used = [key] if key in s1 else []
            cls = (np.digitize(x, S1_BINS[0]) + 1).astype("u1"); cls[~np.isfinite(x)] = 0
            _counts(srows, dict(zone=zone, phase=phase, period=label, dates="|".join(used), layer="S1_VV_orbit14"), np.where(inS, cls, 0).astype("u1"),
                    len(S1_BINS[1]), S1_BINS[1], codeS, inS, 4e-4, Z.STRATA)
            _panel(axs[0, j], cls, ~inS, S1_BINS[2], evS, f"{phase.upper()} · {label}" + (f" · {len(used)} scenes" if key == "spring" else ""), decS)
        _legend(axs[0, len(S1_ROWS) // 2], S1_BINS[1], S1_BINS[2], ncol=6)
        fig.suptitle(f"P95zm {zname}: Sentinel-1 VV on the same orbit (14, ascending) in display classes -- cloud-free. Dark = smooth open water; "
                     "bright = double bounce of vegetation standing in water (or buildings). Black line = event extent 7 June.", fontsize=10)
        fig.savefig(FIG / f"p95zm_{zone}_s1_vv.png", dpi=90); plt.close(fig)
        print(f"  {zone} S1: spring {spring}, {round(time.time() - t0)} s", flush=True)

        # ---- k10e on the best-covered dates --------------------------------------------------------------------------------------------
        kdir = CFG.BULK_ROOT / "zone_spectral" / zname
        kd = sorted(p.name[:10] for p in kdir.glob("20*_class.tif") if "2021-04-01" <= p.name[:10] <= "2023-09-30")
        with rasterio.open(kdir / f"{kd[0]}_class.tif") as s:
            tk, sk = s.transform, s.shape
        winK, _, shK, inK, codeK, evK = on_grid(tk, sk, 1); decK = (slice(None, None, max(1, int(np.ceil(max(shK) / MAX_PX)))),) * 2
        cov = {}
        for d in kd:
            with rasterio.open(kdir / f"{d}_class.tif") as s:
                k = s.read(1, window=winK)[:shK[0], :shK[1]]
            cov[d] = (k, float(((k > 0) & inK).sum() / inK.sum()))

        def pick(cands, n, prefer=None, cov=cov):
            good = [d for d in cands if cov[d][1] >= K10E_MIN_COVER]
            if prefer is not None and good:
                good = sorted(good, key=prefer)
            return good[:n] if good else sorted(cands, key=lambda d: -cov[d][1])[:1]

        season = [d for d in kd if d < "2023-01-01" and d[5:7] in ("05", "06", "07")]
        doy = lambda d: abs(pd.Timestamp(d).dayofyear - pd.Timestamp(BREACH).dayofyear)
        sel = [("before · same season", d) for d in pick(season, 1, prefer=doy)]
        sel += [("before · last", d) for d in pick([d for d in kd if d < BREACH][::-1], 1) if d not in [x[1] for x in sel]]
        sel += [("after", d) for d in pick([d for d in kd if d >= BREACH], 2)]
        kcols = [H.K10E[k][1] for k in sorted(H.K10E)]; klabels = [H.K10E[k][0] for k in sorted(H.K10E)]
        fig, axs = plt.subplots(1, max(1, len(sel)), figsize=(6 * max(1, len(sel)), 6 * shK[0] / shK[1] + 2.0), constrained_layout=True, squeeze=False)
        for j, (phase, d) in enumerate(sel):
            k = np.where(inK, cov[d][0], 0).astype("u1"); k[k > 9] = 0
            _counts(krows, dict(zone=zone, phase=phase.split(" ")[0], period=d, dates=d, layer="k10e"), k, 9, klabels, codeK, inK, 4e-4, Z.STRATA)
            _panel(axs[0, j], k, ~inK, kcols, evK, f"{phase.upper()} · {d} · observed {cov[d][1]:.0%}", decK)
        from matplotlib.patches import Patch
        fig.legend(handles=[Patch(color=c, label=lab) for c, lab in zip(kcols, klabels)] + [Patch(color=GREY, label="no clear observation")],
                   loc="lower center", ncol=5, fontsize=8, frameon=False)
        fig.suptitle(f"P95zm {zname}: SWOT-DNIPRO k10e surface classes (frozen p25 products, 20 m) on the best-covered dates before and after "
                     "the breach; black line = event extent 7 June.", fontsize=10)
        fig.savefig(FIG / f"p95zm_{zone}_k10e.png", dpi=90); plt.close(fig)
        print(f"  {zone} k10e {sel}: {round(time.time() - t0)} s", flush=True)
    pd.DataFrame(rows).to_csv(TAB / "p95zm_index_classes.csv", index=False); pd.DataFrame(srows).to_csv(TAB / "p95zm_s1_classes.csv", index=False)
    pd.DataFrame(krows).to_csv(TAB / "p95zm_k10e_classes.csv", index=False)
    print("->", FIG / "p95zm_*", TAB / "p95zm_*.csv", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
