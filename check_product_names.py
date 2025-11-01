"""
Check for potentially incorrect product names
"""
import json

with open('data/product_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

print('=== CHECKING PRODUCT NAMES ===')
suspicious_names = []

for product_id, product in db['products'].items():
    name = product['name']
    
    # Flag suspicious patterns
    if (len(name) < 5 or  # Very short names
        name.count(' ') > 10 or  # Too many words
        any(char in name for char in ['|', '/', 'PASILLO', 'ESTANTE']) or  # UI elements
        name.startswith(('$', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9')) or  # Starts with numbers/prices
        'HTTP' in name.upper() or
        len([c for c in name if c.isdigit()]) > len(name) // 2):  # Too many numbers
        
        suspicious_names.append({
            'id': product_id,
            'name': name,
            'brand': product['brand']
        })

print(f'Found {len(suspicious_names)} potentially incorrect names:')
for item in suspicious_names[:10]:  # Show first 10
    print(f'  - {item["brand"]}: {item["name"][:60]}...')

if suspicious_names:
    print(f'\nShowing all {len(suspicious_names)} suspicious names:')
    for i, item in enumerate(suspicious_names, 1):
        print(f'{i:2d}. [{item["brand"]}] {item["name"]}')