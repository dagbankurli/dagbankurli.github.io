#!/usr/bin/env python3
"""
Script to extract dictionary data from dagbon-digital.com/dictionary
and convert it to JSON format for the Dagbani Korli application.
"""

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

def extract_word_data(word_element):
    """Extract data from a word entry element"""
    try:
        # Get the word (Dagbani)
        word_heading = word_element.find('h2') or word_element.find('h3')
        if not word_heading:
            return None
        
        dagbani_word = word_heading.get_text(strip=True)
        
        # Get part of speech
        part_of_speech = None
        pos_elem = word_element.find(text=re.compile(r'(Noun|Verb|Adjective|Adverb|Pronoun|Preposition|Conjunction|Interjection)'))
        if pos_elem:
            part_of_speech = pos_elem.strip()
        
        # Get definitions
        definitions = []
        example_sentences = []
        
        # Look for numbered definitions
        definition_items = word_element.find_all('li') or word_element.find_all('p')
        for item in definition_items:
            text = item.get_text(strip=True)
            # Check if it's a definition (starts with number)
            if re.match(r'^\d+\.', text):
                definition = re.sub(r'^\d+\.\s*', '', text)
                definitions.append(definition)
            # Check if it's an example (italicized or in quotes)
            elif text.startswith('*') or text.startswith('"') or text.startswith("'"):
                example = text.lstrip('*').strip().strip('"').strip("'")
                if example:
                    example_sentences.append(example)
        
        # If no definitions found, try to get all text
        if not definitions:
            all_text = word_element.get_text()
            # Try to extract definitions from text
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            for line in lines:
                if re.match(r'^\d+\.', line):
                    definition = re.sub(r'^\d+\.\s*', '', line)
                    definitions.append(definition)
        
        # Get English translation (usually first definition or in a specific format)
        english_word = definitions[0] if definitions else dagbani_word
        
        # Build grammar notes
        grammar_notes = []
        if part_of_speech:
            grammar_notes.append(f"Part of speech: {part_of_speech}")
        if len(definitions) > 1:
            grammar_notes.append(f"Multiple definitions: {len(definitions)}")
        
        return {
            'dagbani': dagbani_word,
            'english': english_word,
            'dialect': 'standard',
            'category': 'general',
            'grammar': '; '.join(grammar_notes) if grammar_notes else None,
            'example': example_sentences[0] if example_sentences else None,
            'definitions': definitions,
            'partOfSpeech': part_of_speech,
            'verified': True,
            'dateAdded': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error extracting word: {e}")
        return None

def scrape_dagbon_digital():
    """Scrape dictionary data from dagbon-digital.com"""
    base_url = "https://dagbon-digital.com/dictionary"
    words = []
    
    print("Fetching dictionary page...")
    try:
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find word entries - adjust selectors based on actual HTML structure
        # Common patterns: article tags, divs with specific classes, etc.
        word_containers = soup.find_all(['article', 'div'], class_=re.compile(r'word|entry|dictionary', re.I))
        
        # If no specific containers, try to find all headings followed by definitions
        if not word_containers:
            # Look for h2/h3 tags that might be word headings
            headings = soup.find_all(['h2', 'h3', 'h4'])
            for heading in headings:
                # Get the parent container
                container = heading.find_parent(['article', 'div', 'section'])
                if container:
                    word_data = extract_word_data(container)
                    if word_data:
                        words.append(word_data)
        else:
            for container in word_containers:
                word_data = extract_word_data(container)
                if word_data:
                    words.append(word_data)
        
        print(f"Found {len(words)} words from main page")
        
        # Try to get more words by browsing letters
        # The site has letter navigation: abchdɛefggbhijkkplmnnyoŋŋmpsshtvwyzʒ
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 's', 't', 'v', 'w', 'y', 'z']
        
        print("Attempting to fetch words by letter...")
        for letter in letters[:5]:  # Limit to first 5 letters to avoid too many requests
            try:
                letter_url = f"{base_url}?letter={letter}"
                print(f"  Fetching {letter}...")
                response = requests.get(letter_url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    letter_containers = soup.find_all(['article', 'div'], class_=re.compile(r'word|entry', re.I))
                    for container in letter_containers:
                        word_data = extract_word_data(container)
                        if word_data and word_data not in words:
                            words.append(word_data)
                time.sleep(1)  # Be respectful with requests
            except Exception as e:
                print(f"  Error fetching letter {letter}: {e}")
                continue
        
    except requests.RequestException as e:
        print(f"Error fetching website: {e}")
        return None
    except Exception as e:
        print(f"Error parsing website: {e}")
        return None
    
    return words

def save_to_json(words, filename='dagbon_digital_import.json'):
    """Save words to JSON file"""
    # Assign IDs
    for i, word in enumerate(words, 1):
        word['id'] = i
    
    output_data = {
        'words': words,
        'exportDate': datetime.now().isoformat(),
        'source': 'dagbon-digital.com/dictionary'
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(words)} words to {filename}")
    return filename

def main():
    print("=" * 60)
    print("Dagbon Digital Dictionary Importer")
    print("=" * 60)
    
    words = scrape_dagbon_digital()
    
    if not words:
        print("\n❌ No words extracted. The website structure may have changed.")
        print("   You may need to manually inspect the HTML or use a different approach.")
        return
    
    # Remove duplicates
    seen = set()
    unique_words = []
    for word in words:
        key = (word['dagbani'].lower(), word['english'].lower())
        if key not in seen:
            seen.add(key)
            unique_words.append(word)
    
    print(f"\nTotal unique words: {len(unique_words)}")
    
    # Show samples
    if unique_words:
        print("\nSample entries:")
        for word in unique_words[:5]:
            print(f"  • {word['dagbani']} → {word['english']}")
            if word.get('example'):
                print(f"    Example: {word['example']}")
    
    # Save to file
    filename = save_to_json(unique_words)
    
    print(f"\n📥 You can now import this file using:")
    print(f"   Settings > Import Data in the Dagbani Korli app")
    print(f"\n   Or manually add the data by opening: {filename}")

if __name__ == '__main__':
    main()
