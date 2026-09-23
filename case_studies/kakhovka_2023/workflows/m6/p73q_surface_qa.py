# New in floodstate-eo, 2026-09-23. STATUS: ACTIVE_DIAGNOSTIC. QA of p73 before freeze; changes no p73 prediction.
"""P73q -- does RF20 map physically meaningful surface classes, or only reproduce WorldCover?

Everything here is DIAGNOSTIC. WorldCover and the old BASE_CLASS are read only to compare against p73; the flood-label
layers (m6_labels_v002) are read only to LOCATE two QA zones (flooded fields, S1-disputed fields) -- nothing feeds back
into p73.

1. class areas per frame, plus cross-frame agreement where B1 and B2
   overlap on the shared global 20 m grid (the same model, different composites: disagreement there is instability).
2. wall-to-wall agreement with WorldCover on 4-cell-pure cells (not a balanced sample: every pure cell counts).
3. crosstab against the old BASE_CLASS (a 20 m cell takes a BASE_CLASS only if its four 10 m cells agree), and the
   decomposition of VEGETATION_AGRICULTURE into p73 classes -- the product this step exists for.
4. where UNCERTAIN occurs (by WorldCover class and by BASE_CLASS).
5. maps: per-class p73-vs-WorldCover agreement for WATER, CROPLAND, WETLAND_REED, BUILT_UP, BARE_SAND, and six QA zones
   chosen from data by declared rules (ZONES below), each shown as NDVI_pre_max | MNDWI_pre_med | WorldCover |
   BASE_CLASS | p73 class | p73 top probability.

Outputs: <case_study>/tables/p73_rf20_baseclass_crosswalk.csv and <case_study>/tables/p73_rf20_qa/ (tables, maps)
"""
from __future__ import annotations
import importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from rasterio.windows import Window
from scipy import ndimage
from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent
OUT = CFG.BULK_ROOT / "frames10"
QAD = CFG.TABLES / "p73_rf20_qa"
FIGD = QAD
KM2 = 4e-4                                                     # one 20 m cell
BASE = {0: "PRE_EXISTING_WATER", 1: "VEGETATION_AGRICULTURE", 2: "BARE_SAND", 3: "BUILT_UP_URBAN",
        4: "WETLAND_MIXED", 5: "OTHER_DRY", 6: "UNCERTAIN", 254: "MIXED_2x2", 255: "INVALID"}
WCN = {10: "tree", 20: "shrub", 30: "grass", 40: "cropland", 50: "built", 60: "bare", 70: "snow", 80: "water",
       90: "herb_wetland", 95: "mangrove", 100: "moss", 0: "none"}
COL = {1: "#2166ac", 2: "#f1c232", 3: "#b6d7a8", 4: "#274e13", 5: "#93c47d", 6: "#8e7cc3", 7: "#cc0000",
       8: "#e6d3a3", 9: "#999999", 10: "#ff00ff", 255: "#ffffff"}
HALF = 150                                                     # QA window half-size in 20 m cells (6 km box)


def _p73():
    s = importlib.util.spec_from_file_location("p73", HERE / "p73_rf20_surface.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def worldcover20(P, fid, g):
    """WorldCover value where all four half-cell-shifted WorldCover cells agree, else 0 (same rule as p73's target)."""
    with rasterio.open(CFG.BULK_ROOT / "worldcover_frames" / P.WCZ[fid] / "wc_2021_20m.tif") as s:
        wc = s.read(1); wt = s.transform
    gt = g["transform"]
    kr, kc = int(np.floor((wt.f - gt.f) / 20.0)), int(np.floor((gt.c - wt.c) / 20.0))
    W = np.zeros((g["ny"] + 1, g["nx"] + 1), wc.dtype)
    r_a, r_b = max(kr, 0), min(kr + g["ny"] + 1, wc.shape[0]); c_a, c_b = max(kc, 0), min(kc + g["nx"] + 1, wc.shape[1])
    W[r_a - kr:r_b - kr, c_a - kc:c_b - kc] = wc[r_a:r_b, c_a:c_b]
    q = [W[i:i + g["ny"], j:j + g["nx"]] for i in (0, 1) for j in (0, 1)]
    pure = (q[0] == q[1]) & (q[0] == q[2]) & (q[0] == q[3])
    return np.where(pure, q[0], 0).astype("u1")


def to20_agree(a10, g, mixed=254):
    s = a10[g["r0"]:g["r0"] + 2 * g["ny"], g["c0"]:g["c0"] + 2 * g["nx"]].reshape(g["ny"], 2, g["nx"], 2)
    first = s[:, 0, :, 0]
    same = (s == first[:, None, :, None]).all(axis=(1, 3))
    return np.where(same, first, mixed).astype(a10.dtype)


def read10(fid, name, band=1):
    with rasterio.open(OUT / fid / name) as s:
        return s.read(band)


def best_window(mask, half=HALF):
    """Centre of the window holding the most True cells (box sum), as (row, col)."""
    k = 2 * half + 1
    cs = ndimage.uniform_filter(mask.astype("f4"), size=k, mode="constant")
    r, c = np.unravel_index(np.argmax(cs), cs.shape)
    return int(np.clip(r, half, mask.shape[0] - half - 1)), int(np.clip(c, half, mask.shape[1] - half - 1))


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm
    P = _p73(); FIGD.mkdir(parents=True, exist_ok=True)
    CL = P.CLASSES
    area, wcagr, bct, unc, zones_t = [], [], [], [], []
    frames = {}
    for fid in ("B1", "B2"):
        g = P.grid20(fid)
        with rasterio.open(OUT / fid / "p73_rf20" / "surface_class_20m.tif") as s:
            cls = s.read(1)
        with rasterio.open(OUT / fid / "p73_rf20" / "surface_max_score_20m.tif") as s:
            top = s.read(1)
        valid = cls != 255
        for c, n in CL.items():
            area.append(dict(frame=fid, p73_class=n, km2=round(float((cls == c).sum()) * KM2, 1),
                             share_pct=round(100 * float((cls == c).sum()) / max(valid.sum(), 1), 2)))
        # 2. WorldCover wall-to-wall on pure cells
        wc = worldcover20(P, fid, g)
        for wv, pc in P.WC2P73.items():
            m = valid & (wc > 0)
            tp = int(((cls == pc) & (wc == wv) & m).sum())
            wcagr.append(dict(frame=fid, p73_class=CL[pc], worldcover=WCN[wv],
                              wc_pure_km2=round(float(((wc == wv) & m).sum()) * KM2, 1),
                              recall_vs_wc=round(tp / max(int(((wc == wv) & m).sum()), 1), 4),
                              precision_vs_wc=round(tp / max(int(((cls == pc) & m).sum()), 1), 4)))
        # 3. BASE_CLASS crosstab (diagnostic)
        bc = to20_agree(read10(fid, "p69a_base_class.tif"), g)
        for b, bn in BASE.items():
            mb = valid & (bc == b)
            if not mb.any():
                continue
            for c, n in CL.items():
                k = float(((cls == c) & mb).sum())
                if k:
                    bct.append(dict(frame=fid, base_class=bn, p73_class=n, km2=round(k * KM2, 2),
                                    pct_of_base=round(100 * k / mb.sum(), 2)))
        # 4. where UNCERTAIN occurs
        u = cls == 10
        for wv in np.unique(wc):
            m = wc == wv
            unc.append(dict(frame=fid, by="worldcover", value=WCN.get(int(wv), int(wv)),
                            uncertain_km2=round(float((u & m).sum()) * KM2, 2),
                            uncertain_pct_of_value=round(100 * float((u & m).sum()) / max(int((m & valid).sum()), 1), 2)))
        for b, bn in BASE.items():
            m = bc == b
            if m.any():
                unc.append(dict(frame=fid, by="base_class", value=bn, uncertain_km2=round(float((u & m).sum()) * KM2, 2),
                                uncertain_pct_of_value=round(100 * float((u & m).sum()) / max(int((m & valid).sum()), 1), 2)))
        frames[fid] = dict(g=g, cls=cls, top=top, wc=wc, bc=bc, valid=valid)
        print(f"{fid}: p73 " + ", ".join(f"{r['p73_class']} {r['share_pct']}%" for r in area if r["frame"] == fid),
              flush=True)

    # cross-frame agreement on the shared global 20 m grid
    a, b = frames["B1"], frames["B2"]
    ta, tb = a["g"]["transform"], b["g"]["transform"]
    dr, dc = int(round((tb.f - ta.f) / 20.0)), int(round((ta.c - tb.c) / 20.0))   # B1 cell (i,j) = B2 (i+dr, j+dc)
    r0, r1 = max(0, -dr), min(a["g"]["ny"], b["g"]["ny"] - dr); c0, c1 = max(0, -dc), min(a["g"]["nx"], b["g"]["nx"] - dc)
    A = a["cls"][r0:r1, c0:c1]; Bm = b["cls"][r0 + dr:r1 + dr, c0 + dc:c1 + dc]
    both = (A != 255) & (Bm != 255)
    xagree = dict(overlap_km2=round(float(both.sum()) * KM2, 1), agreement=round(float((A[both] == Bm[both]).mean()), 4),
                  agreement_excl_uncertain=round(float((A == Bm)[both & (A != 10) & (Bm != 10)].mean()), 4))
    print("cross-frame agreement on overlap:", xagree, flush=True)

    T = CFG.TABLES
    pd.DataFrame(area).to_csv(QAD / "class_areas.csv", index=False)
    pd.DataFrame(wcagr).to_csv(QAD / "worldcover_walltowall.csv", index=False)
    B = pd.DataFrame(bct); B.to_csv(T / "p73_rf20_baseclass_crosswalk.csv", index=False)
    pd.DataFrame(unc).to_csv(QAD / "uncertain_where.csv", index=False)
    (QAD / "cross_frame_agreement.json").write_text(json.dumps(xagree, indent=2))
    print("\nVEGETATION_AGRICULTURE decomposed by p73:")
    print(B[B.base_class == "VEGETATION_AGRICULTURE"].pivot(index="p73_class", columns="frame",
                                                             values="pct_of_base").round(1).to_string())

    # 5a. per-class agreement maps vs WorldCover
    cmap_cls = ListedColormap([COL[k] for k in sorted(COL)]); norm_cls = BoundaryNorm(
        [k - 0.5 for k in sorted(COL)] + [255.5], len(COL))
    for fid, d in frames.items():
        st = 4
        fig, ax = plt.subplots(1, 7, figsize=(35, 8))
        ax[0].imshow(d["cls"][::st, ::st], cmap=cmap_cls, norm=norm_cls, interpolation="nearest")
        ax[0].set_title(f"{fid} p73 class")
        ax[6].imshow(np.where(d["valid"], (d["cls"] == 10), np.nan)[::st, ::st], cmap="magma", interpolation="nearest")
        ax[6].set_title("UNCERTAIN (bright)")
        for x_, (pc, wv, nm) in zip(ax[1:], ((1, 80, "WATER"), (2, 40, "CROPLAND"), (6, 90, "WETLAND_REED"),
                                             (7, 50, "BUILT_UP"), (8, 60, "BARE_SAND"))):
            rgb = np.ones(d["cls"][::st, ::st].shape + (3,), "f4")
            p_, w_ = (d["cls"] == pc)[::st, ::st], (d["wc"] == wv)[::st, ::st]
            rgb[p_ & w_] = (0.3, 0.3, 0.3); rgb[p_ & ~w_] = (0.85, 0.1, 0.1); rgb[~p_ & w_] = (0.1, 0.3, 0.9)
            x_.imshow(rgb, interpolation="nearest"); x_.set_title(f"{nm}: grey both, red p73 only, blue WC only")
        for x_ in ax:
            x_.set_axis_off()
        fig.tight_layout(); fig.savefig(FIGD / f"{fid}_classes_vs_worldcover.png", dpi=90); plt.close(fig)

    # 5b. six QA zones, chosen by declared rules
    def v002(fid, band):
        return to20_agree(read10(fid, "m6_labels_v002.tif", band), frames[fid]["g"], mixed=0)
    b1, b2 = frames["B1"], frames["B2"]
    lab1, dis1 = v002("B1", 1), v002("B1", 7)
    pw2 = to20_agree((read10("B2", "labels.tif", 8) >= 20).astype("u1"), b2["g"], mixed=0)
    from pyproj import Transformer
    tt = Transformer.from_crs(4326, 32636, always_xy=True)
    def at(fid, lon, lat):
        x, y = tt.transform(lon, lat); t = frames[fid]["g"]["transform"]
        return int((t.f - y) / 20), int((x - t.c) / 20)
    wmix = ndimage.uniform_filter(pw2.astype("f4"), size=2 * HALF + 1)
    ZONES = [
        ("Z1_B1_S1_disputed_fields", "B1", best_window((dis1 == 1) & (b1["wc"] == 40)),
         "max count of S1-disputed (v002 band 7) cells on WorldCover cropland"),
        ("Z2_B1_flooded_fields", "B1", best_window((lab1 == 1) & (b1["wc"] == 40)),
         "max count of v002 FLOOD cells on WorldCover cropland"),
        ("Z3_B2_wetland_reed", "B2", best_window(b2["wc"] == 90), "max count of WorldCover herbaceous wetland"),
        ("Z4_B1_Oleshky_sands", "B1", at("B1", 33.05, 46.55), "fixed: Oleshky sands centre 46.55N 33.05E"),
        ("Z5_B1_Kherson_built", "B1", at("B1", 32.61, 46.64), "fixed: Kherson city 46.64N 32.61E"),
        ("Z6_B2_preexisting_water_shore", "B2",
         np.unravel_index(np.argmin(np.abs(wmix - 0.5)), wmix.shape), "window whose p60 pre-water share is closest to 50 %"),
    ]
    cmap_wc = ListedColormap(["#ffffff", "#006400", "#ffbb22", "#ffff4c", "#f096ff", "#fa0000", "#b4b4b4", "#f0f0f0",
                              "#0064c8", "#0096a0", "#00cf75", "#fae6a0"])
    norm_wc = BoundaryNorm([-.5, 5, 15, 25, 35, 45, 55, 65, 75, 85, 92, 97, 105], 12)
    cmap_bc = ListedColormap(["#2166ac", "#f1c232", "#e6d3a3", "#cc0000", "#8e7cc3", "#999999", "#ff00ff", "#dddddd"])
    norm_bc = BoundaryNorm([-.5, .5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 254.5], 8)
    for name, fid, (rc, cc), rule in ZONES:
        d = frames[fid]; g = d["g"]
        rc = int(np.clip(rc, HALF, g["ny"] - HALF - 1)); cc = int(np.clip(cc, HALF, g["nx"] - HALF - 1))
        sl = (slice(rc - HALF, rc + HALF), slice(cc - HALF, cc + HALF))
        win10 = Window(g["c0"] + 2 * (cc - HALF), g["r0"] + 2 * (rc - HALF), 4 * HALF, 4 * HALF)
        with rasterio.open(OUT / fid / "composite_preall.tif") as s:
            dn = list(s.descriptions)
            ndvi = s.read(dn.index("NDVI_pre_max") + 1, window=win10).astype("f4") / 1e4
            mnd = s.read(dn.index("MNDWI_pre_med") + 1, window=win10).astype("f4") / 1e4
        ndvi[ndvi < -3] = np.nan; mnd[mnd < -3] = np.nan
        fig, ax = plt.subplots(1, 6, figsize=(30, 5.6))
        ax[0].imshow(ndvi, vmin=0, vmax=0.9, cmap="YlGn"); ax[0].set_title("NDVI_pre_max")
        ax[1].imshow(mnd, vmin=-0.6, vmax=0.6, cmap="RdBu"); ax[1].set_title("MNDWI_pre_med")
        ax[2].imshow(d["wc"][sl], cmap=cmap_wc, norm=norm_wc, interpolation="nearest"); ax[2].set_title("WorldCover (pure)")
        ax[3].imshow(d["bc"][sl], cmap=cmap_bc, norm=norm_bc, interpolation="nearest"); ax[3].set_title("old BASE_CLASS")
        ax[4].imshow(d["cls"][sl], cmap=cmap_cls, norm=norm_cls, interpolation="nearest"); ax[4].set_title("p73 class")
        ax[5].imshow(np.where(d["top"][sl] == 255, np.nan, d["top"][sl]), vmin=30, vmax=100, cmap="magma")
        ax[5].set_title("p73 top probability x100")
        for x_ in ax:
            x_.set_axis_off()
        t = g["transform"]
        fig.suptitle(f"{name} ({fid}) centre E{t.c + 20 * cc:.0f} N{t.f - 20 * rc:.0f} -- {rule}")
        fig.tight_layout(); fig.savefig(FIGD / f"{name}.png", dpi=80); plt.close(fig)
        c_ = d["cls"][sl]; v_ = c_ != 255
        zones_t.append(dict(zone=name, frame=fid, centre_E=round(t.c + 20 * cc), centre_N=round(t.f - 20 * rc),
                            rule=rule, **{f"p73_{CL[k]}_pct": round(100 * float((c_ == k).sum()) / max(v_.sum(), 1), 1)
                                          for k in CL}))
    pd.DataFrame(zones_t).to_csv(QAD / "zones.csv", index=False)
    legend = ", ".join(f"{k}={v}" for k, v in CL.items())
    (FIGD / "LEGEND.txt").write_text(f"p73 colours: {json.dumps(COL)}\nclasses: {legend}\n")
    print("-> tables/p73_rf20_baseclass_crosswalk.csv, tables/p73_rf20_qa/")


if __name__ == "__main__":
    main()
