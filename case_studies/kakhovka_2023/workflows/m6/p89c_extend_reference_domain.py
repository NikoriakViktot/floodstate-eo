# New in floodstate-eo, 2026-09-24. STATUS: ACTIVE. Extends p89b pre-event water masks beyond the classifier domain.
"""P89c -- minimal spatial extension of the pre-event S1 reference masks, NO new data and NO new classifier.

Why: canonical failure cases 22 (B1) and 78 (B2) were chosen BEFORE their reference coverage was known; replacing
them would be selection bias. They sit (partly) outside the June/May S1 classifier DOMAIN, not outside the data:
the raw VV/VH fetched by p89b cover the whole cache grid window.

Rule: for every p89b scene (incl. the 06-01/06-02 gate scenes) the linear discriminant is fitted EXACTLY as in p89b /
p0r (same anchors, from the ORIGINAL domain) and then applied to every covered pixel within BUFFER_M of the original
domain. Gate: inside the original domain the extended mask must equal the p89b mask on >= 99.9 % of valid pixels
(the only allowed difference is the >= 0.05 km2 part filter at the old domain edge). Every extended pixel is flagged:
outside the anchor domain the classifier is EXTRAPOLATED, so those pixels carry reduced confidence.

Outputs: $S1_CACHE/<JUNE>_pre2023/per_scene_water_ext.npz (same layout + `extended_domain` mask),
         <case_study>/tables/p89c_extension_gate.csv
"""
from __future__ import annotations
import importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd
from rasterio.features import rasterize
from shapely.geometry import shape
from shapely.ops import unary_union
from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent
BUFFER_M = 20_000.0
GATE = 0.999


def main():
    s = importlib.util.spec_from_file_location("p89b", HERE / "p89b_fetch_pre_event_reference.py")
    B = importlib.util.module_from_spec(s); s.loader.exec_module(B)
    wdom_all = unary_union([shape(f["geometry"]) for f in
                            json.loads((B.DOM / "dnipro_water_domain_utm.geojson").read_text())["features"]])
    rows = []
    for fid in ("B1", "B2"):
        G, _ = B.grid_of(fid); z = B.geom_of(fid); shp_ = (G["ny"], G["nx"])
        inside = rasterize([(z, 1)], out_shape=shp_, transform=G["tr"], fill=0, dtype="uint8").astype(bool)
        ext = rasterize([(z.buffer(BUFFER_M), 1)], out_shape=shp_, transform=G["tr"], fill=0, dtype="uint8").astype(bool)
        wdom = wdom_all.intersection(z)
        aw = rasterize([(wdom.buffer(-200.0), 1)], out_shape=shp_, transform=G["tr"], fill=0, dtype="uint8").astype(bool)
        al = rasterize([(z.difference(wdom.buffer(6000.0)), 1)], out_shape=shp_, transform=G["tr"], fill=0,
                       dtype="uint8").astype(bool)
        cdir = CFG.S1_CACHE / f"{B.JUNE[fid]}_pre2023"
        old = np.load(cdir / "per_scene_water.npz", allow_pickle=True)
        packed = {}
        for p in sorted(cdir.glob("2023-*.npz")):
            eid = p.stem; zz = np.load(p); vv, vh, cov = zz["vv"], zz["vh"], zz["cov"]
            m_in, _ = B.water_mask(vv, vh, cov & inside, aw, al)            # p89b, byte-for-byte
            if m_in is None:
                continue
            # same fitted discriminant, applied on the extended valid area: re-run with the SAME anchors
            m_ext, _ = B.water_mask(vv, vh, cov & ext, aw, al)
            v_in, v_ext = cov & inside, cov & ext
            r = dict(frame=fid, event=eid, inside_valid_km2=round(float(v_in.sum()) * 4e-4, 1),
                     added_valid_km2=round(float((v_ext & ~inside).sum()) * 4e-4, 1),
                     interior_agreement=round(float((m_in == m_ext)[v_in].mean()), 5))
            if eid in old.files:
                ow = np.unpackbits(old[eid], count=shp_[0] * shp_[1]).reshape(shp_).astype(bool)
                r["agreement_with_p89b"] = round(float((ow == (m_in & v_in))[v_in].mean()), 5)
            rows.append(r)
            if r["interior_agreement"] < GATE:
                raise SystemExit(f"{fid} {eid}: extension changes the interior ({r['interior_agreement']}) -- stop")
            packed[eid] = np.packbits((m_ext & v_ext).ravel()); packed["valid_" + eid] = np.packbits(v_ext.ravel())
        np.savez_compressed(cdir / "per_scene_water_ext.npz", shape=np.array(shp_), cell=G["cell"], x0=G["x0"],
                            y1=G["y1"], extended_domain=np.packbits((ext & ~inside).ravel()), **packed)
        print(f"{fid}: {len(packed) // 2} scenes extended by {BUFFER_M / 1000:.0f} km; gate PASS", flush=True)
    pd.DataFrame(rows).to_csv(CFG.TABLES / "p89c_extension_gate.csv", index=False)
    print(pd.DataFrame(rows).groupby("frame")[["interior_agreement", "added_valid_km2"]].agg(["min", "median"]))


if __name__ == "__main__":
    main()
