"""
Flask application for searching and viewing indexed PDF documents.
"""
from flask import Flask, render_template, request
from sqlalchemy import or_
from models import PDFDocument, init_db, get_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# Initialize database on startup
init_db()

@app.route('/')
def index():
    """Home page with search form."""
    session = get_session()
    total_docs = session.query(PDFDocument).count()
    session.close()
    return render_template('index.html', total_docs=total_docs)

@app.route('/search')
def search():
    """Search for PDF documents."""
    query = request.args.get('q', '').strip()
    
    if not query:
        return render_template('search_results.html', results=[], query='')
    
    session = get_session()
    
    # Search in title, author, filename, and content
    search_filter = or_(
        PDFDocument.title.ilike(f'%{query}%'),
        PDFDocument.author.ilike(f'%{query}%'),
        PDFDocument.filename.ilike(f'%{query}%'),
        PDFDocument.content.ilike(f'%{query}%')
    )
    
    results = session.query(PDFDocument).filter(search_filter).all()
    session.close()
    
    return render_template('search_results.html', results=results, query=query)

@app.route('/document/<int:doc_id>')
def document_detail(doc_id):
    """View details of a specific document."""
    session = get_session()
    doc = session.query(PDFDocument).get(doc_id)
    session.close()
    
    if not doc:
        return "Document not found", 404
    
    return render_template('document_detail.html', doc=doc)

@app.route('/browse')
def browse():
    """Browse all documents."""
    session = get_session()
    documents = session.query(PDFDocument).order_by(PDFDocument.indexed_at.desc()).all()
    session.close()
    
    return render_template('browse.html', documents=documents)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
