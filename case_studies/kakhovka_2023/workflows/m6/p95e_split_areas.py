# New in floodstate-eo, 2026-10-01 (maintainer, on the reviewer's reading of p95z: report the new flooding of dry ground apart from the
# inundation of the reed / wetland complex). STATUS: ACTIVE. Imports p95e unchanged (its chunk-cache fingerprint stays valid).
"""P95e split -- the same coherent Monte-Carlo worlds as p95e, accounted per ground class (p95x ground_class.tif):

  A_new_dry      new inundation on DRY-BEFORE-EVENT ground (no optical pre-breach water, no reed / wetland complex, not WorldCover water):
                 the new flooding of ground that was dry before the breach -- the strict headline quantity
  A_wet_water    water on the VEGETATED_WETLAND complex (WorldCover herbaceous wetland or model-only normally wet): the inundation of the
                 wetland vegetation; its pre-breach value (5 June, same rule) and the event increase over it are given too. Before the
                 breach the complex already shows a C-band signature consistent with wet or inundated emergent vegetation (p95z); the
                 event produced a distinct canopy-inundation transition. No claim of pre-breach open water is made.
  A_new_wet      the part of the old A_new (new = P_t outside the same-rule baseline) that lies on the wetland complex
  A_new_all      sum over the ground classes = the A_new of p95e (gate: the medians must agree)
Worlds: draw 0 = nominal (kept apart), draws 1..n with the p95e seed; key dates + 5 June. Per world the corridor and the Inhulets valley
are also summed date-matched. Outputs: tables/p95e_split_areas.csv (nominal, p05 / p50 / p95), p95e_split_draws.csv.gz, p95e_split_manifest.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import multiprocessing as mp
import os
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GROUND = {0: "dry_before_event", 1: "vegetated_wetland", 2: "open_water_reference", 3: "other_water", 4: "outside"}
REGIONS = (("DNIPRO_CORRIDOR", 1), ("INHULETS_VALLEY_rect", 2), ("P42_FLOODPLAIN_DOMAIN", 4))
NCODE = 64 * 8


def _ld(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


E = _ld("p95e", HERE / "p95e_uncertainty_mc.py")


def _split_chunk(ks):
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    G = E._G; bidx = G["bidx"]; code2 = G["split_code"]; dates = G["split_dates"]; out = []
    for k in ks:
        m = E.draw_masks(k, dates, with_water=True)
        for d in dates:
            new, pot = m[d]
            out.append((k, d, np.bincount(code2[new.ravel()[bidx]], minlength=NCODE), np.bincount(code2[pot.ravel()[bidx]], minlength=NCODE)))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=1000); ap.add_argument("--seed", type=int, default=20260929)
    ap.add_argument("--workers", type=int, default=8); ap.add_argument("--chunk", type=int, default=10)
    a = ap.parse_args(); t0 = time.time()
    import pandas as pd
    import rasterio

    from floodstate_eo import _kakhovka_legacy_config as CFG
    ea = argparse.Namespace(n=a.n, seed=a.seed, workers=a.workers, rule="connected_ceiling", days="all", mode="primary", chunk=a.chunk, dates=None,
                            sigma_datum=E.SIGMA_DATUM_M, sigma_gauge=E.SIGMA_GAUGE_M, pass_term=0.0, range_m=None, no_nugget=False, connectivity=8,
                            seed_network="main_stem", max_gap_days=None, tag="")
    P95, M, W, prm, _comp, _cv = E.setup(ea)
    prm = dict(prm, seed=a.seed); E._G["prm"] = prm
    with rasterio.open(CFG.BULK_ROOT / "floodplain_dyn" / "_weak_labels" / "ground_class.tif") as s:
        gc = s.read(1)
    r0, r1, c0, c1 = E._G["crop"]; gc = gc[r0:r1, c0:c1].copy(); gc[gc == 255] = 4
    bidx, rc = E._G["bidx"], E._G["rc"]
    code2 = (rc.astype("i4") * 8 + gc.ravel()[bidx].astype("i4")); assert code2.max() < NCODE
    dates = ["2023-06-05"] + list(E.KEY_DATES); E._G.update(split_code=code2, split_dates=dates)
    print(f"setup {round(time.time() - t0)} s; base cells {len(bidx):,}; dates {dates}", flush=True)
    chunks = [list(range(s_, min(s_ + a.chunk, a.n + 1))) for s_ in range(0, a.n + 1, a.chunk)]
    res = []; done = 0
    with mp.get_context("fork").Pool(a.workers) as pool:
        for out in pool.imap_unordered(_split_chunk, chunks, chunksize=1):
            res.extend(out); done += len({o[0] for o in out}); print(f"  split: {done}/{a.n + 1} worlds, {round(time.time() - t0)} s", flush=True)
    ck = P95.CELL_KM2; rows = []
    for k, d, cn, cp in res:
        for rname, bit in REGIONS:
            if rname not in E._G["regions"]:
                continue
            for g, gname in GROUND.items():
                codes = [(zid * 8 + rb) * 8 + g for zid in E._G["zone_ids"] for rb in range(8) if rb & bit]
                rows.append(dict(draw=k, date=d, region=rname, ground=gname, new_km2=float(cn[codes].sum()) * ck, water_km2=float(cp[codes].sum()) * ck))
    D = pd.DataFrame(rows)
    both = D[D.region.isin(["DNIPRO_CORRIDOR", "INHULETS_VALLEY_rect"])].groupby(["draw", "date", "ground"], as_index=False)[["new_km2", "water_km2"]].sum()
    both["region"] = "DNIPRO_CORRIDOR+INHULETS_VALLEY_rect"; D = pd.concat([D, both], ignore_index=True)
    tot = D.groupby(["draw", "date", "region"], as_index=False)[["new_km2", "water_km2"]].sum(); tot["ground"] = "all"; D = pd.concat([D, tot], ignore_index=True)
    pre = D[D.date == "2023-06-05"].set_index(["draw", "region", "ground"]).water_km2
    D["water_increase_km2"] = D.water_km2 - pre.reindex(pd.MultiIndex.from_frame(D[["draw", "region", "ground"]])).to_numpy()
    D.to_csv(CFG.TABLES / "p95e_split_draws.csv.gz", index=False, compression="gzip")
    S = []
    for (d, rname, gname), x in D.groupby(["date", "region", "ground"]):
        nom = x[x.draw == 0]; mc = x[x.draw > 0]
        r = dict(date=d, region=rname, ground=gname, n_draws=len(mc))
        for q in ("new_km2", "water_km2", "water_increase_km2"):
            r[f"{q}_nominal"] = round(float(nom[q].iloc[0]), 2) if len(nom) else np.nan
            for p_ in (5, 50, 95):
                r[f"{q}_p{p_:02d}"] = round(float(np.percentile(mc[q], p_)), 2)
        S.append(r)
    S = pd.DataFrame(S); S.to_csv(CFG.TABLES / "p95e_split_areas.csv", index=False)
    # gate: the sum over the ground classes reproduces the A_new of p95e in the same worlds
    R = pd.read_csv(CFG.TABLES / "p95e_area_volume_uncertainty.csv").set_index(["date", "region"])
    gate = []
    for d in ("2023-06-07", "2023-06-08", "2023-06-09"):
        s_ = S[(S.date == d) & (S.region == "DNIPRO_CORRIDOR") & (S.ground == "all")].iloc[0]
        gate.append(dict(date=d, split_p50=s_["new_km2_p50"], p95e_p50=float(R.loc[(d, "DNIPRO_CORRIDOR"), "A_p50_km2"]),
                         split_nominal=s_["new_km2_nominal"], p95e_nominal=float(R.loc[(d, "DNIPRO_CORRIDOR"), "A_central_km2"])))
    G_ = pd.DataFrame(gate); print(G_.to_string(index=False))
    assert (np.abs(G_.split_p50 - G_.p95e_p50) <= 0.15).all(), "the split worlds do not reproduce p95e's A_new"
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    show = S[(S.region.isin(["DNIPRO_CORRIDOR", "DNIPRO_CORRIDOR+INHULETS_VALLEY_rect"])) & S.ground.isin(["dry_before_event", "vegetated_wetland", "all"])
             & S.date.isin(["2023-06-05", "2023-06-07", "2023-06-08", "2023-06-09", "2023-06-13"])]
    print(show[["date", "region", "ground", "new_km2_nominal", "new_km2_p05", "new_km2_p50", "new_km2_p95", "water_km2_p50", "water_increase_km2_p05", "water_increase_km2_p50", "water_increase_km2_p95"]].to_string(index=False))
    (CFG.TABLES / "p95e_split_manifest.json").write_text(json.dumps(dict(
        producer="p95e_split_areas.py", n_draws=a.n, seed=a.seed, workers=a.workers, dates=dates, seconds=round(time.time() - t0),
        ground_classes=GROUND, ground_source="$BULK/floodplain_dyn/_weak_labels/ground_class.tif (p95x)", worlds="identical to p95e (same draw index, RNG stream, setup)",
        gate=gate, decision="maintainer 2026-10-01: A_new on dry-before-event ground and the vegetated-wetland inundation reported separately"), indent=1, default=str))
    print("->", CFG.TABLES / "p95e_split_areas.csv", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
