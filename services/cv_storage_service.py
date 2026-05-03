# services/cv_storage_service.py
# ─────────────────────────────────────────────────────────────────────────────
# Single entry point for CV file storage.
#
# How it works:
#   - Reads the USE_S3_STORAGE flag from config/.env
#   - If True  → uploads to Amazon S3 and returns the S3 URL
#   - If False → saves to local uploads/cvs/ folder and returns the file path
#
# To switch storage backends, just change USE_S3_STORAGE in .env — no code change needed.
# ─────────────────────────────────────────────────────────────────────────────

import aioboto3
import uuid
import os
from fastapi import UploadFile, HTTPException

from config import settings
from utils.logger import AppLogger

logger = AppLogger.get_logger()

# ── Shared validation constants ───────────────────────────────────────────────
ALLOWED_CONTENT_TYPES = [
    "application/pdf",
    "application/msword",                                                        # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
]
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB
LOCAL_UPLOAD_DIR = "uploads/cvs"


async def save_cv(file: UploadFile):
    """
    Main entry point — saves a CV file either to S3 or locally based on the flag.

    Args:
        file: The uploaded UploadFile from FastAPI

    Returns:
        tuple: (url_or_path: str, file_bytes: bytes)
            - url_or_path: S3 public URL (if S3) or local file path (if local)
            - file_bytes:  Raw file bytes — used to attach CV to emails without
                           re-reading the file or downloading it back from S3

    Raises:
        HTTPException: On invalid file type, file too large, or upload failure
    """

    # Step 1: Validate file type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF, DOC, DOCX are allowed."
        )

    # Step 2: Read file bytes into memory
    file_bytes = await file.read()

    # Step 3: Validate file size
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum allowed size is 5 MB."
        )

    # Step 4: Route to the correct backend based on the flag
    if settings.USE_S3_STORAGE:
        url = await _upload_to_s3(file, file_bytes)
    else:
        url = await _save_locally(file, file_bytes)

    # Return both the URL and the raw bytes so callers can attach the CV to emails
    return url, file_bytes


async def _upload_to_s3(file: UploadFile, file_bytes: bytes) -> str:
    """Uploads the CV to the configured S3 bucket and returns the public URL."""

    # Build a unique S3 key: cvs/uuid.pdf
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "pdf"
    s3_key = f"cvs/{uuid.uuid4()}.{ext}"

    try:
        session = aioboto3.Session()
        async with session.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        ) as s3:
            await s3.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=s3_key,
                Body=file_bytes,
                ContentType=file.content_type,
            )

        # Return the public URL
        url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
        logger.info(f"CV uploaded to S3 → {url}")
        return url

    except Exception as e:
        logger.error(f"S3 upload failed | {e}")
        raise HTTPException(status_code=500, detail="Failed to upload CV to S3.")


async def _save_locally(file: UploadFile, file_bytes: bytes) -> str:
    """Saves the CV to the local uploads/cvs/ folder and returns the file path."""

    os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "pdf"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(LOCAL_UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        logger.error(f"Local CV save failed → {file_path} | {e}")
        raise HTTPException(status_code=500, detail="Failed to save CV file.")

    logger.info(f"CV saved locally → {file_path}")
    return file_path


async def generate_s3_download_url(s3_url: str, expires_in: int = 3600) -> str:
    """
    Generates a temporary pre-signed download URL for a file stored in S3.
    The URL expires after `expires_in` seconds (default: 1 hour).

    Args:
        s3_url:     The full public S3 URL stored in MongoDB
                    e.g. "https://bucket.s3.region.amazonaws.com/cvs/uuid.pdf"
        expires_in: How long the download link is valid in seconds

    Returns:
        str: A pre-signed URL that allows temporary download without credentials

    Raises:
        HTTPException: If S3 is not configured or URL is invalid
    """

    if not settings.USE_S3_STORAGE:
        raise HTTPException(
            status_code=400,
            detail="S3 storage is not enabled. File is stored locally."
        )

    # Extract the S3 key from the full URL
    # URL format: https://bucket-name.s3.region.amazonaws.com/cvs/uuid.pdf
    # We need just: cvs/uuid.pdf
    try:
        # Split on ".amazonaws.com/" and take everything after it
        s3_key = s3_url.split(".amazonaws.com/", 1)[1]
    except (IndexError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid S3 URL format.")

    try:
        session = aioboto3.Session()
        async with session.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        ) as s3:
            download_url = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET_NAME, "Key": s3_key},
                ExpiresIn=expires_in,
            )

        return download_url

    except Exception as e:
        logger.error(f"Pre-signed URL generation failed | key={s3_key} | {e}")
        raise HTTPException(status_code=500, detail="Could not generate download URL.")
