# api/site_content_routes.py
# ─────────────────────────────────────────────────────────────────────────────
# Publicly accessible routes to fetch dynamic site content (Contact, Team, Jobs).
# No authentication required.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from db.db_helper import get_contact_collection, get_team_collection, get_jobs_collection
from schemas.site_content_schema import contact_helper, team_helper, job_helper

router = APIRouter(
    prefix="/api/content",
    tags=["Public Content"],
)


@router.get("/contact", summary="Get company contact details")
async def get_contact_info():
    """
    Returns the company's contact details (address, phone, email, etc.).
    If no contact document is initialized in the database, returns an empty template.
    """
    collection = get_contact_collection()
    doc = await collection.find_one()
    if not doc:
        # Return a clean empty template instead of raising 404
        return {
            "id": None,
            "company_name": "",
            "street": "",
            "zip_code": "",
            "city": "",
            "country": "",
            "phone": "",
            "email": ""
        }
    return contact_helper(doc)


@router.get("/team", summary="Get all team members")
async def get_team(
    department: Optional[str] = Query(None, description="Filter team members by department, e.g. Sales")
):
    """
    Returns a list of all team members, optionally filtered by department.
    """
    filter_query = {}
    if department:
        filter_query["department"] = {"$regex": department, "$options": "i"}

    collection = get_team_collection()
    cursor = collection.find(filter_query)
    
    team_members = []
    async for doc in cursor:
        team_members.append(team_helper(doc))
    
    return team_members


@router.get("/jobs", summary="Get active job openings")
async def get_jobs():
    """
    Returns a list of all currently active job openings.
    """
    collection = get_jobs_collection()
    cursor = collection.find({"is_active": True})
    
    jobs = []
    async for doc in cursor:
        jobs.append(job_helper(doc))
    
    return jobs
