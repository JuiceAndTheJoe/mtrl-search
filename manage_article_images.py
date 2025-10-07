"""
Script to add image URLs to existing articles.
This can be used to populate articles with images from various sources.
"""
from models import get_session, Article
import requests
from urllib.parse import quote

def add_placeholder_images():
    """Add placeholder images to articles that don't have images."""
    session = get_session()
    
    try:
        # Get articles without images
        articles_without_images = session.query(Article).filter(
            (Article.image_url == None) | (Article.image_url == '')
        ).all()
        
        print(f"Found {len(articles_without_images)} articles without images.")
        
        for i, article in enumerate(articles_without_images):
            # Generate a placeholder image URL based on article info
            if article.artikel and len(article.artikel) > 3:
                # Use first letters of article name for placeholder
                text = article.artikel[:10].replace(' ', '+')
            elif article.fbet:
                text = article.fbet
            elif article.fben:
                text = article.fben
            else:
                text = f"Art{article.id}"
            
            # Create a placeholder image URL
            # Using placeholder.com service for demo - you can replace with actual image URLs
            placeholder_url = f"https://via.placeholder.com/150x150/0066cc/ffffff?text={quote(text)}"
            
            article.image_url = placeholder_url
            
            print(f"Added placeholder image for article {article.id}: {text}")
        
        session.commit()
        print(f"Successfully updated {len(articles_without_images)} articles with placeholder images.")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

def add_custom_image_url(article_id, image_url):
    """Add a custom image URL to a specific article."""
    session = get_session()
    
    try:
        article = session.get(Article, article_id)
        if not article:
            print(f"Article with ID {article_id} not found.")
            return False
        
        article.image_url = image_url
        session.commit()
        
        print(f"Updated article {article_id} with image: {image_url}")
        return True
        
    except Exception as e:
        print(f"Error updating article: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def list_articles_without_images():
    """List all articles that don't have images."""
    session = get_session()
    
    try:
        articles = session.query(Article).filter(
            (Article.image_url == None) | (Article.image_url == '')
        ).all()
        
        print(f"Articles without images ({len(articles)}):")
        print("-" * 60)
        
        for article in articles:
            print(f"ID: {article.id}")
            print(f"FBET: {article.fbet or 'N/A'}")
            print(f"FBEN: {article.fben or 'N/A'}")
            print(f"Artikel: {(article.artikel or 'N/A')[:50]}...")
            print("-" * 60)
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    print("Image management script for articles")
    print("1. List articles without images")
    print("2. Add placeholder images to all articles")
    print("3. Add custom image to specific article")
    
    choice = input("Choose option (1-3): ").strip()
    
    if choice == '1':
        list_articles_without_images()
    elif choice == '2':
        add_placeholder_images()
    elif choice == '3':
        article_id = int(input("Enter article ID: "))
        image_url = input("Enter image URL: ").strip()
        add_custom_image_url(article_id, image_url)
    else:
        print("Invalid choice.")