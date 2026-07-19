"""OBS WebSocket v5 authentication helpers."""

from __future__ import annotations

import base64
import hashlib


def build_obs_auth(password: str, salt: str, challenge: str) -> str:
    """Return the authentication token defined by the OBS WebSocket v5 protocol."""
    secret = base64.b64encode(
        hashlib.sha256(f"{password}{salt}".encode("utf-8")).digest()
    ).decode("ascii")
    return base64.b64encode(
        hashlib.sha256(f"{secret}{challenge}".encode("utf-8")).digest()
    ).decode("ascii")
