# Verification of open_citations (p100b, 2026-10-01) against source full text

Checked 2026-10-01. Sources: GROBID TEI from the knoweledg_graf corpus (`data/literature/grobid_xml/`), and for papers
not in the corpus: Maiti 2022 (Copernicus PDF), Lefebvre 2019 and Pulvirenti 2021 (MDPI HTML via web.archive.org).
Manuscript line numbers refer to `valid_artsclt/manuscript.md`.

Verdicts: **VERIFIED** = verbatim or number found in source; **FIX** = source says something different;
**WORDING** = supported, but the manuscript phrasing is stronger than the source; **OPEN** = full text not read.

## Summary

| Reference | Manuscript use | Verdict |
|---|---|---|
| Johnson 2019 | "does not accurately capture inundated cells" | VERIFIED (abstract, verbatim) |
| Olofsson 2014 | "based on a sample of higher quality" | VERIFIED (verbatim; source continues "…change information (i.e., the reference classification)") |
| Zheng 2018 | "local depressions such as ponds or waterbodies … even if they are not connected with the main stem river" | VERIFIED (elided words: "can be identified as flooded with GeoFlood"); see WORDING below |
| Bates 2022 | "do not preserve hydraulic connectivity (i.e., … physical flow path to them)" | VERIFIED (verbatim; Annu. Rev. Fluid Mech., `annurev-fluid-030121-113138`) |
| Hawker 2022 | FABDEM = Copernicus DEM, buildings and forests removed by ML | VERIFIED; licence CC BY-NC-SA 4.0 is not in the paper (data record, data.bris timed out) → OPEN |
| Iqbal 2023 (in the Hawker sentence, l.126) | "residual MAE of 1.1–1.6 m remain in built-up areas" | **FIX**, see 1 |
| Lehnigk 2026 | 1.4–6.1 m, 10–11 m by 8 June, 5.6 m Kherson, ∼8 km³ | numbers VERIFIED; **FIX** in Discussion l.989 and l.1035, WORDING l.93, see 2 |
| Yi 2025 | (5.7 ± 0.8)×10⁴ m³/s; 20.4 ± 1.4 km³/30 d; 21.0 km³ at 17.3 m; 12.6 ± 1.1 m | VERIFIED (all verbatim) |
| Yi 2025 | ~845 km² by 20 June | VERIFIED as derived: 2 125 − 280 − 1 000 = 845 km² (30 May area minus the reported decreases) |
| Monti 2024 | ~80 km of river; ~7.5 km³; S1 change detection | VERIFIED ("almost 80 km", "about 7.50 km³", Conclusions); given name Roberto; Crossref pages "50-50", issued 2024-06-21 |
| Biancamaria 2016 | SWOT, 1-day calibration orbit | VERIFIED ("3 months of fast sampling calibration"); Crossref: online 2015-10-27, print 2016-03, vol. 37, pp. 307–337, so "2016" is correct |
| Lefebvre 2019 | "optical water indices systematically underestimate the flooding duration under a vegetation cover" | VERIFIED (abstract, verbatim). The 5 %/71 % Phragmites figure **does not appear** in the text: keep it out |
| Maiti 2022 | label noise degrades segmentation | VERIFIED in general ("higher label errors in training labels result in lower model performance"); note DeepLabV3+ on aerial images/DSM, low noise levels, not U-Net/flood |
| He 2024 | weak supervision for flood mapping | OPEN: Elsevier, no abstract in OpenAlex/S2; the title supports the use as worded ("weakly supervised semantic segmentation", urban flood mapping) |
| Cohen 2022 (not cited) | forwarded: 'uncertain area' class for semi-forested terrain | VERIFIED: "Areas identified as non-flooded in semi-forested areas are classified as uncertain" |
| Pulvirenti 2021 (not cited) | forwarded: double bounce; no unique SAR signature of flooded vegetation | VERIFIED: "flooded vegetation does not generally have a clear and unique radar signature" (§3.2.4) |
| Giustarini 2013, Pohjankukka 2017, Iakubovskii 2019, CEOBS, REACH, Pedregosa, Rikimaru, Paper 1/2 | not cited in text / metadata only | no content claim to verify |

## Fixes needed

### 1. FABDEM error in built-up areas (l.126): the range is a before/after pair

Iqbal et al. 2023 write "A mean absolute vertical error of 1.12–1.61 m was found for the FABDEM in built-up areas
(Hawker et al., 2022)". Hawker et al. 2022 say: "Our method reduces mean absolute vertical error in built-up areas
from 1.61 to 1.12 m". The 1.61 m is the uncorrected Copernicus DEM. The FABDEM residual is 1.12 m. Iqbal turned that
pair into a range, and the manuscript repeats it as a secondary citation.

Suggested: "…removed by machine learning (Hawker et al. 2022), which reduces the mean absolute vertical error in
built-up areas from 1.61 to 1.12 m (Hawker et al. 2022)". Cite Iqbal 2023 only for its own floodplain assessment, if at all.

### 2. Lehnigk 2026: corrected bathymetry does *not* make the models reproduce stage and timing

Source: "Modifying reservoir and channel bathymetry to reflect geomorphology produces better agreement with SWOT …
yet still fails to reproduce both flood stage and timing". Also: "no version of bathymetry was able to reproduce both
the stage and timing of the flood peak". Even the best configuration (steep channel + river-like reservoir) still
underestimates peak stage by an average of 1.4 m. The other two configurations underestimate it by 5.8 m and 6.1 m.

- **l.989 (Discussion):** "hydraulic models of this flood do not reproduce the observed stages and their timing
  without corrected bathymetry". This implies that correction is sufficient. Suggested: "…do not reproduce the
  observed stages and their timing together, even with corrected bathymetry".
- **l.1035 (Discussion):** "Such models of this event need corrected reservoir and channel bathymetry before they
  reproduce the observed stages and their timing". This contradicts the source. Suggested: "Such models of this event
  improve with corrected reservoir and channel bathymetry but still reproduce neither the peak stage nor its timing
  together (Lehnigk et al. 2026)…".
- **l.93 (Introduction), WORDING:** "underestimate … by 1.4 to 6.1 m … unless bathymetry is corrected" reads as if
  corrected models no longer underestimate. In the source, 1.4 m is the error *with* corrected bathymetry and
  5.8–6.1 m the error without it. Suggested: "underestimate the observed peak stages by 5.8–6.1 m with globally
  available bathymetry and still by 1.4 m with geomorphologically corrected bathymetry, which reproduces neither stage
  nor timing together".
- Also note that Lehnigk's ∼8 km³ is stated without a source in their introduction. The same paper quotes a
  "reported volume of 19 km³ (Naddaf, 2023)". The manuscript wording "Lehnigk et al. cite ∼8 km³" is fair.
  The Kherson 5.6 m is Lehnigk citing Naddaf 2023. SWOT at the same place gave 5–5.3 m.

### 3. Zheng 2018 (l.211), WORDING

The manuscript says "GeoFlood **by design** flags…". The source says these depressions "can be identified as flooded
with GeoFlood even if they are not connected". That is a stated limitation, not a design intent. Suggested: "GeoFlood
can identify as flooded…". The other Zheng sentence ("the case that terrain-index methods list as their limitation")
is consistent with the source.

## Still open

- FABDEM licence (CC BY-NC-SA 4.0): confirm on the data.bris record (the request timed out from here).
- He 2024: read the full text if the citation ever carries more than "weak supervision for flood mapping".
- Zheng 2018 pages 10013–10033: not in Crossref; check on the WRR article page.
- Monti 2024 pages: Crossref says "50-50" (article number style); take them from the AGG article page.
