from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Boolean, ForeignKey
from sqlalchemy.sql import func

from app.database import Base

class GovernmentDataSource(Base):
    __tablename__ = "government_data_sources"

    id = Column(Integer, primary_key=True, index=True)
    
    # Source identification
    source_name = Column(String, nullable=False)  # MoSPI, eSankhyiki, etc.
    api_endpoint = Column(String, nullable=False)
    api_key = Column(String)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer)  # Requests per minute
    timeout = Column(Integer, default=30)  # Request timeout in seconds
    
    # Metadata
    description = Column(Text)
    supported_datasets = Column(JSON)  # List of available datasets
    last_sync = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class GovernmentDataset(Base):
    __tablename__ = "government_datasets"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("government_data_sources.id"), nullable=False)
    
    # Dataset identification
    dataset_id = Column(String, nullable=False)  # External dataset ID
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    
    # Schema information
    schema = Column(JSON)  # Dataset schema/structure
    sample_data = Column(JSON)  # Sample records for reference
    
    # Metadata
    total_records = Column(Integer)
    last_updated = Column(DateTime(timezone=True))
    update_frequency = Column(String)  # daily, weekly, monthly, etc.
    
    # Access information
    is_public = Column(Boolean, default=True)
    access_level = Column(String)  # public, restricted, private
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DataSyncLog(Base):
    __tablename__ = "data_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("government_data_sources.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("government_datasets.id"), nullable=True)
    
    # Sync details
    sync_type = Column(String, nullable=False)  # full, incremental, metadata
    status = Column(String, nullable=False)  # success, failed, partial
    
    # Statistics
    records_processed = Column(Integer, default=0)
    records_added = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Timing
    duration = Column(Float)  # Sync duration in seconds
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

