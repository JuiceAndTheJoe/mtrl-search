# mtrl-search

A Python-based material indexing and search system that extracts text and structured article data from PDF files, stores information in a SQL database, and provides a Flask-powered web interface for searching and viewing documents and articles.

## Features

- **PDF Text Extraction**: Automatically extracts text and metadata from PDF files
- **Article Extraction**: Extracts structured article data (FBET/FBEN codes, descriptions, links) from chapter 9
- **SQLite Database**: Stores document and article information using SQLAlchemy ORM
- **Full-Text Search**: Search through document titles, authors, filenames, content, and articles
- **Web Interface**: Clean, responsive Bootstrap-based UI for searching and browsing
- **Document Details**: View detailed information about each indexed PDF and its articles

## Project Structure

```
mtrl-search/
├── app.py                 # Flask application with routes
├── models.py              # SQLAlchemy database models
├── extract_articles.py    # PDF indexing and article extraction script
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── base.html         # Base template with Bootstrap
│   ├── index.html        # Home page with search form
│   ├── search_results.html  # Search results display
│   ├── document_detail.html # Individual document view
│   └── browse.html       # Browse all documents
├── static/
│   └── css/
│       └── style.css     # Custom CSS styles
├── pdfs/                 # Directory for PDF files
└── pdf_index.db          # SQLite database (created automatically)
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/JuiceAndTheJoe/mtrl-search.git
   cd mtrl-search
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Add PDF Files

Place your PDF files in the `pdfs/` directory:
```bash
cp /path/to/your/document.pdf pdfs/
```

### 2. Index PDFs

Run the extraction script to index all PDFs in a directory:
```bash
python extract_articles.py ./pdfs
```

The script will:
- Extract text from each PDF
- Extract metadata (title, author, number of pages)
- Extract structured article data from chapter 9 (FBET/FBEN codes, descriptions, links)
- Store everything in the SQLite database
- Skip files that have already been indexed

**Example output**:
```
Found 3 PDF file(s)
Indexing document1.pdf...
Successfully indexed document1.pdf
Indexing document2.pdf...
Successfully indexed document2.pdf
Skipping document3.pdf - already indexed

Indexing complete!
```

### 3. Start the Flask Server

Run the Flask application:
```bash
python app.py
```

The server will start on `http://localhost:5000`

### 4. Use the Web Interface

Open your browser and navigate to `http://localhost:5000`

**Available pages**:
- **Home (`/`)**: Search interface and statistics
- **Search (`/search?q=query`)**: Search results for your query
- **Browse (`/browse`)**: View all indexed documents
- **Articles (`/articles`)**: Browse all extracted articles
- **Article Search (`/articles/search?q=query`)**: Search through articles
- **Document Detail (`/document/<id>`)**: Detailed view of a specific document

## Adding New PDFs

To add more PDFs after initial setup:

1. Copy new PDF files to the `pdfs/` directory
2. Run the indexing script again:
   ```bash
   python extract_articles.py ./pdfs
   ```
3. The script will only index new files, skipping already-indexed ones
4. Refresh your browser to see the new documents

## Search Features

The search functionality looks for matches in:

**Document Search**:
- Document titles
- Author names  
- Filenames
- Full document content

**Article Search**:
- FBET codes
- FBEN codes
- Article descriptions

Search is case-insensitive and matches partial words.

## Database Schema

### PDFDocument Model
- `id`: Unique identifier
- `filename`: Original PDF filename
- `title`: Document title (from metadata or filename)
- `author`: Document author (from metadata)
- `num_pages`: Number of pages in the PDF
- `content`: Full text content extracted from all pages
- `file_path`: Path to the original PDF file
- `indexed_at`: Timestamp when the document was indexed

### Article Model
- `id`: Unique identifier
- `document_id`: Foreign key to PDFDocument
- `fbet`: FBET code
- `fben`: FBEN code
- `artikel`: Article name/description
- `link`: Link to documentation
- `extracted_at`: Timestamp when the article was extracted

## Requirements

- Python 3.7+
- Flask 3.0.0
- SQLAlchemy 2.0.23
- PyPDF2 3.0.1

## Development

To run in development mode with debug enabled:
```bash
python app.py
```

The application will automatically reload when you make changes to the code.

## Troubleshooting

**Problem**: "No module named 'PyPDF2'"
**Solution**: Make sure you've installed the requirements: `pip install -r requirements.txt`

**Problem**: PDF text extraction is garbled
**Solution**: Some PDFs use complex formatting or images. PyPDF2 works best with text-based PDFs.

**Problem**: "Database is locked" error
**Solution**: Make sure you're not running multiple instances of the extraction script simultaneously.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.