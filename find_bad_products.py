"""
Find products with bad names that need fixing
"""
import json

with open('data/product_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

print('=== PRODUCTS WITH BAD NAMES ===')
bad_products = []

for product_id, product in db['products'].items():
    name = product['name'].strip()
    
    # Flag very short names or single characters/numbers
    if (len(name) <= 2 or  # Very short
        name in ['g', 'L', 'ml', 'cc', 'un', 'kg', '1500', '500', '200'] or  # Just measurements
        name.isdigit() or  # Just numbers
        len(name.split()) == 1 and len(name) <= 3):  # Single short word
        
        bad_products.append({
            'id': product_id,
            'name': name,
            'brand': product['brand'],
            'frequency': product['frequency'],
            'locations': product['locations']
        })

print(f'Found {len(bad_products)} products with bad names:')
for p in bad_products:
    print(f'  - [{p["brand"]}] "{p["name"]}" (freq: {p["frequency"]}) at {p["locations"]}')