# New in floodstate-eo, 2026-09-30. STATUS: ACTIVE. The production vertical chain of Paper 1 (release v6) for the Paper 3 workflows.
"""paper1_frame -- the vertical frame of Paper 1 of the series (SWOT-DNIPRO release paper1-v6), in one place, so that the heights of
Paper 3 are the heights of Paper 1 (maintainer, 2026-09-30: "our results must match this article").

Paper 1 v6 (Sec. 3.1, S1): gauges are BS-77 stages carried into EVRF2019 by the EPSG:9902 grid step sampled at the post's own
coordinates; satellites are EGG2015-referenced heights -- SWOT h = wse + geoid_hght (its crust is already mean-tide, no permanent-tide
term), ICESat-2 h + free2mean (tide-free -> mean-tide crust), H = h - zeta_EGG2015 -- joined to the gauges by the measured closure
residual c = gauge - satellite. The reservoir value of the production chain is the mean over the six reservoir gauges of the
companion's tide-free corrector minus free2mean at each station, -0.135 m; the tide-free -0.173 m is the superseded 'term omitted'
variant (S1.5) and pairs only with heights WITHOUT the free2mean term.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from floodstate_eo import _kakhovka_legacy_config as CFG

# EPSG:9902 step at the Kherson post 80805 at its own coordinates (Paper 1 v6: data/historical/sea_posts_2023/post_metadata_2023.csv and
# data/processed/gauges/gauge_levels_evrf2019.parquet, both 0.207594 m); the p59 table of the extraction had carried +0.22 m.
KHERSON_DELTA_EPSG9902_M = 0.207594
COMPANION_STATIONS = CFG._ICESAT2_SIBLING / "outputs" / "tables" / "egg2015_to_evrf2019_by_station.csv"


def free2mean(lat):
    """IERS permanent radial displacement, mean-tide minus tide-free crust (m): the ATL03 tide_earth_free2mean (Paper 1 v6 S1.2)."""
    return 0.06029 - 0.180873 * np.sin(np.radians(np.asarray(lat, dtype=float))) ** 2


def reservoir_closures():
    """(c of the companion's tide-free chain, c of Paper 1's production chain) over the six reservoir gauges (zero 12.000 m BS-77)."""
    st = pd.read_csv(COMPANION_STATIONS); st = st[st.gauge_zero_bs77_m == 12.0]
    return float(st.c_station_m.mean()), float((st.c_station_m - free2mean(st.lat)).mean())


def mixed_chain_shift():
    """What a height built as h + free2mean - zeta + c_tide-free (the pairing of the p56/p57/p60 chains) must gain to reach Paper 1's
    production frame: c_production - c_tide-free = -mean free2mean at the reservoir gauges (about +0.038 m)."""
    c_tf, c_v6 = reservoir_closures()
    return c_v6 - c_tf


FABDEM_SOURCES = (3, 4)                        # p55 source codes: FABDEM and FABDEM tapered at the bathymetric edge


def fabdem_to_paper1(z, src):
    """The FABDEM part of the seamless terrain-bed model in Paper 1's frame. Paper 2 converted FABDEM (p56) and the ICESat-2 ground
    (p57) with + free2mean together with the tide-free closure; both therefore sit mixed_chain_shift() below Paper 1's production
    frame. The surveyed bed (sources 1, 2, 5) came through the gauge branch and is unchanged. The residuals FABDEM - ICESat-2 do not
    change (both sides move); the terrain against the water surface does."""
    z = np.array(z, dtype="f4", copy=True); m = np.isin(np.asarray(src), FABDEM_SOURCES)
    z[m] = z[m] + np.float32(mixed_chain_shift())
    return z


def icesat_ground_to_paper1(h):
    """ICESat-2 ATL08 ground heights of the p57 chain (all pulls: + free2mean with the tide-free closure) in Paper 1's frame."""
    return np.asarray(h, dtype="f8") + mixed_chain_shift()
