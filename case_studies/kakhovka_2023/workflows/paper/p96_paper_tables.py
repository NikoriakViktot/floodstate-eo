# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Assembles the publication tables from committed CSV/JSON only.
"""P96 -- publication tables T01..T26 for Paper 3 (Kakhovka 2023 inundation), from committed tables and run outputs only.

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
             "terrain_reconstructed": "cells the reconstructed water surface allows (terrain < WSE, connected), minus the pre-breach regime",
             "observed_S2": "water or surface class seen by Sentinel-2 on that date (frozen p25 rule), observed cells only (reservoir tables T23-T26)",
             "literature_reported":"figure quoted from an operational or published product with its own AOI, date and reference water; context only"}
ARMS_V1 = ["U0d", "U0z", "U1", "U2"]; ARMS_V3 = ["U0d", "U2", "U2b"]; ARMS_V4 = ["U0d", "U1", "U2", "U2b"]
SEEDS_V4 = (20260923, 20261001, 20261002)                          # the p86 default seed first (review F11: seed variability)
KEY_DATES = ["2023-06-05", "2023-06-06", "2023-06-07", "2023-06-08", "2023-06-09", "2023-06-10", "2023-06-11", "2023-06-12", "2023-06-13",
             "2023-06-14", "2023-06-15", "2023-06-16", "2023-06-18", "2023-06-21", "2023-06-25", "2023-06-30"]
LITERATURE = [  # context only; every row must be VERIFIED against the source before submission
    dict(source="UNOSAT product 3616 (9 June 2023)", quantity="flooded LAND, cumulative satellite-detected 6-9 June (ICEYE, Sentinel-3, Sentinel-2); pre-existing water is a separate reference class; preliminary, not field-validated",
         value_km2=620, quantity_semantics="flooded_land_new (reference water excluded)", temporal_semantics="cumulative_2023-06-06..09", verify="VERIFY: product id, AOI, reference-water definition (via CEOBS 2023 / REACH 2023)"),
    dict(source="UNOSAT product 3623 (13 June 2023)", quantity="land that appears flooded on 13 June vs reference water of 3/5 June", value_km2=180,
         quantity_semantics="flooded_land_new (reference water excluded)", temporal_semantics="snapshot_2023-06-13", verify="VERIFY: product id and AOI"),
    dict(source="Kadam et al. 2024 (HEC-RAS 1D/2D, 300 m breach scenario)", quantity="modelled flood extent (scenario, not an observation)", value_km2=823,
         quantity_semantics="model_extent (definition per source)", temporal_semantics="scenario maximum", verify="VERIFY: extent definition, AOI, scenario")]
    # Yale HRL 2023 (520 km2) dropped 2026-09-28: no source found, unknown semantics (literature audit)

OUT = {}   # tid -> (df, caption, sources, evidence_level)
CENTRAL_NOTE = ("reported central value = Monte-Carlo MEDIAN (*_p50_*) with the p05-p95 interval of the coherent Monte-Carlo worlds (p95e rev 2); *_central_* = the "
                "deterministic nominal run (draw 0, unperturbed inputs), a diagnostic given in brackets; its position relative to the ensemble is attributed to "
                "the error components in T11d (maintainer decision 2026-09-28; recomputed 2026-09-29 after the code review)")
UNCERTAINTY_NOTE = ("PRIMARY interval = p05/p50/p95 of the coherent Monte-Carlo worlds of p95e rev 2 (review F01-F05): per draw ONE terrain-error realization over the "
                    "union mosaic (FABDEM-sourced cells only; class NMAD x a unit-variance field with the nested covariance fitted to the FABDEM - ICESat-2 residuals, "
                    "p95j) and ONE water-surface realization over all nodes and days (datum closure, gauge, SWOT wse_u, gap-dependent interpolation error; every term "
                    "once, through the node heights), the pre-breach baseline rebuilt with the same realization; W_total, A_new and both volumes are quantiles of "
                    "their OWN ensembles (no shift construction). The 100 000-draw cluster-normal emulator (p95g) is a computational DIAGNOSTIC outside the evidence "
                    "path (maintainer decision D-EMU, 2026-09-29): it has no connectivity and its W_total is the nominal total plus its new-area deviations; it is "
                    "reported in T12d only")


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
    D = V.merge(A, on="frame"); src = [p1, p2, p3]
    Tr = tr.pivot_table(index=["frame", "v002"], columns="v003_final", values="km2", aggfunc="sum").reset_index(); Tr.columns.name = None; Tr.insert(0, "labels", "v002 -> v003_A")
    q2, q4, q4t = T / "p77_labels_v002_summary_notrace.csv", T / "p77d_v004_areas.csv", T / "p77d_v004_transition_v002.csv"
    if q2.exists() and q4.exists():
        v2n = pd.read_csv(q2).rename(columns={"flood_km2": "v002_notrace_FLOOD_km2", "nonflood_km2": "v002_notrace_NON_FLOOD_km2", "ignore_km2": "v002_notrace_IGNORE_km2"})
        a4 = pd.read_csv(q4); A4 = a4[(a4.reference_domain == "ALL") & (~a4.ontology.str.startswith("event_water"))].pivot(index="frame", columns="ontology", values="km2").reset_index()
        A4.columns.name = None; A4 = A4.rename(columns={c: f"v004_{c}_km2" for c in A4.columns if c != "frame"})
        D = D.merge(v2n[["frame", "v002_notrace_FLOOD_km2", "v002_notrace_NON_FLOOD_km2", "v002_notrace_IGNORE_km2"]], on="frame").merge(A4, on="frame"); src += [q2, q4]
    if q4t.exists():
        t4 = pd.read_csv(q4t).pivot_table(index=["frame", "v002"], columns="v003_final", values="km2", aggfunc="sum").reset_index(); t4.columns.name = None
        t4.insert(0, "labels", "v002_notrace -> v004"); Tr = pd.concat([Tr, t4], ignore_index=True); src.append(q4t)
    D["area_semantics"] = "weak_reference_label"
    put("T02", D, "Weak reference labels per frame, km2: v002 (FLOOD / NON_FLOOD / IGNORE) and v003_A (LAND / EVENT_FLOOD / REFERENCE_WATER / UNKNOWN), built on the original M2 (with the post-event TRACE window, in-sample threshold; frozen history), and v002_notrace and v004, the same rules on the corrected M2 (no TRACE, out-of-fold threshold; review F09/F10). EVENT_FLOOD is pixel-identical to the FLOOD of the v002 version it inherits.", src, "weak_label_agreement")
    put("T02b", Tr, "Transition v002 -> v003_A and v002_notrace -> v004 per frame, km2 (the v003 rule changes the negative side and the UNKNOWN domain).", [p3] + ([q4t] if q4t.exists() else []), "weak_label_agreement")
    q = T / "p77g_label_transitions.csv"
    if q.exists():
        put("T02d", pd.read_csv(q), "What the corrected M2 changed in the weak labels: pixel transitions v003_A -> v004 and v002 -> v002_notrace per frame (km2 and share of the source class). The S1 inputs, the May reference state and W_pre are identical in both versions of a pair, so every change comes from the M2 masks (review F09/F10).", [q], "weak_label_agreement")


def t02c_m2_threshold():
    """Review F09/F10: the optical model M2 behind the labels -- operating threshold from the fit set (superseded) vs from inner
    out-of-fold scores, and the outer-TEST recall each gives; the original model (with TRACE) next to the corrected one."""
    rows, src = [], []
    for tag, model in (("", "M2 original (84 features, 17 from the post-event TRACE window)"), ("_notrace", "M2 corrected (67 PRE + EVENT features; labels v004)")):
        p = T / f"p65b_m2_folds{tag}.csv"
        if not p.exists():
            continue
        f = pd.read_csv(p); f = f[f.baseline == "preall"].copy(); f.insert(0, "model", model); src.append(p)
        f = f.rename(columns={"threshold": "threshold_oof", "recall": "recall_at_oof", "precision": "precision_at_oof", "F1": "F1_at_oof"})
        rows.append(f[["model", "regime", "outer_fold", "n_test", "test_prevalence", "inner_AP", "AP", "threshold_insample_superseded", "recall_at_insample_superseded",
                       "threshold_oof", "n_calibration", "recall_at_oof", "precision_at_oof", "F1_at_oof"]])
        for rg, g in f.groupby("regime"):
            rows.append(pd.DataFrame([dict(model=model, regime=rg, outer_fold="median", n_test=int(g.n_test.sum()), inner_AP=g.inner_AP.median(), AP=g.AP.median(),
                                           threshold_insample_superseded=g.threshold_insample_superseded.median(), recall_at_insample_superseded=g.recall_at_insample_superseded.median(),
                                           threshold_oof=g.threshold_oof.median(), recall_at_oof=g.recall_at_oof.median(), precision_at_oof=g.precision_at_oof.median(), F1_at_oof=g.F1_at_oof.median())]))
    if rows:
        put("T02c", pd.concat(rows, ignore_index=True), "The optical model M2 behind the weak labels (review F09/F10): nested spatial cross-validation on 5 km blocks (PRE_ALL baseline; outer folds block and buffered). Per outer fold, the operating threshold for a target recall of 0.90 set on the forest's own fit cells (in-sample, superseded) and on inner out-of-fold scores (fit and calibration cells disjoint, whole blocks), and the recall each reaches on the outer TEST blocks; the fold median gives T50 of the label masks. Original model (84 features incl. 17 from the post-event TRACE window, labels v002 / v003_A) next to the corrected model (67 PRE + EVENT features, labels v004). M2 is trained on S1-derived weak labels (p60): agreement with them, not accuracy.", src, "weak_label_agreement")


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
    for a in ARMS_V4:
        for sd in SEEDS_V4:
            R.append((a, "v004", RUNS / (f"{a}_B1B2_v004" + ("" if sd == SEEDS_V4[0] else f"_s{sd}"))))
    for sd in SEEDS_V4:                                                  # U2 on the v002 rule of the corrected M2: the label-effect pair of v004
        R.append(("U2", "v002_notrace", RUNS / ("U2_B1B2_v002nt" + ("" if sd == SEEDS_V4[0] else f"_s{sd}"))))
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
            seed = json.loads((rd / "config.json").read_text()).get("seed")
            rows.append(dict(arm=arm, labels=lab, run=rd.name, seed=seed, endpoint=k, value=val, ci_lo=float(ci.lo.get(k, np.nan)), ci_hi=float(ci.hi.get(k, np.nan)),
                             n_defined=float(ci.n_defined.get(k, np.nan)) if "n_defined" in ci.columns else np.nan))
    D = pd.DataFrame(rows); D["meaning"] = "agreement with held-out weak reference labels (TEST blocks), not flood-mapping accuracy"
    put("T05", D, "D1 endpoints per arm on the frozen TEST blocks with 95 % spatial-block bootstrap intervals (2000 resamples; n_defined = resamples in which the endpoint is defined, review F11). v004 arms are trained with three seeds (run suffix _s<seed>; the first seed has no suffix).", src, "weak_label_agreement")


def t06_paired():
    rows, src = [], []
    todo = [("compare_U0d_vs_U0z", "U0d", "U0z", "v002", None), ("compare_U0d_vs_U1", "U0d", "U1", "v002", None), ("compare_U0d_vs_U2", "U0d", "U2", "v002", None),
            ("compare_U0d_vs_U2_v003A", "U0d", "U2", "v003_A", None), ("compare_U2_vs_U2b_v003A", "U2", "U2b", "v003_A", None)]
    for a, b in (("U0d", "U2"), ("U0d", "U1"), ("U2", "U2b")):
        for sd in SEEDS_V4:
            todo.append((f"compare_{a}_vs_{b}_v004" + ("" if sd == SEEDS_V4[0] else f"_s{sd}"), a, b, "v004", sd))
    for name, a, b, lab, sd in todo:
        p = RUNS / name / "paired_bootstrap.csv"
        if not p.exists():
            continue
        pb = pd.read_csv(p, index_col=0); src.append(p)
        for k, r in pb.iterrows():
            rows.append(dict(comparison=f"{b} - {a}", labels=lab, seed=sd, endpoint=k, median=r["median"], ci_lo=r["lo"], ci_hi=r["hi"], excludes_zero=bool((r["lo"] > 0) or (r["hi"] < 0)),
                             n_defined=r.get("n_defined", np.nan), independent="no" if b == "U2b" else "weak-label", note="not independent: W_pre is a label ingredient" if b == "U2b" else ""))
    put("T06", pd.DataFrame(rows), "Paired arm comparisons (B minus A) on identical spatial blocks, 2000 resamples, 95 % intervals; v004 per training seed (both arms of a pair share the seed).", src, "weak_label_agreement")


def t05s_seeds():
    """Review F11: training-seed variability of the arms on the corrected labels (p86s)."""
    q, r = T / "m6_seed_summary.csv", T / "m6_seed_paired.csv"
    if q.exists():
        put("T05s", pd.read_csv(q), "Training-seed variability of the U-Net arms on the corrected labels (v004; U2 also on v002_notrace): D1 endpoints of three seeds per arm on the frozen TEST blocks (same split, labels and recipe; each run at its own frozen validation threshold), with mean, SD and range across seeds -- the training noise a between-arm difference has to exceed (review F11). Agreement with weak labels, not accuracy.", [q], "weak_label_agreement")
    if r.exists():
        put("T06s", pd.read_csv(r), "Paired arm comparisons (B minus A) on the v004 labels for each training seed: median and 95 % block-bootstrap interval per seed, the number of seeds whose interval excludes zero, and whether all seeds agree in sign (review F11).", [r], "weak_label_agreement")


def t07_attribution():
    Ds, Ps, s1, s2 = [], [], [], []
    for tag, lab in (("v003A", "v003_A"), ("v004", "v004")):
        p = T / f"p90_{tag}_endpoints.csv"
        if not p.exists():
            continue
        e = pd.read_csv(p); s1.append(p)
        e["labels"] = e["labels"] if "labels" in e.columns else lab
        base = [c for c in e.columns if c not in ("run", "threshold", "labels") and not c.endswith(("_lo", "_hi", "_n_defined"))]
        L = e.melt(id_vars=["run", "labels", "threshold"], value_vars=base, var_name="endpoint", value_name="value")
        for suf, col in (("_lo", "ci_lo"), ("_hi", "ci_hi"), ("_n_defined", "n_defined")):
            cols = [c for c in e.columns if c.endswith(suf)]
            if cols:
                m = e.melt(id_vars=["run"], value_vars=cols, var_name="endpoint", value_name=col); m["endpoint"] = m.endpoint.str[:-len(suf)]
                L = L.merge(m, on=["run", "endpoint"], how="left")
        Ds.append(L)
        q = T / f"p90_{tag}_paired.csv"
        if q.exists():
            pr = pd.read_csv(q); pr["labels"] = pr["labels"] if "labels" in pr.columns else lab; Ps.append(pr); s2.append(q)
    D = pd.concat(Ds, ignore_index=True); D["area_semantics"] = np.where(D.endpoint.str.contains("km2"), "mapped_UNet", "")
    put("T07", D, "Attribution endpoints of the v003_A ontology per finished run at its own frozen threshold, against the v003_A labels (v002 / v003_A runs) and against the v004 labels (v004 runs): predicted flood on TEST REFERENCE_WATER, EVENT_FLOOD recall, LAND false positives, UNKNOWN burden; 95 % block-bootstrap intervals; ratio endpoints undefined (NaN) on empty support, n_defined resamples (review F11).", s1, "weak_label_agreement")
    pr = pd.concat(Ps, ignore_index=True)
    pr["excludes_zero"] = (pr.lo > 0) | (pr.hi < 0); pr["independent"] = np.where(pr.B.str.startswith("U2b"), "no (W_pre circularity)", "weak-label")
    put("T07b", pr, "Paired differences (B minus A) of the attribution endpoints across label sets, inputs and (v004) training seeds.", s2, "weak_label_agreement")


def t08_audit():
    g, p1 = read("p89_group_summary.csv"); r, p2 = read("p89_retention.csv")
    g["area_semantics"] = "mapped_UNet"
    put("T08", g, "Cropland-associated SAR candidates (p89 audit): groups A (water before the breach), B (wet/irrigated agriculture), D (unresolved / likely SAR artefact) per arm and frame.", [p1], "weak_label_agreement")
    put("T08b", r, "Retention of U0d candidate area by the other v002 arms (fraction of km2).", [p2], "weak_label_agreement")


def _oa_kappa(cm):
    C = cm.values.astype(float); oa = np.trace(C) / C.sum(); pe = (C.sum(0) * C.sum(1)).sum() / C.sum() ** 2
    return round(float(oa), 4), round(float((oa - pe) / (1 - pe)), 4)


def t09_rf():
    """RF20 agreement with WorldCover. Rev 2 (review F08) is the product in use; rev 1 is kept as the superseded row set.
    MACRO_MEAN = mean over the per-class rows only (the p73 tables carry their own MACRO and OVERALL_ACCURACY rows, which must
    not enter the mean; before 2026-09-29 they did, and n was counted three times)."""
    rows, src, cms = [], [], {}
    for rev, tg, status in ((2, "_rev2", "in use (review F08: global UTM blocks, B1/B2 overlap owned by B2 before sampling, CV with and without a 3.5 km buffer, transfers outside the overlap)"),
                            (1, "", "superseded (frame-local block ids, the B1/B2 overlap sampled from both frames)")):
        p = T / f"p73_rf20{tg}_metrics.csv"
        if not p.exists():
            continue
        m = pd.read_csv(p); m["evaluation"] = m.evaluation.astype(str); src.append(p)
        per = m[~m.cls.isin(["MACRO", "OVERALL_ACCURACY"])]
        macro = per.groupby("evaluation")[["precision", "recall", "F1"]].mean().round(4).reset_index(); macro["cls"] = "MACRO_MEAN"
        macro["n"] = per.groupby("evaluation").n.sum().values
        D = pd.concat([m, macro], ignore_index=True); D["OA_spatial_cv"] = np.nan; D["kappa_spatial_cv_csv_only"] = np.nan
        for ev, suf in (("spatial_block_cv_5fold", ""), ("spatial_block_cv_5fold_buffered", "_buffered")):
            c = T / f"p73_rf20_confusion_matrix{tg}{suf}.csv"
            if c.exists():
                cm = pd.read_csv(c, index_col=0); oa, kappa = _oa_kappa(cm); src.append(c); cms[(rev, ev)] = cm
                D.loc[D.evaluation == ev, "OA_spatial_cv"] = oa; D.loc[D.evaluation == ev, "kappa_spatial_cv_csv_only"] = kappa
        D.insert(0, "rev", rev); D["status"] = status; rows.append(D)
    D = pd.concat(rows, ignore_index=True); D["reference"] = "ESA WorldCover 2021 (training reference; agreement, not validation)"
    put("T09", D, "RF20 surface classification: per-class precision / recall / F1 with support, macro means (over the classes) and overall agreement, spatial-block 5-fold CV (rev 2 also with a 3.5 km buffer around the test blocks) and frame transfers (rev 2: outside the B1/B2 overlap). Reference = WorldCover 2021, the training reference. Rev 2 is the product in use (review F08); rev 1 rows are the superseded model.", src, "contextual")
    rv = 2 if (2, "spatial_block_cv_5fold") in cms else 1
    cm2 = cms[(rv, "spatial_block_cv_5fold")].copy(); cm2.index.name = "reference \\ predicted"
    put("T10", cm2.reset_index(), f"RF20 confusion matrix (spatial-block CV, counts; rev {rv}).", [T / f"p73_rf20_confusion_matrix{'_rev2' if rv == 2 else ''}.csv"], "contextual")
    if (2, "spatial_block_cv_5fold_buffered") in cms:
        cb = cms[(2, "spatial_block_cv_5fold_buffered")].copy(); cb.index.name = "reference \\ predicted"
        put("T10d", cb.reset_index(), "RF20 rev 2 confusion matrix, spatial-block CV with a 3.5 km buffer around the test blocks (counts; review F08).", [T / "p73_rf20_confusion_matrix_rev2_buffered.csv"], "contextual")
    tg = "_rev2" if rv == 2 else ""
    ca, p3 = read(f"p73_rf20{tg}_class_area.csv")
    put("T10b", ca, f"RF20 class areas per frame, km2 (mapped areas of a context product; rev {rv}).", [p3], "contextual")
    q = T / f"p73_rf20{tg}_qa" / "worldcover_walltowall.csv"
    if q.exists():
        put("T10c", pd.read_csv(q), f"RF20 vs WorldCover wall-to-wall agreement on WorldCover-pure cells (recall / precision vs the training reference; rev {rv}).", [q], "contextual")

P95_VARIANTS = [("_connected_ceiling", "connected_ceiling"), ("_hand_and_ceiling", "hand_and_ceiling"), ("_ceiling_only", "ceiling_only"),
                ("_connected_ceiling_dem_uncorrected", "connected_ceiling_dem_uncorrected"),
                ("_connected_ceiling_closure_p59_m050", "connected_ceiling (superseded closure, +0.5 m)"),
                ("_connected_ceiling_conn4", "connected_ceiling_conn4"), ("_connected_ceiling_seed_mainstem", "connected_ceiling_seed_mainstem"),
                ("_connected_ceiling_maxgap3", "connected_ceiling_maxgap3"), ("_connected_ceiling_riveraware", "connected_ceiling_riveraware"),
                ("_connected_ceiling_inhulets_gauge_node", "connected_ceiling_inhulets_gauge_node"), ("_connected_ceiling_fallback10km", "connected_ceiling_fallback10km")]
P95_ATTRIBUTION = [("_connected_ceiling_legacyTZA", "rev 5 reproduced: rev-5 terrain table on every cell, per-zone evaluation, grid-anchored lattice"),
                   ("_connected_ceiling_legacyTZ", "+ lattice anchored in map coordinates"),
                   ("_connected_ceiling_legacyT", "+ connectivity on the union mosaic (ownership for accounting only)"),
                   ("_connected_ceiling", "+ FABDEM-only residual table per zone, bed cells uncorrected = rev 6")]


def _p95_variants():
    V = {}
    for sfx, name in P95_VARIANTS:
        p = T / f"p95_manifest{sfx}.json"
        if p.exists():
            V[name] = (sfx, json.loads(p.read_text()), p)
    return V


def t11_terrain():
    rows, src = [], []
    for name, (sfx, man, p) in _p95_variants().items():
        src.append(p); c = man["constants"]
        ter = man.get("terrain", {}); vf = man.get("vertical_frame", {})
        rows.append(dict(variant=name, suffix=sfx, rev=man.get("rev"), rule=man.get("rule_variant"), closure=man.get("closure"), closure_offset_vs_p59_m=man.get("closure_offset_vs_p59_H_evrf_m"),
                         margin_m=c.get("margin_m"), river_floor_m=c["RIVER_LEVEL_M"], swot_max_dist_m=c["SWOT_MAX_DIST_M"], dist_to_prewater_max_m=c["DIST_MAX_M"],
                         baseline_until=c["baseline_until"], connectivity=c.get("connectivity"), seed_network=c.get("seed_network"), max_gap_days=c.get("max_gap_days"),
                         wse_river_aware=c.get("wse_river_aware"), terrain_bias=ter.get("bias_correction"), vertical_datum=vf.get("datum"),
                         evaluation="union mosaic" if "mosaic" in str(man.get("evaluation", "")) else man.get("evaluation"), wse_method=man.get("wse_method", ""),
                         status="superseded" if "p59" in (man.get("closure") or "") else "current"))
    put("T11", pd.DataFrame(rows), "Terrain reconstruction (rev 6): rule, closure, constants, connectivity, seed network, water-surface support options, terrain bias and vertical datum per variant; the primary is connected_ceiling, every other row a sensitivity. The superseded closure row is kept for traceability.", src, "independent_physical")
    p = T / "p95e_uncertainty_components.csv"
    if p.exists():
        put("T11b", pd.read_csv(p), "Uncertainty components of the terrain reconstruction (Monte-Carlo inputs, p95e rev 2): datum closure of the SWOT chain, gauge, SWOT node height, gap-dependent interpolation error, the correlation model of the terrain-error field (nugget + nested exponential structures fitted to the standardized FABDEM - ICESat-2 residuals, p95j) and the class-wise FABDEM residual scale per zone (own zone where N >= 500, else pooled and flagged transferred); bed cells of the seamless terrain-bed model carry no stochastic term (limitation).", [p], "independent_physical")
    extra = [("T11c", "p95e_convergence.csv", "Convergence of the Monte-Carlo quantiles with the ensemble size (corridor; 7, 9 and 13 June): p05 / p50 / p95 and the p05-p95 width of A_new, W_total and V_new from the first n = 40, 100, 250, 500, 1000 draws of two independent seeds, with a bootstrap 95 % interval of each quantile estimator and the share of draws with the areal maximum on 7 / 8 June (finite ensembles carry their own sampling uncertainty of tail quantiles)."),
             ("T11d", "p95e_ablation.csv", "Ablation of the uncertainty budget (250 draws per variant, key dates): the full budget; terrain only; water surface only; baseline fixed at the nominal regime; with a per-day SWOT term of 0.05 m; without the interpolation term; without the nugget; with a single exponential instead of the nested covariance -- attribution of the width and of the offset between the nominal run and the ensemble median."),
             ("T11e", "p95e_wse_threshold_sensitivity.csv", "Sensitivity of the connected reconstruction to a uniform offset of the water surface (-0.20 ... +0.20 m) on the nominal terrain with the nominal baseline: W_total, A_new, V_new and the local derivatives dA/dH, dW/dH (corridor, Inhulets, p42 domain; 7, 9, 13 June). A sensitivity of the connectivity thresholds, not a new model."),
             ("T11f", "p95e_interp_cv.csv", "Error of the per-node time interpolation from a whole-date hold-out: residual NMAD / RMSE by gap length (1, 2, 3-4, 5-8, > 8 days) for interpolated and end-held node-days; the superseded one-day triplet estimate for comparison.")]
    for tid, fn, cap in extra:
        q = T / fn
        if q.exists():
            put(tid, pd.read_csv(q), cap, [q], "independent_physical")
    sc_, sd_ = T / "p95l_supported_core.csv", T / "p95l_support_domain.csv"
    if sc_.exists() and sd_.exists():
        put("T11k", pd.read_csv(sc_).query("date in @KEY_DATES"), "Observational support of the reconstructed new inundation (nominal run of the primary rule; maintainer decision D-SUPPORT): per region and key date the FULL terrain-connectivity reconstruction (the primary product), its DIRECT (nearest SWOT node <= 3 km), EXTRAPOLATED (3-10 km) and WEAK (> 10 km) parts, the SUPPORTED CORE (<= 10 km), the weak share, the parts capped at the Kherson gauge and, in the Inhulets valley, served by a node of another river (cross-river flag), and the 10 km cap run of p95 as a sensitivity (it recomputes the connectivity; it is not the core). The 3 and 10 km limits are operational thresholds, not physical constants.", [sc_], "independent_physical")
        put("T11l", pd.read_csv(sd_).query("date in @KEY_DATES"), "The support classes of T11k with their flags and the median distance of the serving node, per region and key date.", [sd_], "independent_physical")
    sup = T / "p95_wse_support_cells_connected_ceiling.csv"; nod = T / "p95_wse_support_nodes_connected_ceiling.csv"
    if sup.exists() and nod.exists():
        S_ = pd.read_csv(sup); N_ = pd.read_csv(nod); S_ = S_[S_.date.isin(KEY_DATES)].merge(N_, on="date", how="left")
        put("T11g", S_, "Support of the reconstructed water surface on the key dates: share of the corridor base cells whose surface is the median of nodes within 3 km, the nearest-node fallback beyond 3 km, or capped at the Kherson gauge (> 15 km from a node, west of the gauge), with the water cells in each class, and the number of SWOT nodes observed / interpolated / held at an end on the day.", [sup, nod], "independent_physical")
    rows, src = [], []
    for sfx, step in P95_ATTRIBUTION:
        q = T / f"p95_daily_area_pooled{sfx}.csv"
        if q.exists():
            d = pd.read_csv(q); d = d[d.date.isin(["2023-06-05", "2023-06-07", "2023-06-09", "2023-06-13", "2023-06-18"])]; d.insert(0, "step", step); d.insert(1, "suffix", sfx); rows.append(d); src.append(q)
    if rows:
        A = pd.concat(rows, ignore_index=True); A["area_semantics"] = "terrain_reconstructed"
        A["note"] = "nominal runs (no Monte-Carlo); each step adds one change to the previous one; the first row reproduces the committed rev-5 tables exactly (reproduction gate)"
        put("T11h", A, "From rev 5 to rev 6 of the reconstruction (nominal runs, key dates): the committed rev-5 result reproduced exactly by the rev-6 code in legacy mode, then one change at a time -- the water-surface lattice anchored in map coordinates, connectivity on the union mosaic with ownership for accounting only (review F06), and the FABDEM-only residual terrain bias per zone with bed cells uncorrected (review F07).", src, "independent_physical")
    sc = T / "p95_seam_check_connected_ceiling.csv"
    if sc.exists():
        put("T11i", pd.read_csv(sc), "Seam check (review F06): water-surface-allowed area on 7, 9 and 13 June per zone and region, evaluated on the union mosaic versus the superseded per-zone evaluation (ownership applied before the connectivity), with the cells found by only one of the two.", [sc], "independent_physical")
    ss = T / "p95_source_share_connected_ceiling.csv"
    if ss.exists():
        s_ = pd.read_csv(ss); s_ = s_[s_.date.isin(KEY_DATES) & (s_.new_km2 > 0)]
        put("T11j", s_, "Terrain source of the reconstructed newly inundated area (corridor, key dates): FABDEM DTM (p55 source 3), FABDEM tapered at a bathymetric edge (4), surveyed or reconstructed bed (1, 2) and gap fill (5). The terrain-error model perturbs FABDEM-sourced cells only; the bed share is the part of the new area without a stochastic terrain term.", [ss], "independent_physical")


def t12_daily():
    p = T / "p95_daily_area_pooled_connected_ceiling.csv"; d = pd.read_csv(p); src = [p]
    D = d[d.date.isin(KEY_DATES)].copy(); D["area_semantics"] = "terrain_reconstructed"; D = D.rename(columns={"new_km2": "A_central_km2", "new_volume_hm3": "V_central_hm3", "potential_km2": "W_total_central_km2"})
    pu = T / "p95e_area_volume_uncertainty.csv"
    if pu.exists():
        U = pd.read_csv(pu); src.append(pu)
        D = D.merge(U[["date", "region", "A_p05_km2", "A_p50_km2", "A_p95_km2", "V_p05_hm3", "V_p50_hm3", "V_p95_hm3", "W_total_p05_km2", "W_total_p50_km2", "W_total_p95_km2",
                       "Vtot_p05_hm3", "Vtot_p50_hm3", "Vtot_p95_hm3", "baseline_p05_km2", "baseline_p50_km2", "baseline_p95_km2", "n_draws"]], on=["date", "region"], how="left")
        # PRIMARY interval of the total = quantiles of the total-water ensemble itself (review F04; the shift construction is withdrawn)
        D["rel_halfwidth_W_total_pct"] = (D.W_total_p95_km2 - D.W_total_p05_km2) / 2 / D.W_total_central_km2 * 100
        D["rel_halfwidth_A_pct"] = (D.A_p95_km2 - D.A_p05_km2) / 2 / D.A_central_km2 * 100; D["rel_halfwidth_V_pct"] = (D.V_p95_hm3 - D.V_p05_hm3) / 2 / D.V_central_hm3 * 100
        D["mc_shift_A_pct"] = (D.A_p50_km2 - D.A_central_km2) / D.A_central_km2 * 100; D["mc_shift_V_pct"] = (D.V_p50_hm3 - D.V_central_hm3) / D.V_central_hm3 * 100
    for name, (sfx, man, mp) in _p95_variants().items():
        q = T / f"p95_daily_area_pooled{sfx}.csv"
        if q.exists() and name != "connected_ceiling":
            tag = f"{name.split(' ')[0]}{'_superseded' if 'superseded' in name else ''}"
            x = pd.read_csv(q)[["date", "region", "new_km2", "potential_km2"]].rename(columns={"new_km2": f"A_{tag}_km2", "potential_km2": f"W_total_{tag}_km2"}); D = D.merge(x, on=["date", "region"], how="left"); src.append(q)
    D["uncertainty_note"] = UNCERTAINTY_NOTE
    D["definition_note"] = "A_* = NEW inundation (cells allowed by the water surface outside the same-rule pre-breach regime); W_total_* = TOTAL water surface on the day (all cells allowed by the water surface, incl. channels, lakes, reed beds) ; operational 'flooded land' figures (e.g. UNOSAT 3616) exclude pre-existing water and are closer in kind to A_*, but differ in AOI, date and temporal semantics -- context, never validation; wetland submergence is in T13/T14"
    D["central_value_note"] = CENTRAL_NOTE
    lead = [c for c in ["date", "region", "A_p50_km2", "A_p05_km2", "A_p95_km2", "A_central_km2", "W_total_p50_km2", "W_total_p05_km2", "W_total_p95_km2", "W_total_central_km2",
                        "V_p50_hm3", "V_p05_hm3", "V_p95_hm3", "V_central_hm3"] if c in D.columns]
    D = D[lead + [c for c in D.columns if c not in lead]]
    put("T12", D, "Daily terrain-reconstructed inundation per region and key date, REPORTED AS the Monte-Carlo median [p05-p95] of the coherent Monte-Carlo worlds (p95e rev 2; n_draws per row) with the deterministic nominal run (*_central_*, draw 0, a diagnostic) alongside: reconstructed TOTAL water-surface area (W_total_*: all water on the day incl. pre-breach channels, lakes and reed beds; quantiles of the total-water ensemble), reconstructed NEWLY INUNDATED area (A_*), the volume of new water (V_*) and of all water (Vtot_*), and the draw's own pre-breach baseline (baseline_*). *_emu_* = 100 000-draw emulator sensitivity envelope (p95g). The 100 000-draw emulator is not part of this table (a diagnostic, T12d). Sensitivities (nominal runs): p42 HAND rule, ceiling only, terrain as delivered (no residual bias removed), superseded closure, 4-connectivity, main-stem seed, 3-day maximum gap, river-aware water surface, the Kalynivske gauge as an extra water-surface node (the gauge then an input), nearest-node fallback capped at 10 km. Daily reconstructed series, not daily observations.", src, "independent_physical")


def t12d_emulator_diagnostic():
    """D-EMU (maintainer, 2026-09-29): the 100 000-draw emulator stays a computational diagnostic outside the evidence path."""
    pg, pv = T / "p95g_mc_daily.csv", T / "p95g_vs_p95e.csv"
    if pg.exists():
        G = pd.read_csv(pg); G = G[G.date.isin(KEY_DATES)].copy()
        G["status"] = "DIAGNOSTIC, not evidence (D-EMU): cluster-normal emulator without connectivity; W_total = nominal total + emulator new-area deviations; volumes unanchored"
        put("T12d", G, "Computational diagnostic, not evidence (maintainer decision D-EMU, 2026-09-29): the 100 000-draw cluster-normal emulator (p95g) per region and key date. It has no connectivity, its total water-surface envelope is built around the nominal total, and its volumes are unanchored; it is not an uncertainty estimate and no reported number rests on it. The primary interval is the Monte-Carlo ensemble (T12).", [pg] + ([pv] if pv.exists() else []), "contextual")


def t12b_daily_series():
    """Every day of the p95 series with the MC median [p05-p95] and the nominal run (the reported daily series)."""
    p = T / "p95_daily_area_pooled_connected_ceiling.csv"; pu = T / "p95e_area_volume_uncertainty.csv"
    if not (p.exists() and pu.exists()):
        return
    d = pd.read_csv(p).rename(columns={"new_km2": "A_central_km2", "new_volume_hm3": "V_central_hm3", "potential_km2": "W_total_central_km2"})
    U = pd.read_csv(pu)
    D = d[["date", "region", "A_central_km2", "W_total_central_km2", "V_central_hm3", "kherson_gauge_m"]].merge(
        U[["date", "region", "A_p05_km2", "A_p50_km2", "A_p95_km2", "V_p05_hm3", "V_p50_hm3", "V_p95_hm3", "W_total_p05_km2", "W_total_p50_km2", "W_total_p95_km2", "n_draws"]], on=["date", "region"], how="left")
    # every day, including the pre-breach days (A_new = V_new = 0 there by construction; W_total from its own ensemble)
    D["nominal_below_mc_p05"] = (D.A_central_km2 < D.A_p05_km2) | (D.V_central_hm3 < D.V_p05_hm3)
    D["area_semantics"] = "terrain_reconstructed"; D["central_value_note"] = CENTRAL_NOTE
    D = D[["date", "region", "A_p50_km2", "A_p05_km2", "A_p95_km2", "A_central_km2", "W_total_p50_km2", "W_total_p05_km2", "W_total_p95_km2", "W_total_central_km2",
           "V_p50_hm3", "V_p05_hm3", "V_p95_hm3", "V_central_hm3", "nominal_below_mc_p05", "kherson_gauge_m", "n_draws", "area_semantics", "central_value_note"]]
    put("T12b", D.sort_values(["region", "date"]), "The daily reconstructed series, every day 26 May - 10 July 2023 and region: Monte-Carlo median [p05-p95] of the coherent Monte-Carlo worlds (p95e rev 2, every day) for new inundation A, total water surface W_total (its own ensemble, also before the breach) and new-water volume V, with the deterministic nominal run (*_central_*) and a flag where it lies below its own MC p05. Before the breach A = V = 0 by construction. Daily reconstructed series, not daily observations.", [p, pu], "independent_physical")
    pk = T / "p95e_peak_date.csv"
    if pk.exists():
        put("T12c", pd.read_csv(pk), "Day of the reconstructed areal maximum across the Monte-Carlo worlds: for A_new and W_total per region, the share of draws with the maximum on each day, and the day of the nominal run. A distribution conditional on the uncertainty model, not a probability of the true day.", [pk], "independent_physical")


def t21_reservoir():
    p = T / "p95f_reservoir_daily.csv"; h = T / "p95f_hypsometry_dem.csv"
    if not p.exists():
        return
    R = pd.read_csv(p); R["area_semantics"] = "reservoir_pool (terrain-integrated under the observed sloped surface)"
    R = R.rename(columns={"Q_out_breach_est_m3s": "Q_release_eff_daily_mean_m3s", "Q_out_breach_est_hm3_day": "Q_release_eff_hm3_day"})
    R["Q_definition"] = "daily-MEAN effective release = -dV_pool/dt + Q_in(DniproHES); a storage-balance estimate on a sloped surface interpolated between 3-4 level points, NOT an instantaneous breach discharge"
    put("T21", R, "Kakhovka pool during the drawdown, per day: levels at the outlet (SWOT), Nikopol (press) and Rozumivka (gauge), surface gradient, pool water area and volume under the sloped surface (seamless DEM inside the pre-breach pool polygon), daily volume change, DniproHES inflow, the daily-mean effective release (-dV/dt + Q_in; not an instantaneous breach discharge), and the downstream new-water volume and total water surface (terrain reconstruction) with the Kherson stage.", [p], "independent_physical")
    if h.exists():
        H = pd.read_csv(h); H["dV_rel_pct"] = (H.V_dem_km3 - H.V_table19_km3) / H.V_table19_km3 * 100; H["dA_rel_pct"] = (H.A_dem_km2 - H.A_table19_km2) / H.A_table19_km2 * 100
        put("T22", H, "Pool hypsometry from the seamless DEM (level surface) against the design Table 19 (BS-77 levels + 0.185 m), with the relative difference dV/V_design and dA/A_design per level: the seamless DEM gives less volume at the same level: -8.5 % at the full-pool level (17.5 m), -14 % at 13 m, -20 % at 11 m (open question for Paper 4: reservoir bowl on the historical bathymetry).", [h], "independent_physical")


def t23_t26_reservoir_maps():
    """Reservoir drawdown maps (p95h): pool water area by source, S2 k10e classes, S2 index statistics and index classes."""
    p = T / "p95h_reservoir_maps.csv"
    if not p.exists():
        return
    M = pd.read_csv(p)
    M["area_note"] = np.select([M.source == "MODEL", M.source == "S1"], ["pool water under the p95f sloped surface (whole pool)",
                               "VH dark surface = open water OR smooth wet mud, observed cells only; not a water area after ~06-13"],
                               "S2 water (NDWI>0 & MNDWI>0 & SCL-permitted), observed cells only")
    M = M.rename(columns={"yi2025_digitised_km2": "yi2025_S1_archive_km2"})   # review F15: the authors' Sentinel-1 archive values, not digitised
    cols = ["date", "source", "semantics", "water_km2", "observed_frac", "iou_vs_model", "model_km2_on_observed", "vh_threshold_db", "orbits", "regime", "mapped", "yi2025_S1_archive_km2", "area_note"]
    put("T23", M[[c for c in cols if c in M.columns]], "Kakhovka pool water area by source and date inside the pre-breach pool polygon: MODEL (p95f sloped surface over the seamless DEM, terrain_reconstructed, 05-26..06-13), Sentinel-1 VH dark surface (per-date Otsu; open water or smooth wet mud), Sentinel-2 water (frozen p25 water3 and p15 crosscheck), with the observed fraction of the pool, IoU against the model on observed cells, and Yi et al. 2025 (literature_reported; the Sentinel-1 reservoir areas of the authors' code archive, Zenodo 14639520, observations.mat obs.A -- read from the archive, not digitised, not quoted from their text). Areas count observed cells only; not observed is not dry. Maps: FigS08.", [p], "cross_sensor")
    c = T / "p95h_s2_classes.csv"
    if c.exists():
        put("T24", pd.read_csv(c), "Sentinel-2 k10e surface classes inside the pool per date (every 2023 date observing >= 50 % of the pool) and stratum: POOL; EXPOSED_BY_0613 (model: wet on 06-05, dry by 06-13); WET_ON_0613 (model: still wet on 06-13). km2 and % of the observed cells per class; frozen SWOT-DNIPRO p25 products, not re-classified. Context for the drawdown and recolonisation of the bed (FigS08 i-k).", [c], "contextual")
    s = T / "p95h_s2_index_stats.csv"
    if s.exists():
        put("T25", pd.read_csv(s), "Sentinel-2 index statistics inside the pool per date, stratum and index (NDVI, NDWI, MNDWI, NDMI, BSI, AWEIsh, NDTI; offset-corrected reflectance, 20 m, frozen p25 stacks): observed km2 and fraction, mean, std and percentiles p10/p25/p50/p75/p90 over observed cells. Strata as T24. FigS09.", [s], "contextual")
    k = T / "p95h_s2_index_classes.csv"
    if k.exists():
        put("T26", pd.read_csv(k), "Sentinel-2 index display classes inside the pool per date, stratum and index: km2 and % of observed cells per class (bins: NDWI/MNDWI/AWEIsh -0.3/0/0.3; NDVI 0.15/0.3/0.5; NDMI/BSI/NDTI -0.1/0.1). Display classes, not a classifier (the frozen classifier is k10e, T24). FigS09.", [k], "contextual")


def t27_capacity_curves():
    """The design (project) level-area-volume curves of the reservoir and the observed 2023 levels read on them (p95i)."""
    p = T / "p95i_design_hypsometry.csv"; q = T / "p95i_design_daily.csv"
    if not p.exists():
        return
    put("T27", pd.read_csv(p), "Design hypsometry of the Kakhovka reservoir from the Dnipro-reservoirs monograph (Table 19, Figs 13-15; transcribed from photographed pages in SWOT-DNIPRO): water level (historical Baltic, and +0.185 m to EVRF2019), surface area and volume of the whole pool and of the five reaches (dam - Babyne - Nikopol - Verkhnia Tarasivka - Blahovishchenka - Dnipro HPP) at 17 levels, with the design levels (NUF highest forced 17.5, NPG normal impoundment 16.0, UNS navigation drawdown 14.0, GMO dead volume 12.7 m) and the transcription check that the reaches add up to the total. Design data as published; nothing measured or fitted here. FigS10.", [p], "contextual")
    if q.exists():
        put("T27b", pd.read_csv(q), "The observed 2023 levels, 1 February - 10 July, read on the design curve of T27 (level - 0.185 m -> historical Baltic): before the breach the Rozumivka gauge 80959 (terms 08/20 averaged; the only 2023 daily series; the pool was level, so one gauge reads the whole pool), with G-REALM, ICESat-2 and the SWOT outlet as checks; from 26 May the p95f daily levels (the pre-breach outlet value is HELD, not observed daily -- flagged). 'Outlet' = SWOT nodes at 0 km, the pool just above the dam; for comparison the SWOT level 0.5 km below the dam (p59/p60) and the Kherson gauge 80805, with the head across the dam and pool-minus-Kherson. Design volume and area at the Rozumivka and at the outlet level (during the drawdown the surface sloped by up to 4 m, so the two readings bracket the pool), the volume released from the design curve, and the storage balance with the DniproHES inflow, computed separately for each level source and never switched inside a series (review F14): Q_out = Q_in - dV_design/dt on the Rozumivka series (the whole period; the upper-bound level during the drawdown) and on the outlet series (from 26 May; the lower-bound level) = the outflow through the Kakhovka HPP before the breach and the daily-mean effective release after it (design-curve counterpart of T21; a residual without lateral inflow, evaporation or withdrawals); rozumivka_source names the source of every level used. NaN once a level is below 10.0 m BS, the lowest level of Table 19 (never the endpoint value). Context for Paper 4.", [q], "independent_physical")
    w = T / "p95i_design_weekly_2023.csv"
    if w.exists():
        f = json.loads((T / "p95i_manifest.json").read_text())["filling_2023"]; lo, hi = f["minimum"], f["maximum"]; last = f.get("2023-06-05", {})
        put("T27c", pd.read_csv(w), (f"The filling of the Kakhovka reservoir in spring 2023, week by week on the design curve (Rozumivka series only; the pool was level before the breach). "
                                     f"Every term of a week covers the same days (review F14): the change of storage is the sum of the week's daily changes, i.e. V on the week's last day minus V on the previous week's last day; "
                                     f"inflow = DniproHES releases summed over those days; outflow through the Kakhovka HPP = inflow minus the change of storage (a residual: lateral inflow, evaporation and withdrawals are not in it). "
                                     f"A week with a missing day has no balance (complete = False). Levels and means are descriptive. "
                                     f"From {lo['H']:.2f} m / {lo['V']:.2f} km3 on {lo['date']} to {hi['H']:.2f} m / {hi['V']:.2f} km3 on {hi['date']} ({f['filled_min_to_max_km3']:.2f} km3 stored out of "
                                     f"{f['inflow_dniprohes_min_to_max_km3']:.2f} km3 of inflow)" + (f"; {last['H_rozumivka_m']:.2f} m / {last['V_design_km3']:.2f} km3 on 5 June." if last else ".") +
                                     " Design data + gauge + releases; no DEM."), [w, T / "p95i_manifest.json"], "contextual")


def t13_terrain_vs_s1():
    rows, src = [], []
    for name, (sfx, man, mp) in _p95_variants().items():
        q = T / f"p95_validation_s1_pooled{sfx}.csv"
        if q.exists():
            v = pd.read_csv(q); v.insert(0, "variant", name); rows.append(v); src.append(q)
    D = pd.concat(rows, ignore_index=True); D["observation_domain"] = "S1 valid footprint of the date, owned zone area, outside the p42 cut rectangles (Inhulets rows: inside the Inhulets rectangle)"
    D = D.rename(columns={"POD_excl_normally_wet": "POD_cond_outside_normally_wet"})
    D["POD_cond_note"] = "conditional POD outside the normally-wet class (POD | observable dry-background domain): a diagnostic conditional agreement, NOT a corrected POD; the class was fixed a priori (same-rule pre-breach potential) before any comparison was read"
    put("T13", D, "Terrain reconstruction vs Sentinel-1 new dark water per acquisition date, region and variant: hit / miss / miss-on-normally-wet / terrain-only km2, POD, FAR, CSI (raw agreement, primary) and the conditional POD outside the normally-wet class (diagnostic).", src, "cross_sensor")


def t14_ontology():
    rows, src = [], []
    for d in ("20230609", "20230613", "20230614"):
        p = T / f"p95d_agreement_{d}_summary.csv"
        if p.exists():
            rows.append(pd.read_csv(p)); src.append(p)
    if rows:
        D = pd.concat(rows, ignore_index=True); D["category_meaning"] = D.category.map({"A": "terrain+ / S1+", "B": "terrain+ / S1- (sensor blind spot or reconstruction excess)", "C": "terrain- / S1+ (submergence signal on normally-wet ground, or S1-only detections topographically unsupported by the reconstructed surface)", "N": "neither"})
        put("T14", D, "Disagreement ontology terrain x Sentinel-1 by zone and date: category areas split by ground elevation relative to the water surface, normally-wet flag, WorldCover and RF20 classes (km2).", src, "contextual")


def t15_icesat():
    p = T / "p95c_icesat2_check_0609.csv"
    if p.exists():
        D = pd.read_csv(p); D["check_type"] = "altimetric consistency check (night ATL08 ground segments vs seamless DEM and the 06-09 water surface); not a validation of the inundation map"
        put("T15", D, "ICESat-2 altimetric consistency check per zone and agreement category on 9 June (categories inside the S1 valid footprint only, review F12): residual of the FABDEM-sourced terrain minus night ICESat-2 ground, raw (res_*) and after the class-bias correction used by the reconstruction (res_corr_*; median, p10, p90), ICESat-2 ground minus water surface, share of segments below the surface; N segments on n_dates passes (acquisition days: the independent units, far fewer than the segments), n_bed_source segments on bed-sourced cells (excluded from the residual statistics). The same p57 night corpus also calibrates the class bias, so the corrected residual here is in-sample; its pass hold-out is T15b. A consistency check, not an independent validation.", [p], "independent_physical")
    q = T / "p95c_icesat2_bias_holdout.csv"
    if q.exists():
        put("T15b", pd.read_csv(q), "Pass hold-out of the class-bias correction (review F12), FABDEM-sourced check segments only: the class bias is re-estimated with the reconstruction's rule from the ICESat-2 calibration population WITHOUT the passes being checked (a pass = one acquisition day; leave one pass out, five folds of whole passes, and the two epochs either side of the breach) and applied to the held-out passes. Per zone, category and scheme: N segments and n_passes, raw, in-sample and hold-out corrected residual (median; hold-out p10-p90 = spread of the sampled residuals, not a confidence interval), the largest bias shift met by a checked segment, the share of segments whose terrain lies below the 06-09 surface in-sample and with the hold-out bias, the share of ICESat-2 ground below the surface (does not involve the bias), and the number of S1-only segments that change side of the 2 m split.", [q], "independent_physical")
    f = T / "p95c_icesat2_bias_folds.csv"
    if f.exists():
        F = pd.read_csv(f)
        agg = F.groupby(["scheme", "zone", "wc_class"], as_index=False).agg(b_insample=("b_insample", "first"), n_folds=("fold", "nunique"), max_abs_delta=("delta", lambda d: round(float(d.abs().max()), 3)),
                                                                              min_cal_passes=("n_cal_passes", "min"), row_used=("row_used", lambda u: "/".join(sorted(set(u)))))
        ep = F[F.scheme == "epoch"].pivot_table(index=["zone", "wc_class"], columns="fold", values="b_holdout").reset_index().rename(columns={"calibrate_pre_check_post": "b_pre_breach_passes", "calibrate_post_check_pre": "b_post_breach_passes"})
        put("T15c", agg.merge(ep, on=["zone", "wc_class"], how="left"), "Stability of the class residual bias b_c across the pass hold-out folds of T15b (FABDEM - ICESat-2 ground, p95 rule): per scheme, zone and WorldCover class the in-sample b_c, the largest |shift| over the folds, the fewest calibration passes left in a fold, whether the own-zone or the pooled row was used, and b_c estimated from the pre-breach and from the post-breach passes alone. b_c enters the reconstruction as a fixed correction (not perturbed in the Monte-Carlo ensemble).", [f], "independent_physical")


def t16_accounting():
    pk, p1 = read("p93_peak_vs_label_vs_model.csv"); ar, p2 = read("p92_flood_area_dam_to_liman.csv")
    rows = []
    for _, r in pk.iterrows():
        rows += [dict(region=r.region, quantity="S1 new dark water, 06-09 scene", km2=r.peak_0609_new_water_km2, area_semantics="observed_S1", quantity_semantics="new_water (pre-breach water excluded)", temporal_semantics="snapshot_2023-06-09"),
                 dict(region=r.region, quantity="S1 new dark water, >= 2 of 3 peak dates (label recipe)", km2=r.label_recipe_2of3_new_km2, area_semantics="observed_S1", quantity_semantics="new_water (pre-breach water excluded)", temporal_semantics="persistence_2of3_(06-09,06-13,06-14)"),
                 dict(region=r.region, quantity="S1 total dark water, 06-09 (incl. pre-breach water)", km2=r.peak_0609_total_water_km2, area_semantics="observed_S1", quantity_semantics="total_water", temporal_semantics="snapshot_2023-06-09"),
                 dict(region=r.region, quantity="pre-breach water (S1 06-01/02 or p60 pre_water_frac >= 20 %)", km2=r.pre_breach_water_km2, area_semantics="observed_S1", quantity_semantics="reference_water", temporal_semantics="reference_2023-06-01/02"),
                 dict(region=r.region, quantity="U2b predicted event flood (persistent concept)", km2=r.U2b_predicted_km2, area_semantics="mapped_UNet", quantity_semantics="new_water (label concept)", temporal_semantics="persistence (label concept ~13 June regime)")]
    for run_, lab_ in (("U2b_B1B2_v003A", "v003_A labels, original M2"), ("U2b_B1B2_v004", "v004 labels, corrected M2, seed 20260923"),
                       ("U2b_B1B2_v004_s20261001", "v004 labels, corrected M2, seed 20261001"), ("U2b_B1B2_v004_s20261002", "v004 labels, corrected M2, seed 20261002")):
        for _, r in ar[ar.run == run_].iterrows():
            rows.append(dict(region=r.region, quantity=f"U2b predicted flood (p92 accounting; {lab_})", km2=r.predicted_flood_km2, area_semantics="mapped_UNet", quantity_semantics="new_water (label concept)", temporal_semantics="persistence (label concept ~13 June regime)", unobserved_km2=r.unobserved_no_s1_event_km2))
    pu = T / "p95_daily_area_pooled_connected_ceiling.csv"
    if pu.exists():
        d = pd.read_csv(pu)
        for reg in ("DNIPRO_CORRIDOR", "P42_FLOODPLAIN_DOMAIN", "INHULETS_VALLEY_rect"):
            g = d[d.region == reg]; pkrow = g.loc[g.new_km2.idxmax()]
            rows.append(dict(region=reg, quantity=f"reconstructed newly inundated area, areal maximum {pkrow.date}", km2=pkrow.new_km2, area_semantics="terrain_reconstructed", quantity_semantics="new_water (outside the same-rule pre-breach regime)", temporal_semantics=f"daily_snapshot_{pkrow.date} (reconstructed series)"))
            rows.append(dict(region=reg, quantity="reconstructed newly inundated area, 06-09", km2=float(g[g.date == "2023-06-09"].new_km2.iloc[0]), area_semantics="terrain_reconstructed", quantity_semantics="new_water (outside the same-rule pre-breach regime)", temporal_semantics="daily_snapshot_2023-06-09 (reconstructed series)"))
            rows.append(dict(region=reg, quantity=f"reconstructed total water-surface area, {pkrow.date}", km2=float(pkrow.potential_km2), area_semantics="terrain_reconstructed", quantity_semantics="total_water (incl. pre-breach channels, lakes, reed beds)", temporal_semantics=f"daily_snapshot_{pkrow.date} (reconstructed series)"))
            rows.append(dict(region=reg, quantity="reconstructed total water-surface area, normal regime 06-05", km2=float(g[g.date == "2023-06-05"].potential_km2.iloc[0]), area_semantics="terrain_reconstructed", quantity_semantics="total_water (incl. pre-breach channels, lakes, reed beds)", temporal_semantics="daily_snapshot_2023-06-05 (reconstructed series)"))
    for l in LITERATURE:
        rows.append(dict(region="reported AOI (differs)", quantity=f"{l['source']}: {l['quantity']}", km2=l["value_km2"], area_semantics="literature_reported", quantity_semantics=l["quantity_semantics"], temporal_semantics=l["temporal_semantics"], verify=l["verify"]))
    D16 = pd.DataFrame(rows); D16["comparability_note"] = "quantities differ in area_semantics, quantity_semantics (new vs total water) AND temporal_semantics (snapshot vs cumulative vs persistence); operational flooded-LAND figures are closer in kind to A_new than to W_total and are context, never validation"
    put("T16", D16, "Area accounting with explicit semantics: observed (S1), mapped (U-Net), terrain-reconstructed and literature-reported figures are different quantities (new vs total water; snapshot vs cumulative vs persistence) and are never compared as validation.", [p1, p2], "mixed")


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
    k, s = T / "p95k_inhulets_kalynivske.csv", T / "p95k_inhulets_summary.csv"
    if k.exists() and s.exists():
        put("T17c", pd.read_csv(k), "Inhulets gauge Kalynivske (80575; UkrHMC yearbook 2023 table 1.2, daily means in cm above the gauge zero, zero -1.34 m BS from the sheet header -> EVRF2019 by the EPSG:9902 grid step) per day against the reconstructed water surface at the gauge (not an input of the reconstruction; in the gauge-node sensitivity it is), with the support of that surface (nearest SWOT node, river, distance), the Kherson gauge, the upstream Inhulets posts (Kryvyi Rih 80568, Iskrivka 80564: no flood from upstream, i.e. the rise is Dnipro backwater), the terrain at the gauge cell and the days with reconstructed new inundation there. Gauge position 47°6'59\" N 32°57'38\" E (station catalogue, Kakhovka hydrometeorological observatory); date-only daily values (means of more frequent observations during the event). The yearbook remark (vol. 2, item 114) attributes the maximum to the destruction of the Kakhovka HPP, gives high water on 7-18 June with houses and the road bridge 0.75 km upstream flooded, and notes that the levelling of pile No. 5 changed during the hazard (a possible datum step of unknown size and date: post-event levels are not comparable with pre-event levels without it).", [k], "independent_physical")
        lm, ls = T / "p95k_liman_mykolaiv.csv", T / "p95k_liman_summary.csv"
        if lm.exists() and ls.exists():
            put("T17e", pd.read_csv(lm), "The Dnipro-Buh liman at Mykolaiv (Southern Bug 98027; UkrHMC yearbook 2023 table 1.2, daily means in cm above the gauge zero, zero -5.00 m BS in the sheet header, EPSG:9902 grid step to EVRF2019; station catalogue position) per day, with the Kherson gauge and the reconstructed water surface extrapolated to the gauge (outside the terrain domain: water surface only; not an input of the reconstruction). The event days carry the yearbook flag '/' (meaning to be confirmed from the legend); wind setup / setdown of +-0.3-0.5 m is part of the regime.", [lm], "independent_physical")
            put("T17f", pd.read_csv(ls), "Summary of T17e: the liman's highest level of the year (instantaneous, from the yearbook) and highest daily mean, its rise and timing against Kherson, the Kherson - Mykolaiv head, and the reconstructed surface at the liman, which comes from the westernmost SWOT node (E 457.6 km), unobserved from 6 to 22 June and therefore interpolated flat across the flood.", [ls], "independent_physical")
        put("T17d", pd.read_csv(s), "Summary of T17c. Kalynivske is withheld from the primary water surface and kept as an independent tributary validation site (maintainer decision D-INHULETS, 2026-09-29): the backwater hydrograph (the yearbook's highest level of the year -- an instantaneous value, not a daily mean -- and the highest daily mean, rise, days above the floodplain exit, record exceedance, lag after the Kherson peak stage), the validation of the reconstruction at the gauge (absolute error e_abs; event-relative error e_rise, free of any constant datum offset; peak timing; recession), the water-surface support at the gauge, and the water-surface support at the gauge (the support of the valley's whole new area is classified in T11k/T11l).", [s], "independent_physical")


def t18_dem():
    d, p = read("p57_dem_accuracy_night.csv")
    keep = d[d.set.str.contains("C seamless") & (d.set.str.contains("ALL night") | d.set.str.contains("ZONE_2_KHERSON_DELTA") | d.set.str.contains("ZONE_4_DAM_TO_KHERSON_FLOODWAY") | d.set.str.contains("low terrain"))].copy()
    keep["source"] = "Paper 2 / SWOT-DNIPRO p57 (night ICESat-2 ATL08 vs seamless DEM), copied with provenance; not re-validated here"
    put("T18", keep, "Seamless terrain-bed model accuracy against night ICESat-2 ground segments (Paper 2 / p57): RMSE, MAE, bias, median, LE90, LE95, NMAD by zone and WorldCover class, all sources together (context; the uncertainty model uses the FABDEM-only rows of T18b).", [p], "independent_physical")
    q = T / "p95j_terrain_residual_stats.csv"
    if q.exists():
        put("T18b", pd.read_csv(q), "FABDEM-DTM residual against night ICESat-2 ground on FABDEM-sourced cells of the seamless terrain-bed model (p55 source 3/4), per zone and WorldCover class and pooled: N, median (the residual class-dependent terrain-elevation bias removed on FABDEM cells), NMAD (the marginal scale of the perturbed terrain realizations), RMSE, mean, acquisition dates. FABDEM is a bare-earth DTM: the class median is a residual bias, not a canopy correction.", [q], "independent_physical")
    f = T / "p95j_terrain_variogram_fit.csv"
    if f.exists():
        put("T18c", pd.read_csv(f), "Spatial structure of the FABDEM-DTM residual (p95j): empirical semivariograms of same-date ICESat-2 pairs, fitted per zone and class (classical estimator, residual after the class median, m2) and for the standardized residual (r - b_c) / sigma_c (classical and robust Cressie-Hawkins estimators; single exponential + nugget and nested two-exponential + nugget models, Cressie WLS). The pooled robust nested fit is the correlation model of the Monte-Carlo terrain field (T11b); its nugget includes ICESat-2 segment noise and point-to-cell support mismatch.", [f], "independent_physical")


def t19_series():
    s1, p1 = read("p94_flood_dynamics_s1.csv"); s2, p2 = read("p94_flood_dynamics_s2.csv"); e, p3 = read("p94_flood_dynamics_estuary_s1.csv")
    a = s1[["date", "sensor", "orbit", "region", "coverage", "water_km2", "new_water_km2", "new_water_common_footprint_km2"]].copy(); a["area_semantics"] = "observed_S1"
    b = s2[s2.reliable][["date", "sensor", "region", "coverage", "water_km2", "new_water_km2"]].copy(); b["orbit"] = ""; b["area_semantics"] = "observed_S2 (NDWI>0 & MNDWI>0)"
    c = e[["date", "sensor", "region", "coverage", "water_km2", "new_water_km2", "new_water_common_footprint_km2"]].copy(); c["orbit"] = ""; c["area_semantics"] = "observed_S1"
    put("T19", pd.concat([a, b, c], ignore_index=True), "Per-acquisition-date new water (not water before the breach) inside the Sentinel-1 observable domain, with coverage; S2 only where >= 30 % of the region was cloud-free; estuary zone on its own grid.", [p1, p2, p3], "cross_sensor")


def t20_block_sensitivity():
    rows, src = [], []
    for lab, run in (("v003_A", "v003A"), ("v004", "v004")):                  # v004: the same recipe on the corrected labels (stage 2)
        for sp, km in [("m6_split_v1", 10.0), ("m6_split_s5", 5.0), ("m6_split_s7p5", 7.5), ("m6_split_s15", 15.0), ("m6_split_s20", 20.0)]:
            man = T / f"{sp}_manifest.json"; rd = RUNS / (f"U2_B1B2_{run}" if sp == "m6_split_v1" else f"U2_B1B2_{run}_{sp.split('_')[-1]}")
            status = "split built" if man.exists() else "split infeasible (no validation patch survives the buffer)" if sp == "m6_split_s5" else "not built"
            row = dict(labels=lab, split=sp, block_km=km, status=status)
            if man.exists():
                m = json.loads(man.read_text()); row.update(n_blocks=str(m.get("n_blocks")), n_patches=str(m.get("n_patches"))); src.append(man)
            if (rd / "eval_d1a/endpoints.csv").exists():
                e = pd.read_csv(rd / "eval_d1a/endpoints.csv", index_col=0).value; ci = pd.read_csv(rd / "eval_d1a/endpoints_ci.csv", index_col=0); src += [rd / "eval_d1a/endpoints.csv"]
                row["status"] = f"U2 {lab} trained and evaluated"
                for k in ("G_F1", "G_IoU", "G_PR_AUC", "A_FP_area_dry_cropland_km2", "B_recall_flooded_open_low_veg", "W_IoU", "BU_FP_area_km2", "A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2"):
                    row[k] = float(e.get(k, np.nan)); row[f"{k}_lo"] = float(ci.lo.get(k, np.nan)); row[f"{k}_hi"] = float(ci.hi.get(k, np.nan))
                th = json.loads((rd / "validation_threshold.json").read_text()); row["threshold"] = th["threshold"]
            elif lab == "v004":
                continue                                                      # only the v004 splits that were trained
            rows.append(row)
    put("T20", pd.DataFrame(rows), "Block-size sensitivity (U2 on v003_A and on the corrected v004 labels): the same recipe on splits with 7.5, 10 (frozen), 15 and 20 km blocks; each split has its own TEST geography, so only the endpoint values and intervals are compared, never differences.", src, "weak_label_agreement")

def readme():
    defs = [("POD", "hit / (hit + miss): share of S1 new dark water that the reconstruction allows, on the observation domain"),
            ("FAR", "terrain_only / (hit + terrain_only): share of reconstructed new water that S1 did not see (includes sensor blind spots)"),
            ("CSI", "hit / (hit + miss + terrain_only)"), ("POD_cond_outside_normally_wet", "hit / (hit + miss - miss_on_normally_wet): conditional POD outside the normally-wet class (POD | observable dry-background domain); a diagnostic conditional agreement, never a corrected POD; class fixed a priori"),
            ("precision / recall / F1 / IoU", "on unique full-frame TEST pixels owned by the frame, against weak reference labels"), ("PR-AUC", "average precision of the continuous score vs weak labels"),
            ("A1 / A2", "A1 = predicted flood on labelled dry cropland (false positive vs weak label); A2 = predicted flood burden on UNLABELLED cropland (never called false positive)"),
            ("bias / MAE / RMSE", "mean, mean absolute and root-mean-square of the residual (sign stated per table)"), ("NMAD", "1.4826 x median |r - median(r)|"), ("LE90 / LE95", "90th / 95th percentile of |r|"),
            ("95 % interval", "percentile 2.5 / 97.5 of 2000 spatial-block bootstrap resamples (seed 20260923); paired comparisons resample identical physical blocks"),
            ("Monte-Carlo band (PRIMARY)", "p05 / p50 / p95 over the coherent Monte-Carlo worlds of p95e rev 2 (one terrain-error realization over the union mosaic and one water-surface realization per draw, baseline rebuilt with it): the primary uncertainty interval of every reconstructed area and volume; W_total, A_new, V_new and Vtot each from their own ensemble"),
            ("emulator (DIAGNOSTIC)", "100 000 cluster-normal emulator draws per day (p95g) without connectivity: a computational diagnostic outside the evidence path (D-EMU, T12d); never an uncertainty estimate"),
            ("support classes (p95l)", "distance of the nearest SWOT node of a newly inundated cell: direct <= 3 km, extrapolated 3-10 km, weak > 10 km (operational thresholds); flags: capped at the Kherson gauge, cross-river (Inhulets); supported core = direct + extrapolated"),
            ("pool volume", "seamless DEM integrated under the sloped daily water surface inside the pre-breach pool polygon (p95f); design Table 19 for reference (T22 gives dV/V_design)"),
            ("daily-mean effective release", "-dV_pool/dt + Q_in(DniproHES) from the storage balance: a daily mean, not an instantaneous breach discharge (T21)"),
            ("IoU vs model (T23)", "|sensor water ∩ model water| / |sensor water ∪ model water| on pool cells the sensor observed"),
            ("observed_frac", "share of the stratum (or pool) with a valid observation on that date; areas never extrapolate to unobserved cells"),
            ("strata (T24-T26)", "POOL = pre-breach pool polygon; EXPOSED_BY_0613 = wet on 06-05 and dry by 06-13 under the p95f surface; WET_ON_0613 = still wet on 06-13"),
            ("OA", "overall agreement with the reference classification"), ("macro mean", "unweighted mean over classes")]
    lines = ["# Publication tables (generated by workflows/paper/p96_paper_tables.py -- do not edit by hand)", "",
             "Every model number is *agreement with weak reference labels*, never flood-mapping accuracy. Areas carry a semantics column:", ""]
    lines += [f"- `{k}`: {v}" for k, v in SEMANTICS.items()] + ["", "## Metric definitions", ""] + [f"- **{k}**: {v}" for k, v in defs] + ["", "## Tables", ""]
    for tid, (df, cap, src, lvl) in sorted(OUT.items()):
        lines.append(f"- **{tid}** [{lvl}] {cap} ({len(df)} rows)")
    return "\n".join(lines) + "\n"


def build(outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    for f in (t01_inventory, t02_labels, t02c_m2_threshold, t03_split, t04_arms, t05_endpoints, t06_paired, t05s_seeds, t07_attribution, t08_audit, t09_rf, t11_terrain, t12_daily,
              t13_terrain_vs_s1, t14_ontology, t15_icesat, t16_accounting, t17_swot_gauge, t18_dem, t19_series, t20_block_sensitivity, t12b_daily_series, t12d_emulator_diagnostic, t21_reservoir, t27_capacity_curves,
              t23_t26_reservoir_maps):
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
