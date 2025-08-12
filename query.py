from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base

class QueryStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class QueryType(enum.Enum):
    NATURAL_LANGUAGE = "natural_language"
    SQL = "sql"
    STATISTICAL = "statistical"
    REPORT = "report"

class NLQuery(Base):
    __tablename__ = "nl_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Query content
    natural_language_query = Column(Text, nullable=False)
    generated_sql = Column(Text)
    query_type = Column(Enum(QueryType), default=QueryType.NATURAL_LANGUAGE)
    
    # Processing status
    status = Column(Enum(QueryStatus), default=QueryStatus.PENDING)
    error_message = Column(Text)
    
    # Results
    results = Column(JSON)  # Query results
    result_count = Column(Integer)
    execution_time = Column(Float)  # Execution time in seconds
    
    # Metadata
    context = Column(JSON)  # Additional context for query processing
    confidence_score = Column(Float)  # AI confidence in query translation
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    executed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="queries")

class DataProcessingJob(Base):
    __tablename__ = "data_processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Job configuration
    job_type = Column(String, nullable=False)  # cleaning, analysis, export, etc.
    parameters = Column(JSON)  # Job-specific parameters
    
    # Status tracking
    status = Column(String, default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)  # Progress percentage (0-100)
    
    # Results
    results = Column(JSON)
    output_files = Column(JSON)  # List of generated files
    error_log = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User")

