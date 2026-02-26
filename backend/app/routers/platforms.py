"""Platforms router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Platform

router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("")
def list_platforms(db: Session = Depends(get_db)):
    """List all platforms."""
    platforms = db.query(Platform).all()
    return {"data": platforms}
