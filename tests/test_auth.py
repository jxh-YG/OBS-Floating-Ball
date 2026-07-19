from obs_floating_controller.auth import build_obs_auth
from obs_floating_controller.obs_websocket import (
    OUTPUT_EVENT_SUBSCRIPTION,
    build_identify_payload,
    build_request_payload,
)


def test_obs_v5_authentication_matches_reference_algorithm() -> None:
    token = build_obs_auth("secret", "salt-value", "challenge-value")
    assert token == "h94szluIAg3BtKWoFpFowzEXXbx6fl8PlYxdM/LvrEA="


def test_identify_only_adds_auth_when_obs_requests_it() -> None:
    assert build_identify_payload({}, "secret") == {
        "op": 1,
        "d": {"rpcVersion": 1, "eventSubscriptions": OUTPUT_EVENT_SUBSCRIPTION},
    }
    payload = build_identify_payload(
        {"authentication": {"salt": "salt", "challenge": "challenge"}}, "secret"
    )
    assert payload["d"]["rpcVersion"] == 1
    assert payload["d"]["eventSubscriptions"] == OUTPUT_EVENT_SUBSCRIPTION
    assert payload["d"]["authentication"] == build_obs_auth("secret", "salt", "challenge")


def test_recording_requests_use_obs_v5_request_envelope() -> None:
    for request_type in ("StartRecord", "PauseRecord", "ResumeRecord", "StopRecord"):
        assert build_request_payload(request_type, "42") == {
            "op": 6,
            "d": {"requestType": request_type, "requestId": "42"},
        }
