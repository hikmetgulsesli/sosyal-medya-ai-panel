"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.database import engine, Base
from app.routers import auth, users, platforms, competitors, api_keys, scraping

settings = get_settings()

app = FastAPI(
    title="Social Media AI Panel API",
    description="API for Social Media AI Panel - Scraping and AI-powered content management",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_tables():
    """Create database tables on startup."""
    # Only create tables if not in test mode (test uses in-memory SQLite)
    if "sqlite" not in str(engine.url):
        Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Social Media AI Panel API", "docs": "/docs"}


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(platforms.router, prefix="/api/platforms", tags=["platforms"])
app.include_router(competitors.router, prefix="/api/competitors", tags=["competitors"])
app.include_router(api_keys.router, prefix="/api/api-keys", tags=["api-keys"])
app.include_router(scraping.router, prefix="/api/scraping", tags=["scraping"])
