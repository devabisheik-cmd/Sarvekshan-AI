from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.survey import Survey, SurveyStatus, SurveyField
from app.models.user import User
from app.core.auth import get_current_active_user

router = APIRouter()

class SurveyFieldCreate(BaseModel):
    field_type: str
    label: str
    description: Optional[str] = None
    required: bool = False
    options: Optional[dict] = None
    validation_rules: Optional[dict] = None
    order_index: int = 0

class SurveyFieldResponse(BaseModel):
    id: int
    field_type: str
    label: str
    description: Optional[str]
    required: bool
    options: Optional[dict]
    validation_rules: Optional[dict]
    order_index: int

    class Config:
        from_attributes = True

class SurveyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    fields: Optional[dict] = None
    settings: Optional[dict] = None
    is_public: bool = False
    requires_auth: bool = True
    max_responses: Optional[int] = None
    expires_at: Optional[datetime] = None

class SurveyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    fields: Optional[dict] = None
    settings: Optional[dict] = None
    status: Optional[SurveyStatus] = None
    is_public: Optional[bool] = None
    requires_auth: Optional[bool] = None
    max_responses: Optional[int] = None
    expires_at: Optional[datetime] = None

class SurveyResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: SurveyStatus
    fields: Optional[dict]
    settings: Optional[dict]
    is_public: bool
    requires_auth: bool
    max_responses: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    published_at: Optional[datetime]
    expires_at: Optional[datetime]
    creator_id: int

    class Config:
        from_attributes = True

@router.post("/", response_model=SurveyResponse)
def create_survey(
    survey: SurveyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_survey = Survey(
        title=survey.title,
        description=survey.description,
        fields=survey.fields,
        settings=survey.settings,
        is_public=survey.is_public,
        requires_auth=survey.requires_auth,
        max_responses=survey.max_responses,
        expires_at=survey.expires_at,
        creator_id=current_user.id
    )
    db.add(db_survey)
    db.commit()
    db.refresh(db_survey)
    return db_survey

@router.get("/", response_model=List[SurveyResponse])
def get_surveys(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Users can see their own surveys and public surveys
    surveys = db.query(Survey).filter(
        (Survey.creator_id == current_user.id) | (Survey.is_public == True)
    ).offset(skip).limit(limit).all()
    return surveys

@router.get("/{survey_id}", response_model=SurveyResponse)
def get_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # Check permissions
    if not survey.is_public and survey.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return survey

@router.put("/{survey_id}", response_model=SurveyResponse)
def update_survey(
    survey_id: int,
    survey_update: SurveyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # Check permissions
    if survey.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update fields
    for field, value in survey_update.dict(exclude_unset=True).items():
        setattr(survey, field, value)
    
    db.commit()
    db.refresh(survey)
    return survey

@router.delete("/{survey_id}")
def delete_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # Check permissions
    if survey.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(survey)
    db.commit()
    return {"message": "Survey deleted successfully"}

@router.post("/{survey_id}/publish")
def publish_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    # Check permissions
    if survey.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    survey.status = SurveyStatus.ACTIVE
    survey.published_at = datetime.utcnow()
    db.commit()
    db.refresh(survey)
    return survey

