# services/local_storage_service.py
# ─────────────────────────────────────────────────────────────────────────────
# Saves CV files to a local folder on the server.
# This is a temporary solution — later we will swap this with s3_service.py
# by just changing one import line in applicant_routes.py.
# ─────────────────────────────────────────────────────────────────────────────

import uuid
import os
from fastapi import UploadFile, HTTPException
from utils.logger import AppLogger

logger = AppLogger.get_logger()

# Folder where CVs will be stored (created automatically if it doesn't exist)
UPLOAD_DIR = "uploads/cvs"

# Allowed file types for CV uploads
ALLOWED_CONTENT_TYPES = [
    "application/pdf",
    "application/msword",                                                        # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
]

# Max file size: 5 MB
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


async def save_cv_locally(file: UploadFile) -> str:
    """
    Saves an uploaded CV file to the local 'uploads/cvs/' folder.

    Args:
        file: The uploaded file from FastAPI (UploadFile object)

    Returns:
        str: The file path where the CV was saved, e.g. "uploads/cvs/abc123.pdf"

    Raises:
        HTTPException: If file type is invalid or file is too large
    """

    # Check if file type is allowed
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only PDF, DOC, DOCX are allowed."
        )

    # Read file content into memory
    file_content = await file.read()

    # Check file size
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 5 MB."
        )

    # Create the upload folder if it doesn't exist yet
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Give the file a unique name so two people with "cv.pdf" don't clash
    extension = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "pdf"
    unique_filename = f"{uuid.uuid4()}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Write the file to disk
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        logger.error(f"CV save failed → {file_path} | {e}")
        raise HTTPException(status_code=500, detail="Failed to save CV file.")

    logger.info(f"CV saved → {file_path}")
    return file_path  # e.g. "uploads/cvs/550e8400-....pdf"
