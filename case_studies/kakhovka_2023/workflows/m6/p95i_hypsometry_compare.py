# New in floodstate-eo, 2026-09-28. STATUS: ACTIVE. The DESIGN level-area-volume curves of the Kakhovka reservoir and the observed drawdown levels on them.
"""P95i -- the reservoir's design (project) hypsometry, and the observed 2023 levels read on it. No DEM, no soundings.

  TABLE 19   the design capacity curve of the Dnipro-reservoirs monograph: water level (historical Baltic), surface area and
             volume of the whole pool and of its five reaches at 17 levels 10.0-18.0 m (Figs 13-15 of the monograph; transcribed
             from photographed pages in SWOT-DNIPRO data/historical/historical_level_area_volume.csv)
  TABLE 21   the five reaches (dam -> Babyne -> Nikopol -> Verkhnia Tarasivka -> Blahovishchenka -> Dnipro HPP): area and volume
             at the normal impoundment level (NPG) and the dead-volume level (GMO), useful volume
  INFLOW     the daily DniproHES releases (SWOT-DNIPRO dniprohes_releases.csv, post 80039) as the inflow to the pool; the
             storage balance on the DESIGN curve, Q_out = Q_in - dV_design/dt, gives the outflow through the Kakhovka HPP
             before the breach and the daily-mean effective release through the breach after it (design-curve version of T21;
             lateral inflow, evaporation and withdrawals are not in it -- a residual, not a measured discharge)
  LEVELS     the observed 2023 levels, 1 February - 10 July (EVRF2019), brought to the historical Baltic frame by -0.185 m
             (the Paper-1 bridge) and read on the design curve: the design volume and area at that level, the filling of the
             pool in spring and the volume released from the design curve day by day.
             Before the breach: the Rozumivka gauge (80959, 247.5 km from the dam; SWOT-DNIPRO k5, terms 08/20 averaged per
             day) -- the only 2023 daily series in the archive (Nova Kakhovka, Nikopol, Plavni end in 2021); the pool was level
             before the breach (Paper 1 / p1f: pre-breach longitudinal slope ~0.04 cm/km, VERIFY), so one gauge reads the
             whole pool. G-REALM (111 km), ICESat-2 and the SWOT outlet nodes (from 26 May) as independent checks.
             From 26 May: the p95f daily levels (SWOT outlet, Nikopol press, Rozumivka) with their hold / interpolation rules.
             "Outlet" = the SWOT nodes at 0 km, the pool just ABOVE the dam (upper pool). Downstream for comparison: the SWOT level
             0.5 km BELOW the dam (p59/p60) and the Kherson gauge 80805 -- the head across the dam (16.7 m before the breach,
             6.0 m on 6 June, 1.5 m by 14 June) and the pool-minus-Kherson difference.

The design curve assumes a LEVEL pool. During the drawdown the surface sloped (up to 4 m between the outlet and Rozumivka,
p95f), so the design volume is read at the outlet level (lower value) and at the Rozumivka level (upper value) and the pair is
reported as a range, never a single number. Table 19 is undefined below 10.0 m: once the outlet falls below it the design
volume is not defined (NaN), which is stated, not extrapolated. Nothing is fitted or corrected.

Outputs: <case_study>/tables/p95i_design_hypsometry.csv (Table 19 + reaches, both datums), p95i_design_daily.csv (daily
         levels 1 Feb - 10 Jul on the design curve), p95i_design_weekly_2023.csv (the filling, week by week), p95i_manifest.json
"""
from __future__ import annotations
import importlib.util, json, time
from pathlib import Path
import numpy as np, pandas as pd
from floodstate_eo import _kakhovka_legacy_config as CFG
from floodstate_eo.terrain.interp import bounded_interp

HERE = Path(__file__).resolve().parent
SD = Path(CFG._SWOT_DNIPRO_SIBLING)
_s = importlib.util.spec_from_file_location("p95f", HERE / "p95f_reservoir_balance.py"); P95F = importlib.util.module_from_spec(_s); _s.loader.exec_module(P95F)
BS = P95F.BS77_TO_EVRF
REACHES = {1: "Kakhovka HPP – Babyne", 2: "Babyne – Nikopol", 3: "Nikopol – Verkhnia Tarasivka", 4: "Verkhnia Tarasivka – Blahovishchenka", 5: "Blahovishchenka – Dnipro HPP"}


def design_curve():
    t = pd.read_csv(SD / "data/historical/historical_level_area_volume.csv")
    D = pd.DataFrame(dict(level_bs_m=t.water_level_m, level_evrf2019_m=(t.water_level_m + BS).round(3), A_km2=t.surface_area_km2, V_km3=t.volume_total_km3,
                          design_level=t.design_level.fillna(""))).copy()
    for k in REACHES:
        D[f"V_reach{k}_km3"] = t[f"volume_reach{k}_km3"]
    D["V_reaches_sum_km3"] = D[[f"V_reach{k}_km3" for k in REACHES]].sum(axis=1, min_count=5)
    D["reach_sum_minus_total_km3"] = (D.V_reaches_sum_km3 - D.V_km3).round(2)          # transcription check: the reaches must add up to the total
    return D.sort_values("level_bs_m")


def on_curve(D, h_bs, col):
    """Read the design curve at a historical-Baltic level; NaN outside 10.0-18.0 m (never extrapolated; the shared
    `terrain.interp.bounded_interp` of review F13)."""
    return bounded_interp(np.asarray(h_bs, float), D.level_bs_m.to_numpy(float), D[col].to_numpy(float))


def main():
    t0 = time.time()
    D = design_curve(); R21 = pd.read_csv(SD / "data/historical/historical_reservoir_reaches.csv")
    D.sort_values("level_bs_m", ascending=False).to_csv(CFG.TABLES / "p95i_design_hypsometry.csv", index=False)
    lv = pd.read_csv(CFG.TABLES / "p95f_reservoir_daily.csv"); lv["t"] = pd.to_datetime(lv.date)
    DATES = pd.date_range("2023-02-01", "2023-07-10", freq="D")
    k = pd.read_csv(SD / "outputs/tables/k5_gauge_levels_evrf2019.csv", parse_dates=["date"])
    roz = k[(k.station_id == 80959) & (k.QC_flag == "ok")].groupby("date").H_EVRF2019_m.mean().reindex(DATES)      # terms 08 + 20 averaged
    p61 = pd.read_csv(SD / "outputs/tables/p61_pool_levels_2023.csv", parse_dates=["date"]); p61 = p61[p61.quality.isin(P95F.GOOD_Q)]
    src = p61.groupby(["date", "source"]).H_evrf2019.median().unstack().reindex(DATES)
    out = pd.DataFrame(dict(date=DATES.strftime("%Y-%m-%d"), H_rozumivka_m=roz.round(3).values,
                            H_grealm_m=src.get("GREALM_S6A", pd.Series(index=DATES, dtype=float)).round(3).values, H_icesat2_m=src.get("ICESAT2_ATL13", pd.Series(index=DATES, dtype=float)).round(3).values))
    f = lv.set_index("t").reindex(DATES)                                # p95f daily (26 May - 10 July) with its hold / interpolation rules
    out["H_outlet_m"] = f.H_outlet_m.values; out["H_nikopol_m"] = f.H_nikopol_m.values                # outlet = SWOT nodes at 0 km: the pool just ABOVE the dam
    out["H_kherson_m"] = f.kherson_stage_m.values                                                        # downstream: Kherson gauge 80805 (T21)
    bd = pd.read_csv(SD / "outputs/tables/p60_swot_outlet_drawdown.csv"); bd["date"] = pd.to_datetime(bd[[c for c in bd.columns if "date" in c.lower()][0]])
    out["H_below_dam_0_5km_m"] = bd.set_index("date").H_below_dam_0_5km_p59.reindex(DATES).round(3).values   # SWOT just below the dam (p59)
    out["head_across_dam_m"] = (out.H_outlet_m - out.H_below_dam_0_5km_m).round(2); out["pool_minus_kherson_m"] = (out.H_outlet_m - out.H_kherson_m).round(2)
    k5_ok = out.H_rozumivka_m.notna()                                                   # review F14: provenance of every value actually used
    out["H_rozumivka_m"] = out.H_rozumivka_m.fillna(pd.Series(f.H_rozumivka_m.values)).round(3)
    out["gradient_m"] = (out.H_rozumivka_m - out.H_outlet_m).round(3)
    out["phase"] = np.where(pd.to_datetime(out.date) < P95F.BREACH, "pre-breach", np.where(pd.to_datetime(out.date) <= "2023-06-13", "drawdown", "post-drawdown"))
    out["rozumivka_source"] = np.where(k5_ok, "k5 gauge 80959 terms 08/20 mean", np.where(out.H_rozumivka_m.notna(), "p95f daily (T21; fills a missing k5 day)", ""))
    for nm, col in (("outlet", "H_outlet_m"), ("nikopol", "H_nikopol_m"), ("rozumivka", "H_rozumivka_m"), ("grealm", "H_grealm_m"), ("icesat2", "H_icesat2_m")):
        hb = out[col] - BS; out[f"{nm}_level_bs_m"] = hb.round(3)
        out[f"V_design_at_{nm}_km3"] = on_curve(D, hb, "V_km3").round(3); out[f"A_design_at_{nm}_km2"] = on_curve(D, hb, "A_km2").round(0)
    out["V_design_range_km3"] = out.apply(lambda r: f"{r.V_design_at_outlet_km3:.2f}–{r.V_design_at_rozumivka_km3:.2f}" if np.isfinite(r.V_design_at_outlet_km3) and np.isfinite(r.V_design_at_rozumivka_km3) else "", axis=1)
    pre = out[(out.phase == "pre-breach") & (out.date >= "2023-05-26")]; V0 = float(pre.V_design_at_outlet_km3.median()); A0 = float(pre.A_design_at_outlet_km2.median())
    out["released_design_from_outlet_km3"] = (V0 - out.V_design_at_outlet_km3).round(3)
    out["released_design_from_rozumivka_km3"] = (float(pre.V_design_at_rozumivka_km3.median()) - out.V_design_at_rozumivka_km3).round(3)
    out["V_design_km3"] = np.where(out.phase == "pre-breach", out.V_design_at_rozumivka_km3, np.nan)     # level pool before the breach: one number
    out["A_design_km2"] = np.where(out.phase == "pre-breach", out.A_design_at_rozumivka_km2, np.nan)
    # ---- storage balance on the design curve with the DniproHES inflow ----
    q = pd.read_csv(SD / "outputs/tables/dniprohes_releases.csv", parse_dates=["date"]); q = q[q.quality_flag == "ok"].set_index("date").discharge_m3s.reindex(DATES)
    out["Q_in_dniprohes_m3s"] = q.values; out["Q_in_hm3_day"] = (q.values * 86400 / 1e6).round(1)
    # review F14: one balance series per level source, each over its own days -- never a switch from Rozumivka to the outlet
    # inside one series (the first difference across a switch is an inter-source step, not a change of storage).
    # Rozumivka: the whole period (level pool before the breach; the upper-bound level during the drawdown). Outlet: from 26 May
    # (SWOT; before the breach HELD values, see note), the lower-bound level during the drawdown. + = leaves the pool.
    for nm in ("rozumivka", "outlet"):
        dv = out[f"V_design_at_{nm}_km3"].diff() * 1000
        out[f"dV_design_{nm}_hm3_day"] = dv.round(1)
        out[f"Q_out_design_{nm}_m3s"] = ((out.Q_in_hm3_day - dv) * 1e6 / 86400).round(0)
    # weekly summary of the filling (Monday weeks): level, design volume / area, change per week
    # review F14: every term of a week over the SAME days -- the change of storage is the sum of that week's daily changes, i.e.
    # V(last day of the week) - V(last day of the previous week), never a difference of weekly means; a term with a missing day
    # is NaN (min_count), and completeness is reported. The levels and means are descriptive only.
    w = out[out.phase == "pre-breach"].copy(); w["week"] = pd.to_datetime(w.date).dt.to_period("W").dt.start_time.dt.strftime("%Y-%m-%d")
    def weekly(g):
        n = len(g); dv = g.dV_design_rozumivka_hm3_day; qi = g.Q_in_hm3_day
        return pd.Series(dict(date_first=g.date.iloc[0], date_last=g.date.iloc[-1], n_days=n, n_days_dV=int(dv.notna().sum()), n_days_inflow=int(qi.notna().sum()),
                              H_rozumivka_mean_m=g.H_rozumivka_m.mean(), H_rozumivka_last_m=g.H_rozumivka_m.iloc[-1], H_grealm_mean_m=g.H_grealm_m.mean(),
                              H_icesat2_mean_m=g.H_icesat2_m.mean(), H_outlet_swot_mean_m=g.H_outlet_m.mean(), V_design_last_km3=g.V_design_km3.iloc[-1],
                              A_design_last_km2=g.A_design_km2.iloc[-1], Q_in_dniprohes_mean_m3s=qi.mean() * 1e6 / 86400 if qi.notna().any() else np.nan,
                              Q_in_km3=qi.sum(min_count=n) / 1000, dV_week_km3=dv.sum(min_count=n) / 1000,
                              Q_out_design_km3=(qi - dv).sum(min_count=n) / 1000, complete=bool(dv.notna().all() and qi.notna().all())))
    W = w.groupby("week").apply(weekly, include_groups=False)
    W["Q_out_design_mean_m3s"] = W.Q_out_design_km3 * 1e9 / (W.n_days * 86400)
    W["source"] = "Rozumivka series only (level pool before the breach); inflow DniproHES post 80039 (quality ok)"
    W.round(3).reset_index().to_csv(CFG.TABLES / "p95i_design_weekly_2023.csv", index=False)
    out["design_defined"] = out.V_design_at_outlet_km3.notna()
    out["note"] = np.where(out.design_defined, "", "outlet level below 10.0 m (Table 19 undefined) -- no design volume")
    held = (out.phase == "pre-breach") & out.H_outlet_m.notna()
    out.loc[held, "note"] = "pre-breach outlet = SWOT value HELD by the p95f rule (few passes), not a daily observation; the pre-breach gradient is not a measurement -- use the Rozumivka reading"
    out.to_csv(CFG.TABLES / "p95i_design_daily.csv", index=False)
    last = out[out.design_defined & (out.phase == "drawdown")].iloc[-1]
    m = lambda d: out.set_index("date").loc[d]
    fill = dict(**{d: dict(H_rozumivka_m=float(m(d).H_rozumivka_m), V_design_km3=float(m(d).V_design_km3), A_design_km2=float(m(d).A_design_km2)) for d in ("2023-02-01", "2023-03-01", "2023-04-01", "2023-05-01", "2023-06-05") if np.isfinite(m(d).V_design_km3)})
    lo, hi = out[out.phase == "pre-breach"].V_design_km3.idxmin(), out[out.phase == "pre-breach"].V_design_km3.idxmax()
    fill["minimum"] = dict(date=out.date[lo], H=float(out.H_rozumivka_m[lo]), V=float(out.V_design_km3[lo])); fill["maximum"] = dict(date=out.date[hi], H=float(out.H_rozumivka_m[hi]), V=float(out.V_design_km3[hi]))
    fill["filled_min_to_max_km3"] = round(fill["maximum"]["V"] - fill["minimum"]["V"], 2)
    seg = out[(out.date >= fill["minimum"]["date"]) & (out.date <= fill["maximum"]["date"])]
    fill["inflow_dniprohes_min_to_max_km3"] = round(float(seg.Q_in_hm3_day.sum()) / 1000, 2); fill["outflow_design_min_to_max_km3"] = round(fill["inflow_dniprohes_min_to_max_km3"] - fill["filled_min_to_max_km3"], 2)
    fill["share_of_inflow_stored_pct"] = round(100 * fill["filled_min_to_max_km3"] / fill["inflow_dniprohes_min_to_max_km3"], 1)
    dd_ = out[(out.phase == "drawdown") & out.design_defined]
    fill["breach_release_design_06_06_to_06_08"] = dict(Q_out_at_outlet_level_m3s=dd_.Q_out_design_outlet_m3s.round(0).tolist(), Q_out_at_rozumivka_level_m3s=dd_.Q_out_design_rozumivka_m3s.round(0).tolist(),
                                                        Q_in_m3s=dd_.Q_in_dniprohes_m3s.round(0).tolist(), dates=dd_.date.tolist())
    man = dict(sources=dict(inflow=str(SD / "outputs/tables/dniprohes_releases.csv"), rozumivka_2023=str(SD / "outputs/tables/k5_gauge_levels_evrf2019.csv"), p61=str(SD / "outputs/tables/p61_pool_levels_2023.csv"), table19=str(SD / "data/historical/historical_level_area_volume.csv"), table21=str(SD / "data/historical/historical_reservoir_reaches.csv"),
                            levels=str(CFG.TABLES / "p95f_reservoir_daily.csv"), monograph="Dnipro reservoirs monograph, photographed pages (Tables 19-21, Figs 13-16); transcribed in SWOT-DNIPRO hist1"),
               bs_to_evrf_m=BS, design_levels={r.design_level.split(" - ")[0]: float(r.level_bs_m) for _, r in D[D.design_level != ""].iterrows()},
               filling_2023=fill, prebreach_design=dict(level_outlet_bs_m=round(float(pre.outlet_level_bs_m.median()), 2), V_km3=round(V0, 2), A_km2=round(A0)),
               last_defined_day=dict(date=last.date, outlet_level_bs_m=float(last.outlet_level_bs_m), V_design_range_km3=last.V_design_range_km3, released_range_km3=f"{last.released_design_from_outlet_km3:.2f}–{last.released_design_from_rozumivka_km3:.2f}"),
               reach_sum_check_max_abs_km3=float(D.reach_sum_minus_total_km3.abs().max()), note="design curve read at observed levels; sloped surface -> range outlet..Rozumivka; nothing fitted", seconds=round(time.time() - t0, 1))
    (CFG.TABLES / "p95i_manifest.json").write_text(json.dumps(man, indent=1))
    pd.set_option("display.width", 250)
    print(D.sort_values("level_bs_m", ascending=False).to_string(index=False)); print(R21[["reach_id", "extent", "area_npg_km2", "area_gmo_km2", "volume_npg_km3", "volume_gmo_km3", "volume_useful_km3"]].to_string(index=False))
    print(pd.read_csv(CFG.TABLES / "p95i_design_weekly_2023.csv").to_string(index=False)); print(json.dumps(fill, indent=0))
    print(out[(out.date >= "2023-06-03") & (out.date <= "2023-06-10")][["date", "outlet_level_bs_m", "rozumivka_level_bs_m", "gradient_m", "V_design_at_outlet_km3", "V_design_at_rozumivka_km3", "Q_in_dniprohes_m3s", "dV_design_rozumivka_hm3_day", "dV_design_outlet_hm3_day", "Q_out_design_rozumivka_m3s", "Q_out_design_outlet_m3s", "note"]].to_string(index=False))
    print(json.dumps(man["prebreach_design"]), json.dumps(man["last_defined_day"]), "reach-sum check max |diff|", man["reach_sum_check_max_abs_km3"], "km3"); print("-> tables/p95i_*")


if __name__ == "__main__":
    main()
