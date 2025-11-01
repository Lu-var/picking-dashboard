"""
Clean and fix product names in the database
"""

import json
import re
from collections import defaultdict

def clean_product_name(name, brand):
    """Clean product name by removing artifacts and duplicates"""
    if not name:
        return name
    
    # Remove "Pickeado" (OCR artifact from "picked" status)
    cleaned = re.sub(r'\bPickeado\b', '', name, flags=re.IGNORECASE)
    
    # Remove duplicate brand names
    if brand and brand.lower() in cleaned.lower():
        # Remove brand name if it appears multiple times
        brand_pattern = re.escape(brand)
        matches = re.findall(brand_pattern, cleaned, flags=re.IGNORECASE)
        if len(matches) > 1:
            # Keep only the first occurrence
            cleaned = re.sub(brand_pattern, '', cleaned, flags=re.IGNORECASE)
            cleaned = brand + ' ' + cleaned
    
    # Remove common OCR artifacts and UI elements
    artifacts = [
        r'\bPASILLO\s*\d+\b',
        r'\bESTANTE\s*\d+\b',
        r'\b\d{1,3}\s*cc\b',  # Volume indicators that became brands
        r'\b\d{1,3}\s*ml\b',
        r'\b\d{1,3}\s*g\b(?!\w)',  # Weight indicators
        r'\b\d{1,3}\s*L\b',
        r'\b\d+\s*un\.\s*$',  # Unit indicators at the end
        r'\bDrenado\b',
        r'\bNeto\b',
        r'\bPack\s*Ahorro\b',
        r'\bPREMIUM\b',
        r'\bBASICA\b',
        r'^[A-Z\s]+$',  # All caps words at start
    ]
    
    for pattern in artifacts:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Fix repeated words
    words = cleaned.split()
    seen = set()
    unique_words = []
    for word in words:
        word_lower = word.lower()
        if word_lower not in seen or len(word) <= 2:  # Keep short words like "de", "al"
            unique_words.append(word)
            seen.add(word_lower)
    
    cleaned = ' '.join(unique_words)
    
    # Clean up multiple spaces and trim
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Remove leading/trailing punctuation and numbers
    cleaned = re.sub(r'^[^\w]+|[^\w]+$', '', cleaned)
    
    # If result is too short or empty, try to salvage
    if len(cleaned) < 3:
        # Try to extract meaningful parts from original
        words = name.split()
        meaningful_words = []
        for word in words:
            if (len(word) > 2 and 
                not word.isdigit() and 
                word.lower() not in ['pickeado', 'pasillo', 'estante'] and
                not word.startswith('$')):
                meaningful_words.append(word)
        
        if meaningful_words:
            cleaned = ' '.join(meaningful_words[:6])  # Take first 6 meaningful words
        else:
            cleaned = name  # Fallback to original
    
    return cleaned

def fix_incorrect_brands(products):
    """Fix brands that are clearly wrong (like '470cc', 'ml', etc.)"""
    brand_fixes = {
        '470cc': 'Austral',
        'ml': 'Unknown',
        'g': 'Unknown', 
        '25m': 'Confort',
        'L': 'Unknown'
    }
    
    for product in products.values():
        if product['brand'] in brand_fixes:
            # Try to extract real brand from name
            name = product['name']
            if 'Austral' in name:
                product['brand'] = 'Austral'
            elif 'Confort' in name:
                product['brand'] = 'Confort'
            else:
                product['brand'] = brand_fixes[product['brand']]

def main():
    """Clean the product database"""
    print("🧹 Cleaning Product Database...")
    
    # Load database
    with open('data/product_database.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    # Track changes
    changes = []
    
    # Clean product names
    for product_id, product in db['products'].items():
        original_name = product['name']
        original_brand = product['brand']
        
        # Clean the name
        cleaned_name = clean_product_name(original_name, original_brand)
        
        if cleaned_name != original_name:
            changes.append({
                'id': product_id,
                'brand': original_brand,
                'old_name': original_name,
                'new_name': cleaned_name
            })
            product['name'] = cleaned_name
    
    # Fix incorrect brands
    fix_incorrect_brands(db['products'])
    
    # Save cleaned database
    with open('data/product_database_cleaned.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Cleaned {len(changes)} product names")
    print("\n📝 Sample changes:")
    for change in changes[:10]:
        print(f"  [{change['brand']}]")
        print(f"    Old: {change['old_name'][:60]}...")
        print(f"    New: {change['new_name'][:60]}...")
        print()
    
    print(f"💾 Cleaned database saved as 'product_database_cleaned.json'")
    
    # Also update the main database
    with open('data/product_database.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    
    print("✅ Main database updated!")

if __name__ == "__main__":
    main()