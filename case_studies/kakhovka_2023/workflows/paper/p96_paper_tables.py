# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Assembles the publication tables from committed CSV/JSON only.
"""P96 -- publication tables T01..T21 for Paper 3 (Kakhovka 2023 inundation), from committed tables and run outputs only.

Never reads bulk rasters, never reads stdout. Every table carries an evidence level and area semantics where areas
appear; tables/README.md defines every metric; tables/manifest.json lists every source file with sha256 and the git
commit. `--check` re-derives everything into a temporary directory and diffs against the committed tables.

Evidence levels: independent_physical, cross_sensor, weak_label_agreement, contextual.
Area semantics: observed_S1, mapped_UNet, terrain_reconstructed, literature_reported.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, tempfile, time
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]          # case_studies/kakhovka_2023
REPO = ROOT.parents[1]
T = ROOT / "tables"; RUNS = ROOT / "runs"; PUB = ROOT / "publication" / "tables"
SEMANTICS = {"observed_S1": "water seen by the Sentinel-1 dark-water rule on that date, minus pre-breach water (mapped, sensor-limited)",
             "mapped_UNet": "U-Net score >= frozen validation threshold (agreement with weak labels, persistent-water concept)",
             "terrain_reconstructed": "cells the reconstructed water surface allows (DEM < WSE, connected), minus the pre-breach regime",
             "literature_reported": "figure quoted from an operational or published product with its own AOI, date and reference water; context only"}
ARMS_V1 = ["U0d", "U0z", "U1", "U2"]; ARMS_V3 = ["U0d", "U2", "U2b"]
KEY_DATES = ["2023-06-05", "2023-06-06", "2023-06-07", "2023-06-08", "2023-06-09", "2023-06-10", "2023-06-11", "2023-06-12", "2023-06-13",
             "2023-06-14", "2023-06-15", "2023-06-16", "2023-06-18", "2023-06-21", "2023-06-25", "2023-06-30"]
LITERATURE = [  # context only; every row must be VERIFIED against the source before submission
    dict(source="UNOSAT (via CEOBS 2023 / REACH 2023)", quantity="flooded area 6-9 June 2023", value_km2=620, verify="VERIFY: exact product, AOI, date, reference-water definition"),
    dict(source="CEOBS 2023 (citing satellite analyses)", quantity="flooded area on 13 June 2023", value_km2=180, verify="VERIFY: exact product and AOI"),
    dict(source="Yale HRL 2023", quantity="flooded area, southern Ukraine, June 2023", value_km2=520, verify="VERIFY: report, date, AOI")]

OUT = {}   # tid -> (df, caption, sources, evidence_level)


def sha(p: Path) -> str:
    h = hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()


def read(name, **kw):
    p = T / name if not str(name).startswith("runs/") else ROOT / name
    return pd.read_csv(p, **kw), p


def put(tid, df, caption, sources, level):
    OUT[tid] = (df.copy(), caption, [str(s) for s in sources], level)


# --------------------------------------------------------------------------------------------------------------------
def t01_inventory():
    s1, p1 = read("p94_flood_dynamics_s1.csv"); s2, p2 = read("p94_flood_dynamics_s2.csv"); g, p3 = read("p59_swot_vs_kherson.csv")
    n, p4 = read("p59_swot_flood_nodes.csv", usecols=["date", "node_id"]); qa, p5 = read("p77d_v003_A_scene_qa.csv")
    rows = []
    for (d, o), gg in s1[s1.region == "DNIPRO_CORRIDOR"].groupby(["date", "orbit"]):
        rows.append(dict(dataset="Sentinel-1 GRD/RTC, dark-water mask (M3)", date=d, detail=o, coverage_of_observable_domain=float(gg.coverage.iloc[0]), evidence_level="cross_sensor"))
    for d, gg in s2[(s2.region == "DNIPRO_CORRIDOR") & s2.reliable].groupby("date"):
        rows.append(dict(dataset="Sentinel-2 L2A index stack (NDWI>0 & MNDWI>0)", date=d, detail=gg.frames.iloc[0], coverage_of_observable_domain=float(gg.coverage.iloc[0]), evidence_level="cross_sensor"))
    nd = n.groupby("date").node_id.nunique()
    rows.append(dict(dataset="SWOT L2_HR_RiverSP v2.0 nodes (1-day orbit), accepted", date=f"{nd.index.min()}..{nd.index.max()}", detail=f"{len(nd)} days, {int(nd.median())} nodes/day median", coverage_of_observable_domain=np.nan, evidence_level="independent_physical"))
    gg = g.dropna(subset=["H_gauge_evrf"])
    rows.append(dict(dataset="Kherson gauge 80805 (river yearbook), daily", date=f"{gg.date.min()}..{gg.date.max()}", detail=f"{len(gg)} days; BS77 -> EVRF2019 +0.22 m; 6-12 June flagged in the sea yearbook (Paper 1)", coverage_of_observable_domain=np.nan, evidence_level="independent_physical"))
    rows.append(dict(dataset="S1 reference scenes 2023-04-15..05-28 (May reference water, p89b/p89c)", date="2023-04-15..2023-05-28", detail=f"{int(qa.admitted.sum())} admitted of {len(qa)} scenes (variant A QA)", coverage_of_observable_domain=np.nan, evidence_level="cross_sensor"))
    rows += [dict(dataset="Seamless DEM (p55): bathymetric bed + FABDEM v1.2, EVRF2019, 20 m", date="2019-2022 bed; FABDEM 2011-2015 epoch", detail="Paper 2", coverage_of_observable_domain=np.nan, evidence_level="independent_physical"),
             dict(dataset="ICESat-2 ATL08 night ground segments (p57 chain)", date="2019-2025", detail="altimetric consistency check (Paper 2 chain)", coverage_of_observable_domain=np.nan, evidence_level="independent_physical"),
             dict(dataset="ESA WorldCover 2021 v200, 10 m", date="2021", detail="RF20 training reference and decomposition classes", coverage_of_observable_domain=np.nan, evidence_level="contextual")]
    put("T01", pd.DataFrame(rows), "Data inventory: acquisition dates, coverage of the Sentinel-1 observable domain, and the role of every dataset.", [p1, p2, p3, p4, p5], "mixed")


def t02_labels():
    v2, p1 = read("p77_labels_v002_summary.csv"); a, p2 = read("p77d_v003_A_areas.csv"); tr, p3 = read("p77d_v003_A_transition_v002.csv")
    A = a[(a.reference_domain == "ALL") & (~a.ontology.str.startswith("event_water"))].pivot(index="frame", columns="ontology", values="km2").reset_index()
    A.columns.name = None; A = A.rename(columns={c: f"v003A_{c}_km2" for c in A.columns if c != "frame"})
    V = v2.rename(columns={"flood_km2": "v002_FLOOD_km2", "nonflood_km2": "v002_NON_FLOOD_km2", "ignore_km2": "v002_IGNORE_km2"})[["frame", "v002_FLOOD_km2", "v002_NON_FLOOD_km2", "v002_IGNORE_km2"]]
    D = V.merge(A, on="frame"); D["area_semantics"] = "weak_reference_label"
    Tr = tr.pivot_table(index=["frame", "v002"], columns="v003_final", values="km2", aggfunc="sum").reset_index(); Tr.columns.name = None
    put("T02", D, "Weak reference labels per frame: v002 (FLOOD / NON_FLOOD / IGNORE) and v003_A (LAND / EVENT_FLOOD / REFERENCE_WATER / UNKNOWN), km2. EVENT_FLOOD is pixel-identical to v002 FLOOD.", [p1, p2, p3], "weak_label_agreement")
    put("T02b", Tr, "Transition v002 -> v003_A per frame, km2 (the change is on the negative side and in the UNKNOWN domain).", [p3], "weak_label_agreement")


def t03_split():
    c, p1 = read("m6_split_v1_composition.csv"); s, p2 = read("m6_split_v1_strata.csv"); man = json.loads((T / "m6_split_v1_manifest.json").read_text())
    rows = [dict(item="block size (m)", value=man["block_m"]), dict(item="buffer (px / m)", value=f"{man['buffer_px']} / {int(man['buffer_px']) * 10}"),
            dict(item="patch (px / km)", value=f"{man['patch']} / {int(man['patch']) * 10 / 1000:.2f}"), dict(item="blocks train/val/test", value=str(man["n_blocks"])),
            dict(item="patches train/val/test", value=str(man["n_patches"])), dict(item="accepted draw / seed", value=f"{man['accepted_draw']} / {man['seed']}"),
            dict(item="selection reads", value=man["selection_reads"]), dict(item="anti-leakage", value=man["anti_leakage"]),
            dict(item="minimum feasible block", value="patch + 2 x buffer = 5.12 + 1.28 km; a 5 km split leaves no validation patch (p84 rebuild, 2026-09-25)")]
    put("T03", pd.DataFrame(rows), "Frozen spatial-block split m6_split_v1: geometry, counts and rationale.", [p1, p2, T / "m6_split_v1_manifest.json"], "weak_label_agreement")
    put("T03b", s, "Stratum shares of the frozen split (train / validation / test), km2.", [p2], "weak_label_agreement")
    put("T03c", c, "Composition of the frozen split per frame, km2.", [p1], "weak_label_agreement")


def _runs():
    R = []
    for a in ARMS_V1:
        R.append((a, "v002", RUNS / f"{a}_B1B2_v1"))
    for a in ARMS_V3:
        R.append((a, "v003_A", RUNS / f"{a}_B1B2_v003A"))
    return [(a, l, r) for a, l, r in R if (r / "config.json").exists()]


def t04_arms():
    rows, src = [], []
    for arm, lab, rd in _runs():
        c = json.loads((rd / "config.json").read_text()); th = json.loads((rd / "validation_threshold.json").read_text()); src += [rd / "config.json", rd / "validation_threshold.json"]
        rows.append(dict(arm=arm, labels=lab, run=rd.name, n_channels=len(c["channels"]), channels=" ".join(c["channels"]), note=c["note"], threshold=th["threshold"],
                         val_F1=th["val_F1"], epochs=c["epochs"], batch=c["batch"], lr=c["lr"], seed=c["seed"], seconds=c.get("seconds"), diagnostic_only=(arm == "U2b")))
    put("T04", pd.DataFrame(rows), "U-Net arms: inputs, labels, frozen validation threshold and training settings. U2b is a diagnostic experiment (W_pre is also a label ingredient).", src, "weak_label_agreement")


def t05_endpoints():
    rows, src = [], []
    for arm, lab, rd in _runs():
        e = pd.read_csv(rd / "eval_d1a/endpoints.csv", index_col=0).value; ci = pd.read_csv(rd / "eval_d1a/endpoints_ci.csv", index_col=0); src += [rd / "eval_d1a/endpoints.csv", rd / "eval_d1a/endpoints_ci.csv"]
        for k, v in e.items():
            try:
                val = float(v)
            except (TypeError, ValueError):
                continue
            rows.append(dict(arm=arm, labels=lab, endpoint=k, value=val, ci_lo=float(ci.lo.get(k, np.nan)), ci_hi=float(ci.hi.get(k, np.nan))))
    D = pd.DataFrame(rows); D["meaning"] = "agreement with held-out weak reference labels (TEST blocks), not flood-mapping accuracy"
    put("T05", D, "D1 endpoints per arm on the frozen TEST blocks with 95 % spatial-block bootstrap intervals (2000 resamples).", src, "weak_label_agreement")


def t06_paired():
    rows, src = [], []
    for name, a, b, lab in [("compare_U0d_vs_U0z", "U0d", "U0z", "v002"), ("compare_U0d_vs_U1", "U0d", "U1", "v002"), ("compare_U0d_vs_U2", "U0d", "U2", "v002"),
                            ("compare_U0d_vs_U2_v003A", "U0d", "U2", "v003_A"), ("compare_U2_vs_U2b_v003A", "U2", "U2b", "v003_A")]:
        p = RUNS / name / "paired_bootstrap.csv"
        if not p.exists():
            continue
        pb = pd.read_csv(p, index_col=0); src.append(p)
        for k, r in pb.iterrows():
            rows.append(dict(comparison=f"{b} - {a}", labels=lab, endpoint=k, median=r["median"], ci_lo=r["lo"], ci_hi=r["hi"], excludes_zero=bool((r["lo"] > 0) or (r["hi"] < 0)),
                             independent="no" if b == "U2b" else "weak-label", note="not independent: W_pre is a label ingredient" if b == "U2b" else ""))
    put("T06", pd.DataFrame(rows), "Paired arm comparisons (B minus A) on identical spatial blocks, 2000 resamples, 95 % intervals.", src, "weak_label_agreement")


def t07_attribution():
    e, p1 = read("p90_v003A_endpoints.csv"); pr, p2 = read("p90_v003A_paired.csv")
    keep = [c for c in e.columns if not c.endswith(("_lo", "_hi"))]
    L = e.melt(id_vars=["run", "threshold"], value_vars=[c for c in keep if c not in ("run", "threshold")], var_name="endpoint", value_name="value")
    lo = e.melt(id_vars=["run"], value_vars=[c for c in e.columns if c.endswith("_lo")], var_name="endpoint", value_name="ci_lo"); lo["endpoint"] = lo.endpoint.str[:-3]
    hi = e.melt(id_vars=["run"], value_vars=[c for c in e.columns if c.endswith("_hi")], var_name="endpoint", value_name="ci_hi"); hi["endpoint"] = hi.endpoint.str[:-3]
    D = L.merge(lo, on=["run", "endpoint"], how="left").merge(hi, on=["run", "endpoint"], how="left")
    D["area_semantics"] = np.where(D.endpoint.str.contains("km2"), "mapped_UNet", "")
    put("T07", D, "v003_A attribution endpoints per finished run at its own frozen threshold: predicted flood on TEST REFERENCE_WATER, EVENT_FLOOD recall, LAND false positives, UNKNOWN burden; 95 % block-bootstrap intervals.", [p1], "weak_label_agreement")
    pr["excludes_zero"] = (pr.lo > 0) | (pr.hi < 0); pr["independent"] = np.where(pr.B.str.startswith("U2b"), "no (W_pre circularity)", "weak-label")
    put("T07b", pr, "Paired differences (B minus A) of the v003_A attribution endpoints across label sets and inputs.", [p2], "weak_label_agreement")


def t08_audit():
    g, p1 = read("p89_group_summary.csv"); r, p2 = read("p89_retention.csv")
    g["area_semantics"] = "mapped_UNet"
    put("T08", g, "Cropland-associated SAR candidates (p89 audit): groups A (water before the breach), B (wet/irrigated agriculture), D (unresolved / likely SAR artefact) per arm and frame.", [p1], "weak_label_agreement")
    put("T08b", r, "Retention of U0d candidate area by the other v002 arms (fraction of km2).", [p2], "weak_label_agreement")


def t09_rf():
    m, p1 = read("p73_rf20_metrics.csv"); cm, p2 = read("p73_rf20_confusion_matrix.csv", index_col=0)
    M = m.copy(); M["evaluation"] = M.evaluation.astype(str)
    macro = M.groupby("evaluation")[["precision", "recall", "F1"]].mean().round(4).reset_index(); macro["cls"] = "MACRO_MEAN"; macro["n"] = M.groupby("evaluation").n.sum().values
    C = cm.values.astype(float); oa = np.trace(C) / C.sum(); pe = (C.sum(0) * C.sum(1)).sum() / C.sum() ** 2; kappa = (oa - pe) / (1 - pe)
    D = pd.concat([M, macro], ignore_index=True); D["OA_spatial_cv"] = np.where(D.evaluation == "spatial_block_cv_5fold", round(float(oa), 4), np.nan)
    D["kappa_spatial_cv_csv_only"] = np.where(D.evaluation == "spatial_block_cv_5fold", round(float(kappa), 4), np.nan)
    D["reference"] = "ESA WorldCover 2021 (training reference; agreement, not validation)"
    put("T09", D, "RF20 surface classification: per-class precision / recall / F1 with support, macro means and overall agreement, spatial-block 5-fold CV and frame transfers. Reference = WorldCover 2021, the training reference.", [p1, p2], "contextual")
    cm2 = cm.copy(); cm2.index.name = "reference \\ predicted"
    put("T10", cm2.reset_index(), "RF20 confusion matrix (spatial-block CV, counts).", [p2], "contextual")
    ca, p3 = read("p73_rf20_class_area.csv"); wc, p4 = read("p73_rf20_qa/worldcover_walltowall.csv")
    put("T10b", ca, "RF20 class areas per frame, km2 (mapped areas of a context product).", [p3], "contextual")
    put("T10c", wc, "RF20 vs WorldCover wall-to-wall agreement on WorldCover-pure cells (recall / precision vs the training reference).", [p4], "contextual")


def _p95_variants():
    V = {}
    for sfx, name in [("", "hand_and_ceiling"), ("_ceiling_only", "ceiling_only"), ("_connected_ceiling", "connected_ceiling"),
                      ("_connected_ceiling_dem_uncorrected", "connected_ceiling_dem_uncorrected"),
                      ("_connected_ceiling_closure_p59_m050", "connected_ceiling (superseded closure, +0.5 m)")]:
        p = T / f"p95_manifest{sfx}.json"
        if p.exists():
            V[name] = (sfx, json.loads(p.read_text()), p)
    return V


def t11_terrain():
    rows, src = [], []
    for name, (sfx, man, p) in _p95_variants().items():
        src.append(p); c = man["constants"]
        rows.append(dict(variant=name, suffix=sfx or "(default)", rule=man.get("rule_variant"), closure=man.get("closure"), closure_offset_vs_p59_m=man.get("closure_offset_vs_p59_H_evrf_m"),
                         margin_m=c.get("margin_m"), river_floor_m=c["RIVER_LEVEL_M"], swot_max_dist_m=c["SWOT_MAX_DIST_M"], dist_to_prewater_max_m=c["DIST_MAX_M"],
                         baseline_until=c["baseline_until"], wse_method=man.get("wse_method", ""), status="superseded" if "p59" in (man.get("closure") or "") else "current"))
    put("T11", pd.DataFrame(rows), "Terrain reconstruction: rules, closure, constants and the water-surface method per variant. The superseded closure row is kept for traceability.", src, "independent_physical")
    p = T / "p95e_uncertainty_components.csv"
    if p.exists():
        put("T11b", pd.read_csv(p), "Uncertainty components of the terrain reconstruction (Monte-Carlo inputs): closure, gauge, SWOT node height, per-node time interpolation, DEM error by WorldCover class (Paper 2 / p57).", [p], "independent_physical")


def t12_daily():
    p = T / "p95_daily_area_pooled_connected_ceiling.csv"; d = pd.read_csv(p); src = [p]
    D = d[d.date.isin(KEY_DATES)].copy(); D["area_semantics"] = "terrain_reconstructed"; D = D.rename(columns={"new_km2": "A_central_km2", "new_volume_hm3": "V_central_hm3", "potential_km2": "W_total_central_km2"})
    pu = T / "p95e_area_volume_uncertainty.csv"
    if pu.exists():
        U = pd.read_csv(pu); src.append(pu)
        D = D.merge(U[["date", "region", "A_p05_km2", "A_p50_km2", "A_p95_km2", "V_p05_hm3", "V_p50_hm3", "V_p95_hm3", "n_draws"]], on=["date", "region"], how="left")
    pg = T / "p95g_mc_daily.csv"
    if pg.exists():
        G = pd.read_csv(pg); src.append(pg)
        D = D.merge(G[["date", "region", "W_total_km2_p05", "W_total_km2_p25", "W_total_km2_p50", "W_total_km2_p75", "W_total_km2_p95",
                       "A_new_km2_p05", "A_new_km2_p25", "A_new_km2_p50", "A_new_km2_p75", "A_new_km2_p95", "V_new_hm3_p05", "V_new_hm3_p50", "V_new_hm3_p95", "n_draws"]].rename(columns={"n_draws": "n_draws_emulator"}), on=["date", "region"], how="left")
    for name, (sfx, man, mp) in _p95_variants().items():
        q = T / f"p95_daily_area_pooled{sfx}.csv"
        if q.exists() and name != "connected_ceiling":
            tag = f"{name.split(' ')[0]}{'_superseded' if 'superseded' in name else ''}"
            x = pd.read_csv(q)[["date", "region", "new_km2", "potential_km2"]].rename(columns={"new_km2": f"A_{tag}_km2", "potential_km2": f"W_total_{tag}_km2"}); D = D.merge(x, on=["date", "region"], how="left"); src.append(q)
    D["definition_note"] = "A_* = NEW inundation (cells allowed by the water surface outside the same-rule pre-breach regime); W_total_* = TOTAL water surface on the day (all cells allowed by the water surface, incl. channels, lakes, reed beds) -- the quantity comparable with operational 'flooded area' products; wetland submergence is in T13/T14"
    put("T12", D, "Daily terrain-reconstructed inundation per region and key date: TOTAL water surface (W_total_*: all water on the day incl. pre-breach channels, lakes and reed beds; p05..p95 of 100 000 emulator draws) and NEW inundation (A_*: 40 spatial Monte-Carlo draws p05/p50/p95 and 100 000 emulator draws p05..p95), for the central run (DEM class-bias corrected), the p42 HAND rule, the ceiling-only variant, the uncorrected-DEM and superseded-closure sensitivities; volume of new water.", src, "independent_physical")


def t21_reservoir():
    p = T / "p95f_reservoir_daily.csv"; h = T / "p95f_hypsometry_dem.csv"
    if not p.exists():
        return
    R = pd.read_csv(p); R["area_semantics"] = "reservoir_pool (terrain-integrated under the observed sloped surface)"
    put("T21", R, "Kakhovka pool during the drawdown, per day: levels at the outlet (SWOT), Nikopol (press) and Rozumivka (gauge), surface gradient, pool water area and volume under the sloped surface (seamless DEM inside the pre-breach pool polygon), daily volume change, DniproHES inflow, implied breach outflow, and the downstream new-water volume and total water surface (terrain reconstruction) with the Kherson stage.", [p], "independent_physical")
    if h.exists():
        put("T22", pd.read_csv(h), "Pool hypsometry from the seamless DEM (level surface) against the design Table 19 (BS-77 levels + 0.185 m).", [h], "independent_physical")


def t13_terrain_vs_s1():
    rows, src = [], []
    for name, (sfx, man, mp) in _p95_variants().items():
        q = T / f"p95_validation_s1_pooled{sfx}.csv"
        if q.exists():
            v = pd.read_csv(q); v.insert(0, "variant", name); rows.append(v); src.append(q)
    D = pd.concat(rows, ignore_index=True); D["observation_domain"] = "S1 valid footprint of the date, owned zone area, outside the p42 cut rectangles (Inhulets rows: inside the Inhulets rectangle)"
    D["POD_excl_note"] = "sensitivity: exclusion = same-rule pre-breach potential ('normally wet'), fixed before any result was read"
    put("T13", D, "Terrain reconstruction vs Sentinel-1 new dark water per acquisition date, region and variant: hit / miss / miss-on-normally-wet / terrain-only km2, POD, FAR, CSI (primary) and POD excluding normally-wet cells (sensitivity).", src, "cross_sensor")


def t14_ontology():
    rows, src = [], []
    for d in ("20230609", "20230613", "20230614"):
        p = T / f"p95d_agreement_{d}_summary.csv"
        if p.exists():
            rows.append(pd.read_csv(p)); src.append(p)
    if rows:
        D = pd.concat(rows, ignore_index=True); D["category_meaning"] = D.category.map({"A": "terrain+ / S1+", "B": "terrain+ / S1- (sensor blind spot or reconstruction excess)", "C": "terrain- / S1+ (submergence signal on normally-wet ground, or false SAR water on land)", "N": "neither"})
        put("T14", D, "Disagreement ontology terrain x Sentinel-1 by zone and date: category areas split by ground elevation relative to the water surface, normally-wet flag, WorldCover and RF20 classes (km2).", src, "contextual")


def t15_icesat():
    p = T / "p95c_icesat2_check_0609.csv"
    if p.exists():
        D = pd.read_csv(p); D["check_type"] = "altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map"
        put("T15", D, "ICESat-2 altimetric consistency check per zone and agreement category: residual seamless DEM minus ICESat-2 (median, p10, p90), ICESat-2 ground minus water surface, share of segments below the surface.", [p], "independent_physical")


def t16_accounting():
    pk, p1 = read("p93_peak_vs_label_vs_model.csv"); ar, p2 = read("p92_flood_area_dam_to_liman.csv")
    rows = []
    for _, r in pk.iterrows():
        rows += [dict(region=r.region, quantity="S1 new dark water, 06-09 scene", km2=r.peak_0609_new_water_km2, area_semantics="observed_S1"),
                 dict(region=r.region, quantity="S1 new dark water, >= 2 of 3 peak dates (label recipe)", km2=r.label_recipe_2of3_new_km2, area_semantics="observed_S1"),
                 dict(region=r.region, quantity="S1 total dark water, 06-09 (incl. pre-breach water)", km2=r.peak_0609_total_water_km2, area_semantics="observed_S1"),
                 dict(region=r.region, quantity="pre-breach water (S1 06-01/02 or p60 pre_water_frac >= 20 %)", km2=r.pre_breach_water_km2, area_semantics="observed_S1"),
                 dict(region=r.region, quantity="U2b predicted event flood (persistent concept)", km2=r.U2b_predicted_km2, area_semantics="mapped_UNet")]
    for _, r in ar[ar.run == "U2b_B1B2_v003A"].iterrows():
        rows.append(dict(region=r.region, quantity="U2b predicted flood (p92 accounting)", km2=r.predicted_flood_km2, area_semantics="mapped_UNet", unobserved_km2=r.unobserved_no_s1_event_km2))
    pu = T / "p95_daily_area_pooled_connected_ceiling.csv"
    if pu.exists():
        d = pd.read_csv(pu)
        for reg in ("DNIPRO_CORRIDOR", "P42_FLOODPLAIN_DOMAIN", "INHULETS_VALLEY_rect"):
            g = d[d.region == reg]; pkrow = g.loc[g.new_km2.idxmax()]
            rows.append(dict(region=reg, quantity=f"terrain-reconstructed new inundation, peak day {pkrow.date}", km2=pkrow.new_km2, area_semantics="terrain_reconstructed"))
            rows.append(dict(region=reg, quantity="terrain-reconstructed new inundation, 06-09", km2=float(g[g.date == "2023-06-09"].new_km2.iloc[0]), area_semantics="terrain_reconstructed"))
    for l in LITERATURE:
        rows.append(dict(region="reported AOI (differs)", quantity=f"{l['source']}: {l['quantity']}", km2=l["value_km2"], area_semantics="literature_reported", verify=l["verify"]))
    put("T16", pd.DataFrame(rows), "Area accounting with explicit semantics: observed (S1), mapped (U-Net), terrain-reconstructed and literature-reported figures are different quantities and are never compared as validation.", [p1, p2], "mixed")


def t17_swot_gauge():
    n, p1 = read("p59_swot_flood_nodes.csv"); g, p2 = read("p59_swot_vs_kherson.csv", parse_dates=["date"])
    from pyproj import Transformer
    kx, ky = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True).transform(32.612026, 46.623750)
    n["H_local"] = n.wse + n.geoid_hght - n.zeta; n["d_km"] = np.hypot(n.x - kx, n.y - ky) / 1e3; near = n[n.d_km <= 3.0].copy(); near["date"] = pd.to_datetime(near.date)
    day = near.groupby("date").agg(swot_p50=("H_local", "median"), n_nodes=("node_id", "nunique")).reset_index().merge(g[["date", "H_gauge_evrf"]], on="date")
    day["gauge_minus_swot"] = day.H_gauge_evrf - day.swot_p50
    def per(lo, hi): return day[(day.date >= lo) & (day.date <= hi)]
    rows = []
    for name, sub in [("all days", day), ("pre-breach 05-26..06-05", per("2023-05-26", "2023-06-05")), ("rise and peak 06-06..06-14", per("2023-06-06", "2023-06-14")), ("recession 06-15..07-10", per("2023-06-15", "2023-07-10"))]:
        r = sub.gauge_minus_swot.dropna().values
        if len(r):
            rows.append(dict(period=name, n_days=len(r), bias_m=round(float(r.mean()), 3), median_m=round(float(np.median(r)), 3), MAE_m=round(float(np.abs(r).mean()), 3), RMSE_m=round(float(np.sqrt((r ** 2).mean())), 3),
                             NMAD_m=round(float(1.4826 * np.median(np.abs(r - np.median(r)))), 3), min_m=round(float(r.min()), 3), max_m=round(float(r.max()), 3), independent_unit="day (one 11:00 UTC overpass vs a date-only daily gauge value)",
                             sign="gauge - satellite (Paper 1 convention); satellite = EGG2015-referenced SWOT height with c_Kherson = 0"))
    put("T17", pd.DataFrame(rows), "SWOT-input consistency at Kherson after re-anchoring: nodes within 3 km of the gauge, daily median vs the daily gauge (river yearbook, EVRF2019). The frame validation itself is Paper 1; this only checks the p95 input.", [p1, p2], "independent_physical")
    day["date"] = day.date.dt.strftime("%Y-%m-%d"); put("T17b", day.round(3), "Daily values behind T17.", [p1, p2], "independent_physical")


def t18_dem():
    d, p = read("p57_dem_accuracy_night.csv")
    keep = d[d.set.str.contains("C seamless") & (d.set.str.contains("ALL night") | d.set.str.contains("ZONE_2_KHERSON_DELTA") | d.set.str.contains("ZONE_4_DAM_TO_KHERSON_FLOODWAY") | d.set.str.contains("low terrain"))].copy()
    keep["source"] = "Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here"
    put("T18", keep, "Seamless DEM accuracy against night ICESat-2 ground segments (Paper 2): RMSE, MAE, bias, median, LE90, LE95, NMAD by zone and WorldCover class; the class rows feed the DEM error model of T11b.", [p], "independent_physical")


def t19_series():
    s1, p1 = read("p94_flood_dynamics_s1.csv"); s2, p2 = read("p94_flood_dynamics_s2.csv"); e, p3 = read("p94_flood_dynamics_estuary_s1.csv")
    a = s1[["date", "sensor", "orbit", "region", "coverage", "water_km2", "new_water_km2", "new_water_common_footprint_km2"]].copy(); a["area_semantics"] = "observed_S1"
    b = s2[s2.reliable][["date", "sensor", "region", "coverage", "water_km2", "new_water_km2"]].copy(); b["orbit"] = ""; b["area_semantics"] = "observed_S2 (NDWI>0 & MNDWI>0)"
    c = e[["date", "sensor", "region", "coverage", "water_km2", "new_water_km2", "new_water_common_footprint_km2"]].copy(); c["orbit"] = ""; c["area_semantics"] = "observed_S1"
    put("T19", pd.concat([a, b, c], ignore_index=True), "Per-acquisition-date new water (not water before the breach) inside the Sentinel-1 observable domain, with coverage; S2 only where >= 30 % of the region was cloud-free; estuary zone on its own grid.", [p1, p2, p3], "cross_sensor")


def t20_block_sensitivity():
    rows, src = [], []
    for sp, km in [("m6_split_v1", 10.0), ("m6_split_s5", 5.0), ("m6_split_s7p5", 7.5), ("m6_split_s15", 15.0), ("m6_split_s20", 20.0)]:
        man = T / f"{sp}_manifest.json"; rd = RUNS / ("U2_B1B2_v003A" if sp == "m6_split_v1" else f"U2_B1B2_v003A_{sp.split('_')[-1]}")
        status = "split built" if man.exists() else "split infeasible (no validation patch survives the buffer)" if sp == "m6_split_s5" else "not built"
        row = dict(split=sp, block_km=km, status=status)
        if man.exists():
            m = json.loads(man.read_text()); row.update(n_blocks=str(m.get("n_blocks")), n_patches=str(m.get("n_patches"))); src.append(man)
        if (rd / "eval_d1a/endpoints.csv").exists():
            e = pd.read_csv(rd / "eval_d1a/endpoints.csv", index_col=0).value; ci = pd.read_csv(rd / "eval_d1a/endpoints_ci.csv", index_col=0); src += [rd / "eval_d1a/endpoints.csv"]
            row["status"] = "U2 v003_A trained and evaluated"
            for k in ("G_F1", "G_IoU", "G_PR_AUC", "A_FP_area_dry_cropland_km2", "B_recall_flooded_open_low_veg", "W_IoU", "BU_FP_area_km2", "A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2"):
                row[k] = float(e.get(k, np.nan)); row[f"{k}_lo"] = float(ci.lo.get(k, np.nan)); row[f"{k}_hi"] = float(ci.hi.get(k, np.nan))
            th = json.loads((rd / "validation_threshold.json").read_text()); row["threshold"] = th["threshold"]
        rows.append(row)
    put("T20", pd.DataFrame(rows), "Block-size sensitivity (U2 on v003_A): the same recipe on splits with 7.5, 10 (frozen), 15 and 20 km blocks; each split has its own TEST geography, so only the endpoint values and intervals are compared, never differences.", src, "weak_label_agreement")


def readme():
    defs = [("POD", "hit / (hit + miss): share of S1 new dark water that the reconstruction allows, on the observation domain"),
            ("FAR", "terrain_only / (hit + terrain_only): share of reconstructed new water that S1 did not see (includes sensor blind spots)"),
            ("CSI", "hit / (hit + miss + terrain_only)"), ("POD_excl_normally_wet", "hit / (hit + miss - miss_on_normally_wet); sensitivity only; exclusion rule fixed a priori"),
            ("precision / recall / F1 / IoU", "on unique full-frame TEST pixels owned by the frame, against weak reference labels"), ("PR-AUC", "average precision of the continuous score vs weak labels"),
            ("A1 / A2", "A1 = predicted flood on labelled dry cropland (false positive vs weak label); A2 = predicted flood burden on UNLABELLED cropland (never called false positive)"),
            ("bias / MAE / RMSE", "mean, mean absolute and root-mean-square of the residual (sign stated per table)"), ("NMAD", "1.4826 x median |r - median(r)|"), ("LE90 / LE95", "90th / 95th percentile of |r|"),
            ("95 % interval", "percentile 2.5 / 97.5 of 2000 spatial-block bootstrap resamples (seed 20260923); paired comparisons resample identical physical blocks"),
            ("Monte-Carlo band", "p05 / p50 / p95 over 40 full spatial draws of DEM, closure, gauge, SWOT and interpolation errors (p95e); the 100 000-draw cluster-normal emulator (p95g) gives p05/p25/p50/p75/p95 per day"),
            ("pool volume", "seamless DEM integrated under the sloped daily water surface inside the pre-breach pool polygon (p95f); design Table 19 for reference"),
            ("OA", "overall agreement with the reference classification"), ("macro mean", "unweighted mean over classes")]
    lines = ["# Publication tables (generated by workflows/paper/p96_paper_tables.py -- do not edit by hand)", "",
             "Every model number is *agreement with weak reference labels*, never flood-mapping accuracy. Areas carry a semantics column:", ""]
    lines += [f"- `{k}`: {v}" for k, v in SEMANTICS.items()] + ["", "## Metric definitions", ""] + [f"- **{k}**: {v}" for k, v in defs] + ["", "## Tables", ""]
    for tid, (df, cap, src, lvl) in sorted(OUT.items()):
        lines.append(f"- **{tid}** [{lvl}] {cap} ({len(df)} rows)")
    return "\n".join(lines) + "\n"


def build(outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    for f in (t01_inventory, t02_labels, t03_split, t04_arms, t05_endpoints, t06_paired, t07_attribution, t08_audit, t09_rf, t11_terrain, t12_daily,
              t13_terrain_vs_s1, t14_ontology, t15_icesat, t16_accounting, t17_swot_gauge, t18_dem, t19_series, t20_block_sensitivity, t21_reservoir):
        f()
    man = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), git_commit=subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
               tables={}, sources={})
    for tid, (df, cap, src, lvl) in sorted(OUT.items()):
        df.to_csv(outdir / f"{tid}.csv", index=False)
        (outdir / f"{tid}.md").write_text(f"**{tid}.** {cap}  \n*Evidence level: {lvl}.*\n\n" + df.to_markdown(index=False) + "\n")
        man["tables"][tid] = dict(caption=cap, evidence_level=lvl, rows=int(len(df)), sources=[str(Path(s).relative_to(REPO)) if str(s).startswith(str(REPO)) else s for s in src], sha256=sha(outdir / f"{tid}.csv"))
        for s in src:
            p = Path(s)
            if p.exists():
                man["sources"][str(p.relative_to(REPO))] = sha(p)
    (outdir / "README.md").write_text(readme()); (outdir / "manifest.json").write_text(json.dumps(man, indent=1))
    return man


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); a = ap.parse_args()
    if a.check:
        with tempfile.TemporaryDirectory() as td:
            build(Path(td)); bad = []
            for tid in OUT:
                if sha(Path(td) / f"{tid}.csv") != sha(PUB / f"{tid}.csv"):
                    bad.append(tid)
            print("CHECK", "OK" if not bad else f"DRIFT in {bad}"); raise SystemExit(1 if bad else 0)
    man = build(PUB); print(f"-> {PUB.relative_to(REPO)}: {len(man['tables'])} tables, {len(man['sources'])} sources, commit {man['git_commit'][:7]}")
    for tid, (df, cap, src, lvl) in sorted(OUT.items()):
        print(f"  {tid:5s} {len(df):5d} rows  [{lvl}]  {cap[:90]}")


if __name__ == "__main__":
    main()
