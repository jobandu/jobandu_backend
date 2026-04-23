# api/applicant_routes.py
# ─────────────────────────────────────────────────────────────────────────────
# Public routes for applicants (employees looking for jobs).
# No authentication required — anyone can submit a form.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from typing import List, Optional
import json

from db.db_helper import get_applicants_collection
from models.applicant_model import ApplicantResponse
from schemas.applicant_schema import applicant_helper
# TODO: swap this import with s3_service.upload_cv_to_s3 when S3 is ready
from services.local_storage_service import save_cv_locally
from services.email_service import (
    send_applicant_confirmation,
    send_admin_notification_new_applicant,
)
from utils.logger import AppLogger

logger = AppLogger.get_logger()

# Create a router — this is like a mini app that handles only applicant routes
router = APIRouter(
    prefix="/api/applicants",
    tags=["Applicants"],   # Groups these endpoints in the auto-generated docs
)


@router.post("/", summary="Submit a job application")
async def create_applicant(
    # Form fields — sent as multipart/form-data (because we also accept a file)
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    skills: List[str] = Form(..., description="JSON array string, e.g. '[\"driver\",\"warehouse\"]'"),
    experience_years: int = Form(...),
    location: str = Form(...),
    # CV file is optional — the user may not have a digital CV
    cv: Optional[UploadFile] = File(None),
):
    """
    Public endpoint for employees to submit their job application.

    - Accepts form data + optional CV file
    - Saves CV to local folder (if provided) — will move to S3 later
    - Saves applicant data to MongoDB
    - Sends confirmation email to applicant
    - Sends notification email to admin
    """

    # Parse the skills JSON string into a Python list
    # Frontend should send: skills='["driver","warehouse"]'
    try:
        skills_list: List[str] = skills
        if not isinstance(skills_list, list):
            raise ValueError("skills must be a JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Invalid skills input from {email}: {e}")
        raise HTTPException(status_code=400, detail="Invalid skills format. Send a JSON array like '[\"driver\"]'")

    # Save CV to local folder if a file was provided
    cv_url = None
    if cv is not None:
        cv_url = await save_cv_locally(cv)

    # Build the document to save in MongoDB
    applicant_doc = {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills_list,
        "experience_years": experience_years,
        "location": location,
        "cv_url": cv_url,          # local file path or None (later: S3 URL)
        "status": "applied",       # Default starting status
        "tags": [],                # Admin can add tags later
        "created_at": datetime.now(timezone.utc),
    }

    # Save to MongoDB (async insert)
    collection = get_applicants_collection()
    result = await collection.insert_one(applicant_doc)

    logger.info(f"New applicant: {name} ({email}) | id={result.inserted_id}")

    # Send confirmation to applicant — CV is attached so they have a copy
    await send_applicant_confirmation(
        applicant_name=name,
        applicant_email=email,
        cv_path=cv_url,
    )

    # Notify admin team — CV is attached + full details included
    await send_admin_notification_new_applicant(
        applicant_name=name,
        applicant_email=email,
        applicant_phone=phone,
        applicant_skills=skills_list,
        applicant_location=location,
        applicant_experience_years=experience_years,
        cv_path=cv_url,
    )

    return JSONResponse(
        status_code=201,
        content={
            "message": "Application submitted successfully. We will contact you soon!",
            "id": str(result.inserted_id),
        }
    )
