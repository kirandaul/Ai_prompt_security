"""
auth.py — minimal admin authentication for the dashboard.

Stdlib only. A successful login issues an HMAC-signed session token
(value: "username|expiry_epoch|signature") stored in an HttpOnly cookie.
Protected endpoints verify the signature and expiry.

Configure via environment variables:
    PSG_ADMIN_USER      (default: admin)
    PSG_ADMIN_PASSWORD  (default: admin123  -- CHANGE THIS)
    PSG_SECRET_KEY      (default: random per process -- set to persist sessions)
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from typing import Optional

ADMIN_USER = os.environ.get("PSG_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("PSG_ADMIN_PASSWORD", "admin123")
SECRET_KEY = os.environ.get("PSG_SECRET_KEY", secrets.token_hex(32)).encode()

SESSION_TTL_SECONDS = 8 * 60 * 60  # 8 hours
COOKIE_NAME = "psg_session"


def _sign(payload: str) -> str:
    return hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()


def verify_credentials(username: str, password: str) -> bool:
    """Constant-time credential comparison."""
    user_ok = hmac.compare_digest((username or ""), ADMIN_USER)
    pass_ok = hmac.compare_digest((password or ""), ADMIN_PASSWORD)
    return user_ok and pass_ok


def create_token(username: str) -> str:
    expiry = int(time.time()) + SESSION_TTL_SECONDS
    payload = f"{username}|{expiry}"
    return f"{payload}|{_sign(payload)}"


def verify_token(token: Optional[str]) -> Optional[str]:
    """Return the username if the token is valid and unexpired, else None."""
    if not token:
        return None
    try:
        username, expiry, signature = token.rsplit("|", 2)
    except ValueError:
        return None
    payload = f"{username}|{expiry}"
    if not hmac.compare_digest(signature, _sign(payload)):
        return None
    try:
        if int(expiry) < int(time.time()):
            return None
    except ValueError:
        return None
    return username
