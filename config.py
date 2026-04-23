# config.py
# ─────────────────────────────────────────────────────────────────────────────
# All settings come from environment variables (or a .env file via python-dotenv).
# Never hard-code secrets here. Fill your .env file instead.
# ─────────────────────────────────────────────────────────────────────────────

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── MongoDB ──────────────────────────────────────────────────────────────
    MONGODB_URI: str
    DB_NAME: str

    # ── AWS S3 ───────────────────────────────────────────────────────────────
    # S3 is disabled for now — CVs are stored locally in uploads/cvs/
    # Uncomment these when switching to S3:
    # AWS_ACCESS_KEY_ID: str
    # AWS_SECRET_ACCESS_KEY: str
    # AWS_REGION: str = "eu-central-1"
    # S3_BUCKET_NAME: str

    # ── Gmail SMTP ───────────────────────────────────────────────────────────
    GMAIL_USER: str
    GMAIL_APP_PASSWORD: str

    # Comma-separated list of admin emails who receive new applicant/employer notifications.
    # Example: "hr@jobandu.dk,ops@jobandu.dk"
    # These are DIFFERENT from GMAIL_USER (the sending account).
    ADMIN_NOTIFICATION_EMAILS: str = "admin@jobandu.dk"

    # Optional CC list for all admin notification emails.
    # Example: "manager@jobandu.dk,ceo@jobandu.dk"
    ADMIN_CC_EMAILS: str = ""

    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str

    ALLOWED_ORIGINS: str

    class Config:
        # Load variables from a .env file in the project root
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create a single instance used everywhere in the app
settings = Settings()
