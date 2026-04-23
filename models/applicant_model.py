# models/applicant_model.py
# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models define what data looks like going IN and OUT of the API.
# Think of these as the "shape" of your data.
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


class ApplicantCreate(BaseModel):
    """
    Data that the employee (applicant) fills in on the form.
    CV file is uploaded separately and its S3 URL is attached later.
    """
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: str = Field(..., min_length=5, max_length=20, description="Phone number with country code")
    skills: List[str] = Field(..., description="List of skills, e.g. ['driver', 'warehouse']")
    experience_years: int = Field(..., ge=0, description="Total years of experience")
    location: str = Field(..., description="Current city or country")


class ApplicantStatusUpdate(BaseModel):
    """
    Used by admin to update the status of an applicant.
    Workflow: applied → reviewed → contacted → placed
    """
    status: str = Field(
        ...,
        pattern="^(applied|reviewed|contacted|placed)$",
        description="New status for the applicant"
    )
    # Admin can also add tags like 'urgent'
    tags: Optional[List[str]] = Field(default=None)


class ApplicantResponse(BaseModel):
    """
    Data sent back to the client (API response).
    We convert MongoDB's _id to a string 'id' field.
    """
    id: str
    name: str
    email: str
    phone: str
    skills: List[str]
    experience_years: int
    location: str
    cv_url: Optional[str] = None   # S3 link to uploaded CV
    status: str
    tags: List[str]
    created_at: datetime
