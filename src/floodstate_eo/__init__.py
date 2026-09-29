"""FloodState-EO: context-aware multisensor EO framework for flood-state reconstruction.

See the root README for status (version below = pyproject.toml, checked by tests/test_version.py); most submodules here are the
Sentinel-1/2 preprocessing and temporal-composite layer migrated from
SWOT-DNIPRO (see provenance/MIGRATION_MANIFEST.csv). Flood-state classification
and fusion are not yet part of the canonical, event-agnostic core -- see
docs/METHODS.md for what is implemented vs. planned.
"""

__version__ = "0.3.0rc2"          # release candidate in preparation: the response to the 2026-09-28 review (last tag v0.3.0-rc1)
