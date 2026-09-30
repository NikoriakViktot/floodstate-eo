# Note for SWOT-DNIPRO (Papers 1–2): two chains that do not match Paper 1 v6 — found 2026-09-30

Found while aligning Paper 3 with Paper 1 v6 (release `paper1-v6`; maintainer: "our results must match this article").
Nothing in SWOT-DNIPRO was changed; Paper 3 corrects the heights it reads (`case_studies/kakhovka_2023/workflows/m6/paper1_frame.py`).

## 1. Paper 2: FABDEM (p56) and night ICESat-2 ground (p57)

Both are built as `h_ell + free2mean(lat) − ζ_EGG2015 + c`, with `c` = the mean of `c_station_m` of the six reservoir gauges in
`icesat2-atl13-kakhovka/outputs/tables/egg2015_to_evrf2019_by_station.csv` (−0.173 m). That corrector comes from the companion's
**tide-free** chain; Paper 1 v6 (S1.5) calls it the superseded "term omitted" variant and pairs the permanent-tide term with the
production closure −0.135 m (Sec. 5.1). Mixing the two leaves every FABDEM and ICESat-2 ground height `c_prod − c_tf = −mean
free2mean(station lat) ≈ +0.038 m` too low in Paper 1's frame.

- Effect in Paper 2: residuals FABDEM − ICESat-2 and the class statistics are unchanged (both sides carry the offset); absolute
  heights (and anything compared with gauges or SWOT) are 3.8 cm low.
- Fix at the source: either drop `free2mean` and keep the tide-free `c`, or keep `free2mean` and use the production `c`
  (`mean(c_station_m − free2mean(lat_station))` = −0.135 m). Then regenerate `terrain/<ZONE>/fabdem_evrf2019_20m.tif`, the seamless
  model of p55 and the p57 tables. Paper 3 then drops its correction (`paper1_frame.fabdem_to_paper1`, `icesat_ground_to_paper1`).

## 2. The p60/p61 pool levels (SWOT outlet, G-REALM)

p60 builds the SWOT outlet as `wse + geoid_hght + free2mean(lat) − ζ + c_tf`. Paper 1 v6 (Sec. 3.1, S1.2): SWOT's crust is already
mean-tide, so no `free2mean`, and the closure is the production one. p61 therefore holds the outlet 0.073 m below Paper 1's own
numbers (17.53 vs 17.61 m on 31 May; 5.63 vs 5.71 m on 13 June). G-REALM (Sentinel-6A) takes the same terms; its tide convention is
not established in Paper 1, and on 9 June it stands 0.5 m above the Nikopol post upstream. Paper 3 moves the outlet into the
production chain and uses G-REALM only as a plotted check (`p95f_reservoir_balance.py`). The p61 row of Nikopol on 13 June is a
censored upper bound (9.17 m); Paper 3 caps its hold with it.

## 3. The Kherson gauge in the extraction

The table `p59_swot_vs_kherson.csv` that Paper 3 copied at the extraction carried BS-77 + 0.22 m; Paper 1 v6 uses the EPSG:9902 step
at the post's own coordinates, +0.2076 m (`data/processed/gauges/gauge_levels_evrf2019.parquet`). Paper 3 now uses +0.2076 m
(`p59k_kherson_frame.py`).
