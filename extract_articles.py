#!/usr/bin/env python3
"""
Skript för att indexera PDF-dokument och extrahera artikelinformation från kapitel 9 - Tillverkardokumentation
"""

import pdfplumber
import re
import os
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
                    text_upper = text.upper()
                    
                    # Leta efter specifika indikatorer för tillverkardokumentation
                    chapter_indicators = [
                        'TILLVERKARDOKUMENTATION',
                        'KAPITEL 9',
                        'CHAPTER 9'
                    ]
                    
                    # Leta efter artikelkoder och strukturerad data
                    article_indicators = [
                        'FBET',
                        'FBEN', 
                        'F8009-', 'F7773-', 'G8009-', 'G7773-'  # Vanliga FBET-prefixer
                    ]
                    
                    has_chapter = any(indicator in text_upper for indicator in chapter_indicators)
                    has_articles = any(indicator in text_upper for indicator in article_indicators)
                    
                    # Räkna antal potentiella artikelrader (rader med FBET/FBEN-mönster)
                    fbet_matches = len(re.findall(r'[FG]\d{4}-\d{6}', text))
                    
                    if has_chapter or (has_articles and fbet_matches > 2):
                        pages_with_articles.append(page_num)
                        print(f"✅ Hittade artikeldata på sida {page_num + 1} ({fbet_matches} FBET-koder)")
                        
                        # Visa lite kontext
                        if fbet_matches > 0:
                            sample_codes = re.findall(r'[FG]\d{4}-\d{6}', text)[:3]
                            print(f"   Exempel på koder: {', '.join(sample_codes)}")
                            
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
                        row_count = 0
                        for row_idx, row in enumerate(table[header_row + 1:], start=header_row + 1):
                            if row:
                                print(f"  Rad {row_idx}: {row[:5]}...")  # Visa första 5 celler för debug
                                
                                # Kontrollera om raden har tillräckligt med kolumner
                                max_needed_idx = max(filter(None, [fbet_idx, fben_idx, artikel_idx, link_idx] or [0]))
                                if len(row) <= max_needed_idx:
                                    print(f"    Hoppar över rad - för få kolumner ({len(row)} <= {max_needed_idx})")
                                    continue
                                
                                # Extrahera värden
                                fbet = str(row[fbet_idx]).strip() if fbet_idx is not None and fbet_idx < len(row) and row[fbet_idx] else ""
                                fben = str(row[fben_idx]).strip() if fben_idx is not None and fben_idx < len(row) and row[fben_idx] else ""
                                artikel = str(row[artikel_idx]).strip() if artikel_idx is not None and artikel_idx < len(row) and row[artikel_idx] else ""
                                link = str(row[link_idx]).strip() if link_idx is not None and link_idx < len(row) and row[link_idx] else ""
                                
                                # Rensa bort "None" och tomma strängar
                                fbet = fbet if fbet and fbet != 'None' and fbet.strip() != '' else None
                                fben = fben if fben and fben != 'None' and fben.strip() != '' else None
                                artikel = artikel if artikel and artikel != 'None' and artikel.strip() != '' else None
                                link = link if link and link != 'None' and link.strip() != '' else None
                                
                                print(f"    Extraherat - FBET: '{fbet}', FBEN: '{fben}', Artikel: '{artikel}', Länk: '{link}'")
                                
                                # Kontrollera om raden har användbar data
                                if any([fbet, fben, artikel, link]):
                                    articles.append({
                                        'fbet': fbet,
                                        'fben': fben,
                                        'artikel': artikel,
                                        'link': link
                                    })
                                    row_count += 1
                                    print(f"    ✅ Artikel {row_count} tillagd")
                                else:
                                    print(f"    ❌ Tom rad, hoppar över")
                        
                        print(f"Totalt {row_count} artiklar extraherade från tabell {table_idx + 1}")
        
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
        print(f"Textbaserad extraktion: analyserar {len(lines)} rader")
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            # Leta efter specifika mönster för FBET och FBEN
            # FBET: F/G/M följt av 4 siffror, bindestreck och 6 siffror
            fbet_pattern = r'\b([FGM]\d{4}-\d{6})\b'
            
            # FBEN: Försök att hitta mönster för svenska produktnamn
            # Titta efter vanliga FBEN-ord som följer efter FBET-koden
            fben_patterns = [
                r'\b(STANDARDBULT|MINIBULT|KAMSÄKRING|ISSKRUV|BORRKRONA|GUMMFIXERING|EXPANDERBULT|LIMBULT|VAJERKIL|SNABBLÄNK|KLÄTTERSELE|SÄKERHETSSELE|KARBINHAKE|FALLDÄMPARE|SMÖRJFETT|KROK|FIXERING|REPBROMS|REP)\b',
                r'\b([A-ZÅÄÖ]{5,20})\b'  # Backup pattern för andra ord
            ]
            
            fbet_match = re.search(fbet_pattern, line, re.IGNORECASE)
            fben_match = None
            
            # Prova alla FBEN-mönster
            for pattern in fben_patterns:
                fben_match = re.search(pattern, line, re.IGNORECASE)
                if fben_match:
                    break
            
            # Prioritera rader med FBET-koder, de är mest tillförlitliga
            if fbet_match:
                print(f"  Rad {line_num}: {line}")
                
                fbet = fbet_match.group(1).strip()
                fben = fben_match.group(1).strip() if fben_match else None
                
                # Leta efter URL/länk i samma rad
                link_match = re.search(r'(https?://[^\s]+)', line)
                link = link_match.group(1) if link_match else None
                
                # Extrahera och rensa artikelbeskrivning
                artikel = line
                
                # Ta bort FBET-kod från beskrivningen
                if fbet:
                    artikel = artikel.replace(fbet, '').strip()
                
                # Ta bort FBEN-kod från beskrivningen 
                if fben:
                    artikel = artikel.replace(fben, '').strip()
                
                # Ta bort länk från beskrivningen
                if link:
                    artikel = artikel.replace(link, '').strip()
                
                # Ta bort extra mellanslag och tomma delar
                artikel = re.sub(r'\s+', ' ', artikel).strip()
                
                # Hoppa över för korta beskrivningar eller headers
                if not artikel or len(artikel) < 5 or artikel.upper() in ['FBET FBEN ARTIKEL LÄNK', 'FBET', 'FBEN', 'ARTIKEL', 'LÄNK']:
                    artikel = None
                
                # För M-prefix koder, behandla dem som FBET om de är längre än 10 tecken
                if not fbet and re.match(r'M\d{4}-\d{6}', line):
                    m_match = re.search(r'(M\d{4}-\d{6})', line)
                    if m_match:
                        fbet = m_match.group(1)
                        artikel = artikel.replace(fbet, '').strip() if artikel else artikel
                
                print(f"    FBET: '{fbet}', FBEN: '{fben}', Artikel: '{artikel}', Länk: '{link}'")
                
                if any([fbet, fben, artikel, link]):
                    articles.append({
                        'fbet': fbet,
                        'fben': fben,
                        'artikel': artikel,
                        'link': link
                    })
    
    except Exception as e:
        print(f"Fel vid textbaserad extraktion: {e}")
    
    print(f"Textbaserad extraktion: hittade {len(articles)} artiklar")
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

def index_pdf_document(pdf_path):
    """Indexerar ett PDF-dokument och sparar grundläggande information i databasen"""
    session = get_session()
    
    try:
        # Kontrollera om dokumentet redan finns
        filename = pdf_path.name
        existing_doc = session.query(PDFDocument).filter_by(filename=filename).first()
        
        if existing_doc:
            print(f"📋 Dokumentet {filename} finns redan indexerat (ID: {existing_doc.id})")
            return existing_doc
        
        print(f"📝 Indexerar nytt dokument: {filename}")
        
        # Extrahera metadata från PDF
        with pdfplumber.open(pdf_path) as pdf:
            # Hämta metadata
            metadata = pdf.metadata or {}
            title = metadata.get('Title', '') or filename
            author = metadata.get('Author', '') or metadata.get('Creator', '')
            
            # Extrahera text från första sidan för innehållsindexering
            content = ""
            try:
                if len(pdf.pages) > 0:
                    first_page_text = pdf.pages[0].extract_text() or ""
                    content = first_page_text[:5000]  # Begränsa till första 5000 tecken
            except Exception as e:
                print(f"Varning: Kunde inte extrahera text från första sidan: {e}")
            
            # Skapa nytt dokument i databasen
            document = PDFDocument(
                filename=filename,
                title=title,
                author=author,
                num_pages=len(pdf.pages),
                content=content,
                file_path=str(pdf_path.absolute())
            )
            
            session.add(document)
            session.commit()
            
            print(f"✅ Dokument indexerat med ID: {document.id}")
            print(f"   Titel: {title}")
            print(f"   Författare: {author}")
            print(f"   Antal sidor: {len(pdf.pages)}")
            
            return document
            
    except Exception as e:
        session.rollback()
        print(f"❌ Fel vid indexering av dokument: {e}")
        return None
    finally:
        session.close()

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
        
        # Indexera dokumentet (skapar nytt eller hämtar befintligt)
        document = index_pdf_document(pdf_file)
        
        if not document:
            print(f"❌ Kunde inte indexera dokumentet {pdf_file.name}")
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