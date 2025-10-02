"""
Script to extract text and metadata from PDF files and store in the database.
"""
import os
import sys
from PyPDF2 import PdfReader
from models import PDFDocument, init_db, get_session

def extract_pdf_info(pdf_path):
    """
    Extract text and metadata from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing extracted information
    """
    try:
        reader = PdfReader(pdf_path)
        
        # Extract metadata
        metadata = reader.metadata
        title = metadata.get('/Title', '') if metadata else ''
        author = metadata.get('/Author', '') if metadata else ''
        
        # Extract text from all pages
        text_content = []
        for page in reader.pages:
            text_content.append(page.extract_text())
        
        full_text = '\n'.join(text_content)
        
        return {
            'title': title,
            'author': author,
            'num_pages': len(reader.pages),
            'content': full_text
        }
    except Exception as e:
        print(f"Error extracting from {pdf_path}: {str(e)}")
        return None

def index_pdf(pdf_path, session):
    """
    Index a single PDF file into the database.
    
    Args:
        pdf_path: Path to the PDF file
        session: Database session
    """
    filename = os.path.basename(pdf_path)
    
    # Check if already indexed
    existing = session.query(PDFDocument).filter_by(filename=filename).first()
    if existing:
        print(f"Skipping {filename} - already indexed")
        return
    
    print(f"Indexing {filename}...")
    info = extract_pdf_info(pdf_path)
    
    if info is None:
        print(f"Failed to extract info from {filename}")
        return
    
    # Create database entry
    doc = PDFDocument(
        filename=filename,
        title=info['title'] or filename,
        author=info['author'],
        num_pages=info['num_pages'],
        content=info['content'],
        file_path=pdf_path
    )
    
    session.add(doc)
    session.commit()
    print(f"Successfully indexed {filename}")

def index_directory(directory_path):
    """
    Index all PDF files in a directory.
    
    Args:
        directory_path: Path to directory containing PDFs
    """
    init_db()
    session = get_session()
    
    if not os.path.exists(directory_path):
        print(f"Directory {directory_path} does not exist!")
        return
    
    pdf_files = [f for f in os.listdir(directory_path) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {directory_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s)")
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory_path, pdf_file)
        index_pdf(pdf_path, session)
    
    session.close()
    print("\nIndexing complete!")

def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python extract_pdfs.py <directory_path>")
        print("Example: python extract_pdfs.py ./pdfs")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    index_directory(directory_path)

if __name__ == "__main__":
    main()
