from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.query import NLQuery, QueryStatus, QueryType
from app.models.user import User
from app.core.auth import get_current_active_user

router = APIRouter()

class QueryCreate(BaseModel):
    natural_language_query: str
    query_type: QueryType = QueryType.NATURAL_LANGUAGE
    context: Optional[dict] = None

class QueryResponse(BaseModel):
    id: int
    natural_language_query: str
    generated_sql: Optional[str]
    query_type: QueryType
    status: QueryStatus
    error_message: Optional[str]
    results: Optional[dict]
    result_count: Optional[int]
    execution_time: Optional[float]
    context: Optional[dict]
    confidence_score: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]
    executed_at: Optional[datetime]

    class Config:
        from_attributes = True

@router.post("/", response_model=QueryResponse)
def create_query(
    query: QueryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_query = NLQuery(
        user_id=current_user.id,
        natural_language_query=query.natural_language_query,
        query_type=query.query_type,
        context=query.context
    )
    db.add(db_query)
    db.commit()
    db.refresh(db_query)
    
    # TODO: Trigger background task to process the query
    # This would involve NL to SQL translation and execution
    
    return db_query

@router.get("/", response_model=List[QueryResponse])
def get_queries(
    skip: int = 0,
    limit: int = 100,
    status: Optional[QueryStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(NLQuery).filter(NLQuery.user_id == current_user.id)
    
    if status:
        query = query.filter(NLQuery.status == status)
    
    queries = query.offset(skip).limit(limit).all()
    return queries

@router.get("/{query_id}", response_model=QueryResponse)
def get_query(
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(NLQuery).filter(NLQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    # Check permissions
    if query.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return query

@router.delete("/{query_id}")
def delete_query(
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(NLQuery).filter(NLQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    # Check permissions
    if query.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(query)
    db.commit()
    return {"message": "Query deleted successfully"}

@router.post("/{query_id}/execute")
def execute_query(
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(NLQuery).filter(NLQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    # Check permissions
    if query.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # TODO: Implement actual query execution logic
    # This would involve:
    # 1. Translating natural language to SQL
    # 2. Validating the generated SQL
    # 3. Executing the query safely
    # 4. Returning results
    
    query.status = QueryStatus.PROCESSING
    db.commit()
    
    # For now, return a placeholder response
    return {"message": "Query execution started", "query_id": query_id}

