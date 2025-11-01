"""
Targeted cleaning - only fix obviously wrong data, keep useful product information
"""

import json
import re

def fix_only_bad_brands_and_artifacts(products):
    """Fix only obviously wrong brands and clear OCR artifacts"""
    
    # Brands that are clearly wrong (measurements, single letters, etc.)
    bad_brands = {
        '470cc': 'Austral',  # Found from context in name
        'ml': 'Unknown',
        'g': 'Unknown', 
        '25m': 'Confort',  # Found from context in name
        'L': 'Unknown',
        '1500': 'Unknown'  # Just a number
    }
    
    changes = []
    
    for product_id, product in products.items():
        original_name = product['name']
        original_brand = product['brand']
        
        # Fix obviously wrong brands
        if product['brand'] in bad_brands:
            # Try to extract real brand from name first
            name = product['name']
            new_brand = bad_brands[product['brand']]
            
            if 'Austral' in name and product['brand'] == '470cc':
                new_brand = 'Austral'
            elif 'Confort' in name and product['brand'] == '25m':
                new_brand = 'Confort'
            
            product['brand'] = new_brand
            changes.append(f"Fixed brand: '{original_brand}' → '{new_brand}' for {original_name[:50]}...")
        
        # Only remove clear OCR artifacts from names, keep useful info
        cleaned_name = original_name
        
        # Remove "Pickeado" (OCR artifact)
        cleaned_name = re.sub(r'\bPickeado\b', '', cleaned_name, flags=re.IGNORECASE)
        
        # Remove location artifacts but keep product info
        cleaned_name = re.sub(r'\bPASILLO\s*\d+\s*ESTANTE\s*\d+\b', '', cleaned_name, flags=re.IGNORECASE)
        cleaned_name = re.sub(r'\bPASILLO\s*\d+\b', '', cleaned_name, flags=re.IGNORECASE)
        cleaned_name = re.sub(r'\bESTANTE\s*\d+\b', '', cleaned_name, flags=re.IGNORECASE)
        
        # Remove "Drenado" and "Neto" (OCR artifacts)
        cleaned_name = re.sub(r'\bDrenado\b', '', cleaned_name, flags=re.IGNORECASE)
        cleaned_name = re.sub(r'\bNeto\b', '', cleaned_name, flags=re.IGNORECASE)
        
        # Clean up multiple spaces
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
        
        if cleaned_name != original_name:
            product['name'] = cleaned_name
            changes.append(f"Cleaned name: {original_name[:40]}... → {cleaned_name[:40]}...")
    
    return changes

def main():
    """Apply targeted cleaning to product database"""
    print("🧹 Applying Targeted Cleaning (keeping useful product info)...")
    
    # Load the original database to start fresh
    try:
        with open('data/parsed_orders_final.json', 'r', encoding='utf-8') as f:
            orders = json.load(f)
        
        # Rebuild database from scratch
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))
        from product_database import ProductDatabase
        
        db = ProductDatabase()
        db.build_from_orders(orders)
        
        # Convert to the format we need
        products = {}
        for product_id, product in db.products.items():
            products[product_id] = product.to_dict()
        
        print(f"✅ Rebuilt database with {len(products)} products")
        
    except Exception as e:
        print(f"Error rebuilding from source: {e}")
        print("Loading existing database...")
        with open('data/product_database.json', 'r', encoding='utf-8') as f:
            db_data = json.load(f)
        products = db_data['products']
    
    # Apply targeted fixes
    changes = fix_only_bad_brands_and_artifacts(products)
    
    # Rebuild the full database structure
    # Calculate brand stats
    brand_stats = {}
    location_stats = {}
    
    for product in products.values():
        brand = product['brand']
        if brand not in brand_stats:
            brand_stats[brand] = {
                'product_count': 0,
                'total_frequency': 0,
                'avg_price': 0.0,
                'locations': set(),
                'categories': set()
            }
        
        brand_stats[brand]['product_count'] += 1
        brand_stats[brand]['total_frequency'] += product['frequency']
        brand_stats[brand]['locations'].update(product['locations'])
        brand_stats[brand]['categories'].update(product['categories'])
        
        # Update average price
        if product['avg_price_per_unit'] > 0:
            current_avg = brand_stats[brand]['avg_price']
            count = brand_stats[brand]['product_count']
            brand_stats[brand]['avg_price'] = ((current_avg * (count - 1)) + product['avg_price_per_unit']) / count
    
    # Convert sets to lists for JSON serialization
    for brand_data in brand_stats.values():
        brand_data['locations'] = list(brand_data['locations'])
        brand_data['categories'] = list(brand_data['categories'])
        brand_data['avg_price'] = round(brand_data['avg_price'], 2)
    
    # Build location stats
    for product in products.values():
        for location in product['locations']:
            if location not in location_stats:
                location_stats[location] = {
                    'product_count': 0,
                    'total_frequency': 0,
                    'avg_price': 0.0,
                    'brands': set(),
                    'categories': set()
                }
            
            location_stats[location]['product_count'] += 1
            location_stats[location]['total_frequency'] += product['frequency']
            location_stats[location]['brands'].add(product['brand'])
            location_stats[location]['categories'].update(product['categories'])
    
    # Convert sets to lists for location stats
    for loc_data in location_stats.values():
        loc_data['brands'] = list(loc_data['brands'])
        loc_data['categories'] = list(loc_data['categories'])
    
    # Create final database structure
    final_db = {
        'products': products,
        'brand_stats': brand_stats,
        'location_stats': location_stats,
        'price_ranges': {},  # Will be empty for now
        'summary': {
            'total_products': len(products),
            'total_brands': len(brand_stats),
            'total_locations': len(location_stats)
        }
    }
    
    # Save updated database
    with open('data/product_database.json', 'w', encoding='utf-8') as f:
        json.dump(final_db, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Applied {len(changes)} targeted fixes")
    print("\n📝 Changes made:")
    for change in changes[:10]:  # Show first 10 changes
        print(f"  - {change}")
    
    if len(changes) > 10:
        print(f"  ... and {len(changes) - 10} more changes")
    
    print(f"\n✅ Updated database saved - product information preserved!")

if __name__ == "__main__":
    main()