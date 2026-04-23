# api/employer_routes.py
# ─────────────────────────────────────────────────────────────────────────────
# Public routes for employers (companies looking to hire workers).
# No authentication required — anyone can submit a staffing request.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from typing import List
import json

from db.db_helper import get_employers_collection
from models.employer_model import EmployerCreate
from services.email_service import (
    send_employer_confirmation,
    send_admin_notification_new_employer,
)
from utils.logger import AppLogger

logger = AppLogger.get_logger()

# Create a router for employer-related endpoints
router = APIRouter(
    prefix="/api/employers",
    tags=["Employers"],
)


@router.post("/", summary="Submit a staff request")
async def create_employer(employer_data: EmployerCreate):
    """
    Public endpoint for companies to submit a staffing request.

    - Accepts JSON body with company details and requirements
    - Saves the request to MongoDB
    - Sends confirmation email to the employer
    - Sends notification email to admin
    """

    # Build the MongoDB document
    employer_doc = {
        "company_name": employer_data.company_name,
        "contact_person": employer_data.contact_person,
        "email": employer_data.email,
        "phone": employer_data.phone,
        "requirements": employer_data.requirements,
        "location": employer_data.location,
        "notes": employer_data.notes,
        "status": "open",          # Default starting status
        "created_at": datetime.now(timezone.utc),
    }

    # Save to MongoDB
    collection = get_employers_collection()
    result = await collection.insert_one(employer_doc)

    logger.info(f"New employer: {employer_data.company_name} ({employer_data.email}) | id={result.inserted_id}")

    await send_employer_confirmation(
        contact_person=employer_data.contact_person,
        employer_email=employer_data.email,
        company_name=employer_data.company_name,
    )
    await send_admin_notification_new_employer(
        company_name=employer_data.company_name,
        contact_person=employer_data.contact_person,
        contact_email=employer_data.email,
        contact_phone=employer_data.phone,
        requirements=employer_data.requirements,
        location=employer_data.location,
        notes=employer_data.notes or "",
    )

    return JSONResponse(
        status_code=201,
        content={
            "message": "Your staff request has been received. We will contact you shortly!",
            "id": str(result.inserted_id),
        }
    )
