# schemas/employer_schema.py
# ─────────────────────────────────────────────────────────────────────────────
# Schema helper converts raw MongoDB employer document into a clean dict.
# ─────────────────────────────────────────────────────────────────────────────


def employer_helper(employer: dict) -> dict:
    """
    Takes a raw MongoDB document for an employer and returns a clean dict.
    
    Example input from MongoDB:
        {"_id": ObjectId("xyz789"), "company_name": "ABC Logistics", ...}
    
    Example output:
        {"id": "xyz789", "company_name": "ABC Logistics", ...}
    """
    return {
        "id": str(employer["_id"]),           # Convert ObjectId → string
        "company_name": employer["company_name"],
        "contact_person": employer["contact_person"],
        "email": employer["email"],
        "phone": employer["phone"],
        "requirements": employer.get("requirements", []),
        "location": employer.get("location", ""),
        "notes": employer.get("notes"),
        "status": employer.get("status", "open"),
        "created_at": employer.get("created_at"),
    }
