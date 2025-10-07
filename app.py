"""
Flask application for searching and viewing indexed PDF documents.
"""
from flask import Flask, render_template, request, redirect
from sqlalchemy import or_
import urllib.parse
from models import PDFDocument, Article, init_db, get_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# Initialize database on startup
init_db()

@app.route('/')
def index():
    """Home page with article search form."""
    session = get_session()
    total_docs = session.query(PDFDocument).count()
    total_articles = session.query(Article).count()
    session.close()
    return render_template('index.html', total_docs=total_docs, total_articles=total_articles)

# Dokumentsökning borttagen - endast artikelsökning används nu

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

# Dokumentbläddring borttagen - endast artikelvy används nu

@app.route('/articles')
def articles():
    """Browse all extracted articles."""
    session = get_session()
    from sqlalchemy.orm import joinedload
    articles = session.query(Article).options(joinedload(Article.document)).order_by(Article.extracted_at.desc()).all()
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
    
    # Eagerly load the document relationship to avoid DetachedInstanceError
    from sqlalchemy.orm import joinedload
    results = session.query(Article).options(joinedload(Article.document)).filter(search_filter).all()
    session.close()
    
    return render_template('article_search_results.html', results=results, query=query)

@app.route('/duckduckgo_search/<int:article_id>')
def duckduckgo_search(article_id):
    """Redirect to DuckDuckGo search for a specific article."""
    session = get_session()
    article = session.get(Article, article_id)
    session.close()
    
    if not article:
        return "Article not found", 404
    
    # Build search query from article information
    search_terms = []
    
    if article.artikel and article.artikel.strip() and article.artikel != 'None':
        search_terms.append(article.artikel.strip())
    if article.fben and article.fben.strip():
        search_terms.append(article.fben.strip())
    
    # If we have no good search terms, use FBET as fallback
    if not search_terms and article.fbet:
        search_terms.append(article.fbet.strip())
    
    # Join search terms and URL encode
    search_query = ' '.join(search_terms)
    encoded_query = urllib.parse.quote_plus(search_query)
    
    # Redirect to DuckDuckGo search
    duckduckgo_url = f"https://duckduckgo.com/?q={encoded_query}"
    return redirect(duckduckgo_url)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
