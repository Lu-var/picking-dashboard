#!/usr/bin/env python3
"""
Verify the fixed products are correctly displayed
"""
import json

def verify_fixes():
    # Load current database
    with open('data/product_database.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    products = data['products']
    
    print("=== VERIFYING FIXED PRODUCTS ===")
    
    # Look for the products we fixed
    fixed_products = []
    
    for product_id, product in products.items():
        # Check for La Crianza hamburger
        if product['brand'] == 'La Crianza' and 'Hamburguesa' in product['name']:
            fixed_products.append(f"✓ La Crianza: {product['name']}")
        
        # Check for Regimel jalea
        if product['brand'] == 'Regimel' and 'Jalea' in product['name']:
            fixed_products.append(f"✓ Regimel: {product['name']}")
        
        # Check for Genérico 1500ml
        if product['brand'] == 'Genérico' and '1500ml' in product['name']:
            fixed_products.append(f"✓ Genérico: {product['name']} (freq: {product['frequency']})")
        
        # Check for Krea product
        if product['brand'] == 'Krea' and 'Talla' in product['name']:
            fixed_products.append(f"✓ Krea: {product['name']} (price: {product['prices']})")
    
    print(f"Found {len(fixed_products)} fixed products:")
    for product in fixed_products:
        print(f"  {product}")
    
    # Check for any remaining single-letter or very short names
    print("\n=== CHECKING FOR REMAINING SHORT NAMES ===")
    short_names = []
    
    for product_id, product in products.items():
        if len(product['name']) <= 2 or product['name'] in ['g', 'L', 'ml', '1500']:
            short_names.append(f"  ⚠️  {product['brand']}: '{product['name']}'")
    
    if short_names:
        print(f"Found {len(short_names)} products with potentially short names:")
        for name in short_names:
            print(name)
    else:
        print("✅ No remaining short/bad product names found!")
    
    # Show brand stats for the fixed brands
    print("\n=== BRAND STATS FOR FIXED BRANDS ===")
    target_brands = ['La Crianza', 'Regimel', 'Genérico', 'Krea']
    
    brand_stats = data.get('brand_stats', {})
    for brand in target_brands:
        if brand in brand_stats:
            stats = brand_stats[brand]
            print(f"{brand}:")
            print(f"  • Products: {stats['product_count']}")
            print(f"  • Avg frequency: {stats['avg_frequency']}")
            print(f"  • Locations: {len(stats['locations'])}")

if __name__ == "__main__":
    verify_fixes()