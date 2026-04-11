from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.application import ApplicationOut, ApplicationCreate, ApplicationPatch
from app.models.job_application import JobApplication
from app.services.cache import invalidate_user_application_summary
from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/applications", tags=["applications"])

@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    app = JobApplication(
        user_id = current_user.id,
        job_title=payload.job_title.strip(),
        company=payload.company.strip(),
        job_url=str(payload.job_url) if payload.job_url else None, 
        status=payload.status,
        notes=payload.notes,
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    invalidate_user_application_summary(current_user.id)
    return app

@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    app = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return app

@router.get("", response_model=list[ApplicationOut])
def get_all_applications(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    apps = db.query(JobApplication).filter(JobApplication.user_id == current_user.id).order_by(JobApplication.updated_at.desc()).all()
    return apps

@router.patch("/{application_id}", response_model=ApplicationOut)
def patch_application(
    application_id: int,
    payload: ApplicationPatch,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    app = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    if app.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    if payload.status is not None:
        app.status = payload.status
    if payload.notes is not None:
        app.notes = payload.notes
    
    db.commit()
    db.refresh(app)

    invalidate_user_application_summary(current_user.id)
    return app