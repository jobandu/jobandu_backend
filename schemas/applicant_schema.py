# schemas/applicant_schema.py
# ─────────────────────────────────────────────────────────────────────────────
# Schema helpers convert raw MongoDB documents (dicts with ObjectId) into
# clean Python dicts that our Pydantic models can work with.
#
# MongoDB stores _id as ObjectId type. JSON doesn't understand ObjectId,
# so we convert it to a plain string.
# ─────────────────────────────────────────────────────────────────────────────


def applicant_helper(applicant: dict) -> dict:
    """
    Takes a raw MongoDB document for an applicant and returns a clean dict.
    
    Example input from MongoDB:
        {"_id": ObjectId("abc123"), "name": "Rahul", ...}
    
    Example output:
        {"id": "abc123", "name": "Rahul", ...}
    """
    return {
        "id": str(applicant["_id"]),         # Convert ObjectId → string
        "name": applicant["name"],
        "email": applicant["email"],
        "phone": applicant["phone"],
        "skills": applicant.get("skills", []),
        "experience_years": applicant.get("experience_years", 0),
        "location": applicant.get("location", ""),
        "cv_url": applicant.get("cv_url"),    # May be None if no CV uploaded yet
        "status": applicant.get("status", "applied"),
        "tags": applicant.get("tags", []),
        "created_at": applicant.get("created_at"),
    }
