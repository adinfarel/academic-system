"""
main.py — Entry point for the PolsriEduAI application

The FastAPI app is created here. All routers are registered here.
Run with: uvicorn backend.main:app --reload
"""

from backend.utils.logger import get_logger

# LOGGER
logger = get_logger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from backend.config import get_settings
from backend.database import check_db_connection, engine, Base
from backend.models import User, Mahasiswa, Dosen, Absensi
from backend.routers import auth, absensi, ai_agent, academic

settings = get_settings()

# LIFESPAN
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler — code that runs when the app START and STOP.

    Section before 'yield' = startup:
    - Check database connection
    - Create table if it doesn't exist (development only)

    Section after 'yield' = shutdown:
    - Cleanup resources if necessary
    """
    # STARTUP
    logger.info(f"[APP STARTUP] {settings.APP_NAME} v{settings.APP_VERSION} is starting...")
    
    if check_db_connection():
        logger.info("[APP STARTUP] Database connection successfully.")
    else:
        logger.warning("[APP STARTUP] Database connection failed. The app may not function properly.")
    
    
    if settings.DEBUG:
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created")
    
    yield
    
    # SHUTDOWN
    logger.info(f"[APP SHUTDOWN] {settings.APP_NAME} is shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    description="Integrated Academic System - Computer Vision & AI Agent",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://academic-system.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============
# ENDPOINTS
# ===============

# 1. Health Check
@app.get("/", tags=["Health"])
def root():
    """
    Health check endpoint.
    If this return OK, the server is running and can accept requests.
    """
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }

@app.get("/health", tags=["Health"])
def health_check():
    """
    Check all status components system
    Useful for monitoring and debugging early
    """
    db_ok = check_db_connection()
    
    return {
        "status": "healthy" if db_ok else "degraded",
        "components": {
            "database": "ok" if db_ok else "error",
            "api": "ok"
        }
    }

# 2. Routes 
# AUTH
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Auth"],
)

# ABSENCE
app.include_router(
    absensi.router,
    prefix="/api/v1/absence",
    tags=["Absence"],
)

# AGENTS
app.include_router(
    ai_agent.router,
    prefix="/api/v1/agent",
    tags=["Agents"]
)

# ACADEMIC
app.include_router(
    academic.router,
    prefix="/api/v1/academic",
    tags=["Academic"]
)

# MOUNT
app.mount("/static", StaticFiles(directory="frontend/assets"), name="static")

# Serve frontend HTML pages
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")