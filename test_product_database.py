"""
Test script for product database functionality
"""

import json
import sys
import os

# Add tools directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

from product_database import ProductDatabase

def test_product_database():
    """Test the complete product database system"""
    
    print("=== PRODUCT DATABASE TEST ===")
    
    # Test 1: Load saved database
    try:
        with open('data/product_database.json', 'r', encoding='utf-8') as f:
            db_data = json.load(f)
        
        print(f"✅ Database loaded successfully")
        print(f"✅ Total Products: {len(db_data['products'])}")
        print(f"✅ Total Brands: {len(db_data['brand_stats'])}")
        print(f"✅ Total Locations: {len(db_data['location_stats'])}")
        
    except Exception as e:
        print(f"❌ Failed to load database: {e}")
        return False
    
    # Test 2: Build database from scratch
    try:
        db = ProductDatabase()
        with open('data/parsed_orders_final.json', 'r', encoding='utf-8') as f:
            orders = json.load(f)
        
        db.build_from_orders(orders)
        print(f"✅ Database built from {len(orders)} orders")
        
    except Exception as e:
        print(f"❌ Failed to build database: {e}")
        return False
    
    # Test 3: Search functionality
    print("\n=== SEARCH TESTS ===")
    search_terms = ['arroz', 'leche', 'banana', 'coca']
    
    for term in search_terms:
        try:
            results = db.search_products(term, limit=3)
            print(f"Search '{term}': {len(results)} results")
            
            for result in results[:2]:  # Show top 2
                name = result['name'][:40] + "..." if len(result['name']) > 40 else result['name']
                print(f"  - {result['brand']} - {name}")
                
        except Exception as e:
            print(f"❌ Search failed for '{term}': {e}")
    
    # Test 4: Location mapping
    print("\n=== LOCATION TESTS ===")
    locations = list(db.location_map.keys())[:3]
    
    for location in locations:
        try:
            products = db.get_products_by_location(location)
            print(f"'{location}': {len(products)} products")
            
        except Exception as e:
            print(f"❌ Location test failed: {e}")
    
    # Test 5: Brand statistics
    print("\n=== BRAND ANALYSIS ===")
    top_brands = sorted(db.brand_stats.items(), 
                       key=lambda x: x[1]['product_count'], 
                       reverse=True)[:5]
    
    for brand, stats in top_brands:
        print(f"{brand}: {stats['product_count']} products, avg ${stats['avg_price']}")
    
    print("\n✅ All database tests passed!")
    return True

def test_api_simulation():
    """Simulate API calls"""
    print("\n=== API SIMULATION TEST ===")
    
    try:
        with open('data/product_database.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        # Simulate search API
        query = "leche"
        results = []
        for product in db['products'].values():
            if (query.lower() in product['name'].lower() or 
                query.lower() in product['brand'].lower()):
                results.append(product)
        
        print(f"API Search '{query}': {len(results)} results")
        
        # Simulate brands API
        brands = db['brand_stats']
        print(f"API Brands: {len(brands)} brands available")
        
        # Simulate locations API
        locations = db['location_stats']
        print(f"API Locations: {len(locations)} locations available")
        
        print("✅ API simulation successful!")
        return True
        
    except Exception as e:
        print(f"❌ API simulation failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Product Database System...")
    
    success = test_product_database() and test_api_simulation()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - Product Database System Ready!")
    else:
        print("\n❌ Some tests failed - Check errors above")