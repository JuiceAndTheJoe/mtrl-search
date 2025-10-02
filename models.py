"""
Database models for the PDF indexing system.
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class PDFDocument(Base):
    """Model for storing PDF document information."""
    __tablename__ = 'pdf_documents'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    title = Column(String(500))
    author = Column(String(255))
    num_pages = Column(Integer)
    content = Column(Text)
    file_path = Column(String(500))
    indexed_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PDFDocument(id={self.id}, filename='{self.filename}')>"

# Database setup
engine = create_engine('sqlite:///pdf_index.db', echo=False)
Session = sessionmaker(bind=engine)

def init_db():
    """Initialize the database schema."""
    Base.metadata.create_all(engine)

def get_session():
    """Get a new database session."""
    return Session()
