"""Auth router."""
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.database import get_db
from app.models.models import User
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    username: str = Form(...),  # OAuth2 uses 'username' for email
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login user."""
    user = db.query(User).filter(User.email == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
def register(
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """Register new user."""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email}
