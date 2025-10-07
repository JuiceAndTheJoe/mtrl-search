"""
Database models for the PDF indexing system.
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
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
    
    # Relation till artiklar
    articles = relationship("Article", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PDFDocument(id={self.id}, filename='{self.filename}')>"

class Article(Base):
    """Model för att lagra artikelinformation från Tillverkardokumentation."""
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('pdf_documents.id'), nullable=False)
    fbet = Column(String(50))  # FBET-kod
    fben = Column(String(50))  # FBEN-kod  
    artikel = Column(String(500))  # Artikelnamn/beskrivning
    link = Column(String(1000))  # Länk till dokumentation
    image_url = Column(String(1000))  # URL till artikelbild
    extracted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relation tillbaka till dokument
    document = relationship("PDFDocument", back_populates="articles")
    
    def __repr__(self):
        return f"<Article(id={self.id}, fbet='{self.fbet}', fben='{self.fben}', artikel='{self.artikel}')>"

# Database setup
engine = create_engine('sqlite:///pdf_index.db', echo=False)
Session = sessionmaker(bind=engine)

def init_db():
    """Initialize the database schema."""
    Base.metadata.create_all(engine)

def get_session():
    """Get a new database session."""
    return Session()
