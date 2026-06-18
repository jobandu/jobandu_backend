# schemas/site_content_schema.py
# ─────────────────────────────────────────────────────────────────────────────
# Schema helpers to serialize MongoDB documents for site content.
# ─────────────────────────────────────────────────────────────────────────────

def contact_helper(contact: dict) -> dict:
    """
    Serializes a site_contact document.
    Since there is only one contact document, we can return a serialized dictionary.
    """
    return {
        "id": str(contact["_id"]) if "_id" in contact else None,
        "company_name": contact.get("company_name", ""),
        "street": contact.get("street", ""),
        "zip_code": contact.get("zip_code", ""),
        "city": contact.get("city", ""),
        "country": contact.get("country"),
        "phone": contact.get("phone", ""),
        "email": contact.get("email", ""),
    }


def team_helper(member: dict) -> dict:
    """
    Serializes a site_team document.
    """
    return {
        "id": str(member["_id"]),
        "name": member.get("name", ""),
        "role": member.get("role", ""),
        "department": member.get("department", ""),
        "phone": member.get("phone"),
        "email": member.get("email", ""),
    }


def job_helper(job: dict) -> dict:
    """
    Serializes a site_jobs document.
    """
    return {
        "id": str(job["_id"]),
        "title": job.get("title", ""),
        "location": job.get("location", ""),
        "apply_url": job.get("apply_url"),
        "is_active": job.get("is_active", True),
    }
