# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Fills n / value / uncertainty of the claims register from the tables.
"""fill_evidence -- writes the numeric fields of publication/evidence_matrix.csv from publication tables (same placeholder
syntax as fill_manuscript), then sets validation_status = TABLES_LINKED. Statements are never rewritten here."""
from __future__ import annotations
import re
from pathlib import Path
import pandas as pd
from fill_manuscript import PAT, resolve

PUB = Path(__file__).resolve().parents[2] / "publication"
C = "region=DNIPRO_CORRIDOR"; P = "variant=connected_ceiling,region=P42_FLOODPLAIN_DOMAIN"; I = "variant=connected_ceiling,region=INHULETS_VALLEY_rect"


def t12(d, c, f=".0f"):
    return "{{T12|%s,date=%s|%s||%s}}" % (C, d, c, f)


FILL = {
    "C01": dict(n="{{T12|region=DNIPRO_CORRIDOR|date|count|}} key dates of the reconstructed series; 11 S1 dates",
                value="A_new 06-06 %s, 06-07 %s (maximum), 06-08 %s, 06-09 %s km2; Kherson stage 06-07 %s m, 06-08 %s m (gauge maximum)" % (t12("2023-06-06","A_p50_km2"), t12("2023-06-07","A_p50_km2"), t12("2023-06-08","A_p50_km2"), t12("2023-06-09","A_p50_km2"), t12("2023-06-07","kherson_gauge_m",".2f"), t12("2023-06-08","kherson_gauge_m",".2f")),
                uncertainty="spatial MC p05-p95 on 06-07 %s-%s km2; the day of the maximum is not itself bootstrapped" % (t12("2023-06-07","A_p05_km2"), t12("2023-06-07","A_p95_km2"))),
    "C02": dict(n="%s key dates x 40 spatial draws (primary); 100 000 emulator draws (sensitivity)" % "{{T12|region=DNIPRO_CORRIDOR|date|count|}}",
                value="W_total 06-05 %s (observed regime) -> 06-07 MC median %s km2; A_new 06-07 MC median %s km2 (DEM as delivered, nominal run: %s); V_new 06-07 MC median %s hm3; nominal runs %s km2 / %s km2 / %s hm3" % (t12("2023-06-05","W_total_central_km2"), t12("2023-06-07","W_total_p50_km2"), t12("2023-06-07","A_p50_km2"), t12("2023-06-07","A_connected_ceiling_dem_uncorrected_km2"), t12("2023-06-07","V_p50_hm3"), t12("2023-06-07","W_total_central_km2"), t12("2023-06-07","A_central_km2"), t12("2023-06-07","V_central_hm3")),
                uncertainty="PRIMARY spatial MC p05-p95: W_total %s-%s km2, A_new %s-%s km2, V_new %s-%s hm3; emulator envelope (sensitivity): W_total %s-%s, A_new %s-%s km2" % (t12("2023-06-07","W_total_p05_km2"), t12("2023-06-07","W_total_p95_km2"), t12("2023-06-07","A_p05_km2"), t12("2023-06-07","A_p95_km2"), t12("2023-06-07","V_p05_hm3"), t12("2023-06-07","V_p95_hm3"), t12("2023-06-07","W_total_emu_km2_p05"), t12("2023-06-07","W_total_emu_km2_p95"), t12("2023-06-07","A_emu_km2_p05"), t12("2023-06-07","A_emu_km2_p95"))),
    "C03": dict(n="{{T12|region=DNIPRO_CORRIDOR|date|count|}} key dates x 2 regions",
                value="corridor A_new 06-09 %s, 06-13 %s, 06-18 %s, 06-21 %s km2 (stage %s m); Inhulets A_new maximum %s km2 on 06-09, W_total %s km2" % (t12("2023-06-09","A_p50_km2"), t12("2023-06-13","A_p50_km2"), t12("2023-06-18","A_p50_km2"), t12("2023-06-21","A_p50_km2"), t12("2023-06-21","kherson_gauge_m",".2f"), "{{T12|region=INHULETS_VALLEY_rect,date=2023-06-09|A_p50_km2||.0f}}", "{{T12|region=INHULETS_VALLEY_rect,date=2023-06-09|W_total_p50_km2||.0f}}"),
                uncertainty="corridor spatial MC 06-13 %s-%s km2; Inhulets 06-09: terrain %s vs S1 %s km2, POD {{T13|%s,date=2023-06-09|POD||.2f}}, CSI {{T13|%s,date=2023-06-09|CSI||.2f}}" % (t12("2023-06-13","A_p05_km2"), t12("2023-06-13","A_p95_km2"), "{{T13|%s,date=2023-06-09|hand_new_km2||.0f}}" % I, "{{T13|%s,date=2023-06-09|s1_new_km2||.0f}}" % I, I, I)),
    "C04": dict(n="11 S1 dates (p42 floodplain footprint)",
                value="06-09: POD {{T13|%s,date=2023-06-09|POD||.2f}}, FAR {{T13|%s,date=2023-06-09|FAR||.2f}}, CSI {{T13|%s,date=2023-06-09|CSI||.2f}}; 06-13: POD {{T13|%s,date=2023-06-13|POD||.2f}}; misses on normally-wet cells {{T13|%s,date=2023-06-09|miss_on_normally_wet_km2||.0f}} of {{T13|%s,date=2023-06-09|miss_km2||.0f}} km2" % (P,P,P,P,P,P),
                uncertainty="conditional POD outside the normally-wet class (diagnostic) 06-09 {{T13|%s,date=2023-06-09|POD_cond_outside_normally_wet||.2f}}, 06-13 {{T13|%s,date=2023-06-13|POD_cond_outside_normally_wet||.2f}}" % (P,P)),
    "C05": dict(n="2 zones, 06-09 (also 06-13, 06-14)",
                value="A {{T14|date=2023-06-09,category=A|km2|sum|.0f}} km2; B {{T14|date=2023-06-09,category=B|km2|sum|.0f}} km2 (trees {{T14|date=2023-06-09,category=B|km2_wc_trees|sum|.0f}}, wetland {{T14|date=2023-06-09,category=B|km2_wc_wetland|sum|.0f}}, built {{T14|date=2023-06-09,category=B|km2_wc_built|sum|.0f}}); C {{T14|date=2023-06-09,category=C|km2|sum|.0f}} km2 (normally wet {{T14|date=2023-06-09,category=C|km2_normally_wet|sum|.0f}}; >= 5 m above the surface {{T14|date=2023-06-09,category=C|km2_ground_ge5m_above|sum|.0f}})",
                uncertainty="mapped areas; class maps carry their own error"),
    "C06": dict(n="ICESat-2: {{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|N||.0f}} + {{T15|zone=ZONE_4_DAM_TO_KHERSON_FLOODWAY,category=S1_only_ground_ge2m_above|N||.0f}} night segments on the S1-only >= 2 m cells (tracks and dates in T15); SWOT vs gauge {{T17|period=all days|n_days||.0f}} days",
                value="DEM - ICESat-2 median {{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|res_median||+.2f}} m (delta), {{T15|zone=ZONE_4_DAM_TO_KHERSON_FLOODWAY,category=S1_only_ground_ge2m_above|res_median||+.2f}} m (floodway); ground - surface {{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|ice_minus_wse_median||+.1f}} m; share below surface {{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|share_ice_below_wse||.1%}}; gauge - SWOT median {{T17|period=all days|median_m||+.2f}} m, NMAD {{T17|period=all days|NMAD_m||.2f}} m",
                uncertainty="DEM - ICESat-2 p10-p90 {{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|res_p10||+.2f}} to {{T15|zone=ZONE_2_KHERSON_DELTA,category=S1_only_ground_ge2m_above|res_p90||+.2f}} m; DEM class NMAD {{T18|set=C seamless DEM (p55) -- ALL night points (land below dam + exposed bed)|NMAD||.2f}} m over {{T18|set=C seamless DEM (p55) -- ALL night points (land below dam + exposed bed)|N||.0f}} segments (Paper 2); supports, does not prove"),
    "C07": dict(n="40 spatial draws x {{T12|region=DNIPRO_CORRIDOR|date|count|}} key dates",
                value="06-07: A_new MC median %s km2 [p05-p95 %s-%s] (nominal run %s); V_new MC median %s hm3 [p05-p95 %s-%s] (nominal run %s)" % (t12("2023-06-07","A_p50_km2"), t12("2023-06-07","A_p05_km2"), t12("2023-06-07","A_p95_km2"), t12("2023-06-07","A_central_km2"), t12("2023-06-07","V_p50_hm3"), t12("2023-06-07","V_p05_hm3"), t12("2023-06-07","V_p95_hm3"), t12("2023-06-07","V_central_hm3")),
                uncertainty="MC relative half-width: area %s %%, volume %s %%; MC median above the deterministic nominal run (which lies below the MC p05): area %s %%, volume %s %% (06-07); emulator AREA envelope A_new %s-%s km2 (sensitivity); emulator volume draws not used (unanchored)" % ("{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|rel_halfwidth_A_pct||.0f}}", "{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|rel_halfwidth_V_pct||.0f}}", "{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|mc_shift_A_pct||+.0f}}", "{{T12|region=DNIPRO_CORRIDOR,date=2023-06-07|mc_shift_V_pct||+.0f}}", t12("2023-06-07","A_emu_km2_p05"), t12("2023-06-07","A_emu_km2_p95"))),
    "C08": dict(n="corridor accounting rows of T16", value="06-09 S1 new dark water {{T16|quantity=S1 new dark water, 06-09 scene;region=DNIPRO_CORRIDOR|km2||.0f}} km2 (observed_S1, snapshot); label recipe {{T16|quantity=S1 new dark water, >= 2 of 3 peak dates (label recipe);region=DNIPRO_CORRIDOR|km2||.0f}} km2 (persistence); U2b {{T16|quantity=U2b predicted event flood (persistent concept);region=DNIPRO_CORRIDOR|km2||.0f}} km2 (mapped_UNet); A_new 06-09 %s km2 (terrain_reconstructed, snapshot)" % t12("2023-06-09","A_p50_km2"),
                uncertainty="literature rows VERIFY (UNOSAT 3616: ~620 km2 flooded land cumulative 6-9 June; 3623: ~180 km2 on 13 June); different AOI, temporal semantics and reference water"),
    "C09": dict(n="TEST blocks, paired bootstrap 2000", value="flood on REFERENCE_WATER {{T07|run=U2_B1B2_v1,endpoint=R_pred_on_reference_water_km2|value||.1f}} -> {{T07|run=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|value||.1f}} km2; paired {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|median||.1f}} km2; EVENT_FLOOD recall diff {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=E_recall_event_flood|median||+.3f}}",
                uncertainty="95 % [{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|lo||.1f}}, {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|hi||.1f}}]; recall [{{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=E_recall_event_flood|lo||+.3f}}, {{T07b|A=U2_B1B2_v1,B=U2_B1B2_v003A,endpoint=E_recall_event_flood|hi||+.3f}}] (crosses zero: no statistically resolved change)"),
    "C10": dict(n="TEST blocks; 19.2 km2 audited candidates", value="U0d -> U2 unlabelled-cropland burden {{T06|comparison=U2 - U0d,labels=v002,endpoint=A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2|median||.1f}} km2; BU FP {{T06|comparison=U2 - U0d,labels=v002,endpoint=BU_FP_area_km2|median||+.2f}} km2; U1 retention A {{T08b|group=A|retention_U1||.2f}}, B {{T08b|group=B|retention_U1||.2f}}, D {{T08b|group=D|retention_U1||.2f}}",
                uncertainty="95 % [{{T06|comparison=U2 - U0d,labels=v002,endpoint=A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2|ci_lo||.1f}}, {{T06|comparison=U2 - U0d,labels=v002,endpoint=A2_PREDICTED_FLOOD_BURDEN_ON_UNLABELLED_CROPLAND_km2|ci_hi||.1f}}]"),
    "C11": dict(n="TEST blocks, paired bootstrap 2000", value="U2 -> U2b flood on REFERENCE_WATER {{T07b|A=U2_B1B2_v003A,B=U2b_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|median||.2f}} km2",
                uncertainty="95 % [{{T07b|A=U2_B1B2_v003A,B=U2b_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|lo||.2f}}, {{T07b|A=U2_B1B2_v003A,B=U2b_B1B2_v003A,endpoint=R_pred_on_reference_water_km2|hi||.2f}}]; not independent"),
    "C12": dict(n="{{T09|evaluation=spatial_block_cv_5fold,cls=MACRO_MEAN|n||.0f}} CV samples", value="OA {{T09|evaluation=spatial_block_cv_5fold,cls=MACRO_MEAN|OA_spatial_cv||.3f}}, macro F1 {{T09|evaluation=spatial_block_cv_5fold,cls=MACRO_MEAN|F1||.3f}}; transfer B1->B2 macro F1 {{T09|evaluation=transfer_B1_to_B2,cls=MACRO_MEAN|F1||.3f}}, B2->B1 {{T09|evaluation=transfer_B2_to_B1,cls=MACRO_MEAN|F1||.3f}}",
                uncertainty="agreement with WorldCover (training reference), not validation"),
    "C13": dict(n="4 splits (7.5, 10, 15, 20 km); 5 km infeasible", value="U2 v003_A global F1: 10 km {{T20|split=m6_split_v1|G_F1||.3f}}, 7.5 km {{T20|split=m6_split_s7p5|G_F1||.3f}}, 15 km {{T20|split=m6_split_s15|G_F1||.3f}}, 20 km {{T20|split=m6_split_s20|G_F1||.3f}}",
                uncertainty="each split has its own TEST geography; intervals in T20"),
    "C14": dict(n="{{T21|phase=drawdown|date|count|}} drawdown days with >= 2 level sources", value="pool volume {{T21|date=2023-06-05|V_pool_km3||.1f}} -> {{T21|date=2023-06-13|V_pool_km3||.1f}} km3 (released {{T21|date=2023-06-13|cum_released_km3||.1f}} km3); largest daily volume change {{T21|date=2023-06-07|dV_pool_hm3||.0f}} hm3; daily-mean effective release {{T21|date=2023-06-07|Q_release_eff_daily_mean_m3s||.0f}} m3/s on 06-07 (inflow {{T21|date=2023-06-07|Q_in_dniprohes_m3s||.0f}}); downstream stored new water peak {{T21|date=2023-06-09|downstream_new_volume_hm3||.0f}} hm3",
                uncertainty="DEM hypsometry vs design table at 17.5 m: {{T22|level_evrf2019_m=17.5|V_dem_km3||.1f}} vs {{T22|level_evrf2019_m=17.5|V_table19_km3||.1f}} km3 ({{T22|level_evrf2019_m=17.5|dV_rel_pct||.0f}} %); surface interpolated between 3-4 points; independent estimates of a different quantity (initial breach flow) 5.7e4 (Yi 2025), 3.6e4 (Kadam 2024) m3/s -- VERIFY"),
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
