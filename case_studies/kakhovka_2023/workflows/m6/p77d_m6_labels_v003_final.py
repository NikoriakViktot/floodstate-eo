# New in floodstate-eo, 2026-09-24. STATUS: CANDIDATE -- NOT FROZEN: transition audit failed (low-separation May scenes).
"""P77d -- m6_labels_v003_final: water retrieval target + reference state + event attribution (LAND / EVENT_FLOOD /
REFERENCE_WATER / UNKNOWN). Supersedes the v003 CANDIDATE (p77c). v002 and every arm trained on it stay frozen.

LAYERS (all per 10 m pixel, frame lattice; the 20 m S1 masks are replicated by nearest)
Reference state -- MAY-2023 S1 ONLY (p89c extended masks, 2023-04-15..05-28), counted per DISTINCT acquisition date:
    reference_domain  1 ANCHORED (p89b classifier domain), 2 EXTRAPOLATED (p89c buffer), 0 UNOBSERVED
    REFERENCE_WATER   ANCHORED and >= 2 distinct May dates classified water       reason RECURRENT_ANCHORED_WATER
    LAND              ANCHORED and >= 2 valid May dates and < 2 water dates       reason ANCHORED_DRY
    UNKNOWN           ANCHORED with < 2 valid May dates                           reason INSUFFICIENT_MAY_SUPPORT
                      EXTRAPOLATED (no independent corroboration exists here)     reason REFERENCE_EXTRAPOLATED_UNCORROBORATED
                      no valid May date                                           reason UNOBSERVED
Immediate pre-event state -- S1 06-01 / 06-02 ONLY (attribution evidence; never used to build REFERENCE_WATER):
    w_pre_state 0 dry on every valid date, 1 water on any valid date, 255 unobserved; w_pre_valid = n valid dates
Event water (STAGE-1 TARGET: water, not flood):
    1  S1 water on >= 2 of the 3 peak dates (p60 n_pos_peak) AND optical agreement (M2 central flood OR
       REFERENCE_WATER)          -- water present during the event, whatever its origin
    0  v002 NON_FLOOD (dry in every observed post-breach S1 event, >= 6 observed)
    255 otherwise
Attribution ontology (band 1):
    EVENT_FLOOD (1)      event_water = 1 AND reference_state != REFERENCE_WATER AND w_pre_state = 0 AND v002 FLOOD
    REFERENCE_WATER (2)  reference_state = REFERENCE_WATER (precedence over EVENT_FLOOD)
    LAND (0)             event_water = 0 AND reference_state = LAND
    UNKNOWN (255)        everything else (insufficient / conflicting / extrapolated evidence)
No land cover, HAND or model output is read.

Outputs: $BULK_ROOT/frames10/<F>/m6_labels_v003_final.tif (10 uint8 bands, see BANDS),
         <case_study>/tables/p77d_v003_final_{areas,transition_v002,candidates}.csv, p77d_v003_final_manifest.json
"""
from __future__ import annotations
import hashlib, json, subprocess, time
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG

OUT = CFG.BULK_ROOT / "frames10"
VERSION = "m6_labels_v003_final"
JUNE = {"B1": "ZONE_4_FLOODWAY_june2023_s32", "B2": "ZONE_2_KHERSON_DELTA_flood_june2023"}
MAY = ("2023-04-15", "2023-05-31"); WPRE = ("2023-06-01", "2023-06-02")
BANDS = ("ontology", "event_water", "reference_state", "reference_reason", "reference_domain", "n_may_valid_dates",
         "n_may_water_dates", "may_water_fraction_x100", "w_pre_state", "w_pre_valid")
REASON = {1: "RECURRENT_ANCHORED_WATER", 2: "ANCHORED_DRY", 3: "INSUFFICIENT_MAY_SUPPORT",
          4: "REFERENCE_EXTRAPOLATED_UNCORROBORATED", 5: "UNOBSERVED"}
PX = 1e-4


def to10(a, tr, F):
    d = np.zeros((F["ny"], F["nx"]), "u1")
    reproject(a.astype("u1"), d, src_transform=tr, src_crs=CFG.CRS_METRIC, dst_transform=F["transform"],
              dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest)
    return d.astype(bool)


def per_date(fid, F, lo, hi):
    """{date: (water, valid)} with scenes of the same date OR-combined (one date counts once)."""
    p = CFG.S1_CACHE / f"{JUNE[fid]}_pre2023" / "per_scene_water_ext.npz"
    z = np.load(p, allow_pickle=True); shp = tuple(int(v) for v in z["shape"])
    tr = from_origin(float(z["x0"]), float(z["y1"]), float(z["cell"]), float(z["cell"]))
    un = lambda k: np.unpackbits(z[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)
    out = {}
    for k in sorted(k for k in z.files if k[:4] == "2023" and lo <= k[:10] <= hi):
        w, v = un(k), un("valid_" + k); d = k[:10]
        if d in out:
            w, v = (out[d][0] | w), (out[d][1] | v)
        out[d] = (w & v, v)
    ext = to10(un("extended_domain"), tr, F)
    return {d: (to10(w, tr, F), to10(v, tr, F)) for d, (w, v) in out.items()}, ext, p


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(16 << 20), b""):
            h.update(c)
    return h.hexdigest()


def build(fid):
    F = CG.frame_grid(fid)
    with rasterio.open(OUT / fid / "m6_labels_v002.tif") as s:
        y2 = s.read(1)
    with rasterio.open(OUT / fid / "labels.tif") as s:
        npos = s.read(3)
    with rasterio.open(OUT / fid / "flood_central.tif") as s:
        cen = s.read(1) == 1
    may, ext, src = per_date(fid, F, *MAY)
    wpre, _, _ = per_date(fid, F, *WPRE)
    nv = np.sum([v for _, v in may.values()], 0).astype("u1")
    nw = np.sum([w for w, _ in may.values()], 0).astype("u1")
    anyv = nv > 0
    dom = np.where(~anyv, 0, np.where(ext, 2, 1)).astype("u1")
    reason = np.full(y2.shape, 5, "u1")
    reason[(dom == 1) & (nw >= 2)] = 1
    reason[(dom == 1) & (nv >= 2) & (nw < 2)] = 2
    reason[(dom == 1) & (nv < 2)] = 3
    reason[dom == 2] = 4
    ref = np.full(y2.shape, 255, "u1"); ref[reason == 1] = 2; ref[reason == 2] = 0     # 0 LAND, 2 REF_WATER
    pv = np.sum([v for _, v in wpre.values()], 0).astype("u1")
    pw = np.any([w for w, _ in wpre.values()], 0)
    wps = np.where(pv == 0, 255, np.where(pw, 1, 0)).astype("u1")
    ew = np.full(y2.shape, 255, "u1")
    ew[y2 == 0] = 0
    ew[(npos >= 2) & (cen | (ref == 2))] = 1
    ont = np.full(y2.shape, 255, "u1")
    ont[(ew == 0) & (ref == 0)] = 0
    ont[(ew == 1) & (ref != 2) & (wps == 0) & (y2 == 1)] = 1
    ont[ref == 2] = 2
    frac = np.where(nv > 0, np.round(100 * nw / np.maximum(nv, 1)), 255).astype("u1")
    arrs = (ont, ew, ref, reason, dom, nv, nw, frac, wps, pv)
    prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=len(BANDS), dtype="uint8", nodata=None,
                crs=CFG.CRS_METRIC, transform=F["transform"], compress="deflate", tiled=True, blockxsize=512,
                blockysize=512)
    p = OUT / fid / f"{VERSION}.tif"
    with rasterio.open(p.with_suffix(".tif.part"), "w", **prof) as o:
        for b, (a, nm) in enumerate(zip(arrs, BANDS), 1):
            o.write(a, b); o.set_band_description(b, nm)
        o.update_tags(version=VERSION, ontology="0 LAND, 1 EVENT_FLOOD, 2 REFERENCE_WATER, 255 UNKNOWN",
                      event_water="1 water during event, 0 dry, 255 unknown (STAGE-1 target)",
                      reference_state="0 LAND, 2 REFERENCE_WATER, 255 UNKNOWN", reference_reason=json.dumps(REASON),
                      reference_domain="0 UNOBSERVED, 1 ANCHORED, 2 EXTRAPOLATED",
                      may_dates=json.dumps(sorted(may)), w_pre_dates=json.dumps(sorted(wpre)),
                      producer="p77d_m6_labels_v003_final.py")
    p.with_suffix(".tif.part").replace(p)
    rows = []
    for dn, dm in (("ALL", np.ones(y2.shape, bool)), ("ANCHORED", dom == 1), ("EXTRAPOLATED", dom == 2),
                   ("UNOBSERVED", dom == 0)):
        for c, cn in ((0, "LAND"), (1, "EVENT_FLOOD"), (2, "REFERENCE_WATER"), (255, "UNKNOWN")):
            rows.append(dict(frame=fid, reference_domain=dn, ontology=cn, km2=round(float(((ont == c) & dm).sum()) * PX, 2)))
        for c, cn in ((0, "LAND"), (1, "WATER"), (255, "UNKNOWN")):
            rows.append(dict(frame=fid, reference_domain=dn, ontology=f"event_water_{cn}",
                             km2=round(float(((ew == c) & dm).sum()) * PX, 2)))
    tr = []
    for a, an in ((0, "NON_FLOOD"), (1, "FLOOD"), (255, "IGNORE")):
        for b, bn in ((0, "LAND"), (1, "EVENT_FLOOD"), (2, "REFERENCE_WATER"), (255, "UNKNOWN")):
            tr.append(dict(frame=fid, v002=an, v003_final=bn, km2=round(float(((y2 == a) & (ont == b)).sum()) * PX, 2)))
    return rows, tr, str(src), dict(ont=ont, reason=reason, dom=dom, nv=nv, nw=nw, wps=wps, F=F)


def main():
    A, T, srcs, S = [], [], {}, {}
    for fid in ("B1", "B2"):
        r, t, src, st = build(fid); A += r; T += t; srcs[src] = sha(Path(src)); S[fid] = st
        print(fid, "done", flush=True)
    pd.DataFrame(A).to_csv(CFG.TABLES / "p77d_v003_final_areas.csv", index=False)
    pd.DataFrame(T).to_csv(CFG.TABLES / "p77d_v003_final_transition_v002.csv", index=False)
    # the two pre-registered canonical failure cases: component masks of the frozen U0d TEST prediction
    import importlib.util
    here = Path(__file__).resolve().parent
    ld = lambda n: (lambda s: (s.loader.exec_module(m := importlib.util.module_from_spec(s)), m)[1])(
        importlib.util.spec_from_file_location(n, here / f"{n}.py"))
    E, P84 = ld("m6_eval"), ld("p84_m6_split_b1b2")
    thr = json.loads((here.parents[1] / "runs" / "U0d_B1B2_v1" / "validation_threshold.json").read_text())["threshold"]
    cand = []
    for fid, comp in (("B1", 22), ("B2", 78)):
        st = S[fid]; F = st["F"]
        role = rasterio.open(OUT / fid / "m6_split_v1_role.tif").read(1)
        s1 = rasterio.open(OUT / fid / "s1_change.tif"); d = list(s1.descriptions)
        has = (s1.read(d.index("n_valid_event") + 1) > 0) & (s1.read(1) != -32768)
        y = rasterio.open(OUT / fid / "m6_labels_v002.tif").read(1); y = np.where(np.isin(role, (1, 2, 3)) & has, y, 255)
        q = rasterio.open(OUT / fid / "m6" / "U0d_score.tif").read(1); sc = np.where(q == 65535, -1, q / 1e4)
        geo = (role == 3) & has
        cm, _, _ = E._isolated(geo & (sc >= thr), geo, P84.p73_10m(fid, F), geo & (y == 1))
        m = cm == comp
        r = dict(frame=fid, component=comp, area_km2=round(float(m.sum()) * PX, 4))
        for c, cn in ((0, "LAND"), (1, "EVENT_FLOOD"), (2, "REFERENCE_WATER"), (255, "UNKNOWN")):
            r[f"ontology_{cn}_frac"] = round(float((st["ont"][m] == c).mean()), 3)
        for k, v in REASON.items():
            r[f"reason_{v}_frac"] = round(float((st["reason"][m] == k).mean()), 3)
        r["w_pre_water_frac"] = round(float((st["wps"][m] == 1).mean()), 3)
        cand.append(r)
    pd.DataFrame(cand).to_csv(CFG.TABLES / "p77d_v003_final_candidates.csv", index=False)
    print(pd.DataFrame(cand).T.to_string())
    git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    man = dict(version=VERSION, status="CANDIDATE_NOT_FROZEN", frozen_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               code_commit=git, rules=__doc__, sources_sha256=srcs,
               outputs={f: str(OUT / f / f"{VERSION}.tif") for f in S},
               output_sha256={f: sha(OUT / f / f"{VERSION}.tif") for f in S},
               use="Stage-1 trains on band 2 (event_water) ONLY; attribution uses bands 3-10; ontology band 1 is the "
                   "product/evaluation label. W_pre never enters REFERENCE_WATER nor Stage-1 inputs.")
    (CFG.TABLES / "p77d_v003_final_manifest.json").write_text(json.dumps(man, indent=1))
    D = pd.DataFrame(A); print(D.pivot_table(index=["frame", "reference_domain"], columns="ontology", values="km2").to_string())
    print(pd.DataFrame(T).pivot_table(index=["frame", "v002"], columns="v003_final", values="km2").to_string())


if __name__ == "__main__":
    main()
