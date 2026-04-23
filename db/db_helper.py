# db/db_helper.py
# ─────────────────────────────────────────────────────────────────────────────
# We create ONE client for the whole app lifetime (singleton pattern).
# ─────────────────────────────────────────────────────────────────────────────

import ssl
import certifi
from pymongo import AsyncMongoClient
from config import settings

# Patch ssl.create_default_context BEFORE pymongo uses it
_orig = ssl.create_default_context
def _patched(*args, **kwargs):
    ctx = _orig(*args, **kwargs)
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    return ctx
ssl.create_default_context = _patched

# No ssl_context parameter — pymongo will use the patched ssl module internally
client: AsyncMongoClient = AsyncMongoClient(
    settings.MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where(),
)


# Select our database
db = client[settings.DB_NAME]


# ── Helper functions to get collections ──────────────────────────────────────
# Using functions instead of global variables makes it easy to mock in tests.

def get_applicants_collection():
    """Returns the 'applicants' collection."""
    return db["applicants"]


def get_employers_collection():
    """Returns the 'employers' collection."""
    return db["employers"]


def get_admins_collection():
    """Returns the 'admins' collection (stores admin login info)."""
    return db["admins"]
