from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.services import auth_service
from app.core.security import create_access_token
from app.core.config import settings
from fastapi_sso.sso.google import GoogleSSO
from fastapi_sso.sso.github import GithubSSO
import os

router = APIRouter()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

google_sso = GoogleSSO(
    settings.GOOGLE_CLIENT_ID, 
    settings.GOOGLE_CLIENT_SECRET, 
    f"{BACKEND_URL}/auth/google/callback"
    ) if settings.GOOGLE_CLIENT_ID else None
github_sso = GithubSSO(
    settings.GITHUB_CLIENT_ID, 
    settings.GITHUB_CLIENT_SECRET, 
    f"{BACKEND_URL}/auth/github/callback"
    ) if settings.GITHUB_CLIENT_ID else None

@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate, db: Session = Depends(get_db)):

    db_user = auth_service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return auth_service.create_user(db=db, user=user)

@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):

    user = auth_service.authenticate_user(db, user.email, user.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = create_access_token(subject=user.email)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/google/login")
async def google_login():
    if not google_sso:
        raise HTTPException(status_code=501, detail="Google Auth not configured")
    return await google_sso.get_login_redirect()

@router.get("/google/callback")
async def google_callback(request, db: Session = Depends(get_db)):
    if not google_sso:
        raise HTTPException(status_code=501, detail="Google Auth not configured")
    
    user_info = await google_sso.verify_and_process(request)
    email = user_info.email

    user = auth_service.get_user_by_email(db, email)
    if not user:
        user = auth_service.create_oauth_user(db, email, provider="google")
    
    access_token = create_access_token(subject=user.email)

    frontend_url = f"{FRONTEND_URL}/login/success?token={access_token}"
    return RedirectResponse(url=frontend_url)

@router.get("/github/login")
async def github_login():
    if not github_sso:
        raise HTTPException(status_code=501, detail="GitHub Auth not configured")
    return await github_sso.get_login_redirect()

@router.get("/github/callback")
async def github_callback(request, db:Session = Depends(get_db)):
    if not github_sso:
        raise HTTPException(status_code=501, detail="GitHub Auth not configured")
    
    user_info = await github_sso.verify_and_process(request)
    email = user_info.email

    user = auth_service.get_user_by_email(db, email)
    if not user:
        user = auth_service.create_oauth_user(db, email, provider="github")
    
    access_token = create_access_token(subject=user.email)

    frontend_url = f"{FRONTEND_URL}/login/success?token={access_token}"
    return RedirectResponse(url=frontend_url)