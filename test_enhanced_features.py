#!/usr/bin/env python3
"""
Test script for enhanced dashboard features
Tests all new API endpoints and validates functionality
"""

import requests
import json
from datetime import datetime

def test_endpoint(url, description):
    """Test an API endpoint and return results"""
    try:
        print(f"\n🧪 Testing {description}")
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS - Status: {response.status_code}")
            
            if isinstance(data, list):
                print(f"📊 Returned {len(data)} items")
                if data:
                    print(f"📋 First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
            elif isinstance(data, dict):
                print(f"📊 Returned dict with keys: {list(data.keys())}")
            
            return True, data
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return False, None

def main():
    """Test all enhanced dashboard features"""
    base_url = "http://127.0.0.1:5000"
    
    print("🚀 Enhanced Dashboard API Test Suite")
    print("=" * 50)
    
    # Test basic health
    success, _ = test_endpoint(f"{base_url}/api/today", "Basic API Health Check")
    if not success:
        print("❌ Basic API not responding. Check if server is running.")
        return
    
    # Test new enhanced order endpoints
    endpoints_to_test = [
        ("/api/orders/daily", "Daily Orders Breakdown"),
        ("/api/orders/monthly", "Monthly Orders Summary"), 
        ("/api/products/enhanced/by-brand", "Products Grouped by Brand"),
        ("/api/products/enhanced/by-location", "Products Grouped by Location"), 
        ("/api/products/enhanced/by-category", "Products Grouped by Category"),
    ]
    
    results = {}
    
    for endpoint, description in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        success, data = test_endpoint(url, description)
        results[endpoint] = {
            'success': success,
            'data': data,
            'description': description
        }
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    total_tests = len(endpoints_to_test)
    passed_tests = sum(1 for r in results.values() if r['success'])
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    
    for endpoint, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} {endpoint} - {result['description']}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL ENHANCED FEATURES ARE WORKING PERFECTLY!")
        print("Dashboard is ready for production use.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed. Check the errors above.")
    
    # Test specific data structure for orders
    if results.get('/api/orders/daily', {}).get('success'):
        daily_data = results['/api/orders/daily']['data']
        if daily_data:
            print(f"\n📅 Daily Orders Sample:")
            sample_day = daily_data[0] if isinstance(daily_data, list) else daily_data
            print(f"   Date: {sample_day.get('date', 'N/A')}")
            print(f"   Orders: {sample_day.get('total_orders', 'N/A')}")
            print(f"   Items: {sample_day.get('total_items', 'N/A')}")
    
    # Test specific data structure for products by brand
    if results.get('/api/products/enhanced/by-brand', {}).get('success'):
        brand_data = results['/api/products/enhanced/by-brand']['data']
        if brand_data:
            print(f"\n🏷️  Product Brands Sample:")
            brands = list(brand_data.keys())[:3] if isinstance(brand_data, dict) else []
            for brand in brands:
                products = brand_data[brand] if isinstance(brand_data, dict) else []
                count = len(products) if isinstance(products, list) else 'N/A'
                print(f"   {brand}: {count} products")

if __name__ == "__main__":
    main()