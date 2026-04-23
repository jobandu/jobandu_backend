# models/employer_model.py
# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models for employers (companies requesting staff).
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


class EmployerCreate(BaseModel):
    """
    Data that the employer (company) fills in on the form
    when they need to hire workers.
    """
    company_name: str = Field(..., min_length=2, max_length=200)
    contact_person: str = Field(..., min_length=2, max_length=100, description="Name of the person to contact")
    email: EmailStr
    phone: str = Field(..., min_length=5, max_length=20)
    requirements: List[str] = Field(..., description="Type of workers needed, e.g. ['driver', 'packer']")
    location: str = Field(..., description="City or country where workers are needed")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Extra notes or requirements")


class EmployerStatusUpdate(BaseModel):
    """
    Used by admin to update the status of an employer request.
    """
    status: str = Field(
        ...,
        pattern="^(open|in_progress|closed)$",
        description="New status for the employer request"
    )


class EmployerResponse(BaseModel):
    """
    Data sent back to client when returning employer info.
    """
    id: str
    company_name: str
    contact_person: str
    email: str
    phone: str
    requirements: List[str]
    location: str
    notes: Optional[str] = None
    status: str
    created_at: datetime
