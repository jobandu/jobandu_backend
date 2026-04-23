# db/db_helper.py
# ─────────────────────────────────────────────────────────────────────────────
# We create ONE client for the whole app lifetime (singleton pattern).
# ─────────────────────────────────────────────────────────────────────────────

from config import settings
from pymongo import AsyncMongoClient


# ── Create the async MongoDB client ──────────────────────────────────────────
# This connection is re-used for every request (not created per request).
client: AsyncMongoClient = AsyncMongoClient(settings.MONGODB_URI)

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
