from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import (
    UserCreate, UserLogin, Token, UserResponse, 
    ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest, MessageResponse
)
from app.services import auth_service
from app.core.security import create_access_token, get_current_user, revoked_tokens
from app.services.email import send_password_reset_email
from app.core.config import settings
from app.models.user import User
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
import os

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)

@router.post("/signup", response_model=UserResponse)
@limiter.limit("5/minute")
async def signup(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    db_user = auth_service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return auth_service.create_user(db=db, user=user)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, user: UserLogin, db: Session = Depends(get_db)):
    authenticated_user = auth_service.authenticate_user(db, user.email, user.password)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = create_access_token(subject=authenticated_user.email)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, user: User = Depends(get_current_user)):
    auth_header = request.headers.get("Authorization")
    if auth_header:
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() == "bearer" and token:
            revoked_tokens.add(token)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    auth_service.change_password(db, current_user, data.old_password, data.new_password)
    return {"message": "Password changed successfully"}


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def forgot_password(request: Request, data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    token = auth_service.create_password_reset_token(db, data.email)
    if token:
        send_password_reset_email(data.email, token)
    return {"message": "If an account exists with this email, a reset link has been sent."}


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def reset_password(request: Request, data: ResetPasswordRequest, db: Session = Depends(get_db)):
    auth_service.reset_password(db, data.token, data.new_password)
    return {"message": "Password has been reset successfully"}
