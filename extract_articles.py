#!/usr/bin/env python3
"""
Skript för att extrahera artikelinformation från kapitel 9 - Tillverkardokumentation
"""

import pdfplumber
import re
from pathlib import Path
from models import get_session, PDFDocument, Article, init_db
from sqlalchemy import or_

def find_chapter_9_pages(pdf_path):
    """Hitta sidorna som innehåller kapitel 9 - Tillverkardokumentation"""
    pages_with_articles = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Analyserar {total_pages} sidor för att hitta artikeltabeller...")
        
        for page_num in range(total_pages):
            try:
                page = pdf.pages[page_num]
                text = page.extract_text()
                
                if text:
                    # Leta efter kolumnrubriker eller FBET/FBEN-koder
                    if any(header in text.upper() for header in ['FBET', 'FBEN', 'ARTIKEL']):
                        # Kontrollera om det verkligen ser ut som en tabell med alla kolumner
                        if all(col in text.upper() for col in ['FBET', 'FBEN', 'ARTIKEL', 'LÄNK']):
                            pages_with_articles.append(page_num)
                            print(f"✅ Hittade komplett artikeltabell på sida {page_num + 1}")
                        elif 'FBET' in text.upper() or 'FBEN' in text.upper():
                            pages_with_articles.append(page_num)
                            print(f"📋 Hittade partiell artikeldata på sida {page_num + 1}")
                            
            except Exception as e:
                print(f"Fel vid analys av sida {page_num + 1}: {e}")
                continue
    
    return pages_with_articles

def extract_articles_from_page(page):
    """Extraherar artikeldata från en enskild sida"""
    articles = []
    
    try:
        # Prova först att extrahera som tabell
        tables = page.extract_tables()
        
        if tables:
            print(f"Hittade {len(tables)} tabeller på sidan")
            
            for table_idx, table in enumerate(tables):
                if table and len(table) > 0:
                    # Leta efter header-raden
                    header_row = None
                    for i, row in enumerate(table):
                        if row and any(cell and any(header in str(cell).upper() 
                                     for header in ['FBET', 'FBEN', 'ARTIKEL', 'LÄNK']) 
                                     for cell in row if cell):
                            header_row = i
                            break
                    
                    if header_row is not None:
                        headers = table[header_row]
                        print(f"Tabell {table_idx + 1} headers: {headers}")
                        
                        # Hitta kolumnindex
                        fbet_idx = fben_idx = artikel_idx = link_idx = None
                        
                        for i, header in enumerate(headers):
                            if header:
                                header_upper = str(header).upper()
                                if 'FBET' in header_upper:
                                    fbet_idx = i
                                elif 'FBEN' in header_upper:
                                    fben_idx = i
                                elif 'ARTIKEL' in header_upper:
                                    artikel_idx = i
                                elif 'LÄNK' in header_upper or 'LINK' in header_upper:
                                    link_idx = i
                        
                        print(f"Kolumnindex - FBET: {fbet_idx}, FBEN: {fben_idx}, ARTIKEL: {artikel_idx}, LÄNK: {link_idx}")
                        
                        # Extrahera data från raderna efter header
                        for row in table[header_row + 1:]:
                            if row and len(row) > max(filter(None, [fbet_idx, fben_idx, artikel_idx, link_idx] or [0])):
                                fbet = str(row[fbet_idx]) if fbet_idx is not None and fbet_idx < len(row) and row[fbet_idx] else None
                                fben = str(row[fben_idx]) if fben_idx is not None and fben_idx < len(row) and row[fben_idx] else None
                                artikel = str(row[artikel_idx]) if artikel_idx is not None and artikel_idx < len(row) and row[artikel_idx] else None
                                link = str(row[link_idx]) if link_idx is not None and link_idx < len(row) and row[link_idx] else None
                                
                                # Filtrera bort tomma rader
                                if any(val and val.strip() and val.strip() != 'None' for val in [fbet, fben, artikel, link]):
                                    articles.append({
                                        'fbet': fbet.strip() if fbet and fbet != 'None' else None,
                                        'fben': fben.strip() if fben and fben != 'None' else None,
                                        'artikel': artikel.strip() if artikel and artikel != 'None' else None,
                                        'link': link.strip() if link and link != 'None' else None
                                    })
        
        # Om inga tabeller hittades, prova textbaserad extraktion
        if not articles:
            text = page.extract_text()
            if text:
                articles.extend(extract_articles_from_text(text))
                
    except Exception as e:
        print(f"Fel vid extraktion från sida: {e}")
    
    return articles

def extract_articles_from_text(text):
    """Försöker extrahera artikeldata från vanlig text"""
    articles = []
    
    try:
        lines = text.split('\n')
        
        for line in lines:
            # Leta efter rader som kan innehålla FBET/FBEN-koder
            fbet_match = re.search(r'FBET\s*[-:]?\s*(\w+)', line, re.IGNORECASE)
            fben_match = re.search(r'FBEN\s*[-:]?\s*(\w+)', line, re.IGNORECASE)
            
            if fbet_match or fben_match:
                # Försök extrahera mer information från samma rad
                fbet = fbet_match.group(1) if fbet_match else None
                fben = fben_match.group(1) if fben_match else None
                
                # Leta efter URL/länk i samma rad
                link_match = re.search(r'(https?://[^\s]+)', line)
                link = link_match.group(1) if link_match else None
                
                # Resten av raden kan vara artikelbeskrivning
                artikel = line.strip()
                
                articles.append({
                    'fbet': fbet,
                    'fben': fben,
                    'artikel': artikel,
                    'link': link
                })
    
    except Exception as e:
        print(f"Fel vid textbaserad extraktion: {e}")
    
    return articles

def extract_all_articles(pdf_path, document_id):
    """Extraherar alla artiklar från PDF:en och sparar i databasen"""
    
    # Hitta relevanta sidor
    article_pages = find_chapter_9_pages(pdf_path)
    
    if not article_pages:
        print("❌ Inga sidor med artikeldata hittades")
        return []
    
    all_articles = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in article_pages:
            print(f"\n📄 Extraherar från sida {page_num + 1}...")
            page = pdf.pages[page_num]
            
            page_articles = extract_articles_from_page(page)
            
            if page_articles:
                print(f"   Hittade {len(page_articles)} artiklar")
                all_articles.extend(page_articles)
                
                # Visa exempel
                for i, article in enumerate(page_articles[:3]):  # Visa första 3
                    print(f"   {i+1}: FBET={article.get('fbet', 'N/A')}, FBEN={article.get('fben', 'N/A')}")
                    print(f"      Artikel: {article.get('artikel', 'N/A')[:100]}...")
            else:
                print(f"   Inga artiklar hittades på denna sida")
    
    # Spara i databas
    if all_articles:
        session = get_session()
        try:
            # Ta bort gamla artiklar för detta dokument först
            session.query(Article).filter_by(document_id=document_id).delete()
            
            # Lägg till nya artiklar
            for article_data in all_articles:
                article = Article(
                    document_id=document_id,
                    fbet=article_data.get('fbet'),
                    fben=article_data.get('fben'),
                    artikel=article_data.get('artikel'),
                    link=article_data.get('link')
                )
                session.add(article)
            
            session.commit()
            print(f"\n✅ Sparade {len(all_articles)} artiklar i databasen")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Fel vid sparande i databas: {e}")
        finally:
            session.close()
    
    return all_articles

def main():
    """Huvudfunktion"""
    # Initiera databas (skapa nya tabeller)
    init_db()
    
    # Hitta PDF-fil
    pdf_dir = Path("./pdfs")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ Ingen PDF-fil hittades i pdfs-mappen")
        return
    
    # Hitta motsvarande dokument i databasen
    session = get_session()
    
    for pdf_file in pdf_files:
        print(f"\n{'='*60}")
        print(f"Bearbetar: {pdf_file.name}")
        print(f"{'='*60}")
        
        # Hitta dokumentet i databasen
        document = session.query(PDFDocument).filter_by(filename=pdf_file.name).first()
        
        if not document:
            print(f"❌ Dokumentet {pdf_file.name} hittades inte i databasen")
            print("Kör först extract_pdfs.py för att indexera PDF:en")
            continue
        
        print(f"📋 Extraherar artiklar från dokument ID: {document.id}")
        
        # Extrahera artiklar
        articles = extract_all_articles(pdf_file, document.id)
        
        print(f"\n📊 Sammanfattning:")
        print(f"   Extraherade artiklar: {len(articles)}")
        
        # Visa statistik
        if articles:
            with_fbet = sum(1 for a in articles if a.get('fbet'))
            with_fben = sum(1 for a in articles if a.get('fben'))
            with_links = sum(1 for a in articles if a.get('link'))
            
            print(f"   Med FBET-kod: {with_fbet}")
            print(f"   Med FBEN-kod: {with_fben}")
            print(f"   Med länkar: {with_links}")
    
    session.close()

if __name__ == "__main__":
    main()