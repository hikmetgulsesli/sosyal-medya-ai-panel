from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.db.database import engine, Base
from app.routers import auth, scraping, competitors, platforms, api_keys, ai_generation, analytics, scheduler
from app.routers.scraping import scrape_router
from app.services.scheduler_service import start_scheduler_worker, stop_scheduler_worker

settings = get_settings()

app = FastAPI(
    title="Social Media AI Panel API",
    description="API for Social Media AI Panel - Scraping and AI-powered content management",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(scraping.router, prefix="/api")
app.include_router(scrape_router, prefix="/api")
app.include_router(competitors.router, prefix="/api")
app.include_router(platforms.router, prefix="/api")
app.include_router(api_keys.router, prefix="/api")
app.include_router(ai_generation.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(scheduler.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Create database tables and start scheduler worker on startup."""
    # Skip table creation in test environment
    if settings.environment != "test":
        Base.metadata.create_all(bind=engine)
        # Start the scheduler background worker
        await start_scheduler_worker()


@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler worker on shutdown."""
    await stop_scheduler_worker()


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Social Media AI Panel API",
        "docs": "/docs",
        "version": "0.1.0"
    }
