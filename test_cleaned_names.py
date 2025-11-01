"""
Test cleaned product names
"""
import json

with open('data/product_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

print('=== SAMPLE CLEANED PRODUCT NAMES ===')
products = list(db['products'].values())[:10]
for p in products:
    print(f'{p["brand"]:15} | {p["name"][:50]}')

print('\n=== SEARCH TEST: "leche" ===')
results = []
for p in db['products'].values():
    if 'leche' in p['name'].lower() or 'leche' in p['brand'].lower():
        results.append(p)

for p in results[:5]:
    print(f'{p["brand"]:15} | {p["name"][:50]}')