# New in floodstate-eo, 2026-09-24. STATUS: ACTIVE_DIAGNOSTIC. Per-candidate pre-event S1 history (May recurrence, W_pre 06-01/02, extrapolation flag) on p89c masks.
import importlib.util, json, numpy as np, pandas as pd, rasterio
from pathlib import Path
from rasterio.transform import from_origin
from rasterio.warp import reproject
from rasterio.enums import Resampling
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.spatial import canonical_grid as CG
W=Path("case_studies/kakhovka_2023/workflows/m6")
def L(n):
    s=importlib.util.spec_from_file_location(n,W/f"{n}.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
E,P84=L("m6_eval"),L("p84_m6_split_b1b2")
J={"B1":"ZONE_4_FLOODWAY_june2023_s32","B2":"ZONE_2_KHERSON_DELTA_flood_june2023"}
OUT=CFG.BULK_ROOT/"frames10"; rows=[]
for f in ("B1","B2"):
    F=CG.frame_grid(f); p73=P84.p73_10m(f,F)
    role=rasterio.open(OUT/f/"m6_split_v1_role.tif").read(1)
    s=rasterio.open(OUT/f/"s1_change.tif"); d=list(s.descriptions); has=(s.read(d.index("n_valid_event")+1)>0)&(s.read(1)!=-32768)
    y=rasterio.open(OUT/f/"m6_labels_v002.tif").read(1); y=np.where(np.isin(role,(1,2,3))&has,y,255)
    q=rasterio.open(OUT/f/"m6"/"U0d_score.tif").read(1); sc=np.where(q==65535,-1,q/1e4)
    thr=json.loads(Path("case_studies/kakhovka_2023/runs/U0d_B1B2_v1/validation_threshold.json").read_text())["threshold"]
    geo=(role==3)&has; comp,sel,_=E._isolated(geo&(sc>=thr),geo,p73,geo&(y==1))
    z=np.load(CFG.S1_CACHE/(J[f]+"_pre2023")/"per_scene_water_ext.npz",allow_pickle=True); shp=tuple(int(v) for v in z["shape"])
    tr=from_origin(float(z["x0"]),float(z["y1"]),20,20); ev=sorted(k for k in z.keys() if k.startswith("2023-0"))
    Wm,Vm=[],[]
    for k in ev:
        for arr,lst in ((z[k],Wm),(z["valid_"+k],Vm)):
            a=np.unpackbits(arr,count=shp[0]*shp[1]).reshape(shp).astype("u1"); dd=np.zeros((F["ny"],F["nx"]),"u1")
            reproject(a,dd,src_transform=tr,src_crs="EPSG:32636",dst_transform=F["transform"],dst_crs="EPSG:32636",resampling=Resampling.nearest); lst.append(dd.astype(bool))
    Wm,Vm=np.stack(Wm),np.stack(Vm)
    may=np.array([k[:7]=="2023-05" or k[:7]=="2023-04" for k in ev]); jun=~may
    nval=Vm[may].sum(0); nwat=(Wm[may]&Vm[may]).sum(0); jval=Vm[jun].sum(0); jwat=(Wm[jun]&Vm[jun]).sum(0)
    extd=np.zeros((F["ny"],F["nx"]),"u1"); reproject(np.unpackbits(z["extended_domain"],count=shp[0]*shp[1]).reshape(shp).astype("u1"),extd,src_transform=tr,src_crs="EPSG:32636",dst_transform=F["transform"],dst_crs="EPSG:32636",resampling=Resampling.nearest)
    A=pd.read_csv("case_studies/kakhovka_2023/tables/p89_candidates_U0d.csv"); A=A[A.frame==f].set_index("component")
    for k in np.flatnonzero(sel):
        m=comp==k; area=m.sum()*1e-4
        obs=(nval[m]>=2)
        rw=(nval[m]>=2)&(nwat[m]>=2)
        rows.append(dict(frame=f,component=int(k),group=A.loc[k,"group"],area_km2=round(area,4),
            frac_px_may_observed_ge2=round(float(obs.mean()),3),n_may_valid_median=float(np.median(nval[m])),
            n_may_water_median=float(np.median(nwat[m])),may_water_fraction=round(float(nwat[m].sum()/max(nval[m].sum(),1)),3),
            recurrent_pre_event_water_frac=round(float(rw.mean()),3),
            w_pre_0601_0602_observed_frac=round(float((jval[m]>=1).mean()),3), w_pre_water_frac=round(float(jwat[m].sum()/max(jval[m].sum(),1)),3),
            extrapolated_domain_frac=round(float(extd[m].astype(bool).mean()),3)))
D=pd.DataFrame(rows)
D["pre_event_reference"]=np.where(D.frac_px_may_observed_ge2<0.5,"UNOBSERVED",np.where(D.recurrent_pre_event_water_frac>=0.5,"RECURRENT_PRE_EVENT_WATER","NO_RECURRENT_WATER"))
D.to_csv("case_studies/kakhovka_2023/tables/p89b_candidate_may_history.csv",index=False)
print(D.groupby(["frame","group","pre_event_reference"]).agg(n=("area_km2","size"),km2=("area_km2","sum"),w_pre=("w_pre_water_frac","median"),extrap=("extrapolated_domain_frac","median")).round(2).to_string())
print(D[((D.frame=="B1")&(D.component==22))|((D.frame=="B2")&(D.component==78))].to_string(index=False))
