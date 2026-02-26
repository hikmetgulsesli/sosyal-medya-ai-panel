"""Competitor service for business logic."""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import CompetitorProfile, Platform as PlatformModel
from app.schemas.competitor import CompetitorCreate, CompetitorUpdate
from app.core.constants import Platform


class CompetitorService:
    """Service for competitor operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        platform: Optional[Platform] = None
    ) -> Tuple[List[CompetitorProfile], int]:
        """Get all competitors with optional filtering."""
        query = self.db.query(CompetitorProfile)
        
        if platform:
            # Convert Platform enum to platform_id lookup
            platform_record = self.db.query(PlatformModel).filter(
                PlatformModel.name == platform.value
            ).first()
            if platform_record:
                query = query.filter(CompetitorProfile.platform_id == platform_record.id)
        
        total = query.count()
        competitors = query.offset(skip).limit(limit).all()
        
        return competitors, total
    
    def get_by_id(self, competitor_id: str) -> Optional[CompetitorProfile]:
        """Get competitor by ID."""
        return self.db.query(CompetitorProfile).filter(
            CompetitorProfile.id == competitor_id
        ).first()
    
    def create(self, competitor_data: CompetitorCreate) -> CompetitorProfile:
        """Create a new competitor."""
        # Check for duplicate handle + platform combination
        platform_record = self.db.query(PlatformModel).filter(
            PlatformModel.name == competitor_data.platform.value
        ).first()
        
        if not platform_record:
            raise ValueError(f"Platform {competitor_data.platform.value} not found")
        
        existing = self.db.query(CompetitorProfile).filter(
            CompetitorProfile.username == competitor_data.handle,
            CompetitorProfile.platform_id == platform_record.id
        ).first()
        
        if existing:
            raise ValueError(
                f"Competitor with handle '{competitor_data.handle}' already exists for platform {competitor_data.platform.value}"
            )
        
        db_competitor = CompetitorProfile(
            user_id=None,  # Will be set from auth context
            platform_id=platform_record.id,
            username=competitor_data.handle,
            display_name=competitor_data.name,
            profile_url=str(competitor_data.url),
            bio=competitor_data.description,
            is_active=True
        )
        
        self.db.add(db_competitor)
        self.db.commit()
        self.db.refresh(db_competitor)
        
        return db_competitor
    
    def update(
        self, 
        competitor_id: str, 
        competitor_data: CompetitorUpdate
    ) -> Optional[CompetitorProfile]:
        """Update an existing competitor."""
        competitor = self.get_by_id(competitor_id)
        if not competitor:
            return None
        
        update_data = competitor_data.model_dump(exclude_unset=True)
        
        # Map schema fields to model fields
        field_mapping = {
            'name': 'display_name',
            'handle': 'username',
            'url': 'profile_url',
            'description': 'bio'
        }
        
        for schema_field, value in update_data.items():
            model_field = field_mapping.get(schema_field, schema_field)
            if hasattr(competitor, model_field):
                setattr(competitor, model_field, value)
        
        self.db.commit()
        self.db.refresh(competitor)
        
        return competitor
    
    def delete(self, competitor_id: str) -> bool:
        """Delete a competitor."""
        competitor = self.get_by_id(competitor_id)
        if not competitor:
            return False
        
        self.db.delete(competitor)
        self.db.commit()
        
        return True
