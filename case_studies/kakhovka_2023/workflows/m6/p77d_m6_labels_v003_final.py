# New in floodstate-eo, 2026-09-24. STATUS: CANDIDATE. Variant A = primary candidate, variant B = sensitivity only.
# Rev 2 (2026-09-24): scene QA + temporal-persistence pixel rule; REFERENCE_WATER no longer vetoes EVENT_FLOOD.
"""P77d -- m6_labels_v003_final: water retrieval target + reference state + event attribution (LAND / EVENT_FLOOD /
REFERENCE_WATER / UNKNOWN). Supersedes the v003 CANDIDATE (p77c). v002 and every arm trained on it stay frozen.

LAYERS (all per 10 m pixel, frame lattice; the 20 m S1 masks are replicated by nearest)
Reference state -- MAY-2023 S1 ONLY (p89c extended masks, 2023-04-15..05-28), counted per DISTINCT acquisition date:
    reference_domain  1 ANCHORED (p89b classifier domain), 2 EXTRAPOLATED (p89c buffer), 0 UNOBSERVED
    SCENE QA  A (primary): exact p0v/p0w classify_scenes -- robust z of LDA separation and of largest-part fraction
                 WITHIN the frame's May scenes; GOOD and MARGINAL admitted, POOR (z_sep >= 3.5 AND z_topo >= 3.0)
                 rejected; no other threshold.
              B (SENSITIVITY ONLY -- "June-referenced scene-separation QA"): z_sep against the frame's June scene
                 separations admitted by p0v/p0w; z_sep >= 2.5 rejected. Note: the June set contains event-period
                 scenes, so B lets event-period behaviour filter the PRE reference; it must never replace A.
    REFERENCE_WATER   ANCHORED, >= 3 admitted valid dates, >= 2 water dates, water fraction >= 0.50
                                                                                  reason RECURRENT_ANCHORED_WATER
    LAND              ANCHORED, >= 3 admitted valid dates, <= 1 water date        reason ANCHORED_DRY
    UNKNOWN           ANCHORED, < 3 admitted valid dates                          reason INSUFFICIENT_MAY_SUPPORT
                      ANCHORED, >= 3 valid, water dates >= 2 but fraction < 0.5   reason MIXED_MAY_EVIDENCE
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
    EVENT_FLOOD (1)      event_water = 1 AND w_pre_state = 0 AND v002 FLOOD -- REFERENCE_WATER is NOT a veto;
                         where both hold, band 11 flags SEASONALLY_WET_BUT_DRY_AT_EVENT_ONSET
    REFERENCE_WATER (2)  reference_state = REFERENCE_WATER and not EVENT_FLOOD
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
         "n_may_water_dates", "may_water_fraction_x100", "w_pre_state", "w_pre_valid",
         "seasonally_wet_but_dry_at_event_onset")
REASON = {1: "RECURRENT_ANCHORED_WATER", 2: "ANCHORED_DRY", 3: "INSUFFICIENT_MAY_SUPPORT",
          4: "REFERENCE_EXTRAPOLATED_UNCORROBORATED", 5: "UNOBSERVED", 6: "MIXED_MAY_EVIDENCE"}
QA_SRC = {"B1": "p0v_zone4_scene_qa.csv", "B2": "p0w_zone2_scene_qa.csv"}
ADMITTED: dict = {}
PX = 1e-4


def to10(a, tr, F):
    d = np.zeros((F["ny"], F["nx"]), "u1")
    reproject(a.astype("u1"), d, src_transform=tr, src_crs=CFG.CRS_METRIC, dst_transform=F["transform"],
              dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest)
    return d.astype(bool)


def robust_z(x):
    x = np.asarray(x, float); med = np.nanmedian(x); mad = np.nanmedian(np.abs(x - med)) * 1.4826
    return np.zeros_like(x) if not np.isfinite(mad) or mad <= 0 else (med - x) / mad


def scene_qa(fid, variant):
    """Admitted May event ids (see SCENE QA). Topology = largest-part fraction of the ORIGINAL-domain p89b mask."""
    import io
    from scipy import ndimage
    z = np.load(CFG.S1_CACHE / f"{JUNE[fid]}_pre2023" / "per_scene_water.npz", allow_pickle=True)
    shp = tuple(int(v) for v in z["shape"])
    S = pd.read_csv(CFG.TABLES / "p89b_scenes.csv"); S = S[(S.frame == fid) & (S.role == "PRE_REFERENCE")].copy()
    top = []
    for e in S.event:
        m = np.unpackbits(z[e], count=shp[0] * shp[1]).reshape(shp).astype(bool)
        lab, n = ndimage.label(m, structure=np.ones((3, 3), int))
        sz = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)) if n else np.array([0.0])
        top.append(float(sz.max() / max(sz.sum(), 1)))
    S["largest_part_fraction"] = top
    if variant == "A":
        S["z_sep"] = robust_z(S.lda_separation); S["z_topo"] = robust_z(S.largest_part_fraction)
        S["qa"] = np.where((S.z_sep >= 3.5) & (S.z_topo >= 3.0), "POOR",
                           np.where(S.z_sep >= 2.5, "MARGINAL", "GOOD"))
        S["admitted"] = S.qa != "POOR"
    else:
        J = pd.read_csv(io.StringIO(subprocess.run(["git", "-C", str(CFG._SWOT_DNIPRO_SIBLING), "show",
                                                    f"f3e3e1a:outputs/tables/{QA_SRC[fid]}"],
                                                   capture_output=True, text=True, check=True).stdout))
        js = J.lda_separation.to_numpy(float); med = np.median(js); mad = np.median(np.abs(js - med)) * 1.4826
        S["z_sep"] = (med - S.lda_separation) / mad
        S["qa"] = np.where(S.z_sep >= 2.5, "REJECT_JUNE_REFERENCED", "ADMIT")
        S["admitted"] = S.z_sep < 2.5
    S["variant"] = variant
    ADMITTED[(fid, variant)] = S
    return set(S[S.admitted].event)


def per_date(fid, F, lo, hi, admit=None):
    """{date: (water, valid)} with scenes of the same date OR-combined (one date counts once)."""
    p = CFG.S1_CACHE / f"{JUNE[fid]}_pre2023" / "per_scene_water_ext.npz"
    z = np.load(p, allow_pickle=True); shp = tuple(int(v) for v in z["shape"])
    tr = from_origin(float(z["x0"]), float(z["y1"]), float(z["cell"]), float(z["cell"]))
    un = lambda k: np.unpackbits(z[k], count=shp[0] * shp[1]).reshape(shp).astype(bool)
    out = {}
    for k in sorted(k for k in z.files if k[:4] == "2023" and lo <= k[:10] <= hi and (admit is None or k in admit)):
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


def build(fid, variant):
    F = CG.frame_grid(fid)
    with rasterio.open(OUT / fid / "m6_labels_v002.tif") as s:
        y2 = s.read(1)
    with rasterio.open(OUT / fid / "labels.tif") as s:
        npos = s.read(3)
    with rasterio.open(OUT / fid / "flood_central.tif") as s:
        cen = s.read(1) == 1
    may, ext, src = per_date(fid, F, *MAY, admit=scene_qa(fid, variant))
    wpre, _, _ = per_date(fid, F, *WPRE)
    nv = np.sum([v for _, v in may.values()], 0).astype("u1")
    nw = np.sum([w for w, _ in may.values()], 0).astype("u1")
    anyv = nv > 0
    dom = np.where(~anyv, 0, np.where(ext, 2, 1)).astype("u1")
    reason = np.full(y2.shape, 5, "u1")
    frac_ = nw / np.maximum(nv, 1)
    reason[(dom == 1) & (nv < 3)] = 3
    reason[(dom == 1) & (nv >= 3) & (nw <= 1)] = 2
    reason[(dom == 1) & (nv >= 3) & (nw >= 2) & (frac_ < 0.5)] = 6
    reason[(dom == 1) & (nv >= 3) & (nw >= 2) & (frac_ >= 0.5)] = 1
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
    ev_flood = (ew == 1) & (wps == 0) & (y2 == 1)
    ont[(ref == 2) & ~ev_flood] = 2
    ont[ev_flood] = 1
    seas = (ev_flood & (ref == 2)).astype("u1")
    frac = np.where(nv > 0, np.round(100 * nw / np.maximum(nv, 1)), 255).astype("u1")
    arrs = (ont, ew, ref, reason, dom, nv, nw, frac, wps, pv, seas)
    prof = dict(driver="GTiff", height=F["ny"], width=F["nx"], count=len(BANDS), dtype="uint8", nodata=None,
                crs=CFG.CRS_METRIC, transform=F["transform"], compress="deflate", tiled=True, blockxsize=512,
                blockysize=512)
    p = OUT / fid / f"m6_labels_v003_{variant}.tif"
    with rasterio.open(p.with_suffix(".tif.part"), "w", **prof) as o:
        for b, (a, nm) in enumerate(zip(arrs, BANDS), 1):
            o.write(a, b); o.set_band_description(b, nm)
        o.update_tags(version=VERSION, ontology="0 LAND, 1 EVENT_FLOOD, 2 REFERENCE_WATER, 255 UNKNOWN",
                      event_water="1 water during event, 0 dry, 255 unknown (STAGE-1 target)",
                      reference_state="0 LAND, 2 REFERENCE_WATER, 255 UNKNOWN", reference_reason=json.dumps(REASON),
                      reference_domain="0 UNOBSERVED, 1 ANCHORED, 2 EXTRAPOLATED",
                      may_dates=json.dumps(sorted(may)), w_pre_dates=json.dumps(sorted(wpre)),
                      variant=variant, producer="p77d_m6_labels_v003_final.py")
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
    for r_ in rows + tr:
        r_["variant"] = variant
    return rows, tr, str(src), dict(ont=ont, reason=reason, dom=dom, nv=nv, nw=nw, wps=wps, F=F, ref=ref, seas=seas,
                                    y2=y2, frac=frac, ew=ew)


def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--variant", choices=["A", "B"], required=True); a = ap.parse_args()
    v = a.variant; tag = f"v003_{v}"
    A, T, srcs, S = [], [], {}, {}
    for fid in ("B1", "B2"):
        r, t, src, st = build(fid, v); A += r; T += t; srcs[src] = sha(Path(src)); S[fid] = st
        print(fid, "done", flush=True)
    pd.concat(ADMITTED.values()).to_csv(CFG.TABLES / f"p77d_{tag}_scene_qa.csv", index=False)
    pd.DataFrame(A).to_csv(CFG.TABLES / f"p77d_{tag}_areas.csv", index=False)
    pd.DataFrame(T).to_csv(CFG.TABLES / f"p77d_{tag}_transition_v002.csv", index=False)
    # distributions for every REFERENCE_WATER pixel
    dist = []
    for fid, st in S.items():
        m = st["ref"] == 2
        for k, c in zip(*np.unique(st["nv"][m], return_counts=True)):
            dist.append(dict(variant=v, frame=fid, what="n_valid_dates", value=int(k), km2=round(float(c) * PX, 3)))
        for k, c in zip(*np.unique((st["frac"][m] // 10) * 10, return_counts=True)):
            dist.append(dict(variant=v, frame=fid, what="may_water_fraction_decile", value=int(k), km2=round(float(c) * PX, 3)))
    pd.DataFrame(dist).to_csv(CFG.TABLES / f"p77d_{tag}_refwater_distributions.csv", index=False)
    # canonical failure cases (pre-registered): component masks of the frozen U0d TEST prediction
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
        y = np.where(np.isin(role, (1, 2, 3)) & has, st["y2"], 255)
        q = rasterio.open(OUT / fid / "m6" / "U0d_score.tif").read(1); sc = np.where(q == 65535, -1, q / 1e4)
        geo = (role == 3) & has
        cm, _, _ = E._isolated(geo & (sc >= thr), geo, P84.p73_10m(fid, F), geo & (y == 1))
        m = cm == comp
        r = dict(variant=v, frame=fid, component=comp)
        for c, cn in ((0, "LAND"), (1, "EVENT_FLOOD"), (2, "REFERENCE_WATER"), (255, "UNKNOWN")):
            r[f"ontology_{cn}_frac"] = round(float((st["ont"][m] == c).mean()), 3)
        for k, rn in REASON.items():
            r[f"reason_{rn}_frac"] = round(float((st["reason"][m] == k).mean()), 3)
        cand.append(r)
    pd.DataFrame(cand).to_csv(CFG.TABLES / f"p77d_{tag}_candidates.csv", index=False)
    # SEASONALLY_WET_BUT_DRY_AT_EVENT_ONSET: component audit (8-connected)
    from scipy import ndimage
    comps = []
    for fid, st in S.items():
        F = st["F"]
        wf = rasterio.open(OUT / fid / "labels.tif").read(8).astype("f4"); wf[wf < 0] = np.nan
        p73 = P84.p73_10m(fid, F)
        hz = {"B1": "ZONE_4_DAM_TO_KHERSON_FLOODWAY", "B2": "ZONE_2_KHERSON_DELTA"}[fid]
        with rasterio.open(CFG.BULK_ROOT / "floodplain" / hz / f"{hz}_hand_m.tif") as s:
            h = s.read(1).astype("f4"); h[h == s.nodata] = np.nan
            hand = np.full((F["ny"], F["nx"]), np.nan, "f4")
            reproject(h, hand, src_transform=s.transform, src_crs=s.crs, dst_transform=F["transform"],
                      dst_crs=CFG.CRS_METRIC, resampling=Resampling.nearest, src_nodata=np.nan, dst_nodata=np.nan)
        dpw = ndimage.distance_transform_edt(~(np.nan_to_num(wf) >= 20)) * 10.0
        lab, n = ndimage.label(st["seas"] == 1, structure=np.ones((3, 3), int))
        for k in range(1, n + 1):
            m = lab == k
            if m.sum() < 10:
                continue
            cls, cnt = np.unique(p73[m], return_counts=True)
            comps.append(dict(variant=v, frame=fid, component=k, area_km2=round(float(m.sum()) * PX, 4),
                              n_may_valid_dates_median=float(np.median(st["nv"][m])),
                              n_may_water_dates_median=float(np.median(st["nw"][m])),
                              may_water_fraction_median=float(np.median(st["frac"][m])) / 100,
                              p73_dominant=int(cls[np.argmax(cnt)]),
                              pre_water_frac_median=float(np.nanmedian(wf[m])) if np.isfinite(wf[m]).any() else None,
                              dist_to_pre_water_m_min=float(dpw[m].min()),
                              hand_median=float(np.nanmedian(hand[m])) if np.isfinite(hand[m]).any() else None,
                              reason="SEASONALLY_WET_BUT_DRY_AT_EVENT_ONSET"))
    pd.DataFrame(comps).to_csv(CFG.TABLES / f"p77d_{tag}_seasonal_components.csv", index=False)
    git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    man = dict(version=tag, status="CANDIDATE_NOT_FROZEN" if v == "A" else "SENSITIVITY_ONLY",
               created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), code_commit=git, rules=__doc__,
               sources_sha256=srcs, outputs={f: str(OUT / f / f"m6_labels_{tag}.tif") for f in S},
               output_sha256={f: sha(OUT / f / f"m6_labels_{tag}.tif") for f in S})
    (CFG.TABLES / f"p77d_{tag}_manifest.json").write_text(json.dumps(man, indent=1))
    print("done", tag)


if __name__ == "__main__":
    main()
