from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, CompetitorProfile, Platform
from app.schemas.schemas import CompetitorProfileCreate, CompetitorProfileResponse

router = APIRouter(prefix="/competitors", tags=["competitors"])


@router.get("/", response_model=List[CompetitorProfileResponse])
def list_competitors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all competitor profiles for the current user."""
    competitors = db.query(CompetitorProfile).filter(
        CompetitorProfile.user_id == current_user.id
    ).all()
    return competitors


@router.post("/", response_model=CompetitorProfileResponse, status_code=status.HTTP_201_CREATED)
def create_competitor(
    competitor_data: CompetitorProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new competitor profile."""
    # Verify platform exists
    platform = db.query(Platform).filter(Platform.id == competitor_data.platform_id).first()
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform not found"
        )
    
    db_competitor = CompetitorProfile(
        user_id=current_user.id,
        platform_id=competitor_data.platform_id,
        username=competitor_data.username,
        display_name=competitor_data.display_name,
        profile_url=competitor_data.profile_url
    )
    db.add(db_competitor)
    db.commit()
    db.refresh(db_competitor)
    
    return db_competitor


@router.get("/{competitor_id}", response_model=CompetitorProfileResponse)
def get_competitor(
    competitor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific competitor profile."""
    competitor = db.query(CompetitorProfile).filter(
        CompetitorProfile.id == competitor_id,
        CompetitorProfile.user_id == current_user.id
    ).first()
    
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor profile not found"
        )
    
    return competitor


@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_competitor(
    competitor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a competitor profile."""
    competitor = db.query(CompetitorProfile).filter(
        CompetitorProfile.id == competitor_id,
        CompetitorProfile.user_id == current_user.id
    ).first()
    
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor profile not found"
        )
    
    db.delete(competitor)
    db.commit()
    
    return None
