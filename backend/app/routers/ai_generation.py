"""AI Content Generation API routes."""
import logging
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, ContentTemplate
from app.schemas.ai_generation import (
    GeneratePostRequest,
    GeneratePostResponse,
    GenerateThreadRequest,
    GenerateThreadResponse,
    ThreadPost,
    SuggestHashtagsRequest,
    SuggestHashtagsResponse,
    ContentTemplateCreate,
    ContentTemplateUpdate,
    ContentTemplateResponse,
    ContentTemplateList,
    AIProviderInfo,
    AIServiceStatus,
)
from app.services.ai_service import ai_service, GenerationRequest

logger = logging.getLogger(__name__)

# Common words to filter when parsing hashtags (module-level constant)
_COMMON_WORDS = frozenset({
    'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
    'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
    'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy',
    'did', 'she', 'use', 'way', 'many', 'oil', 'sit', 'set', 'run', 'eat',
    'far', 'sea', 'eye', 'ago', 'off', 'too', 'any', 'say', 'man', 'try',
    'ask', 'end', 'why', 'let', 'put', 'own', 'tell', 'very', 'when', 'much',
    'would', 'there', 'their', 'what', 'said', 'each', 'which', 'will',
    'about', 'could', 'other', 'after', 'first', 'never', 'these', 'think',
    'where', 'being', 'every', 'great', 'might', 'shall', 'still', 'those',
    'while', 'this', 'that', 'with', 'have', 'from', 'they', 'know', 'want',
    'been', 'good', 'some', 'time', 'than', 'them', 'well', 'were'
})
router = APIRouter(prefix="/ai", tags=["AI Generation"])


def _get_template_if_provided(
    template_id: Optional[str],
    user_id: str,
    db: Session
) -> Optional[ContentTemplate]:
    """Get template if template_id is provided."""
    if not template_id:
        return None
    
    template = db.query(ContentTemplate).filter(
        ContentTemplate.id == template_id,
        ContentTemplate.user_id == user_id,
        ContentTemplate.is_active == True
    ).first()
    
    return template


@router.post("/generate/post", response_model=GeneratePostResponse)
def generate_post(
    request: GeneratePostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a single social media post."""
    # Check if AI service is available
    available_provider = ai_service.get_available_provider()
    if available_provider == "none":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI generation service is not available. Please configure API keys."
        )
    
    # Get template if specified
    template = _get_template_if_provided(request.template_id, current_user.id, db)
    
    # Build prompt
    prompt = f"Write a social media post about: {request.topic}"
    if template:
        prompt = template.prompt_template.replace("{{topic}}", request.topic)
    
    # Create generation request
    gen_request = GenerationRequest(
        prompt=prompt,
        tone=template.tone if template else request.tone,
        max_length=template.max_length if template else request.max_length,
        context=request.context
    )
    
    # Generate content
    response = ai_service.generate_text(gen_request)
    
    if response.error:
        logger.error(f"AI generation failed: {response.error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {response.error}"
        )
    
    return GeneratePostResponse(
        content=response.content,
        provider=AIProviderInfo(
            provider=response.provider,
            model=response.model,
            tokens_used=response.tokens_used
        ),
        char_count=len(response.content),
        estimated_read_time="< 1 min" if len(response.content) < 200 else "~1 min"
    )


@router.post("/generate/thread", response_model=GenerateThreadResponse)
def generate_thread(
    request: GenerateThreadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a thread of connected posts."""
    # Check if AI service is available
    available_provider = ai_service.get_available_provider()
    if available_provider == "none":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI generation service is not available. Please configure API keys."
        )
    
    # Get template if specified
    template = _get_template_if_provided(request.template_id, current_user.id, db)
    
    # Generate thread
    response = ai_service.generate_thread(
        topic=request.topic,
        tone=template.tone if template else request.tone,
        num_posts=request.num_posts,
        context=request.context
    )
    
    if response.error:
        logger.error(f"AI thread generation failed: {response.error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Thread generation failed: {response.error}"
        )
    
    # Parse thread into individual posts
    posts = _parse_thread_content(response.content, request.num_posts)
    
    return GenerateThreadResponse(
        posts=posts,
        provider=AIProviderInfo(
            provider=response.provider,
            model=response.model,
            tokens_used=response.tokens_used
        ),
        total_posts=len(posts)
    )


def _parse_thread_content(content: str, expected_posts: int) -> list[ThreadPost]:
    """Parse thread content into individual posts."""
    posts = []
    lines = content.strip().split('\n')
    
    current_post_num = 0
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line starts with a number (e.g., "1.", "1)", "Post 1:")
        match = re.match(r'^(?:Post\s*)?(\d+)[:.)\s]+(.+)', line, re.IGNORECASE)
        
        if match:
            # Save previous post if exists
            if current_content and current_post_num > 0:
                post_text = ' '.join(current_content).strip()
                if post_text:
                    posts.append(ThreadPost(
                        number=current_post_num,
                        content=post_text,
                        char_count=len(post_text)
                    ))
            
            # Start new post
            current_post_num = int(match.group(1))
            current_content = [match.group(2)]
        else:
            # Continue current post
            if current_post_num > 0:
                current_content.append(line)
            else:
                # First post without number
                current_post_num = 1
                current_content.append(line)
    
    # Don't forget the last post
    if current_content and current_post_num > 0:
        post_text = ' '.join(current_content).strip()
        if post_text:
            posts.append(ThreadPost(
                number=current_post_num,
                content=post_text,
                char_count=len(post_text)
            ))
    
    # If we have a single post that's too long, split it
    if len(posts) == 1 and posts[0].char_count > 280:
        long_content = posts[0].content
        posts = []
        # Split into chunks of ~250 characters at word boundaries
        words = long_content.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > 250 and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        # Add remaining content
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        # Create posts from chunks
        for i, chunk in enumerate(chunks, 1):
            posts.append(ThreadPost(
                number=i,
                content=chunk,
                char_count=len(chunk)
            ))
    
    return posts


@router.post("/suggest/hashtags", response_model=SuggestHashtagsResponse)
def suggest_hashtags(
    request: SuggestHashtagsRequest,
    current_user: User = Depends(get_current_user)
):
    """Suggest relevant hashtags for content."""
    # Check if AI service is available
    available_provider = ai_service.get_available_provider()
    if available_provider == "none":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI generation service is not available. Please configure API keys."
        )
    
    # Generate hashtags
    response = ai_service.suggest_hashtags(
        content=request.content,
        count=request.count
    )
    
    if response.error:
        logger.error(f"AI hashtag suggestion failed: {response.error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hashtag suggestion failed: {response.error}"
        )
    
    # Parse hashtags from response
    hashtags = _parse_hashtags(response.content)
    
    return SuggestHashtagsResponse(
        hashtags=hashtags[:request.count],
        provider=AIProviderInfo(
            provider=response.provider,
            model=response.model,
            tokens_used=response.tokens_used
        )
    )


def _parse_hashtags(content: str) -> list[str]:
    """Parse hashtags from AI response."""
    # Find all hashtags
    hashtags = re.findall(r'#\w+', content)
    
    # If no hashtags found, try to extract words and add #
    if not hashtags:
        words = re.findall(r'\b\w+\b', content)
        # Filter out common words and short words using module-level constant
        hashtags = [f"#{word.lower()}" for word in words 
                   if len(word) > 3 and word.lower() not in _COMMON_WORDS]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_hashtags = []
    for tag in hashtags:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            unique_hashtags.append(tag)
    
    return unique_hashtags


# Content Template Routes

@router.get("/templates", response_model=ContentTemplateList)
def list_templates(
    template_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List content templates for the current user."""
    query = db.query(ContentTemplate).filter(
        ContentTemplate.user_id == current_user.id,
        ContentTemplate.is_active == True
    )
    
    if template_type:
        query = query.filter(ContentTemplate.template_type == template_type)
    
    templates = query.order_by(ContentTemplate.created_at.desc()).all()
    
    return ContentTemplateList(
        templates=[ContentTemplateResponse.model_validate(t) for t in templates],
        total=len(templates)
    )


@router.post("/templates", response_model=ContentTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    request: ContentTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new content template."""
    template = ContentTemplate(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        template_type=request.template_type,
        tone=request.tone,
        prompt_template=request.prompt_template,
        max_length=request.max_length,
        is_active=True,
        is_default=False
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return ContentTemplateResponse.model_validate(template)


@router.get("/templates/{template_id}", response_model=ContentTemplateResponse)
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific content template."""
    template = db.query(ContentTemplate).filter(
        ContentTemplate.id == template_id,
        ContentTemplate.user_id == current_user.id,
        ContentTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return ContentTemplateResponse.model_validate(template)


@router.patch("/templates/{template_id}", response_model=ContentTemplateResponse)
def update_template(
    template_id: str,
    request: ContentTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a content template."""
    template = db.query(ContentTemplate).filter(
        ContentTemplate.id == template_id,
        ContentTemplate.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return ContentTemplateResponse.model_validate(template)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete (soft delete) a content template."""
    template = db.query(ContentTemplate).filter(
        ContentTemplate.id == template_id,
        ContentTemplate.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    template.is_active = False
    db.commit()
    
    return None


@router.get("/status", response_model=AIServiceStatus)
def get_ai_status(
    current_user: User = Depends(get_current_user)
):
    """Get AI service status."""
    primary_available = ai_service.primary_provider.is_available()
    fallback_available = ai_service.fallback_provider.is_available()
    
    if primary_available:
        status = "ready"
    elif fallback_available:
        status = "fallback"
    else:
        status = "unavailable"
    
    return AIServiceStatus(
        primary_provider="minimax",
        primary_available=primary_available,
        fallback_provider="openai",
        fallback_available=fallback_available,
        status=status
    )
