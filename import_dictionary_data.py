#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive script to import dictionary data from multiple sources:
1. Dagbon Digital website (dagbon-digital.com/dictionary)
2. PDF files (Dagbani_Dictionary_24_Oct_2014.pdf)
"""

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Try to import PDF libraries
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

def extract_from_pdf(pdf_path):
    """Extract dictionary data from PDF file"""
    if not HAS_PDFPLUMBER:
        print("pdfplumber not installed. Install with: pip install pdfplumber")
        return []
    
    print(f"\n[PDF] Extracting from PDF: {pdf_path}")
    words = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"   Total pages: {len(pdf.pages)}")
            
            for page_num, page in enumerate(pdf.pages, 1):
                if page_num % 10 == 0:
                    print(f"   Processing page {page_num}...")
                
                text = page.extract_text()
                if not text:
                    continue
                
                # Try to extract words from the page
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line or len(line) < 3:
                        continue
                    
                    # Pattern: English : Dagbani
                    if ':' in line:
                        parts = line.split(':', 1)
                        english = parts[0].strip()
                        dagbani = parts[1].strip()
                        
                        if len(english) < 100 and len(dagbani) < 100:
                            words.append({
                                'english': english,
                                'dagbani': dagbani,
                                'dialect': 'standard',
                                'category': 'general',
                                'grammar': None,
                                'example': None,
                                'verified': True,
                                'dateAdded': datetime.now().isoformat()
                            })
        
        print(f"   Extracted {len(words)} potential entries")
        return words
        
    except Exception as e:
        print(f"   Error: {e}")
        return []

def extract_from_website():
    """Extract dictionary data from dagbon-digital.com"""
    print("\n🌐 Extracting from dagbon-digital.com...")
    words = []
    
    try:
        # Try to fetch the main dictionary page
        url = "https://dagbon-digital.com/dictionary"
        print(f"   Fetching: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Based on the website structure, look for word entries
        # The site shows words with definitions, examples, etc.
        
        # Try to find word containers - adjust based on actual HTML
        word_sections = soup.find_all(['article', 'div', 'section'], 
                                      class_=re.compile(r'word|entry|dictionary|card', re.I))
        
        if not word_sections:
            # Alternative: look for headings that might be words
            headings = soup.find_all(['h2', 'h3', 'h4'])
            for heading in headings:
                text = heading.get_text(strip=True)
                # If it looks like a Dagbani word (not too long, has special chars)
                if len(text) < 50 and text:
                    # Get the next sibling or parent for definition
                    parent = heading.find_parent(['article', 'div', 'section'])
                    if parent:
                        # Try to extract definition
                        definition_elem = parent.find('p') or parent.find('li')
                        if definition_elem:
                            definition = definition_elem.get_text(strip=True)
                            # Extract English from definition
                            english = definition.split('.')[0] if '.' in definition else definition[:50]
                            
                            words.append({
                                'dagbani': text,
                                'english': english,
                                'dialect': 'standard',
                                'category': 'general',
                                'grammar': None,
                                'example': None,
                                'verified': True,
                                'dateAdded': datetime.now().isoformat()
                            })
        else:
            for section in word_sections:
                # Extract word data
                heading = section.find(['h2', 'h3', 'h4'])
                if heading:
                    dagbani = heading.get_text(strip=True)
                    
                    # Find definition
                    definition = None
                    for p in section.find_all('p'):
                        text = p.get_text(strip=True)
                        if text and not text.startswith('*'):
                            definition = text
                            break
                    
                    if dagbani and definition:
                        words.append({
                            'dagbani': dagbani,
                            'english': definition[:100],
                            'dialect': 'standard',
                            'category': 'general',
                            'grammar': None,
                            'example': None,
                            'verified': True,
                            'dateAdded': datetime.now().isoformat()
                        })
        
        print(f"   Found {len(words)} words")
        return words
        
    except Exception as e:
        print(f"   Error: {e}")
        return []

def clean_and_deduplicate(words):
    """Clean and remove duplicate entries"""
    seen = set()
    cleaned = []
    
    for word in words:
        # Clean whitespace
        word['english'] = word.get('english', '').strip()
        word['dagbani'] = word.get('dagbani', '').strip()
        
        # Skip empty entries
        if not word['english'] or not word['dagbani']:
            continue
        
        # Skip if too long (probably not a word)
        if len(word['english']) > 200 or len(word['dagbani']) > 200:
            continue
        
        # Check for duplicates
        key = (word['english'].lower(), word['dagbani'].lower())
        if key not in seen:
            seen.add(key)
            cleaned.append(word)
    
    return cleaned

def save_to_json(words, source, filename=None):
    """Save words to JSON file"""
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'dictionary_import_{timestamp}.json'
    
    # Assign IDs
    for i, word in enumerate(words, 1):
        word['id'] = i
    
    output_data = {
        'words': words,
        'exportDate': datetime.now().isoformat(),
        'source': source,
        'totalEntries': len(words)
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    return filename

def main():
    print("=" * 70)
    print("Dagbani Dictionary Data Importer")
    print("=" * 70)
    
    all_words = []
    sources = []
    
    # Option 1: Extract from PDF
    pdf_path = 'Dagbani_Dictionary_24_Oct_2014.pdf'
    try:
        import os
        if os.path.exists(pdf_path):
            pdf_words = extract_from_pdf(pdf_path)
            if pdf_words:
                all_words.extend(pdf_words)
                sources.append('PDF: Dagbani_Dictionary_24_Oct_2014.pdf')
    except Exception as e:
        print(f"PDF extraction error: {e}")
    
    # Option 2: Extract from website
    try:
        website_words = extract_from_website()
        if website_words:
            all_words.extend(website_words)
            sources.append('Website: dagbon-digital.com')
    except Exception as e:
        print(f"Website extraction error: {e}")
    
    if not all_words:
        print("\n[ERROR] No words extracted from any source.")
        print("\nOptions:")
        print("1. Check if the PDF file exists and is readable")
        print("2. The website structure may have changed")
        print("3. You can manually create a JSON file with this format:")
        print('{"words": [{"english": "Hello", "dagbani": "Antire", "dialect": "standard", "category": "greetings", "grammar": null, "example": null, "verified": true}]}')
        return
    
    # Clean and deduplicate
    print(f"\n[CLEAN] Cleaning {len(all_words)} entries...")
    cleaned_words = clean_and_deduplicate(all_words)
    print(f"   After cleaning: {len(cleaned_words)} unique entries")
    
    # Show samples
    if cleaned_words:
        print("\n[SAMPLE] Sample entries:")
        for word in cleaned_words[:5]:
            print(f"   - {word['english']} -> {word['dagbani']}")
    
    # Save to file
    source_str = ' + '.join(sources) if sources else 'Unknown'
    filename = save_to_json(cleaned_words, source_str)
    
    print(f"\n[SUCCESS] Dictionary data saved to: {filename}")
    print(f"   Total entries: {len(cleaned_words)}")
    print(f"\n[IMPORT] To import into the app:")
    print(f"   1. Open the Dagbani Korli app in your browser")
    print(f"   2. Go to Settings")
    print(f"   3. Click 'Import Data (Restore)'")
    print(f"   4. Select the file: {filename}")

if __name__ == '__main__':
    main()
