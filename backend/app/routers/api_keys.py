"""API Keys router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("")
def list_api_keys(db: Session = Depends(get_db)):
    """List API keys."""
    return {"data": []}


@router.post("")
def create_api_key(db: Session = Depends(get_db)):
    """Create API key."""
    return {"data": {}}
