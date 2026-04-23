# api/admin_routes.py
# ─────────────────────────────────────────────────────────────────────────────
# Protected routes for the admin panel.
# ALL routes here require HTTP Basic Auth (admin username + password).
#
# Admin can:
#   - View all applicants (with optional filters)
#   - View all employers
#   - Update applicant status
#   - Update employer status
#   - Send a custom email to any applicant or employer
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from bson import ObjectId
from typing import List, Optional

from db.db_helper import get_applicants_collection, get_employers_collection
from models.applicant_model import ApplicantStatusUpdate
from models.employer_model import EmployerStatusUpdate
from schemas.applicant_schema import applicant_helper
from schemas.employer_schema import employer_helper
from services.email_service import send_email
from utils.auth import verify_admin
from utils.logger import AppLogger
from pydantic import BaseModel

logger = AppLogger.get_logger()

# All admin routes are protected — Depends(verify_admin) checks credentials
router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(verify_admin)],  # <-- applies to ALL routes in this router
)


# ── APPLICANT ROUTES ─────────────────────────────────────────────────────────

@router.get("/applicants", summary="Get all applicants with optional filters")
async def get_all_applicants(
    # Optional query parameters for filtering
    skill: Optional[str] = Query(None, description="Filter by skill, e.g. 'driver'"),
    status: Optional[str] = Query(None, description="Filter by status, e.g. 'applied'"),
    location: Optional[str] = Query(None, description="Filter by location"),
    limit: int = Query(50, ge=1, le=200, description="Max number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip (for pagination)"),
):
    """
    Returns a list of all applicants.
    Admin can filter by skill, status, or location.
    Supports pagination with limit and skip.
    """

    # Build a MongoDB filter dictionary
    # Only add a filter key if the query param was provided
    filter_query = {}

    if skill:
        # Search inside the 'skills' array (case-insensitive)
        filter_query["skills"] = {"$regex": skill, "$options": "i"}

    if status:
        filter_query["status"] = status

    if location:
        filter_query["location"] = {"$regex": location, "$options": "i"}

    collection = get_applicants_collection()

    # Fetch documents from MongoDB (newest first)
    cursor = collection.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)

    # Collect all results into a list (async iteration)
    applicants = []
    async for doc in cursor:
        applicants.append(applicant_helper(doc))

    return {"total": len(applicants), "applicants": applicants}


@router.patch("/applicants/{applicant_id}", summary="Update applicant status or tags")
async def update_applicant_status(applicant_id: str, update_data: ApplicantStatusUpdate):
    """
    Updates an applicant's status and optionally their tags.

    Status workflow: applied → reviewed → contacted → placed
    """

    # Validate that the ID is a valid MongoDB ObjectId
    if not ObjectId.is_valid(applicant_id):
        raise HTTPException(status_code=400, detail="Invalid applicant ID format")

    # Build the fields to update
    update_fields = {"status": update_data.status}
    if update_data.tags is not None:
        update_fields["tags"] = update_data.tags

    collection = get_applicants_collection()

    # Update the document in MongoDB
    result = await collection.update_one(
        {"_id": ObjectId(applicant_id)},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Applicant not found")

    logger.info(f"Applicant {applicant_id} status updated to '{update_data.status}'")
    return {"message": "Applicant updated successfully", "updated_fields": update_fields}


@router.delete("/applicants/{applicant_id}", summary="Delete an applicant")
async def delete_applicant(applicant_id: str):
    """Permanently deletes an applicant record from the database."""

    if not ObjectId.is_valid(applicant_id):
        raise HTTPException(status_code=400, detail="Invalid applicant ID format")

    collection = get_applicants_collection()
    result = await collection.delete_one({"_id": ObjectId(applicant_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Applicant not found")

    logger.info(f"Applicant {applicant_id} deleted")
    return {"message": "Applicant deleted successfully"}


# ── EMPLOYER ROUTES ───────────────────────────────────────────────────────────

@router.get("/employers", summary="Get all employer requests with optional filters")
async def get_all_employers(
    status: Optional[str] = Query(None, description="Filter by status: open, in_progress, closed"),
    location: Optional[str] = Query(None, description="Filter by location"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
):
    """
    Returns a list of all employer staffing requests.
    Admin can filter by status or location.
    """

    filter_query = {}

    if status:
        filter_query["status"] = status

    if location:
        filter_query["location"] = {"$regex": location, "$options": "i"}

    collection = get_employers_collection()
    cursor = collection.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)

    employers = []
    async for doc in cursor:
        employers.append(employer_helper(doc))

    return {"total": len(employers), "employers": employers}


@router.patch("/employers/{employer_id}", summary="Update employer request status")
async def update_employer_status(employer_id: str, update_data: EmployerStatusUpdate):
    """Updates the status of an employer request."""

    if not ObjectId.is_valid(employer_id):
        raise HTTPException(status_code=400, detail="Invalid employer ID format")

    collection = get_employers_collection()
    result = await collection.update_one(
        {"_id": ObjectId(employer_id)},
        {"$set": {"status": update_data.status}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employer not found")

    logger.info(f"Employer {employer_id} status updated to '{update_data.status}'")
    return {"message": "Employer status updated successfully"}


@router.delete("/employers/{employer_id}", summary="Delete an employer request")
async def delete_employer(employer_id: str):
    """Permanently deletes an employer record."""

    if not ObjectId.is_valid(employer_id):
        raise HTTPException(status_code=400, detail="Invalid employer ID format")

    collection = get_employers_collection()
    result = await collection.delete_one({"_id": ObjectId(employer_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employer not found")

    logger.info(f"Employer {employer_id} deleted")
    return {"message": "Employer deleted successfully"}


# ── EMAIL ROUTES (Admin manually sends emails) ────────────────────────────────

class CustomEmailRequest(BaseModel):
    """Request body for sending a custom email."""
    to_email: str
    subject: str
    body_html: str


@router.post("/send-email", summary="Send a custom email to an applicant or employer")
async def admin_send_email(email_data: CustomEmailRequest):
    """
    Admin can manually send a custom HTML email to any email address.
    This is used to contact applicants or employers directly.
    """
    success = await send_email(
        to_email=email_data.to_email,
        subject=email_data.subject,
        body_html=email_data.body_html,
    )

    if not success:
        logger.error(f"Admin email failed → {email_data.to_email} | subject: {email_data.subject}")
        raise HTTPException(status_code=500, detail="Failed to send email. Check Gmail credentials.")

    logger.info(f"Admin sent email → {email_data.to_email}")
    return {"message": f"Email sent successfully to {email_data.to_email}"}


# ── DASHBOARD STATS ────────────────────────────────────────────────────────────

@router.get("/stats", summary="Get dashboard statistics")
async def get_dashboard_stats():
    """
    Returns counts for the admin dashboard.
    - Total applicants by status
    - Total employers by status
    """
    applicants_col = get_applicants_collection()
    employers_col = get_employers_collection()

    # Count applicants by each status
    applicant_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    employer_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]

    # Run aggregation queries
    # NOTE: with pymongo AsyncMongoClient, aggregate() is a coroutine.
    # You must await it first to get the cursor, then iterate.
    applicant_stats = {}
    applicant_cursor = await applicants_col.aggregate(applicant_pipeline)
    async for doc in applicant_cursor:
        applicant_stats[doc["_id"]] = doc["count"]

    employer_stats = {}
    employer_cursor = await employers_col.aggregate(employer_pipeline)
    async for doc in employer_cursor:
        employer_stats[doc["_id"]] = doc["count"]

    return {
        "applicants": {
            "applied": applicant_stats.get("applied", 0),
            "reviewed": applicant_stats.get("reviewed", 0),
            "contacted": applicant_stats.get("contacted", 0),
            "placed": applicant_stats.get("placed", 0),
            "total": sum(applicant_stats.values()),
        },
        "employers": {
            "open": employer_stats.get("open", 0),
            "in_progress": employer_stats.get("in_progress", 0),
            "closed": employer_stats.get("closed", 0),
            "total": sum(employer_stats.values()),
        },
    }
