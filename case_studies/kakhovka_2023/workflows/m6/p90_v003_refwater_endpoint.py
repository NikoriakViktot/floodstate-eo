# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Evaluates finished arms against the v003_A ontology; trains nothing.
"""P90 -- v003_A attribution endpoints for finished M6 arms, on the frozen m6_split_v1 TEST geography.

The D1 harness (m6_eval) scores agreement with a binary label. v003_A adds what D1 cannot see: a labelled
REFERENCE_WATER class (recurrent May-2023 S1 water) and the immediate pre-event S1 state W_pre. This script reports,
per arm, at that arm's OWN frozen validation threshold (nothing is re-thresholded):

    R_pred_on_reference_water_km2      predicted flood on TEST REFERENCE_WATER  (the temporal-attribution error;
                                       split into W_pre = water and W_pre = dry)
    R_frac_reference_water_above_thr   the same as a fraction of the REFERENCE_WATER area
    E_recall_event_flood               recall on TEST EVENT_FLOOD (identical positives in v002 and v003_A)
    L_FP_on_land_km2                   predicted flood on TEST LAND (v003_A negatives with >= 3 admitted May dates)
    U_pred_on_unknown_km2              predicted flood burden on TEST UNKNOWN (never called FP)

Spatial-block bootstrap CI (2000 resamples of the 10 km blocks) per arm; paired B - A differences on identical
blocks for every requested pair. Arms trained on v002 (runs/<ARM>_B1B2_v1) can be listed next to arms trained on
v003_A (runs/<ARM>_B1B2_v003A): the label effect and the input effect are then separable.

--labels v004 (2026-09-29): the same endpoints against the v004 ontology (the v003_A rule on the corrected M2 without TRACE,
docs/LABEL_CONTRACTS.md); outputs tagged p90_v004_*. Review F11: a ratio endpoint whose denominator is empty in a (re)sample
is UNDEFINED (NaN), never 0; every bootstrap reports how many resamples defined it (<endpoint>_n_defined, paired n_defined).

Output: <case_study>/tables/p90_{v003A|v004}_{endpoints,by_frame,paired,blocks}.csv
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = CFG.BULK_ROOT / "frames10"
PX = 1e-4
FRAMES = ("B1", "B2")
KEYS = ["R_ref_px", "R_ref_wpre_water_px", "R_ref_wpre_dry_px", "R_pred_px", "R_pred_wpre_water_px", "R_pred_wpre_dry_px",
        "E_px", "E_pred_px", "L_px", "L_pred_px", "U_px", "U_pred_px"]


def _load(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


RATIOS = ("R_frac_reference_water_above_thr", "E_recall_event_flood", "L_FP_rate_land")


def _ratio(num, den, nd):
    return round(num / den, nd) if den > 0 else float("nan")                  # F11: empty support -> undefined, not 0


def endpoints(c):
    g = lambda k: float(c[k])
    return dict(R_pred_on_reference_water_km2=round(g("R_pred_px") * PX, 4),
                R_pred_on_reference_water_wpre_water_km2=round(g("R_pred_wpre_water_px") * PX, 4),
                R_pred_on_reference_water_wpre_dry_km2=round(g("R_pred_wpre_dry_px") * PX, 4),
                R_frac_reference_water_above_thr=_ratio(g("R_pred_px"), g("R_ref_px"), 5),
                R_reference_water_evaluated_km2=round(g("R_ref_px") * PX, 2),
                E_recall_event_flood=_ratio(g("E_pred_px"), g("E_px"), 4),
                E_FN_km2=round((g("E_px") - g("E_pred_px")) * PX, 4), E_reference_km2=round(g("E_px") * PX, 2),
                L_FP_on_land_km2=round(g("L_pred_px") * PX, 4), L_FP_rate_land=_ratio(g("L_pred_px"), g("L_px"), 6),
                L_evaluated_km2=round(g("L_px") * PX, 2),
                U_pred_on_unknown_km2=round(g("U_pred_px") * PX, 4), U_evaluated_km2=round(g("U_px") * PX, 2))


def frame_layers(fid, P84, P86, labels="v003_A"):
    F = CG.frame_grid(fid)
    with rasterio.open(OUT / fid / "s1_change.tif") as s:
        d = list(s.descriptions); ne = s.read(d.index("n_valid_event") + 1); d0 = s.read(1)
    has = (ne > 0) & (d0 != P86.ND)
    role = P86.read(fid, f"{P86.SPLIT}_role.tif", 1)[0]
    with rasterio.open(OUT / fid / f"m6_labels_{labels}.tif") as s:
        d = list(s.descriptions); ont = s.read(1); wp = s.read(d.index("w_pre_state") + 1)
    geo = (role == 3) & has
    gx = F["transform"].c + 10.0 * np.arange(F["nx"]); gy = F["transform"].f - 10.0 * np.arange(F["ny"])
    blk = np.floor(gy / P84.BLOCK_M).astype("i8")[:, None] * 100000 + np.floor(gx / P84.BLOCK_M).astype("i8")[None, :]
    return dict(geo=geo, ont=np.where(geo, ont, 255).astype("u1"), wp=wp, blk=blk)


def counts(pred, L, mask=None):
    m = L["geo"] if mask is None else (L["geo"] & mask)
    ref, ev, land, unk = m & (L["ont"] == 2), m & (L["ont"] == 1), m & (L["ont"] == 0), m & (L["ont"] == 255)
    ww, wd = ref & (L["wp"] == 1), ref & (L["wp"] != 1)
    return dict(R_ref_px=int(ref.sum()), R_ref_wpre_water_px=int(ww.sum()), R_ref_wpre_dry_px=int(wd.sum()),
                R_pred_px=int((pred & ref).sum()), R_pred_wpre_water_px=int((pred & ww).sum()),
                R_pred_wpre_dry_px=int((pred & wd).sum()), E_px=int(ev.sum()), E_pred_px=int((pred & ev).sum()),
                L_px=int(land.sum()), L_pred_px=int((pred & land).sum()), U_px=int(unk.sum()),
                U_pred_px=int((pred & unk).sum()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True, help="run dirs under runs/, e.g. U2_B1B2_v1 U2b_B1B2_v003A")
    ap.add_argument("--pairs", nargs="*", default=[], help="A:B pairs of run dirs for paired block bootstrap")
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--labels", default="v003_A", choices=["v003_A", "v004"], help="reference ontology raster m6_labels_<labels>.tif")
    a = ap.parse_args(); tag = a.labels.replace("_", "")
    P84, P86 = _load("p84_m6_split_b1b2"), _load("p86_m6_train_arm")
    L = {f: frame_layers(f, P84, P86, a.labels) for f in FRAMES}
    rows, byf, blocks = [], [], {}
    for run in a.runs:
        rd = ROOT / "runs" / run
        thr = json.loads((rd / "validation_threshold.json").read_text())["threshold"]
        arm, suffix = run.split("_B1B2_")
        score_name = f"{arm}_score.tif" if suffix == "v1" else f"{arm}_{suffix}_score.tif"
        tot, per_block = {k: 0 for k in KEYS}, []
        for f in FRAMES:
            with rasterio.open(OUT / f / "m6" / score_name) as s:
                q = s.read(1)
            pred = L[f]["geo"] & (q != 65535) & (q / 1e4 >= thr)
            c = counts(pred, L[f]); byf.append(dict(run=run, frame=f, threshold=thr, **endpoints(c)))
            for k in KEYS:
                tot[k] += c[k]
            for b in np.unique(L[f]["blk"][L[f]["geo"]]):
                per_block.append(dict(block=int(b), **counts(pred, L[f], L[f]["blk"] == b)))
        B = pd.DataFrame(per_block).groupby("block").sum().sort_index(); blocks[run] = B
        rows.append(dict(run=run, threshold=thr, **endpoints(tot)))
        rng = np.random.default_rng(20260923); M = B[KEYS].to_numpy(); bs = []
        for _ in range(a.n_boot):
            bs.append(endpoints(dict(zip(KEYS, M[rng.integers(0, len(M), len(M))].sum(0)))))
        D = pd.DataFrame(bs)
        rows[-1].update({f"{k}_lo": round(float(D[k].quantile(0.025)), 5) for k in D.columns})
        rows[-1].update({f"{k}_hi": round(float(D[k].quantile(0.975)), 5) for k in D.columns})
        rows[-1].update({f"{k}_n_defined": int(D[k].notna().sum()) for k in RATIOS})
        print(run, {k: v for k, v in rows[-1].items() if not k.endswith(("_lo", "_hi"))})
    T = CFG.TABLES
    pd.DataFrame(rows).assign(labels=a.labels).to_csv(T / f"p90_{tag}_endpoints.csv", index=False)
    pd.DataFrame(byf).assign(labels=a.labels).to_csv(T / f"p90_{tag}_by_frame.csv", index=False)
    pd.concat([b.assign(run=r) for r, b in blocks.items()]).to_csv(T / f"p90_{tag}_blocks.csv")
    pr = []
    for pair in a.pairs:
        ra, rb = pair.split(":")
        A, Bm = blocks[ra], blocks[rb]; assert A.index.equals(Bm.index)
        MA, MB = A[KEYS].to_numpy(), Bm[KEYS].to_numpy(); rng = np.random.default_rng(20260923); out = []
        for _ in range(a.n_boot):
            i = rng.integers(0, len(MA), len(MA))
            ea, eb = endpoints(dict(zip(KEYS, MA[i].sum(0)))), endpoints(dict(zip(KEYS, MB[i].sum(0))))
            out.append({k: eb[k] - ea[k] for k in ea})
        D = pd.DataFrame(out)
        for k in D.columns:
            pr.append(dict(A=ra, B=rb, endpoint=k, median=round(float(D[k].median()), 5),
                           lo=round(float(D[k].quantile(0.025)), 5), hi=round(float(D[k].quantile(0.975)), 5), n_defined=int(D[k].notna().sum())))
    if pr:
        P = pd.DataFrame(pr).assign(labels=a.labels); P.to_csv(T / f"p90_{tag}_paired.csv", index=False)
        print(P[P.endpoint.isin(["R_pred_on_reference_water_km2", "E_recall_event_flood", "L_FP_on_land_km2",
                                 "U_pred_on_unknown_km2"])].to_string(index=False))
    print(f"-> tables/p90_{tag}_*.csv")


if __name__ == "__main__":
    main()
