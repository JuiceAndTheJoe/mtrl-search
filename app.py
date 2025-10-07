"""
Flask application for searching and viewing indexed PDF documents.
"""
from flask import Flask, render_template, request, redirect, jsonify
from sqlalchemy import or_
import urllib.parse
import os
from werkzeug.utils import secure_filename
from models import PDFDocument, Article, init_db, get_session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

@app.route('/api/article/<int:article_id>/image', methods=['POST'])
def update_article_image(article_id):
    """Update article image via URL or file upload."""
    session = get_session()
    
    try:
        article = session.get(Article, article_id)
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Handle URL update
        if 'image_url' in request.form:
            image_url = request.form['image_url'].strip()
            if image_url:
                article.image_url = image_url
                session.commit()
                return jsonify({'success': True, 'image_url': image_url})
        
        # Handle file upload
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add article ID to filename to avoid conflicts
                name, ext = os.path.splitext(filename)
                filename = f"article_{article_id}_{name}{ext}"
                
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Store relative URL in database
                image_url = f"/static/uploads/{filename}"
                article.image_url = image_url
                session.commit()
                
                return jsonify({'success': True, 'image_url': image_url})
        
        return jsonify({'error': 'No valid image provided'}), 400
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/article/<int:article_id>/image', methods=['DELETE'])
def delete_article_image(article_id):
    """Delete article image."""
    session = get_session()
    
    try:
        article = session.get(Article, article_id)
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        old_image_url = article.image_url
        
        # Remove image URL from database
        article.image_url = None
        session.commit()
        
        # Try to delete the physical file if it's an uploaded file
        if old_image_url and old_image_url.startswith('/static/uploads/'):
            try:
                file_path = old_image_url[1:]  # Remove leading '/'
                full_path = os.path.join(os.getcwd(), file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
            except Exception as e:
                # Log the error but don't fail the request
                print(f"Could not delete file {old_image_url}: {e}")
        
        return jsonify({'success': True, 'message': 'Image deleted successfully'})
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

def allowed_file(filename):
    """Check if file extension is allowed."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
