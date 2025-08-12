from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.response import SurveyResponse, FieldResponse
from app.models.survey import Survey
from app.models.user import User
from app.core.auth import get_current_active_user

router = APIRouter()

class ResponseCreate(BaseModel):
    survey_id: int
    data: dict
    response_metadata: Optional[dict] = None

class ResponseUpdate(BaseModel):
    data: Optional[dict] = None
    response_metadata: Optional[dict] = None
    is_complete: Optional[bool] = None

class ResponseResponse(BaseModel):
    id: int
    survey_id: int
    respondent_id: Optional[int]
    data: dict
    response_metadata: Optional[dict]
    completion_time: Optional[float]
    is_complete: bool
    quality_score: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

@router.post("/", response_model=ResponseResponse)
def create_response(
    response: ResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if survey exists and is active
    survey = db.query(Survey).filter(Survey.id == response.survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    if survey.status.value != "active":
        raise HTTPException(status_code=400, detail="Survey is not active")
    
    # Check if survey requires authentication
    respondent_id = current_user.id if survey.requires_auth else None
    
    db_response = SurveyResponse(
        survey_id=response.survey_id,
        respondent_id=respondent_id,
        data=response.data,
        response_metadata=response.response_metadata
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response

@router.get("/", response_model=List[ResponseResponse])
def get_responses(
    survey_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(SurveyResponse)
    
    if survey_id:
        # Check if user has access to this survey's responses
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        if survey.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        query = query.filter(SurveyResponse.survey_id == survey_id)
    else:
        # Only show responses for surveys the user created
        user_survey_ids = db.query(Survey.id).filter(Survey.creator_id == current_user.id).subquery()
        query = query.filter(SurveyResponse.survey_id.in_(user_survey_ids))
    
    responses = query.offset(skip).limit(limit).all()
    return responses

@router.get("/{response_id}", response_model=ResponseResponse)
def get_response(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    response = db.query(SurveyResponse).filter(SurveyResponse.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # Check permissions
    survey = db.query(Survey).filter(Survey.id == response.survey_id).first()
    if survey.creator_id != current_user.id and response.respondent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return response

@router.put("/{response_id}", response_model=ResponseResponse)
def update_response(
    response_id: int,
    response_update: ResponseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    response = db.query(SurveyResponse).filter(SurveyResponse.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # Check permissions - only respondent can update their response
    if response.respondent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update fields
    for field, value in response_update.dict(exclude_unset=True).items():
        setattr(response, field, value)
    
    if response_update.is_complete and not response.completed_at:
        response.completed_at = datetime.utcnow()
        if response.started_at:
            response.completion_time = (response.completed_at - response.started_at).total_seconds()
    
    db.commit()
    db.refresh(response)
    return response

@router.delete("/{response_id}")
def delete_response(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    response = db.query(SurveyResponse).filter(SurveyResponse.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # Check permissions - survey creator or respondent can delete
    survey = db.query(Survey).filter(Survey.id == response.survey_id).first()
    if survey.creator_id != current_user.id and response.respondent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(response)
    db.commit()
    return {"message": "Response deleted successfully"}

