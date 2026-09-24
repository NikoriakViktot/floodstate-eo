# New in floodstate-eo, 2026-09-24. STATUS: ACTIVE_DIAGNOSTIC. Explains A2 candidates; changes no model, label or split.
"""P89 -- cropland candidate audit: what physically ARE the isolated field-like predictions on cropland?

The ~18-22 km2 of A2 "large isolated field-like components" (p73 CROPLAND share >= 0.8, no v002 FLOOD pixel,
>= 0.01 km2) are UNRESOLVED CROPLAND-ASSOCIATED SAR CANDIDATES -- not false water. A 20 m CROPLAND class can hide
irrigation channels, ponds, waterlogged patches, narrow water absorbed by the dominant class, genuinely flooded fields
missing from v002, and wet soil / irrigation that changes backscatter without a flood.

For every candidate component of every arm (TEST geography, frozen threshold) this computes evidence that already
exists in the repository, and assigns a DIAGNOSTIC group by rules fixed here before the first run:

  A PRE_EXISTING_OR_IRRIGATION_WATER  pre-breach water: S2 pre-water frequency >= 20 % on >= 20 % of the component,
                                      OR S1 water on the PRE-breach June dates (06-01, 06-02) on >= 30 %,
                                      OR p73 WATER on >= 20 %
  C FLOOD_PLAUSIBLE_CROPLAND          not A; S1 water on >= 50 % at the peak dates (06-09/13/14) and < 10 % pre-breach;
                                      within 500 m of v002 FLOOD or median HAND <= 2 m; and, where S2 06-08/06-18 is
                                      valid, median dMNDWI or dNDWI > +0.05 at one of them (otherwise flagged
                                      optical_unavailable, still C)
  B WET_OR_IRRIGATED_AGRICULTURE      not A/C; some wetness evidence (S1 water on >= 30 % at any date, or S2 median
                                      dMNDWI/dNDMI > +0.05) but disconnected (> 500 m from v002 FLOOD and HAND > 2 m)
  D UNRESOLVED_OR_LIKELY_SAR_ARTIFACT everything else
These groups are a triage for the next step, not ground truth. HAND: floodplain/<zone>_hand_m.tif read with its own
transform (its origin sits half a 20 m cell off the S2 grid; irrelevant for component medians, recorded anyway).

Outputs: <case_study>/tables/p89_candidates_<ARM>.csv, p89_group_summary.csv, p89_persistence.csv;
         <case_study>/tables/p89_maps/*.png (frame maps for all arms, candidate gallery, group maps)
"""
from __future__ import annotations
import importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from scipy import ndimage
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

HERE = Path(__file__).resolve().parent
OUT = CFG.BULK_ROOT / "frames10"
RUNS = HERE.parents[1] / "runs"
MAPS = CFG.TABLES / "p89_maps"
ARMS = ("U0d", "U0z", "U1")
FRAMES = ("B1", "B2")
JUNE = {"B1": "ZONE_4_FLOODWAY_june2023_s32", "B2": "ZONE_2_KHERSON_DELTA_flood_june2023"}
HANDZ = {"B1": "ZONE_4_DAM_TO_KHERSON_FLOODWAY", "B2": "ZONE_2_KHERSON_DELTA"}
PRE_D, PEAK_D = ("2023-06-01", "2023-06-02"), ("2023-06-09", "2023-06-13", "2023-06-14")
GROUPS = {"A": "PRE_EXISTING_OR_IRRIGATION_WATER", "B": "WET_OR_IRRIGATED_AGRICULTURE",
          "C": "FLOOD_PLAUSIBLE_CROPLAND", "D": "UNRESOLVED_OR_LIKELY_SAR_ARTIFACT"}
PX = 1e-4


def _load(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def onto(src, tr, crs, F, rs=Resampling.nearest, nd=np.nan, dtype="f4"):
    d = np.full((F["ny"], F["nx"]), nd, dtype)
    reproject(source=src.astype(dtype), destination=d, src_transform=tr, src_crs=crs, dst_transform=F["transform"],
              dst_crs=CFG.CRS_METRIC, resampling=rs, src_nodata=nd, dst_nodata=nd)
    return d


def evidence(fid, F):
    """Per-pixel evidence layers on the frame's 10 m lattice."""
    Ev = {}
    with rasterio.open(OUT / fid / "labels.tif") as s:
        Ev["pre_wf"] = s.read(8).astype("f4"); Ev["pre_wf"][Ev["pre_wf"] < 0] = np.nan
    with rasterio.open(OUT / fid / "m6_labels_v002.tif") as s:
        Ev["y"] = s.read(1); Ev["disputed"] = s.read(7) == 1; Ev["n_pos_peak"] = s.read(2)
    with rasterio.open(OUT / fid / "composite_preall.tif") as s:
        d = list(s.descriptions)
        for b in ("MNDWI_pre_med", "NDWI_pre_med", "NDVI_pre_max", "NDMI_pre_med"):
            a = s.read(d.index(b) + 1).astype("f4"); a[a == -32768] = np.nan; Ev[b] = a / 1e4
    # s2_sparse_support d* bands are NOT used: p72 subtracts an UNSCALED pre median (x10000) from a scaled event
    # index, so every d* value saturates at +-32767 (found here, 2026-09-24). The change is recomputed from the
    # correctly scaled absolute event bands minus the composite PRE median, both in index units.
    with rasterio.open(OUT / fid / "s2_sparse_support.tif") as s:
        d = list(s.descriptions)
        for tag in ("0608", "0618"):
            Ev["valid_" + tag] = s.read(d.index("valid_" + tag) + 1).astype("f4")
            for i in ("MNDWI", "NDWI", "NDMI"):
                v = s.read(d.index(f"{i}_{tag}") + 1).astype("f4"); v[v == -32768] = np.nan
                v = v / 1e4 - Ev[f"{i}_pre_med"]; v[Ev["valid_" + tag] == 0] = np.nan
                Ev[f"d{i}_{tag}"] = v
    with rasterio.open(CFG.BULK_ROOT / "floodplain" / HANDZ[fid] / f"{HANDZ[fid]}_hand_m.tif") as s:
        h = s.read(1).astype("f4"); h[h == s.nodata] = np.nan
        Ev["hand"] = onto(h, s.transform, s.crs, F)
    z = np.load(CFG.S1_CACHE / JUNE[fid] / "per_scene_water.npz", allow_pickle=True)
    shp = tuple(int(v) for v in z["shape"]); tr = from_origin(float(z["x0"]), float(z["y1"]), float(z["cell"]),
                                                              float(z["cell"]))
    Ev["s1_dates"] = sorted(k for k in z.keys() if k.startswith("2023"))
    for k in Ev["s1_dates"]:
        w = np.unpackbits(z[k], count=shp[0] * shp[1]).astype("f4").reshape(shp)
        v = np.unpackbits(z["valid_" + k], count=shp[0] * shp[1]).astype(bool).reshape(shp)
        w[~v] = np.nan
        Ev["s1_" + k[:10]] = onto(w, tr, CFG.CRS_METRIC, F)
    prew = Ev["pre_wf"] >= 20
    Ev["dist_prewater_m"] = ndimage.distance_transform_edt(~prew) * 10.0
    Ev["dist_flood_m"] = ndimage.distance_transform_edt(Ev["y"] != 1) * 10.0
    return Ev


def med(a, m):
    v = a[m]; v = v[np.isfinite(v)]
    return float(np.median(v)) if v.size else np.nan


def frac(a, m):
    v = a[m]; v = v[np.isfinite(v)]
    return float(np.mean(v)) if v.size else np.nan


def audit_arm(arm, fid, F, Ev, p73, p73max, role, has, E):
    thr = json.loads((RUNS / f"{arm}_B1B2_v1" / "validation_threshold.json").read_text())["threshold"]
    with rasterio.open(OUT / fid / "m6" / f"{arm}_score.tif") as s:
        q = s.read(1)
    score = np.where(q == 65535, np.nan, q / 1e4).astype("f4")
    geo = (role == 3) & has
    y = np.where(np.isin(role, (1, 2, 3)) & has, Ev["y"], 255)
    fl = geo & (y == 1)
    pred = geo & (np.nan_to_num(score, nan=-1) >= thr)
    comp, sel, area = E._isolated(pred, geo, p73, fl)
    rows = []
    for k in np.flatnonzero(sel):
        m = comp == k
        rr, cc = np.nonzero(m)
        ring = ndimage.binary_dilation(m, iterations=2) & ~m
        pts = np.vstack([rr, cc]).astype("f8"); ev_, vec = np.linalg.eigh(np.cov(pts)); ev_ = np.clip(ev_, 1e-9, None)
        pr = pts.T @ vec; ext = (pr.max(0) - pr.min(0) + 1).prod()
        perim = int((np.pad(m, 1)[1:, :] != np.pad(m, 1)[:-1, :]).sum() + (np.pad(m, 1)[:, 1:] != np.pad(m, 1)[:, :-1]).sum())
        s1 = {d[:10]: frac(Ev["s1_" + d[:10]], m) for d in Ev["s1_dates"]}
        r = dict(arm=arm, frame=fid, component=int(k), area_km2=round(float(m.sum()) * PX, 4),
                 centre_E=round(F["transform"].c + 10 * cc.mean()), centre_N=round(F["transform"].f - 10 * rr.mean()),
                 rectangularity=round(float(m.sum() / ext), 3), elongation=round(float(np.sqrt(ev_[1] / ev_[0])), 2),
                 compactness=round(float(4 * np.pi * m.sum() / max(perim, 1) ** 2), 3),
                 score_median=round(med(score, m), 3),
                 pre_wf_median=med(Ev["pre_wf"], m), pre_wf_ge20_frac=frac((Ev["pre_wf"] >= 20).astype("f4"), m),
                 p73_water_frac=frac((p73 == 1).astype("f4"), m), p73_cropland_frac=frac((p73 == 2).astype("f4"), m),
                 p73_maxscore_median=med(p73max, m),
                 ring_water_or_wetland_frac=frac(np.isin(p73, (1, 6)).astype("f4"), ring),
                 dist_prewater_m_min=float(Ev["dist_prewater_m"][m].min()),
                 dist_flood_m_min=float(Ev["dist_flood_m"][m].min()),
                 hand_median=med(Ev["hand"], m),
                 MNDWI_pre_med=med(Ev["MNDWI_pre_med"], m), NDWI_pre_med=med(Ev["NDWI_pre_med"], m),
                 NDVI_pre_max=med(Ev["NDVI_pre_max"], m),
                 **{f"{b}_median": med(Ev[b], m) for b in ("dMNDWI_0608", "dNDWI_0608", "dNDMI_0608",
                                                            "dMNDWI_0618", "dNDWI_0618", "dNDMI_0618")},
                 s2_0608_valid_frac=frac(Ev["valid_0608"], m), s2_0618_valid_frac=frac(Ev["valid_0618"], m),
                 disputed_frac=frac(Ev["disputed"].astype("f4"), m),
                 p60_npos_peak_ge2_frac=frac((Ev["n_pos_peak"] >= 2).astype("f4"), m),
                 **{f"s1_wet_{d}": (round(v, 3) if np.isfinite(v) else None) for d, v in s1.items()})
        pre = np.nanmean([s1.get(d, np.nan) for d in PRE_D]); peak = np.nanmean([s1.get(d, np.nan) for d in PEAK_D])
        anyd = np.nanmax(list(s1.values()))
        r.update(s1_wet_pre_mean=round(float(pre), 3), s1_wet_peak_mean=round(float(peak), 3),
                 s1_wet_any_max=round(float(anyd), 3))
        opt_valid = (r["s2_0608_valid_frac"] or 0) > 0.5 or (r["s2_0618_valid_frac"] or 0) > 0.5
        wet_opt = any((r.get(f"{b}_median") or -9) > 0.05 for b in ("dMNDWI_0608", "dNDWI_0608", "dMNDWI_0618",
                                                                     "dNDWI_0618"))
        wet_soil = any((r.get(f"{b}_median") or -9) > 0.05 for b in ("dMNDWI_0608", "dNDMI_0608", "dMNDWI_0618",
                                                                      "dNDMI_0618"))
        connected = r["dist_flood_m_min"] <= 500 or (np.isfinite(r["hand_median"]) and r["hand_median"] <= 2.0)
        if (r["pre_wf_ge20_frac"] or 0) >= 0.2 or (pre >= 0.3) or (r["p73_water_frac"] or 0) >= 0.2:
            g = "A"
        elif peak >= 0.5 and pre < 0.1 and connected and (wet_opt or not opt_valid):
            g = "C"
        elif (anyd >= 0.3 or wet_soil) and not connected:
            g = "B"
        else:
            g = "D"
        r.update(group=g, group_name=GROUPS[g], optical_unavailable=not opt_valid, connected=bool(connected))
        rows.append(r)
    return pd.DataFrame(rows), comp, sel, score, thr, pred, geo, y


def main():
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    E, P84 = _load("m6_eval"), _load("p84_m6_split_b1b2")
    MAPS.mkdir(parents=True, exist_ok=True)
    allc, store = [], {}
    for fid in FRAMES:
        F = CG.frame_grid(fid); Ev = evidence(fid, F)
        p73 = P84.p73_10m(fid, F)
        with rasterio.open(OUT / fid / "p73_rf20" / "surface_max_score_20m.tif") as s:
            ms = s.read(1).astype("f4"); ms[ms == 255] = np.nan
            p73max = np.repeat(np.repeat(ms, 2, 0), 2, 1)
        r0 = int(round((F["transform"].f - s.transform.f) / 10)); c0 = int(round((s.transform.c - F["transform"].c) / 10))
        pm = np.full((F["ny"], F["nx"]), np.nan, "f4"); h, w = min(p73max.shape[0], F["ny"] - r0), min(p73max.shape[1], F["nx"] - c0)
        pm[r0:r0 + h, c0:c0 + w] = p73max[:h, :w] / 100.0
        with rasterio.open(OUT / fid / "m6_split_v1_role.tif") as s:
            role = s.read(1)
        with rasterio.open(OUT / fid / "s1_change.tif") as s:
            d = list(s.descriptions); has = (s.read(d.index("n_valid_event") + 1) > 0) & (s.read(1) != -32768)
        store[fid] = dict(F=F, Ev=Ev, p73=p73, role=role, arms={})
        for arm in ARMS:
            df, comp, sel, score, thr, pred, geo, y = audit_arm(arm, fid, F, Ev, p73, pm, role, has, E)
            allc.append(df); store[fid]["arms"][arm] = dict(comp=comp, sel=sel, score=score, thr=thr, pred=pred,
                                                            geo=geo, y=y, df=df)
            print(f"{fid} {arm}: {len(df)} candidates, {df.area_km2.sum():.2f} km2; groups "
                  + ", ".join(f"{g} {df[df.group == g].area_km2.sum():.2f}" for g in "ABCD"), flush=True)
    C = pd.concat(allc, ignore_index=True)
    for arm in ARMS:
        C[C.arm == arm].to_csv(CFG.TABLES / f"p89_candidates_{arm}.csv", index=False)
    S = C.groupby(["arm", "frame", "group", "group_name"]).agg(n=("component", "size"), km2=("area_km2", "sum")).reset_index()
    tot = C.groupby(["arm", "group", "group_name"]).agg(n=("component", "size"), km2=("area_km2", "sum")).reset_index()
    tot.insert(1, "frame", "ALL"); S = pd.concat([S, tot], ignore_index=True)
    S["km2"] = S.km2.round(3); S.to_csv(CFG.TABLES / "p89_group_summary.csv", index=False)
    print(S[S.frame == "ALL"].to_string(index=False))

    # persistence: how much of each U0d candidate's area is still a candidate in U0z / U1
    per = []
    for fid in FRAMES:
        a = store[fid]["arms"]
        base_mask = a["U0d"]["sel"][a["U0d"]["comp"]]
        for r in a["U0d"]["df"].itertuples():
            m = a["U0d"]["comp"] == r.component
            per.append(dict(frame=fid, component=r.component, group=r.group, area_km2=r.area_km2,
                            **{f"still_candidate_in_{o}": round(float((a[o]["sel"][a[o]["comp"]] & m).sum() / m.sum()), 3)
                               for o in ("U0z", "U1")},
                            **{f"predicted_in_{o}": round(float((a[o]["pred"] & m).sum() / m.sum()), 3)
                               for o in ("U0z", "U1")}))
        del base_mask
    Pp = pd.DataFrame(per); Pp.to_csv(CFG.TABLES / "p89_persistence.csv", index=False)
    print(Pp.groupby("group")[["area_km2", "predicted_in_U0z", "predicted_in_U1"]].agg(
        {"area_km2": "sum", "predicted_in_U0z": "mean", "predicted_in_U1": "mean"}).round(3).to_string())

    # ---- maps -------------------------------------------------------------------------------------------------------
    gcol = {"A": (0.1, 0.4, 0.9), "B": (0.1, 0.7, 0.2), "C": (0.9, 0.1, 0.1), "D": (0.95, 0.6, 0.0)}
    for fid in FRAMES:
        st = 4; d = store[fid]; fig, ax = plt.subplots(1, len(ARMS) + 1, figsize=(8 * (len(ARMS) + 1), 12))
        for j, arm in enumerate(ARMS):
            a = d["arms"][arm]; y = a["y"]; geo = a["geo"]; pr = a["pred"]
            rgb = np.ones(pr.shape + (3,), "f4") * 0.95
            rgb[np.isin(d["role"], (1, 2))] = 0.85
            rgb[geo] = 0.75
            rgb[geo & (y == 1) & pr] = (0.1, 0.6, 0.1); rgb[geo & (y == 1) & ~pr] = (0.1, 0.2, 0.9)
            rgb[geo & (y == 0) & pr] = (0.9, 0.0, 0.0); rgb[geo & (y == 255) & pr] = (1.0, 0.6, 0.0)
            rgb[a["sel"][a["comp"]]] = (0.6, 0.0, 0.6)
            ax[j].imshow(rgb[::st, ::st], interpolation="nearest")
            ax[j].set_title(f"{fid} {arm} (thr {a['thr']:.2f}) TEST: green TP, blue FN, red FP on labelled dry,\n"
                            f"orange predicted on IGNORE, purple = A2 isolated field-like candidates")
        g = np.ones(d["p73"].shape + (3,), "f4") * 0.9
        a = d["arms"]["U0d"]
        for r in a["df"].itertuples():
            g[a["comp"] == r.component] = gcol[r.group]
        ax[-1].imshow(g[::st, ::st], interpolation="nearest")
        ax[-1].set_title("U0d candidates by diagnostic group: A blue pre-existing/irrigation, B green wet/irrigated,\n"
                         "C red flood-plausible, D orange unresolved/artefact")
        for x_ in ax:
            x_.set_axis_off()
        fig.tight_layout(); fig.savefig(MAPS / f"{fid}_arms_and_groups.png", dpi=70); plt.close(fig)

    # candidate gallery: the largest U0d candidates of each group, every arm side by side with evidence
    big = C[C.arm == "U0d"].sort_values("area_km2", ascending=False).groupby("group").head(3)
    for r in big.itertuples():
        d = store[r.frame]; a0 = d["arms"]["U0d"]; m = a0["comp"] == r.component
        rr, cc = np.nonzero(m); pad = 60
        sl = (slice(max(rr.min() - pad, 0), rr.max() + pad), slice(max(cc.min() - pad, 0), cc.max() + pad))
        Ev = d["Ev"]
        panels = [("MNDWI_pre_med", Ev["MNDWI_pre_med"][sl], "RdBu", -0.6, 0.6),
                  ("pre-water freq % (S2)", Ev["pre_wf"][sl], "Blues", 0, 100),
                  ("S1 water 06-01/02 (pre)", np.nanmean([Ev["s1_2023-06-01"][sl], Ev["s1_2023-06-02"][sl]], 0), "Blues", 0, 1),
                  ("S1 water peak 06-09/13/14", np.nanmean([Ev["s1_" + x][sl] for x in PEAK_D], 0), "Blues", 0, 1),
                  ("dMNDWI 06-08", Ev["dMNDWI_0608"][sl], "RdBu", -0.4, 0.4),
                  ("HAND m", Ev["hand"][sl], "terrain", 0, 10),
                  ("p73 class", d["p73"][sl].astype("f4"), ListedColormap(["#2166ac", "#f1c232", "#b6d7a8", "#274e13", "#93c47d",
                   "#8e7cc3", "#cc0000", "#e6d3a3", "#999999", "#ff00ff"]), 0.5, 10.5)]
        panels += [(f"{arm} score (thr {d['arms'][arm]['thr']:.2f})", d["arms"][arm]["score"][sl], "magma", 0, 1)
                   for arm in ARMS]
        fig, ax = plt.subplots(1, len(panels), figsize=(3.2 * len(panels), 3.8))
        for x_, (t, im, cm, lo, hi) in zip(ax, panels):
            x_.imshow(im, cmap=cm, vmin=lo, vmax=hi, interpolation="nearest")
            x_.contour(m[sl], levels=[0.5], colors="cyan", linewidths=0.6); x_.set_title(t, fontsize=8); x_.set_axis_off()
        fig.suptitle(f"{r.frame} U0d candidate {r.component}: {r.area_km2:.3f} km2, group {r.group} {r.group_name} "
                     f"(E{r.centre_E} N{r.centre_N})", fontsize=9)
        fig.tight_layout(); fig.savefig(MAPS / f"cand_{r.group}_{r.frame}_{r.component}.png", dpi=80); plt.close(fig)
    print("-> tables/p89_candidates_*.csv, p89_group_summary.csv, p89_persistence.csv, p89_maps/")


if __name__ == "__main__":
    main()
