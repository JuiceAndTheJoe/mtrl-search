#!/usr/bin/env python3
"""
Skript för att visa innehållet i PDF-databasen
"""

from models import get_session, PDFDocument
from datetime import datetime

def view_database():
    """Visar alla dokument i databasen"""
    session = get_session()
    
    try:
        # Hämta alla dokument
        documents = session.query(PDFDocument).all()
        
        print(f"\n=== mtrl-search Databas ===")
        print(f"Totalt antal dokument: {len(documents)}\n")
        
        if not documents:
            print("Inga dokument hittades i databasen.")
            return
        
        # Visa detaljerad information för varje dokument
        for i, doc in enumerate(documents, 1):
            print(f"--- Dokument {i} ---")
            print(f"ID: {doc.id}")
            print(f"Filnamn: {doc.filename}")
            print(f"Titel: {doc.title or 'Ingen titel'}")
            print(f"Författare: {doc.author or 'Okänd'}")
            print(f"Antal sidor: {doc.num_pages}")
            print(f"Filsökväg: {doc.file_path}")
            print(f"Indexerad: {doc.indexed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Visa första 200 tecken av innehållet
            content_preview = doc.content[:200] if doc.content else "Inget innehåll"
            print(f"Innehåll (förhandsgranskning): {content_preview}...")
            print(f"Totalt innehåll: {len(doc.content)} tecken")
            print("-" * 50)
        
    except Exception as e:
        print(f"Fel vid läsning av databas: {e}")
    
    finally:
        session.close()

def search_database(query):
    """Söker i databasen efter en specifik term"""
    session = get_session()
    
    try:
        from sqlalchemy import or_
        
        # Sök i titel, författare, filnamn och innehåll
        search_filter = or_(
            PDFDocument.title.ilike(f'%{query}%'),
            PDFDocument.author.ilike(f'%{query}%'),
            PDFDocument.filename.ilike(f'%{query}%'),
            PDFDocument.content.ilike(f'%{query}%')
        )
        
        results = session.query(PDFDocument).filter(search_filter).all()
        
        print(f"\n=== Sökresultat för '{query}' ===")
        print(f"Hittade {len(results)} resultat\n")
        
        for i, doc in enumerate(results, 1):
            print(f"--- Resultat {i} ---")
            print(f"Titel: {doc.title or doc.filename}")
            print(f"Filnamn: {doc.filename}")
            print(f"Författare: {doc.author or 'Okänd'}")
            print(f"Sidor: {doc.num_pages}")
            print("-" * 30)
    
    except Exception as e:
        print(f"Fel vid sökning: {e}")
    
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Om argument anges, använd det som sökterm
        query = " ".join(sys.argv[1:])
        search_database(query)
    else:
        # Annars visa alla dokument
        view_database()
    
    print("\nAnvändning:")
    print("python view_database.py                    # Visa alla dokument")
    print("python view_database.py 'sökterm'         # Sök efter specifik term")