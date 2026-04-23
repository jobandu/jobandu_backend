# main.py

import ssl

# Must be before ALL other imports
_orig = ssl.create_default_context
def _patched(*args, **kwargs):
    ctx = _orig(*args, **kwargs)
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    return ctx
ssl.create_default_context = _patched


import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from config import settings
from db.db_helper import client as mongo_client
from api.applicant_routes import router as applicant_router
from api.employer_routes import router as employer_router
from api.admin_routes import router as admin_router
from utils.logger import AppLogger


logger = AppLogger.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Jobandu backend starting up...")

    # Test MongoDB connection
    try:
        await mongo_client.admin.command("ping")
        logger.info("✅ Connected to MongoDB Atlas successfully")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")

    yield  # The app runs here

    logger.info("🛑 Shutting down — closing MongoDB connection...")
    mongo_client.close()


# ── Create FastAPI app ────────────────────────────────────────────────────────
app = FastAPI(
    title="Jobandu API",
    description=(
        "Backend API for Jobandu recruitment platform. "
        "Employees submit applications, employers submit staffing requests, "
        "and admins manage everything from the admin panel."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI available at /docs
    redoc_url="/redoc",     # ReDoc available at /redoc
    lifespan=lifespan,
)


# CORS Middleware 
# CORS = Cross-Origin Resource Sharing.
# This allows your frontend (running on a different port/domain) to talk to this API.
#
# ALLOWED_ORIGINS in .env should be a comma-separated list of frontend URLs.
# Example: "http://localhost:3000,https://jobandu.dk"
allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Only these origins are allowed
    allow_credentials=True,              # Allow cookies / Authorization headers
    allow_methods=["*"],                 # Allow GET, POST, PATCH, DELETE, etc.
    allow_headers=["*"],                 # Allow all headers (Content-Type, Authorization, etc.)
)


# Request Logging Middleware
# Logs every incoming request with method, URL, and response time.
# This helps you debug and monitor the API.
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware that runs for EVERY request.
    Logs: method, path, status code, and how long it took.
    """
    start_time = time.time()

    # Process the request (passes it to the actual route handler)
    response = await call_next(request)

    # Calculate how long the request took
    process_time_ms = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({process_time_ms}ms)"
    )

    # Add the processing time to response headers (useful for debugging)
    response.headers["X-Process-Time-Ms"] = str(process_time_ms)

    return response


# Global Exception Handler
# If an unexpected error happens, return a clean JSON response instead of crashing.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# Include each router — all their routes will be added to the app
app.include_router(applicant_router)
app.include_router(employer_router)
app.include_router(admin_router)


# Root Health Check
@app.get("/", tags=["Health"])
async def root():
    """Simple health check endpoint — useful for monitoring."""
    return {
        "status": "ok",
        "service": "Jobandu API",
        "version": "1.0.0",
        "docs": "/docs",
    }

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="[IP_ADDRESS]", port=8000, reload=True)
