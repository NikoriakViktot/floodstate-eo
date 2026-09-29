# New in floodstate-eo, 2026-09-29 (answer to the scientific/code review of 2026-09-28, findings F01-F07). STATUS: ACTIVE.
"""Event-agnostic building blocks of the terrain-connectivity inundation reconstruction and its uncertainty propagation:

    fields        spatially correlated Gaussian random fields with unit marginal variance (perturbed terrain realizations)
    connectivity  cells connected to a seed network (the flood-fill core: terrain < water surface AND connected)
    mosaic        one union lattice for several aligned member grids (connectivity on the mosaic, ownership for accounting)
    interp        bounded 1-D interpolation (NaN outside the table's domain -- never a silent endpoint plateau)
    vertical      one vertical reference frame for every height that enters a comparison

Nothing here knows an event, a zone or a data root; the case-study scripts wire these operators to their data.
"""
