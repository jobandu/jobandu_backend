# models/site_content_model.py
# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models for site content that admin can edit and public can view.
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


class ContactInfo(BaseModel):
    """
    Company contact details shown on the website.
    """
    company_name: str = Field(..., description="Name of the company, e.g. Jobandu GmbH")
    street: str = Field(..., description="Street and building number")
    zip_code: str = Field(..., description="ZIP code")
    city: str = Field(..., description="City")
    country: Optional[str] = Field(None, description="Country (optional)")
    phone: str = Field(..., description="Phone number")
    email: EmailStr = Field(..., description="Contact email address")


class TeamMember(BaseModel):
    """
    Team member details.
    """
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the team member")
    role: str = Field(..., description="Role/Position, e.g. Sales, Recruiting, Managing Director")
    department: str = Field(..., description="Department name, e.g. Sales, Recruiting, Customer Support")
    phone: Optional[str] = Field(None, description="Direct phone number (optional)")
    email: EmailStr = Field(..., description="Direct email address")


class TeamMemberUpdate(BaseModel):
    """
    Used for updating team member details. All fields are optional.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[str] = Field(None)
    department: Optional[str] = Field(None)
    phone: Optional[str] = Field(None)
    email: Optional[EmailStr] = Field(None)


class JobOpening(BaseModel):
    """
    Job opening details.
    """
    title: str = Field(..., description="Job title, e.g. Forklift Operator (m/f/d)")
    location: str = Field(..., description="Location of the job, e.g. Hamburg")
    apply_url: Optional[str] = Field(None, description="External/internal URL to apply (optional)")
    is_active: bool = Field(True, description="Whether the job opening is currently active/visible")


class JobOpeningUpdate(BaseModel):
    """
    Used for updating job opening details. All fields are optional.
    """
    title: Optional[str] = Field(None)
    location: Optional[str] = Field(None)
    apply_url: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)
