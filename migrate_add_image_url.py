"""
Migration script to add image_url column to articles table.
Run this once to update your existing database with the new image_url field.
"""
import sqlite3
import os

def migrate_database():
    """Add image_url column to articles table if it doesn't exist."""
    db_path = 'pdf_index.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. No migration needed.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if image_url column already exists
        cursor.execute("PRAGMA table_info(articles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'image_url' in columns:
            print("Column 'image_url' already exists in articles table. No migration needed.")
            return
        
        # Add the image_url column
        cursor.execute("ALTER TABLE articles ADD COLUMN image_url VARCHAR(1000)")
        conn.commit()
        print("Successfully added 'image_url' column to articles table.")
        
        # Optional: Set some example image URLs for testing
        # You can uncomment and modify this section to add test images
        """
        cursor.execute('''
            UPDATE articles 
            SET image_url = 'https://via.placeholder.com/80x80?text=IMG' 
            WHERE id <= 3
        ''')
        conn.commit()
        print("Added example image URLs to first 3 articles for testing.")
        """
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()