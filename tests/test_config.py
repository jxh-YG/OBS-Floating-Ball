import os

import pytest

from obs_floating_controller.config import DpapiProtector


@pytest.mark.skipif(os.name != "nt", reason="DPAPI is Windows-only")
def test_dpapi_round_trip_uses_the_current_windows_user() -> None:
    protector = DpapiProtector()
    assert protector.unprotect(protector.protect("test-password")) == "test-password"
