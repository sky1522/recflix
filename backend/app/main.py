"""
RecFlix FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.exceptions import AppException
from app.core.rate_limit import limiter

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from app.api.v1.router import api_router
from app.database import Base, engine
from app.models import *  # noqa: F401, F403 - Import all models for table creation

# --- Sentry initialization (skip if DSN is empty) ---
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=settings.APP_ENV,
        send_default_pii=False,
    )
    logger.info("Sentry initialized (env=%s)", settings.APP_ENV)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Environment: %s", settings.APP_ENV)
    logger.info("Database: %s", "connected" if settings.DATABASE_URL else "NOT SET")
    logger.info("Redis: %s", "enabled" if settings.REDIS_URL else "disabled")
    logger.info("Sentry: %s", "enabled" if settings.SENTRY_DSN else "disabled")
    logger.info("Weather API: %s", "enabled" if settings.WEATHER_API_KEY else "disabled")
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    description="Context-Aware Personalized Movie Recommendation Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate Limiter
app.state.limiter = limiter

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Global exception handlers (unified {error, message} format) ---

@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    """Handle custom AppException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error, "message": exc.message},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Wrap FastAPI HTTPException in unified format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail if isinstance(exc.detail, str) else "HTTP_ERROR", "message": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Handle request validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "요청 데이터가 올바르지 않습니다",
            "detail": exc.errors() if settings.DEBUG else None,
        },
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc: RateLimitExceeded):
    """Handle rate limit exceeded with unified format."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "RATE_LIMIT_EXCEEDED",
            "message": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    sentry_sdk.capture_exception(exc)
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "서버 내부 오류가 발생했습니다",
        },
    )


# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to RecFlix API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
