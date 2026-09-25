# New in floodstate-eo, 2026-09-25. STATUS: ACTIVE. Summary figure + table over the p95 variants; computes nothing new.
"""P95b -- the dynamics figure and table of the paper: daily inundation dam -> liman, three independent lines of evidence.

    terrain (p95)   connected_ceiling, margin 0.5 m (primary), band = margins 0.3 / 0.8 m, and hand_and_ceiling (p42 rule,
                    channel-connected lower bound);  what the observed water surface ALLOWS, every day incl. 06-07/08
    S1 observed     p94 new dark water per acquisition date (what the sensor SAW, dark-water rule: blind under reeds,
                    forest and buildings; noisy on fields and sand after 06-18)
    U-Net (M6)      U2b_v003A predicted event flood (persistent water, >= 2 of the 06-09/13/14 peak dates) -- one number
Regions: Dnipro corridor (outside the p42 cut rectangles), p42 terrain-eligible floodplain, Inhulets valley (backwater
assumption: Dnipro level at the mouth). The gauge panel is the Kherson daily stage (EVRF2019).

Outputs: <case_study>/tables/p95b_dynamics_summary.csv, <case_study>/figures/m6_v003A/hand_dyn_summary.png
"""
from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from floodstate_eo import _kakhovka_legacy_config as CFG

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = ROOT / "figures" / "m6_v003A"
T = CFG.TABLES
C_TERR, C_S1, C_UNET, C_LOW = "#2a78d6", "#eb6834", "#4a3aa7", "#1baf7a"
REGIONS = ["DNIPRO_CORRIDOR", "P42_FLOODPLAIN_DOMAIN", "INHULETS_VALLEY_rect"]


def pooled(sfx):
    d = pd.read_csv(T / f"p95_daily_area_pooled{sfx}.csv"); d["t"] = pd.to_datetime(d.date)
    return d


def main():
    prim, lo, hi, hand = pooled("_connected_ceiling"), pooled("_connected_ceiling_m030"), pooled("_connected_ceiling_m080"), pooled("")
    s1 = pd.read_csv(T / "p94_flood_dynamics_s1.csv"); s1["t"] = pd.to_datetime(s1.date)
    p92 = pd.read_csv(T / "p92_flood_area_dam_to_liman.csv"); u2b = p92[p92.run == "U2b_B1B2_v003A"].set_index("region").predicted_flood_km2
    rows = []
    for r in REGIONS:
        a, b, c, h = (x[x.region == r].set_index("t") for x in (prim, lo, hi, hand))
        s = s1[s1.region == r].set_index("t")
        for t in a.index:
            rows.append(dict(date=str(t.date()), region=r, terrain_connected_m050_km2=a.new_km2[t], terrain_m030_km2=b.new_km2[t],
                             terrain_m080_km2=c.new_km2[t], terrain_hand_rule_km2=h.new_km2[t], volume_m050_hm3=a.new_volume_hm3[t],
                             s1_observed_new_km2=s.new_water_km2.get(t, np.nan), s1_coverage=s.coverage.get(t, np.nan),
                             kherson_gauge_m=a.kherson_gauge_m[t]))
    S = pd.DataFrame(rows); S.to_csv(T / "p95b_dynamics_summary.csv", index=False)
    fig, axs = plt.subplots(2, 3, figsize=(15.5, 6.6), constrained_layout=True, gridspec_kw=dict(height_ratios=[3, 1.1]))
    for j, r in enumerate(REGIONS):
        a, b = axs[0, j], axs[1, j]; s = S[S.region == r].copy(); s["t"] = pd.to_datetime(s.date)
        a.fill_between(s.t, s.terrain_m030_km2, s.terrain_m080_km2, color=C_TERR, alpha=0.18, lw=0, label="terrain, WSE margin 0.3–0.8 m")
        a.plot(s.t, s.terrain_connected_m050_km2, color=C_TERR, lw=2.2, label="terrain: DEM < WSE, connected (margin 0.5 m)")
        a.plot(s.t, s.terrain_hand_rule_km2, color=C_LOW, lw=1.4, ls="--", label="terrain: p42 HAND rule (lower bound)")
        o = s.dropna(subset=["s1_observed_new_km2"]); full, part = o[o.s1_coverage >= 0.9], o[o.s1_coverage < 0.9]
        a.plot(full.t, full.s1_observed_new_km2, color=C_S1, lw=0, marker="o", ms=6, label="S1 observed new dark water")
        a.plot(part.t, part.s1_observed_new_km2, color=C_S1, lw=0, marker="o", ms=6, mfc="white", label="S1, partial coverage (orbit 138)")
        if r in u2b.index:
            a.axhline(u2b[r], color=C_UNET, lw=1.2, ls=":", label=f"U-Net U2b event flood, persistent ({u2b[r]:.0f} km²)")
        pk = s.loc[s.terrain_connected_m050_km2.idxmax()]
        a.annotate(f"{pk.terrain_connected_m050_km2:.0f} km² on {pk.date[5:]}", (pk.t, pk.terrain_connected_m050_km2), fontsize=7.5,
                   color="#0b0b0b", xytext=(6, 2), textcoords="offset points")
        a.axvline(pd.Timestamp("2023-06-06"), color="#e34948", lw=0.8, ls="--")
        a.set_title({"DNIPRO_CORRIDOR": "Dnipro corridor (dam → liman, without the Inhulets)", "P42_FLOODPLAIN_DOMAIN": "p42 terrain-eligible floodplain",
                     "INHULETS_VALLEY_rect": "Inhulets valley (backwater)"}[r], fontsize=9.5, loc="left")
        a.set_ylabel("new inundation, km²", fontsize=8); a.set_ylim(0, None)
        b.plot(s.t, s.kherson_gauge_m, color="#52514e", lw=1.5); b.set_ylabel("Kherson stage, m EVRF2019", fontsize=7.5)
        for ax in (a, b):
            ax.grid(color="#efece6", lw=0.8); ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=7)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d")); ax.set_xlim(pd.Timestamp("2023-05-30"), pd.Timestamp("2023-07-05"))
    axs[0, 0].legend(fontsize=6.6, frameon=False, loc="upper right")
    fig.suptitle("Kakhovka 2023, daily inundation dam → liman: what the water surface allowed (SWOT + gauge on terrain), what Sentinel-1 saw, "
                 "what the U-Net calls persistent event flood", fontsize=10)
    fig.savefig(FIG / "hand_dyn_summary.png", dpi=125, bbox_inches="tight"); plt.close(fig)
    pd.set_option("display.width", 250)
    k = S[(S.region == "DNIPRO_CORRIDOR") & (S.date >= "2023-06-05") & (S.date <= "2023-06-22")]
    print(k[["date", "terrain_connected_m050_km2", "terrain_m030_km2", "terrain_m080_km2", "terrain_hand_rule_km2", "volume_m050_hm3", "s1_observed_new_km2", "kherson_gauge_m"]].to_string(index=False))
    print("-> tables/p95b_dynamics_summary.csv, figures/m6_v003A/hand_dyn_summary.png")


if __name__ == "__main__":
    main()
