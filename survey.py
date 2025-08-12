from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base

class SurveyStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class Survey(Base):
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(Enum(SurveyStatus), default=SurveyStatus.DRAFT)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Survey configuration
    fields = Column(JSON)  # Dynamic form fields configuration
    settings = Column(JSON)  # Survey settings (max responses, time limits, etc.)
    
    # Metadata
    is_public = Column(Boolean, default=False)
    requires_auth = Column(Boolean, default=True)
    max_responses = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))

    # Relationships
    creator = relationship("User", back_populates="surveys")
    responses = relationship("SurveyResponse", back_populates="survey", cascade="all, delete-orphan")

class SurveyField(Base):
    __tablename__ = "survey_fields"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    field_type = Column(String, nullable=False)  # text, number, select, radio, checkbox, etc.
    label = Column(String, nullable=False)
    description = Column(Text)
    required = Column(Boolean, default=False)
    options = Column(JSON)  # For select, radio, checkbox fields
    validation_rules = Column(JSON)  # Validation configuration
    order_index = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    survey = relationship("Survey")
    responses = relationship("FieldResponse", back_populates="field")

