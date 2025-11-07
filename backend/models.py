
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from datetime import datetime
from database import Base

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)

class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_type = Column(String)  # pdf, jpg, png
    
    # Extracted text
    raw_text = Column(Text)
    
    # Structured data (stored as JSON string)
    structured_data = Column(Text)  # Will store JSON with patient, charges, etc.
    
    # Analysis results
    analysis_results = Column(Text)  # Will store JSON with issues, severity, etc.
    summary = Column(Text)  # Human-readable summary
    
    # Status tracking
    status = Column(String, default="uploaded")  # uploaded, extracted, analyzed
    total_amount = Column(Float)
