# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Fills n / value / uncertainty of the claims register from the tables.
"""fill_evidence -- writes the numeric fields of publication/evidence_matrix.csv from publication tables (same placeholder
syntax as fill_manuscript), then sets validation_status = TABLES_LINKED. Statements are never rewritten here."""
from __future__ import annotations
import re
from pathlib import Path
import pandas as pd
from fill_manuscript import PAT, resolve

PUB = Path(__file__).resolve().parents[2] / "publication"
FILL = {
    "C01": dict(n="{{T12|region=DNIPRO_CORRIDOR|date|count|}} key dates x 40 draws",
                value="peak {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_central_km2||.0f}} km2 on 2023-06-07 (DEM-uncorrected sensitivity {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_connected_ceiling_dem_uncorrected_km2||.0f}}); 06-13 {{T12|region=DNIPRO_CORRIDOR,date=2023-06-13|A_central_km2||.0f}}; 06-21 {{T12|region=DNIPRO_CORRIDOR,date=2023-06-21|A_central_km2||.0f}}; peak volume {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_central_hm3||.0f}} hm3; TOTAL water surface 06-07 {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|W_total_central_km2||.0f}} km2 (normal regime 06-05 {{T12|region=DNIPRO_CORRIDOR,date=2023-06-05|W_total_central_km2||.0f}} km2)",
                uncertainty="MC p05-p95 {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_p05_km2||.0f}}-{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_p95_km2||.0f}} km2; volume {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_p05_hm3||.0f}}-{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|V_p95_hm3||.0f}} hm3; HAND lower bound {{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|A_hand_and_ceiling_km2||.0f}} km2"),
    "C02": dict(n="11 S1 dates (p42 floodplain footprint)",
                value="06-09: POD {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|POD||.2f}}, FAR {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|FAR||.2f}}, CSI {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|CSI||.2f}}; 06-13: POD {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-13|POD||.2f}}",
                uncertainty="POD excluding normally-wet cells (sensitivity) 06-09 {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|POD_excl_normally_wet||.2f}}; misses on normally-wet {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|miss_on_normally_wet_km2||.0f}} of {{T13|variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN,date=2023-06-09|miss_km2||.0f}} km2"),
    "C03": dict(n="2 zones, 06-09 (also 06-13, 06-14)",
                value="A {{T14|date=2023-06-09,category=A|km2|sum|.0f}} km2; B {{T14|date=2023-06-09,category=B|km2|sum|.0f}} km2 (trees {{T14|date=2023-06-09,category=B|km2_wc_trees|sum|.0f}}, wetland {{T14|date=2023-06-09,category=B|km2_wc_wetland|sum|.0f}}, built {{T14|date=2023-06-09,category=B|km2_wc_built|sum|.0f}}); C {{T14|date=2023-06-09,category=C|km2|sum|.0f}} km2 (normally wet {{T14|date=2023-06-09,category=C|km2_normally_wet|sum|.0f}}; >= 5 m above {{T14|date=2023-06-09,category=C|km2_ground_ge5m_above|sum|.0f}})",
                uncertainty="mapped areas; class maps carry their own error"),
    "C04": dict(n="{{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|N||.0f}} + {{T15|zone=ZONE_4_DAM_TO_KHERSON_FLOODWAY,category=S1_only_ground_ge2m_above|N||.0f}} night segments",
                value="DEM - ICESat-2 median {{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|res_median||+.2f}} m (delta), {{T15|zone=ZONE_4_DAM_TO_KHERSON_FLOODWAY,category=S1_only_ground_ge2m_above|res_median||+.2f}} m (floodway); ground - surface {{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|ice_minus_wse_median||+.1f}} m; share below surface {{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|share_ice_below_wse||.1%}}",
                uncertainty="p10-p90 {{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|res_p10||+.2f}} to {{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|res_p90||+.2f}} m"),
    "C05": dict(n="{{T17|period=all days|n_days||.0f}} days; DEM: {{T18|set=C seamless DEM (p55) -- ALL night points (land below dam + exposed bed)|N||.0f}} segments (Paper 2)",
                value="gauge - SWOT median {{T17|period=all days|median_m||+.2f}} m, NMAD {{T17|period=all days|NMAD_m||.2f}} m, RMSE {{T17|period=all days|RMSE_m||.2f}} m; DEM RMSE {{T18|set=C seamless DEM (p55) -- ALL night points (land below dam + exposed bed)|RMSE||.2f}} m, NMAD {{T18|set=C seamless DEM (p55) -- ALL night points (land below dam + exposed bed)|NMAD||.2f}} m",
                uncertainty="rise and peak: median {{T17|period=rise and peak 06-06..06-14|median_m||+.2f}} m over {{T17|period=rise and peak 06-06..06-14|n_days||.0f}} days"),
    "C06": dict(n="corridor accounting rows of T16", value="06-09 S1 new dark water {{T16|quantity=S1 new dark water, 06-09 scene;region=DNIPRO_CORRIDOR|km2||.0f}} km2 (observed_S1); label recipe {{T16|quantity=S1 new dark water, >= 2 of 3 peak dates (label recipe);region=DNIPRO_CORRIDOR|km2||.0f}} km2; U2b {{T16|quantity=U2b predicted event flood (persistent concept);region=DNIPRO_CORRIDOR|km2||.0f}} km2 (mapped_UNet); terrain 06-09 {{T12|region=DNIPRO_CORRIDOR,date=2023-06-09|A_central_km2||.0f}} km2",
                uncertainty="literature rows VERIFY; different AOI/date/reference water"),
    "C07": dict(n="11 S1 dates (Inhulets rectangle)", value="06-09: terrain {{T13|variant=connected_ceiling,region=INHULETS_VALLEY_rect,date=2023-06-09|hand_new_km2||.0f}} km2 vs S1 {{T13|variant=connected_ceiling,region=INHULETS_VALLEY_rect,date=2023-06-09|s1_new_km2||.0f}} km2; POD {{T13|variant=connected_ceiling,region=INHULETS_VALLEY_rect,date=2023-06-09|POD||.2f}}, CSI {{T13|variant=connected_ceiling,region=INHULETS_VALLEY_rect,date=2023-06-09|CSI||.2f}}",
                uncertainty="backwater assumption; earlier 0.78-0.98 figures withdrawn"),
    "C08": dict(n="TEST blocks, paired bootstrap 2000", value="flood on REFERENCE_WATER {{T07|run=U2_B1B2_v1,endpoint=R_pred_on_reference_water_km2|value||.1f}} -> {{T07|run=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|value||.1f}} km2; paired {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|median||.1f}} km2; EVENT_FLOOD recall diff {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=E_recall_event_flood|median||+.3f}}",
                uncertainty="95 % [{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|lo||.1f}}, {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|hi||.1f}}]; recall [{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=E_recall_event_flood|lo||+.3f}}, {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=E_recall_event_flood|hi||+.3f}}]"),
    "C09": dict(n="TEST blocks, paired bootstrap 2000", value="U2 -> U2b flood on REFERENCE_WATER {{T07b|A=U2_B1B2_v003A,B=U2b_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|median||.2f}} km2",
                uncertainty="95 % [{{T07b|A=U2_B1B2_v003A,B=U2b_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|lo||.2f}}, {{T07b|A=U2_B1B2_v003A,B=U2b_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|hi||.2f}}]; not independent"),
    "C10": dict(n="TEST blocks; 19.2 km2 audited candidates", value="U0d -> U2 unlabelled-cropland burden {{T06|comparison=U2 - U0d,labels=v002,endpoint=A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2|median||.1f}} km2; BU FP {{T06|comparison=U2 - U0d,labels=v002,endpoint=BU_FP_area_km2|median||+.2f}} km2; U1 retention A {{T08b|group=A|retention_U1||.2f}}, B {{T08b|group=B|retention_U1||.2f}}, D {{T08b|group=D|retention_U1||.2f}}",
                uncertainty="95 % [{{T06|comparison=U2 - U0d,labels=v002,endpoint=A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2|ci_lo||.1f}}, {{T06|comparison=U2 - U0d,labels=v002,endpoint=A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2|ci_hi||.1f}}]"),
    "C11": dict(n="{{T09|evaluation=spatial_block_cv_5fold,cls=MACRO_MEAN|n||.0f}} CV samples", value="OA {{T09|evaluation=spatial_block_cv_5fold,cls=MACRO_MEAN|OA_spatial_cv||.3f}}, macro F1 {{T09|evaluation=spatial_block_cv_5fold,cls=MACRO_MEAN|F1||.3f}}; transfer B1->B2 macro F1 {{T09|evaluation=transfer_B1_to_B2,cls=MACRO_MEAN|F1||.3f}}, B2->B1 {{T09|evaluation=transfer_B2_to_B1,cls=MACRO_MEAN|F1||.3f}}",
                uncertainty="agreement with WorldCover (training reference), not validation"),
    "C12": dict(n="4 splits (7.5, 10, 15, 20 km); 5 km infeasible", value="U2 v003_A global F1: 10 km {{T20|split=m6_split_v1|G_F1||.3f}}, 7.5 km {{T20|split=m6_split_s7p5|G_F1||.3f}}, 15 km {{T20|split=m6_split_s15|G_F1||.3f}}, 20 km {{T20|split=m6_split_s20|G_F1||.3f}}",
                uncertainty="each split has its own TEST geography; intervals in T20"),
}


def main():
    M = pd.read_csv(PUB / "evidence_matrix.csv").fillna("")
    for cid, f in FILL.items():
        for k, v in f.items():
            M.loc[M.claim_id == cid, k] = PAT.sub(resolve, v)
        M.loc[M.claim_id == cid, "validation_status"] = "TABLES_LINKED"
    M.to_csv(PUB / "evidence_matrix.csv", index=False)
    miss = [(cid, k) for cid in FILL for k in ("n", "value", "uncertainty") if "[[MISSING" in str(M.loc[M.claim_id == cid, k].iloc[0])]
    print("evidence matrix filled;", "unresolved:", miss if miss else "none")


if __name__ == "__main__":
    main()
