"""Review F16: the un-migrated fetch helpers of p52d fail with a clear reason, not an AttributeError on None."""
import pytest

from floodstate_eo.io import p52d_fetch_event_optics as P


def test_missing_fetch_helpers_raise_a_clear_error():
    with pytest.raises(NotImplementedError, match="p1_targeted_fetch"):
        P.P1F.verified("x.zip")
