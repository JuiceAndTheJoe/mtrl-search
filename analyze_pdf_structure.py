#!/usr/bin/env python3
"""
Skript för att analysera PDF-struktur och hitta kapitel 9 med artikeltabellen
"""

import PyPDF2
import re
from pathlib import Path

def analyze_pdf_structure(pdf_path):
    """Analyserar PDF:en för att hitta kapitel 9 och tabellstrukturen"""
    
    print(f"Analyserar PDF: {pdf_path}")
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            print(f"Totalt antal sidor: {total_pages}")
            
            # Leta efter kapitel 9
            chapter_9_found = False
            chapter_9_page = None
            
            for page_num in range(total_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    # Leta efter kapitel 9
                    if not chapter_9_found:
                        # Olika sätt att skriva kapitel 9
                        patterns = [
                            r'9\s*[-–—]\s*Tillverkardokumentation',
                            r'Kapitel\s*9',
                            r'9\.\s*Tillverkardokumentation',
                            r'9\s+Tillverkardokumentation'
                        ]
                        
                        for pattern in patterns:
                            if re.search(pattern, text, re.IGNORECASE):
                                chapter_9_found = True
                                chapter_9_page = page_num + 1
                                print(f"\n✅ Hittade kapitel 9 på sida {chapter_9_page}")
                                break
                    
                    # Om vi hittat kapitel 9, leta efter tabelldata
                    if chapter_9_found and (page_num >= chapter_9_page - 1):
                        # Leta efter kolumnrubriker
                        if any(header in text.upper() for header in ['FBET', 'FBEN', 'ARTIKEL', 'LÄNK']):
                            print(f"\n📋 Hittade potentiell tabelldel på sida {page_num + 1}")
                            
                            # Visa textutdrag för analys
                            lines = text.split('\n')
                            relevant_lines = []
                            
                            for i, line in enumerate(lines):
                                line_upper = line.upper()
                                if any(header in line_upper for header in ['FBET', 'FBEN', 'ARTIKEL', 'LÄNK']):
                                    # Ta med 5 rader före och 20 rader efter
                                    start = max(0, i - 5)
                                    end = min(len(lines), i + 20)
                                    relevant_lines.extend(lines[start:end])
                                    break
                            
                            if relevant_lines:
                                print(f"\n--- Textutdrag från sida {page_num + 1} ---")
                                for line in relevant_lines[:30]:  # Visa första 30 raderna
                                    if line.strip():
                                        print(f"{line}")
                                print("...")
                                break
                
                except Exception as e:
                    print(f"Fel vid läsning av sida {page_num + 1}: {e}")
                    continue
            
            if not chapter_9_found:
                print("\n❌ Kunde inte hitta kapitel 9. Låt oss söka efter 'Tillverkardokumentation':")
                
                # Bred sökning efter nyckelord
                for page_num in range(min(20, total_pages)):  # Kolla första 20 sidorna
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        
                        if 'Tillverkardokumentation' in text or 'TILLVERKARDOKUMENTATION' in text:
                            print(f"\n📄 Hittade 'Tillverkardokumentation' på sida {page_num + 1}")
                            
                            # Visa sammanhang
                            lines = text.split('\n')
                            for i, line in enumerate(lines):
                                if 'tillverkardokumentation' in line.lower():
                                    start = max(0, i - 3)
                                    end = min(len(lines), i + 10)
                                    print("--- Sammanhang ---")
                                    for j in range(start, end):
                                        marker = ">>> " if j == i else "    "
                                        print(f"{marker}{lines[j]}")
                                    break
                            break
                    
                    except Exception as e:
                        continue
            
            # Sök även efter tabellmönster med FBET/FBEN
            print(f"\n🔍 Söker efter FBET/FBEN-mönster i hela dokumentet...")
            
            for page_num in range(total_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    # Leta efter FBET eller FBEN följt av siffror
                    fbet_matches = re.findall(r'FBET\s*\d+', text, re.IGNORECASE)
                    fben_matches = re.findall(r'FBEN\s*\d+', text, re.IGNORECASE)
                    
                    if fbet_matches or fben_matches:
                        print(f"\n📊 Sida {page_num + 1} innehåller:")
                        if fbet_matches:
                            print(f"   FBET-koder: {fbet_matches[:5]}...")  # Visa första 5
                        if fben_matches:
                            print(f"   FBEN-koder: {fben_matches[:5]}...")  # Visa första 5
                
                except Exception as e:
                    continue
                
    except Exception as e:
        print(f"Fel vid analys av PDF: {e}")

def main():
    # Hitta PDF-filen
    pdf_dir = Path("./pdfs")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("Ingen PDF-fil hittades i pdfs-mappen")
        return
    
    for pdf_file in pdf_files:
        print(f"\n{'='*60}")
        analyze_pdf_structure(pdf_file)
        print(f"{'='*60}")

if __name__ == "__main__":
    main()