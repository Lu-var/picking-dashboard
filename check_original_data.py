"""
Check original data to find correct product names
"""
import json

with open('data/parsed_orders_final.json', 'r', encoding='utf-8') as f:
    orders = json.load(f)

brands_to_check = ['La Crianza', 'Krea', 'Regimel']
print('=== CHECKING ORIGINAL DATA FOR PROBLEMATIC BRANDS ===')

for order in orders:
    for item in order.get('items', []):
        brand = item.get('brand', '').strip()
        if brand in brands_to_check:
            print(f'Brand: {brand}')
            print(f'  Product: {item.get("product_name", "")}')
            print(f'  Price: {item.get("price", "")}')
            print(f'  Location: {item.get("location", "")}')
            print()

# Also check for items that might have become "Unknown" brand
print('=== CHECKING FOR ITEMS THAT MIGHT BE THE "1500" PRODUCT ===')
for order in orders:
    for item in order.get('items', []):
        name = item.get('product_name', '')
        if '1500' in name or 'PASILLO 1' in item.get('location', ''):
            print(f'Found potential match:')
            print(f'  Brand: {item.get("brand", "")}')
            print(f'  Product: {name}')
            print(f'  Price: {item.get("price", "")}')
            print(f'  Location: {item.get("location", "")}')
            print()