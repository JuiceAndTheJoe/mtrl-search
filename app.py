"""
Flask application for searching and viewing indexed PDF documents.
"""
from flask import Flask, render_template, request
from sqlalchemy import or_
from models import PDFDocument, Article, init_db, get_session

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
    doc = session.get(PDFDocument, doc_id)  # Uppdaterad syntax
    
    articles = []
    if doc:
        articles = session.query(Article).filter_by(document_id=doc_id).all()
    
    session.close()
    
    if not doc:
        return "Document not found", 404
    
    return render_template('document_detail.html', doc=doc, articles=articles)

@app.route('/browse')
def browse():
    """Browse all documents."""
    session = get_session()
    documents = session.query(PDFDocument).order_by(PDFDocument.indexed_at.desc()).all()
    session.close()
    
    return render_template('browse.html', documents=documents)

@app.route('/articles')
def articles():
    """Browse all extracted articles."""
    session = get_session()
    articles = session.query(Article).join(PDFDocument).order_by(Article.extracted_at.desc()).all()
    session.close()
    
    return render_template('articles.html', articles=articles)

@app.route('/articles/search')
def search_articles():
    """Search for articles."""
    query = request.args.get('q', '').strip()
    
    if not query:
        return render_template('article_search_results.html', results=[], query='')
    
    session = get_session()
    
    # Search in FBET, FBEN, artikel fields
    search_filter = or_(
        Article.fbet.ilike(f'%{query}%'),
        Article.fben.ilike(f'%{query}%'),
        Article.artikel.ilike(f'%{query}%')
    )
    
    results = session.query(Article).join(PDFDocument).filter(search_filter).all()
    session.close()
    
    return render_template('article_search_results.html', results=results, query=query)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
