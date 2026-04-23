# services/s3_service.py
# ─────────────────────────────────────────────────────────────────────────────
# Handles uploading CV files to Amazon S3.
# We use aioboto3 for async uploads so the API stays non-blocking.
# ─────────────────────────────────────────────────────────────────────────────

import aioboto3
import uuid
from fastapi import UploadFile, HTTPException
from config import settings

# Allowed file types for CV uploads
ALLOWED_CONTENT_TYPES = [
    "application/pdf",
    "application/msword",                                                    # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # .docx
]

# Maximum file size: 5 MB
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


async def upload_cv_to_s3(file: UploadFile) -> str:
    """
    Uploads a CV file to the configured S3 bucket.

    Steps:
    1. Validate file type (only PDF, DOC, DOCX allowed)
    2. Read file content
    3. Validate file size (max 5 MB)
    4. Upload to S3 with a unique filename
    5. Return the public S3 URL

    Args:
        file: The uploaded file from FastAPI (UploadFile object)

    Returns:
        str: The public S3 URL of the uploaded file

    Raises:
        HTTPException: If the file type is invalid or file is too large
    """

    # Step 1: Check file type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Only PDF, DOC, DOCX are allowed."
        )

    # Step 2: Read the file content into memory
    file_content = await file.read()

    # Step 3: Check file size
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum allowed size is 5 MB."
        )

    # Step 4: Create a unique filename to avoid overwriting files
    # Example filename: cvs/550e8400-e29b-41d4-a716-446655440000.pdf
    file_extension = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "pdf"
    unique_filename = f"cvs/{uuid.uuid4()}.{file_extension}"

    # Step 5: Upload to S3 using aioboto3 (async)
    session = aioboto3.Session()
    async with session.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    ) as s3_client:
        await s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=unique_filename,
            Body=file_content,
            ContentType=file.content_type,
        )

    # Build and return the public URL
    # Format: https://bucket-name.s3.region.amazonaws.com/cvs/uuid.pdf
    s3_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_filename}"
    return s3_url
