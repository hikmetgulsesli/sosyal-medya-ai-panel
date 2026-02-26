"""AI content generation router."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import re

from app.db.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, ContentTemplate, AIGenerationLog
from app.schemas.ai import (
    PostGenerateRequest,
    PostGenerateResponse,
    ThreadGenerateRequest,
    ThreadGenerateResponse,
    HashtagSuggestRequest,
    HashtagSuggestResponse,
    ContentTemplateCreate,
    ContentTemplateUpdate,
    ContentTemplateResponse,
    ContentTemplateListResponse,
    AIGenerationLogResponse,
    AIGenerationLogListResponse,
    AIProviderStatus
)
from app.services.ai_service import ai_service, AIService

router = APIRouter(prefix="/ai", tags=["ai"])


def get_ai_service() -> AIService:
    """Dependency to get AI service instance."""
    return ai_service


@router.get("/status", response_model=AIProviderStatus)
async def get_ai_status(
    current_user: User = Depends(get_current_user)
):
    """Get AI provider status and availability."""
    providers = ai_service.get_available_providers()
    return AIProviderStatus(
        providers=providers,
        primary="minimax" if "minimax" in providers else "openai" if "openai" in providers else "none",
        fallback="openai" if "openai" in providers else "none"
    )


@router.post("/generate/post", response_model=PostGenerateResponse)
async def generate_post(
    request: PostGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a single social media post using AI."""
    
    # Check if template is specified
    template_prompt = None
    if request.template_id:
        template = db.query(ContentTemplate).filter(
            ContentTemplate.id == request.template_id,
            (ContentTemplate.user_id == current_user.id) | (ContentTemplate.is_system == True),
            ContentTemplate.is_active == True
        ).first()
        
        if template:
            template_prompt = template.template_prompt
            # Update usage count
            template.usage_count += 1
            db.commit()
    
    # Build the prompt
    if template_prompt:
        prompt = f"{template_prompt}\n\nTopic: {request.topic}"
        if request.context:
            prompt += f"\nContext: {request.context}"
    else:
        prompt = request.topic
    
    # Generate content
    response = await ai_service.generate_post(
        topic=prompt,
        tone=request.tone,
        platform=request.platform,
        max_length=request.max_length,
        context=request.context
    )
    
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI generation failed: {response.error}"
        )
    
    # Log the generation
    log = AIGenerationLog(
        user_id=current_user.id,
        generation_type="post",
        platform=request.platform,
        prompt=request.topic,
        generated_content=response.content,
        provider_used=response.provider,
        tokens_used=response.tokens_used,
        tone=request.tone,
        template_id=request.template_id
    )
    db.add(log)
    db.commit()
    
    return PostGenerateResponse(
        content=response.content,
        provider=response.provider,
        tokens_used=response.tokens_used,
        character_count=len(response.content),
        platform=request.platform,
        tone=request.tone
    )


@router.post("/generate/thread", response_model=ThreadGenerateResponse)
async def generate_thread(
    request: ThreadGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a Twitter/X thread using AI."""
    
    response = await ai_service.generate_thread(
        topic=request.topic,
        tone=request.tone,
        num_posts=request.num_posts,
        context=request.context
    )
    
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI generation failed: {response.error}"
        )
    
    # Parse thread posts from response
    content = response.content
    posts = []
    for line in content.split('\n'):
        line = line.strip()
        # Remove numbering like "1.", "2.", etc.
        if line and not line.startswith('#'):
            # Remove leading numbers and dots
            line = re.sub(r'^\d+[.\)]\s*', '', line)
            if line:
                posts.append(line)
    
    # If no posts parsed, split by double newline
    if not posts:
        posts = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    # Log the generation
    log = AIGenerationLog(
        user_id=current_user.id,
        generation_type="thread",
        platform="twitter",
        prompt=request.topic,
        generated_content=response.content,
        provider_used=response.provider,
        tokens_used=response.tokens_used,
        tone=request.tone
    )
    db.add(log)
    db.commit()
    
    return ThreadGenerateResponse(
        posts=posts,
        provider=response.provider,
        tokens_used=response.tokens_used,
        post_count=len(posts),
        platform="twitter",
        tone=request.tone
    )


@router.post("/suggest/hashtags", response_model=HashtagSuggestResponse)
async def suggest_hashtags(
    request: HashtagSuggestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Suggest relevant hashtags for content using AI."""
    
    response = await ai_service.suggest_hashtags(
        content=request.content,
        platform=request.platform,
        count=request.count
    )
    
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI generation failed: {response.error}"
        )
    
    # Parse hashtags from response
    hashtags = []
    content_clean = response.content.strip()
    
    # Extract hashtags
    hashtag_pattern = r'#\w+'
    found_hashtags = re.findall(hashtag_pattern, content_clean)
    
    if found_hashtags:
        hashtags = found_hashtags[:request.count]
    else:
        # Split by comma and add # if missing
        parts = [p.strip() for p in content_clean.split(',')]
        for part in parts:
            if part:
                if not part.startswith('#'):
                    part = '#' + part
                hashtags.append(part)
        hashtags = hashtags[:request.count]
    
    # Log the generation
    log = AIGenerationLog(
        user_id=current_user.id,
        generation_type="hashtags",
        platform=request.platform,
        prompt=request.content,
        generated_content=response.content,
        provider_used=response.provider,
        tokens_used=response.tokens_used
    )
    db.add(log)
    db.commit()
    
    return HashtagSuggestResponse(
        hashtags=hashtags,
        provider=response.provider,
        tokens_used=response.tokens_used
    )


# Content Template Endpoints

@router.get("/templates", response_model=ContentTemplateListResponse)
def list_templates(
    platform: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List content templates for the current user (including system templates)."""
    
    query = db.query(ContentTemplate).filter(
        (ContentTemplate.user_id == current_user.id) | (ContentTemplate.is_system == True),
        ContentTemplate.is_active == True
    )
    
    if platform:
        query = query.filter(ContentTemplate.platform == platform)
    
    templates = query.order_by(ContentTemplate.name).all()
    
    return ContentTemplateListResponse(
        data=templates,
        meta={"total": len(templates)}
    )


@router.post("/templates", response_model=ContentTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template_data: ContentTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new content template."""
    
    template = ContentTemplate(
        user_id=current_user.id,
        name=template_data.name,
        description=template_data.description,
        platform=template_data.platform,
        tone=template_data.tone,
        template_prompt=template_data.template_prompt,
        max_length=template_data.max_length,
        is_system=False,
        is_active=True
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


@router.get("/templates/{template_id}", response_model=ContentTemplateResponse)
def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific content template."""
    
    template = db.query(ContentTemplate).filter(
        ContentTemplate.id == template_id,
        (ContentTemplate.user_id == current_user.id) | (ContentTemplate.is_system == True)
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template


@router.patch("/templates/{template_id}", response_model=ContentTemplateResponse)
def update_template(
    template_id: str,
    template_data: ContentTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a content template."""
    
    template = db.query(ContentTemplate).filter(
        ContentTemplate.id == template_id,
        ContentTemplate.user_id == current_user.id,
        ContentTemplate.is_system == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or cannot modify system templates"
        )
    
    update_data = template_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a content template."""
    
    template = db.query(ContentTemplate).filter(
        ContentTemplate.id == template_id,
        ContentTemplate.user_id == current_user.id,
        ContentTemplate.is_system == False
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or cannot delete system templates"
        )
    
    db.delete(template)
    db.commit()
    
    return None


# Generation History Endpoints

@router.get("/history", response_model=AIGenerationLogListResponse)
def list_generation_history(
    generation_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List AI generation history for the current user."""
    
    query = db.query(AIGenerationLog).filter(
        AIGenerationLog.user_id == current_user.id
    )
    
    if generation_type:
        query = query.filter(AIGenerationLog.generation_type == generation_type)
    
    total = query.count()
    logs = query.order_by(AIGenerationLog.created_at.desc()).offset(offset).limit(limit).all()
    
    return AIGenerationLogListResponse(
        data=logs,
        meta={
            "total": total,
            "limit": limit,
            "offset": offset
        }
    )
