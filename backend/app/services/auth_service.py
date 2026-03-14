import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User, PasswordResetToken
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password, validate_password_strength
from app.core.config import settings


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate):
    strength_error = validate_password_strength(user.password)
    if strength_error:
        raise HTTPException(status_code=400, detail=strength_error)

    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
  
    if not user.hashed_password:
        return None
        
    print(f"DEBUG: Verifying password for {email}...")
    is_valid = verify_password(password, user.hashed_password)
    if not is_valid:
        print(f"DEBUG: Password verification failed for {email}")
        return None
    
    print(f"DEBUG: Authentication successful for {email}")
    return user


def create_oauth_user(db: Session, email: str, provider: str):
    db_user = User(
        email=email,
        hashed_password=None,
        is_active=True,
        provider=provider
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_password_reset_token(db: Session, email: str) -> str | None :
    user = get_user_by_email(db, email)
    if not user:
        return None

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False,
    ).update({"used": True})

    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
    
    db_token = PasswordResetToken(user_id=user.id, token=token, expires_at=expires_at)
    db.add(db_token)
    db.commit()
    
    return token


def verify_reset_token(db: Session, token: str) -> User | None:
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if not reset_token:
        return None
        
    return db.query(User).filter(User.id == reset_token.user_id).first()


def reset_password(db: Session, token: str, new_password: str):
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()

    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # Validate new password
    strength_error = validate_password_strength(new_password)
    if strength_error:
        raise HTTPException(status_code=400, detail=strength_error)

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = get_password_hash(new_password)
    reset_token.used = True
    
    db.add(user)
    db.add(reset_token)
    db.commit()
    
    return True


def change_password(db: Session, user: User, old_password: str, new_password: str):
    if not user.hashed_password:
        raise HTTPException(status_code=400, detail="User account is OAuth-only, cannot change password")
        
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
        
    strength_error = validate_password_strength(new_password)
    if strength_error:
        raise HTTPException(status_code=400, detail=strength_error)

    user.hashed_password = get_password_hash(new_password)
    db.add(user)
    db.commit()
    return True