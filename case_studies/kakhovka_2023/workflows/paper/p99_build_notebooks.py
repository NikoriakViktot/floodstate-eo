# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Builds (nbformat) and executes (nbconvert) the three paper notebooks.
"""P99 -- the executable notebooks of Paper 3, generated from code so they stay reproducible, and the filled narrative
skeleton. All three read ONLY committed tables (case_studies/kakhovka_2023/tables, runs/*/eval_d1a, runs/compare_*,
publication/tables) and show committed figures; no bulk data, no floodstate_eo import, no rasterio.

  01_physical_reconstruction_and_checks.ipynb   terrain reconstruction, uncertainty, S1 checks, disagreement ontology, ICESat-2
  02_surface_context.ipynb                       RF20 surface classes as context (agreement with WorldCover, crosswalk, QA)
  03_unet_weak_label_experiments.ipynb           labels, split, arms, paired comparisons, audit, block sensitivity

--build writes them, --execute runs them in place with the venv kernel, --fill-narrative rewrites the 26 markdown cells of
00_kakhovka_flood_state_reconstruction.ipynb with honest Status lines and links.
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]; NB = ROOT / "notebooks"
HEAD = '''from pathlib import Path
import json, numpy as np, pandas as pd, matplotlib.pyplot as plt
from IPython.display import Image, display, Markdown
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "case_studies/kakhovka_2023/tables").exists())
CS = ROOT / "case_studies/kakhovka_2023"; T = CS / "tables"; PT = CS / "publication/tables"; PF = CS / "publication/figures"; RUNS = CS / "runs"
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 40)
C = {"terrain": "#2a78d6", "s1": "#eb6834", "unet": "#4a3aa7", "rf": "#1baf7a", "gauge": "#52514e"}
def show(tid, n=None):
    df = pd.read_csv(PT / f"{tid}.csv"); cap = json.loads((PT / "manifest.json").read_text())["tables"][tid]
    display(Markdown(f"**{tid}** [{cap['evidence_level']}] {cap['caption']}")); return df.head(n) if n else df
def fig(name): p = next(PF.glob(name + "*.png"), None); display(Image(str(p), width=900)) if p else print("figure not rendered yet:", name)
print("repo:", ROOT)'''

RULES = ("**Reading rules.** Every model number is *agreement with weak reference labels*, never flood-mapping accuracy. "
         "\"Not observed is not dry.\" Areas carry their semantics (observed_S1 / mapped_UNet / terrain_reconstructed / literature_reported). "
         "Evidence levels: independent_physical › cross_sensor › weak_label_agreement › contextual.")


def nb01():
    c = []
    c.append(nbf.v4.new_markdown_cell("# 01 · Observation-constrained terrain inundation reconstruction (daily reconstructed series) and its checks\n\nPaper 3 of the Kakhovka series. This notebook reads committed tables only.\n\n" + RULES))
    c.append(nbf.v4.new_code_cell(HEAD))
    c.append(nbf.v4.new_markdown_cell("## 1. The water surface\nSWOT node heights (EGG2015-referenced, gauge-anchored with the Kherson-local closure of Paper 1) and the Kherson gauge; node-based interpolation (no chainage)."))
    c.append(nbf.v4.new_code_cell("show('T11')"))
    c.append(nbf.v4.new_code_cell("fig('Fig06'); show('T17')"))
    c.append(nbf.v4.new_markdown_cell("### Withheld gauges (never inputs): Kalynivske 80575 tests the tributary backwater, Mykolaiv 98027 the western delta; absolute and event-relative errors (T17c-T17f, FigS15)"))
    c.append(nbf.v4.new_code_cell("show('T17d'); show('T17f'); fig('FigS15')"))
    c.append(nbf.v4.new_markdown_cell("## 2. Daily reconstructed series: total water-surface area, newly inundated area, volume — PRIMARY interval = the coherent Monte-Carlo worlds of p95e rev 2 (T11b-T11d)"))
    c.append(nbf.v4.new_code_cell("d = show('T12'); d[d.region == 'DNIPRO_CORRIDOR'][['date','W_total_central_km2','W_total_p05_km2','W_total_p95_km2','A_central_km2','A_p05_km2','A_p95_km2','V_central_hm3','V_p05_hm3','V_p95_hm3','A_hand_and_ceiling_km2','A_ceiling_only_km2']]"))
    c.append(nbf.v4.new_code_cell('''u = pd.read_csv(T / "p95e_area_volume_uncertainty.csv") if (T / "p95e_area_volume_uncertainty.csv").exists() else None
dd = pd.read_csv(T / "p95_daily_area_pooled_connected_ceiling.csv"); dd["t"] = pd.to_datetime(dd.date)
fig_, axs = plt.subplots(1, 3, figsize=(13, 3.6))
for ax, r in zip(axs, ["DNIPRO_CORRIDOR", "P42_FLOODPLAIN_DOMAIN", "INHULETS_VALLEY_rect"]):
    s = dd[dd.region == r]; ax.plot(s.t, s.new_km2, color=C["terrain"], lw=2, label="central")
    if u is not None:
        uu = u[u.region == r].copy(); uu["t"] = pd.to_datetime(uu.date); uu = uu.sort_values("t"); ax.fill_between(uu.t, uu.A_p05_km2, uu.A_p95_km2, color=C["terrain"], alpha=0.2, label="MC p05-p95")
    ax.set_title(r); ax.set_ylabel("reconstructed newly inundated area, km²"); ax.tick_params(axis="x", rotation=45)
axs[0].legend(); plt.tight_layout()'''))
    c.append(nbf.v4.new_code_cell("show('T11b')"))
    c.append(nbf.v4.new_markdown_cell("### Observational support of the new area (D-SUPPORT): the full terrain-connectivity reconstruction is the primary product; its direct (<= 3 km), extrapolated (3-10 km) and weak (> 10 km) parts, the supported core and the 10 km cap sensitivity"))
    c.append(nbf.v4.new_code_cell("show('T11k'); fig('FigS14')"))
    c.append(nbf.v4.new_markdown_cell("### Computational diagnostic, not evidence (D-EMU): the 100 000-draw emulator (p95g) has no connectivity and a total built around the nominal run; no reported number rests on it"))
    c.append(nbf.v4.new_code_cell("show('T12d')"))
    c.append(nbf.v4.new_markdown_cell("### Reservoir side of the balance (T21, T22, Fig09, FigS07): daily-MEAN effective release (-dV/dt + Q_in), not an instantaneous breach discharge; hypsometry DEM vs design is the open question of Paper 4 (historical bathymetry)"))
    c.append(nbf.v4.new_code_cell("show('T21'); show('T22'); fig('Fig09'); fig('FigS07')"))
    c.append(nbf.v4.new_markdown_cell("## 3. Cross-sensor check against Sentinel-1 (per acquisition date)\nRaw POD / FAR / CSI on the S1 observation domain are primary; the conditional POD outside the normally-wet class is a diagnostic conditional agreement (a-priori class), never a corrected POD."))
    c.append(nbf.v4.new_code_cell("v = show('T13'); v[(v.variant == 'connected_ceiling') & v.date.isin(['2023-06-09','2023-06-13','2023-06-14','2023-06-18','2023-06-21'])][['date','region','s1_new_km2','hand_new_km2','hit_km2','miss_km2','miss_on_normally_wet_km2','hand_only_km2','POD','FAR','CSI','POD_cond_outside_normally_wet']]"))
    c.append(nbf.v4.new_code_cell("fig('Fig04')"))
    c.append(nbf.v4.new_markdown_cell("## 4. Disagreement ontology (A both / B terrain-only / C S1-only)\nB decomposed by land cover (SAR blind spots); C by ground elevation relative to the surface (submergence of normally-wet reeds vs S1-only detections topographically unsupported by the reconstructed water surface)."))
    c.append(nbf.v4.new_code_cell("o = show('T14'); o[o.date == '2023-06-09']"))
    c.append(nbf.v4.new_code_cell("fig('Fig05')"))
    c.append(nbf.v4.new_markdown_cell("## 5. ICESat-2 altimetric consistency check\nA track-based consistency check of the DEM and the water surface, not a validation of the inundation map. The independent units are the passes (acquisition days), far fewer than the segments. The class bias is calibrated on the same night corpus, so T15b repeats the corrected residual with the bias re-estimated without the checked passes (one pass out, five folds of passes, the two epochs either side of the breach); T15c shows how stable each class bias is."))
    c.append(nbf.v4.new_code_cell("show('T15'); show('T15b'); show('T15c'); fig('Fig08')"))
    c.append(nbf.v4.new_markdown_cell("## 6. Area accounting with semantics and the per-date series"))
    c.append(nbf.v4.new_code_cell("show('T16')"))
    c.append(nbf.v4.new_code_cell("show('T19', 30); fig('FigS03')"))
    c.append(nbf.v4.new_markdown_cell("## 7. Sensitivities\nRules, closure (superseded p59 chain) and the DEM accuracy that feeds the error model (Paper 2)."))
    c.append(nbf.v4.new_code_cell("fig('FigS02'); show('T18')"))
    return c


def nb02():
    c = [nbf.v4.new_markdown_cell("# 02 · Surface context: the RF20 PRE-event surface classification\n\nContext layer of Paper 3: evaluation strata for the U-Net arms and the classes of the disagreement ontology. Reference = ESA WorldCover 2021, the training reference — these are *agreement* numbers, not validation.\n\n" + RULES),
         nbf.v4.new_code_cell(HEAD), nbf.v4.new_markdown_cell("## 1. Per-class agreement (spatial-block 5-fold CV and frame transfers)"), nbf.v4.new_code_cell("show('T09')"),
         nbf.v4.new_code_cell("fig('FigS04')"), nbf.v4.new_markdown_cell("## 2. Confusion matrix and class areas"), nbf.v4.new_code_cell("show('T10'); show('T10b')"),
         nbf.v4.new_markdown_cell("## 3. Wall-to-wall agreement with WorldCover (crosswalk, not validation)"), nbf.v4.new_code_cell("show('T10c')"),
         nbf.v4.new_markdown_cell("## 4. QA verdict and known limitations (p73 freeze)\nRev 2 (review F08: global blocks, the B1/B2 overlap owned by B2 before sampling, buffered CV) is the product in use once built; rev 1 is the superseded model."),
         nbf.v4.new_code_cell("QA = T / ('p73_rf20_rev2_qa' if (T / 'p73_rf20_rev2_qa').exists() else 'p73_rf20_qa'); print(QA.name)\n"
                              "v = QA / 'QA_VERDICT.md'; print(v.read_text()[:6000] if v.exists() else 'no verdict file in ' + QA.name)"),
         nbf.v4.new_code_cell("for p in sorted(QA.glob('Z*.png'))[:3]: display(Image(str(p), width=800))")]
    return c


def nb03():
    c = [nbf.v4.new_markdown_cell("# 03 · What EO inputs recover under weak labels: the U-Net arm experiments\n\nControlled experiments on flood-state representation under weak, sensor-dependent supervision. U2b (+W_pre) is a diagnostic upper bound: W_pre is also a label ingredient.\n\n" + RULES),
         nbf.v4.new_code_cell(HEAD), nbf.v4.new_markdown_cell("## 1. Labels v002 and v003_A (frozen)"), nbf.v4.new_code_cell("show('T02'); show('T02b')"),
         nbf.v4.new_markdown_cell("## 2. The frozen spatial-block split and its rationale"), nbf.v4.new_code_cell("show('T03'); show('T03b')"),
         nbf.v4.new_markdown_cell("## 3. Arms"), nbf.v4.new_code_cell("show('T04')"), nbf.v4.new_code_cell("fig('FigS01')"),
         nbf.v4.new_markdown_cell("## 4. D1 endpoints with spatial-block bootstrap intervals"),
         nbf.v4.new_code_cell("e = show('T05'); e[e.endpoint.isin(['G_F1','G_IoU','G_PR_AUC','A_FP_area_dry_cropland_km2','A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2','B_recall_flooded_open_low_veg','W_IoU','BU_FP_area_km2'])].pivot_table(index=['arm','labels'], columns='endpoint', values='value')"),
         nbf.v4.new_markdown_cell("## 5. Paired comparisons (identical blocks)"), nbf.v4.new_code_cell("p = show('T06'); p[p.endpoint.isin(['A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2','B_recall_flooded_open_low_veg','G_F1','BU_FP_area_km2'])]"),
         nbf.v4.new_code_cell("show('T07b')"), nbf.v4.new_code_cell("fig('Fig03')"),
         nbf.v4.new_markdown_cell("## 6. Cropland-associated SAR candidates (audit)\nWording rule: none of the audited candidates showed positive evidence consistent with breach-induced inundation under the available SAR, optical and terrain constraints."),
         nbf.v4.new_code_cell("show('T08'); show('T08b')"), nbf.v4.new_markdown_cell("## 7. Block-size sensitivity"), nbf.v4.new_code_cell("show('T20'); fig('FigS05')")]
    return c


NARRATIVE = [
    ("Scientific question", "Can the daily inundation after the Kakhovka dam breach be reconstructed from the observed water-surface geometry constrained on the terrain (an observation-constrained terrain reconstruction, not a hydrodynamic model), checked against independent observations, and what do EO-based flood products recover of it under weak labels? See `publication/claims.md` (C01–C14) and `publication/TERMINOLOGY.md`.", "framed 2026-09-25; the evidence hierarchy is observation-constrained terrain reconstruction → cross-sensor checks → surface context → ML under weak labels"),
    ("Study area", "Lower Dnipro from the Kakhovka dam to the Dnipro–Buh liman: frames B1 (dam → Kherson) and B2 (Kherson delta) on one 10 m lattice; the Inhulets valley is reported separately (Fig01).", "implemented"),
    ("Dam-breach context", "Breach on 2023-06-06; Kherson stage 0.5 → 5.78 m on 06-08 (peak stage), back to the pre-breach regime by ~22 June (Fig06b, T17b); the reconstructed areal maximum falls on 06-07, between the S1 acquisitions — peak stage and peak area are different quantities. Water-surface geometry and the vertical frame are Paper 1.", "implemented (Paper 1)"),
    ("Why binary water mapping is insufficient", "On 2023-06-09 the terrain reconstruction and the S1 dark-water rule disagree on ~200 km²: forest, reeds and buildings hide water from SAR, reed beds below the normal surface show a depth signal, and dark fields far above the surface are S1-only detections topographically unsupported by the reconstructed water surface (T14, Fig05, Fig08).", "measured, not modelled"),
    ("Frames B1/B2/B3", "B1 and B2 built; B3 (delta with the liman) is NOT built. The estuary S1 series exists on its own grid (T19).", "partial: B3 missing"),
    ("Input datasets", "T01 lists every dataset with its role and evidence level; manifests under `manifests/`.", "implemented"),
    ("PRE surface context", "RF20 PRE-only Sentinel-2 classification (p73, frozen) is the context product (notebook 02, T09/T10); BASE_CLASS is historical.", "implemented, frozen"),
    ("Sentinel-1", "Orbit-matched dB change channels (p71) feed the U-Net; per-scene dark-water masks give the per-date observations (T19) and the labels.", "implemented"),
    ("Sentinel-2", "Per-date index stacks and PRE/EVENT/TRACE composites exist; S2 adds almost nothing to the event series (cloud, open-water rule) — T19.", "implemented"),
    ("PRE/EVENT/TRACE", "Composites frozen (p54); used by p73 (PRE only) and p72 (event support, rebuilt after the scaling fix).", "implemented"),
    ("Observation coverage", "Coverage is reported per date relative to the S1 observable domain; orbit-138 dates cover 62 %. Not observed is not dry (T19, T01).", "implemented"),
    ("Spectral indices", "Seven indices per date (p54a); the water rule is NDWI > 0 ∧ MNDWI > 0.", "implemented"),
    ("Surface-state classification", "RF20 replaces BASE_CLASS as the strata product: per-class F1 vs WorldCover (agreement), transfers B1↔B2 (T09).", "implemented, frozen"),
    ("Flood-state classification", "Ontology LAND / EVENT_FLOOD / REFERENCE_WATER / UNKNOWN (labels v003_A, frozen D3) trained as U-Net arms; a canonical multi-class FLOOD_STATE product still does not exist.", "implemented as experiments; product not canonical"),
    ("S1/S2 evidence", "S1 per date vs terrain (T13); S2 reliable dates only (T19).", "implemented"),
    ("Urban flood", "Built-up appears as a terrain-only category (SAR blind spot, T14) and as the BU false-positive endpoint of the arms (T05); no dedicated urban product.", "measured as endpoints"),
    ("Flooded vegetation", "Reed beds: S1 dark-water onset where the ground is below the normal surface is a submergence (depth) signal, not inundation onset (T14, C category, normally-wet flag).", "measured, not modelled"),
    ("Wet sand / bare soil", "S1 new water ≥ 5 m above the surface (54 km² on 06-09) is topographically inconsistent with the reconstructed connected water surface; along the ICESat-2 tracks that sample it the DEM agrees with the altimetry within a few decimetres, so the available ICESat-2 observations give no evidence for a DEM bias large enough to explain it (T15, Fig08). Supports, does not prove; alternatives (radar shadow, smooth surfaces, local ponding, timing) not individually tested.", "evidence in tables"),
    ("M0–M5", "Not defined. The arm ladder U0d → U0z → U1 → U2 → U2b on v002 / v003_A is the experiment matrix (T04–T07).", "not defined"),
    ("Spatial CV", "Frozen 10 km spatial-block split with 640 m buffers and paired block bootstrap; block-size sensitivity 7.5 / 15 / 20 km (T03, T20).", "implemented"),
    ("Leave-one-zone-out", "For RF20 the frame transfers B1→B2 and B2→B1 (T09); the legacy p51 LOZO is not migrated.", "implemented for RF20"),
    ("Uncertainty", "Terrain: PRIMARY interval = the coherent Monte-Carlo worlds of p95e rev 2 (T11b, T11c convergence, T11d ablation, T12); the 100 000-draw emulator is a computational diagnostic outside the evidence path (T12d); the support of the new area is classified in T11k (supported core <= 10 km); volumes always carry p05–p95. Arms: block-bootstrap intervals. No per-cell uncertainty product.", "partial"),
    ("Final products and maps", "Fig03 (U-Net), Fig04 (dynamics), Fig05 (disagreement), Fig07 (peak-day depth and duration); rasters under $BULK_ROOT/floodplain_dyn are not redistributed (FABDEM licence).", "figures committed"),
    ("Limitations", "Planar water surface per node neighbourhood, no timing; residual terrain error under reeds, forest and buildings (FABDEM DTM, T18b); bed cells without a stochastic terrain term; SWOT nodes on channels only; no scene at the peak; weak labels; W_pre circularity; B3 missing; no probability-sample reference for areas.", "stated"),
    ("Conclusions", "See `publication/claims.md` — the claims register is the source of every statement. Next step (separate paper, Paper 4): the reservoir bowl reconstructed on the historical bathymetry, resolving the DEM-vs-design hypsometry gap; Paper 5: HEC-RAS calibrated on these daily surfaces.", "draft")]


def fill_narrative():
    p = NB / "00_kakhovka_flood_state_reconstruction.ipynb"; nb = nbf.read(p, as_version=4)
    md = [c for c in nb.cells if c.cell_type == "markdown"]
    assert len(md) >= 26, len(md)
    md[0].source = ("# Kakhovka 2023 — flood-state reconstruction: narrative index\n\nUpdated 2026-09-25. Each section links to the executable notebooks "
                    "(01 observation-constrained terrain reconstruction and checks, 02 surface context, 03 U-Net weak-label experiments), to publication tables (T01–T22) and figures (Fig01–Fig09, FigS01–S07). "
                    + RULES)
    for cell, (title, text, status) in zip(md[1:26], NARRATIVE):
        cell.source = f"## {title}\n\n{text}\n\n**Status: {status}.**"
    nbf.write(nb, p); print("narrative filled:", p.name)


def build(only=None):
    for name, make in (("01_physical_reconstruction_and_checks", nb01), ("02_surface_context", nb02), ("03_unet_weak_label_experiments", nb03)):
        if only and name[:2] not in only:
            continue
        cells = make()
        nb = nbf.v4.new_notebook(); nb.cells = cells; nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
        nbf.write(nb, NB / f"{name}.ipynb"); print("built", name)


def execute(only=None):
    for name in ("01_physical_reconstruction_and_checks", "02_surface_context", "03_unet_weak_label_experiments"):
        if only and name[:2] not in only:
            continue
        cmd = [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", "--ExecutePreprocessor.timeout=600", str(NB / f"{name}.ipynb")]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT)); print(name, "exit", r.returncode); print(r.stderr[-800:] if r.returncode else "")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--build", action="store_true"); ap.add_argument("--execute", action="store_true"); ap.add_argument("--fill-narrative", action="store_true")
    ap.add_argument("--only", nargs="*", help="notebook numbers to build/execute, e.g. --only 01"); a = ap.parse_args()
    if a.build:
        build(a.only)
    if a.fill_narrative:
        fill_narrative()
    if a.execute:
        execute(a.only)
