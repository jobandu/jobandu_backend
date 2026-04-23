# utils/auth.py
# ─────────────────────────────────────────────────────────────────────────────
# Simple admin authentication using HTTP Basic Auth with base64 encoding.
# FastAPI has built-in HTTPBasic support — we just check credentials against
# the values stored in config.
# ─────────────────────────────────────────────────────────────────────────────

import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from config import settings

# This tells FastAPI to look for a "Basic" Authorization header
security = HTTPBasic()


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """
    FastAPI dependency that checks if the request has valid admin credentials.

    How it works:
    - FastAPI automatically reads the Authorization header
    - Decodes the base64 credentials to get username and password
    - We compare them securely using secrets.compare_digest (prevents timing attacks)

    Usage in routes:
        @router.get("/admin/something")
        async def some_route(admin=Depends(verify_admin)):
            ...

    Raises:
        HTTPException 401: If credentials are missing or wrong
    """

    # Use secrets.compare_digest for safe comparison (avoids timing attacks)
    username_ok = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        settings.ADMIN_USERNAME.encode("utf-8")
    )
    password_ok = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        settings.ADMIN_PASSWORD.encode("utf-8")
    )

    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},  # Tells browser to show login popup
        )

    # Return the username (not used currently, but useful for logging)
    return credentials.username
