# Data

GitHub is not a data archive. No SAFE archive, JP2, raw GeoTIFF, NPZ stack, or large Parquet file is committed
here (`.gitignore` already excludes them). This file, plus the three CSVs in
`case_studies/kakhovka_2023/manifests/`, is the authoritative record of what data this repository's code reads —
row-level identity, licence and (where computed) checksum live in the CSVs; this page is the narrative index.

This corrects `08_DATA_POLICY.md` of the source migration audit, which was written *before* this session's code
migration and drafted this table from the audit's read of SWOT-DNIPRO, not from `src/floodstate_eo/**` as it
actually ended up. Every row below was re-verified by grep against the migrated tree
(source commit `f3e3e1afe91902a82a73f3c09354d1f9eb847766`) rather than carried over from that draft.

## Datasets actually used by `src/floodstate_eo/**`

| Dataset | Source / API | Required? | Licence | Redistribution | Manifest |
|---|---|---|---|---|---|
| Sentinel-1 IW SLC | Copernicus Data Space Ecosystem (CDSE) | Required — `sar/p82_coherence_graph.py` coherence chain | Copernicus Sentinel Data, free/open, attribution required | Raw SAFE never redistributed from this repo | `manifests/s1_scenes.csv` (30 products, 4 orbits) |
| Sentinel-2 L2A | Copernicus Data Space Ecosystem (CDSE) | Required — `optical/p54a_frame_index_stacks_10m.py` and the whole 10 m composite chain | Copernicus Sentinel Data, free/open, attribution required | Raw SAFE never redistributed from this repo | `manifests/s2_scenes.csv` (44 products, real sha256) |
| Sentinel-1 GRD/RTC orbit-aware cache | Built by SWOT-DNIPRO's `p0o`/`p0v`/`p0w` (**not migrated — no fetch/build code exists in this repo**) | Required — `sar/p71_s1_event_change.py` | Same chain as raw S1 | Not vendored | `manifests/external.csv` |
| ESA WorldCover v200 (2021) | esa-worldcover.org | Required, load-bearing — `surface_state/p69a_base_class.py` BASE_CLASS rules key on WorldCover class codes directly | CC-BY 4.0 | Permits redistribution with attribution | `manifests/external.csv` |
| SRTM 1 Arc-Second HGT | NASA/USGS, auto-fetched by SNAP's `gpt` at run time | Required — `sar/p82_coherence_graph.py`'s Terrain-Correction/Back-Geocoding nodes | Public domain (US Government work) | Yes | `manifests/external.csv` |
| FABDEM (ZONE_4 only) | data.bris.ac.uk | Optional, visualization-only — `spatial/p52a_processing_frames_qa.py` hillshade background, guarded by `if p.exists()` | CC BY-NC-SA 4.0 — **NC clause unverified against this repo's release licence, do not bundle in a public figure export until checked** | Not verified — treat as NO until checked | `manifests/external.csv` |
| Kakhovka zone + reservoir geometry | Two sibling-repo GeoJSON files (`SWOT-DNIPRO/data/processed/domains/`, `icesat2-atl13-kakhovka/data/`) | Required for every `CFG.load_utm(zone)` call | Unspecified — same as SWOT-DNIPRO project (TBD) | Not vendored, not redistributed | `manifests/external.csv`, `provenance/UNRESOLVED_DEPENDENCIES.md` #3 |

**Explicitly checked and excluded** (present in the pre-migration draft, absent from the actual migrated code —
verified by grep, not assumed): Dynamic World (zero references anywhere in `src/floodstate_eo/**`), HAND
(referenced only in docstrings as something the migrated scripts explicitly do *not* open), EGG2015
quasigeoid / UA2019Z datum grid / gauge yearbook / ICESat-2 ATL13 parquet (all belong to SWOT-DNIPRO's
bathymetry/vertical-datum chain, never imported by anything under `src/floodstate_eo/**`), SWOT altimetry
(same — legacy `p42`/`p59` coupling in SWOT-DNIPRO, not part of this migration's scope at all).

## Credentials

Read from environment variables only, never committed. Names as actually used by the migrated fetch code
(`io/p52c_cdse_optical_gap.py`, `io/p52d_fetch_event_optics.py`, `io/p81_fetch_slc.py`):

- `username_CDSE`, `password_CDSE` — CDSE OAuth token exchange (`TOKEN_URL` = `identity.dataspace.copernicus.eu`).
- `SWOT_DNIPRO_ROOT` (default `~/repo/SWOT-DNIPRO`), `SWOT_DNIPRO_ICESAT_ROOT` — sibling-repo checkout locations
  for the zone/reservoir geometry dependency (see `provenance/UNRESOLVED_DEPENDENCIES.md` #3).
- `FLOODSTATE_DATA_ROOT` (falls back to `SWOT_DNIPRO_BULK_ROOT`, then a local default) — the bulk data root
  (`_kakhovka_legacy_config.py`), i.e. `$FLOODSTATE_DATA_ROOT/s1_slc/`, `.../s2_l2a/`, `.../worldcover_frames/`,
  `.../terrain/`, `.../frames10/` per the manifests' `local_relpath` column.

A committed `.env.example` documenting these names (values never filled in) does not yet exist in this repo —
add one as part of whatever Phase 6/7 work replaces `_kakhovka_legacy_config.py` with real config-file wiring.

## Reproduction path

There is no `workflows/fetch_*` CLI yet (`05_PROPOSED_REPOSITORY_TREE.md`'s design, not built in this migration).
Until it exists, the three manifest CSVs are the reproduction record: re-running `io/p52c_cdse_optical_gap.py` →
`io/p52d_fetch_event_optics.py` / `io/p52f_pass2_b2_targeted.py` (S2) and `io/p81_fetch_slc.py` (S1) against
`case_studies/kakhovka_2023/manifests/{s1_scenes,s2_scenes}.csv`'s `product_id_or_scene_id` column reproduces the
same CDSE products by id. The two dependencies with no migrated fetch code at all (the S1 GRD/RTC cache, the
zone/reservoir geometry) cannot be reproduced from this repository alone yet — see `external.csv`'s notes and
`provenance/UNRESOLVED_DEPENDENCIES.md`.

## Checksums

`manifests/s2_scenes.csv` carries real `sha256`/`size_bytes` per scene, copied from SWOT-DNIPRO's own fetch
ledgers (`p52d_fetch_ledger.csv`, `p52d_fetch_ledger_pass_2_b2.csv`) — not recomputed here. `manifests/s1_scenes.csv`
does not: neither `p80_c1_frozen_products.csv` nor `io/p81_fetch_slc.py` records a checksum for the SLC archives,
so those cells are `TBD` pending a Phase 9 measurement pass over the ~82 GB S1 cache (not attempted in this task —
hashing that much data was judged out of scope for a documentation pass).
