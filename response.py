from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base

class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    respondent_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous responses
    
    # Response data
    data = Column(JSON)  # Complete response data
    response_metadata = Column(JSON)  # Browser info, location, etc.
    
    # Quality metrics
    completion_time = Column(Float)  # Time taken to complete in seconds
    is_complete = Column(Boolean, default=False)
    quality_score = Column(Float)  # AI-calculated quality score
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    survey = relationship("Survey", back_populates="responses")
    respondent = relationship("User")
    field_responses = relationship("FieldResponse", back_populates="response", cascade="all, delete-orphan")

class FieldResponse(Base):
    __tablename__ = "field_responses"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("survey_responses.id"), nullable=False)
    field_id = Column(Integer, ForeignKey("survey_fields.id"), nullable=False)
    
    # Response value (stored as JSON to handle different data types)
    value = Column(JSON)
    text_value = Column(Text)  # For text responses and search indexing
    numeric_value = Column(Float)  # For numeric responses and calculations
    
    # Metadata
    confidence_score = Column(Float)  # AI confidence in response quality
    processing_notes = Column(Text)  # AI processing notes
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    response = relationship("SurveyResponse", back_populates="field_responses")
    field = relationship("SurveyField", back_populates="responses")

