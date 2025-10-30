"""
Product Database Builder
Extracts unique products from parsed order data and creates a searchable database
"""

import json
import re
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Set
import unicodedata

@dataclass
class Product:
    """Product data structure"""
    product_id: str
    name: str
    brand: str
    normalized_name: str
    locations: Set[str]
    prices: List[str]
    avg_price_per_unit: float
    categories: List[str]
    frequency: int  # How many times this product appears in orders
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        d = asdict(self)
        d['locations'] = list(d['locations'])  # Convert set to list
        return d

class ProductDatabase:
    """Product database manager"""
    
    def __init__(self):
        self.products: Dict[str, Product] = {}
        self.brand_stats: Dict[str, dict] = {}
        self.location_map: Dict[str, List[str]] = defaultdict(list)  # location -> [product_ids]
        self.price_ranges: Dict[str, List[str]] = defaultdict(list)  # price_range -> [product_ids]
        
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison (remove accents, lowercase, etc.)"""
        if not text:
            return ""
        
        # Remove accents
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        
        # Lowercase and remove extra spaces
        text = re.sub(r'\s+', ' ', text.lower().strip())
        
        # Remove common words that don't affect product identity
        stop_words = ['de', 'del', 'la', 'el', 'con', 'sin', 'y', 'o', 'en']
        words = text.split()
        words = [w for w in words if w not in stop_words]
        
        return ' '.join(words)
    
    def extract_price_info(self, price_str: str) -> tuple:
        """Extract numeric price and unit price from price string"""
        if not price_str:
            return 0.0, 0.0
        
        # Extract total price: $2.670 ($445 uni)
        total_match = re.search(r'\$?([\d.,]+)', price_str.replace(',', ''))
        unit_match = re.search(r'\(\$?([\d.,]+)\s*uni\)', price_str.replace(',', ''))
        
        total_price = float(total_match.group(1)) if total_match else 0.0
        unit_price = float(unit_match.group(1)) if unit_match else total_price
        
        return total_price, unit_price
    
    def categorize_by_location(self, location: str) -> List[str]:
        """Categorize product based on its location"""
        categories = []
        
        if not location:
            return ["Sin categoría"]
        
        location_lower = location.lower()
        
        # Map pasillo numbers to categories (based on typical supermarket layout)
        if "pasillo" in location_lower:
            pasillo_match = re.search(r'pasillo\s*(\d+)', location_lower)
            if pasillo_match:
                pasillo_num = int(pasillo_match.group(1))
                
                if pasillo_num in [1, 2]:
                    categories.append("Frutas y Verduras")
                elif pasillo_num in [3, 4]:
                    categories.append("Despensa")
                elif pasillo_num in [5, 6]:
                    categories.append("Granos y Cereales")
                elif pasillo_num in [7, 8]:
                    categories.append("Bebidas")
                elif pasillo_num in [9, 10]:
                    categories.append("Limpieza y Hogar")
                else:
                    categories.append(f"Pasillo {pasillo_num}")
        
        # Special locations
        if any(word in location_lower for word in ["refrigerad", "frio"]):
            categories.append("Refrigerados")
        if any(word in location_lower for word in ["congelad", "frozen"]):
            categories.append("Congelados")
        if any(word in location_lower for word in ["panaderia", "bread"]):
            categories.append("Panadería")
        if any(word in location_lower for word in ["verduleria", "produce"]):
            categories.append("Verdulería")
        
        return categories if categories else ["General"]
    
    def generate_product_id(self, name: str, brand: str) -> str:
        """Generate unique product ID based on normalized name and brand"""
        normalized = self.normalize_text(f"{brand} {name}")
        # Create a hash-like ID from normalized text
        return f"prod_{abs(hash(normalized)) % 100000:05d}"
    
    def add_product_from_item(self, item: dict):
        """Add or update product from order item"""
        name = item.get('product_name', '').strip()
        brand = item.get('brand', '').strip()
        location = item.get('location', '').strip()
        price = item.get('price', '').strip()
        quantity = item.get('quantity', 1)
        
        if not name or not brand:
            return
        
        # Generate product ID
        product_id = self.generate_product_id(name, brand)
        
        # Extract price information
        total_price, unit_price = self.extract_price_info(price)
        
        # Get categories
        categories = self.categorize_by_location(location)
        
        # Add or update product
        if product_id in self.products:
            product = self.products[product_id]
            product.locations.add(location)
            if price and price not in product.prices:
                product.prices.append(price)
            product.frequency += quantity
            
            # Update average price
            if unit_price > 0:
                current_avg = product.avg_price_per_unit
                new_count = len(product.prices)
                product.avg_price_per_unit = ((current_avg * (new_count - 1)) + unit_price) / new_count
        else:
            # Create new product
            product = Product(
                product_id=product_id,
                name=name,
                brand=brand,
                normalized_name=self.normalize_text(name),
                locations={location} if location else set(),
                prices=[price] if price else [],
                avg_price_per_unit=unit_price,
                categories=categories,
                frequency=quantity
            )
            self.products[product_id] = product
        
        # Update location mapping
        if location:
            self.location_map[location].append(product_id)
        
        # Update price range mapping
        if unit_price > 0:
            if unit_price < 500:
                price_range = "< $500"
            elif unit_price < 1000:
                price_range = "$500-$1000"
            elif unit_price < 2000:
                price_range = "$1000-$2000"
            elif unit_price < 5000:
                price_range = "$2000-$5000"
            else:
                price_range = "> $5000"
            
            if product_id not in self.price_ranges[price_range]:
                self.price_ranges[price_range].append(product_id)
    
    def build_from_orders(self, orders_data: List[dict]):
        """Build product database from parsed orders"""
        print(f"Processing {len(orders_data)} orders...")
        
        for order in orders_data:
            items = order.get('items', [])
            for item in items:
                self.add_product_from_item(item)
        
        # Calculate brand statistics
        self.calculate_brand_stats()
        
        print(f"✅ Built database with {len(self.products)} unique products")
        print(f"📦 {len(self.brand_stats)} brands identified")
        print(f"📍 {len(self.location_map)} unique locations")
    
    def calculate_brand_stats(self):
        """Calculate statistics for each brand"""
        brand_data = defaultdict(lambda: {
            'product_count': 0,
            'total_frequency': 0,
            'avg_price': 0.0,
            'locations': set(),
            'categories': set()
        })
        
        for product in self.products.values():
            brand = product.brand
            brand_data[brand]['product_count'] += 1
            brand_data[brand]['total_frequency'] += product.frequency
            brand_data[brand]['locations'].update(product.locations)
            brand_data[brand]['categories'].update(product.categories)
            
            if product.avg_price_per_unit > 0:
                current_avg = brand_data[brand]['avg_price']
                count = brand_data[brand]['product_count']
                brand_data[brand]['avg_price'] = ((current_avg * (count - 1)) + product.avg_price_per_unit) / count
        
        # Convert sets to lists for JSON serialization
        self.brand_stats = {}
        for brand, data in brand_data.items():
            self.brand_stats[brand] = {
                'product_count': data['product_count'],
                'total_frequency': data['total_frequency'],
                'avg_price': round(data['avg_price'], 2),
                'locations': list(data['locations']),
                'categories': list(data['categories'])
            }
    
    def search_products(self, query: str, limit: int = 20) -> List[dict]:
        """Search products by name, brand, or category"""
        query_normalized = self.normalize_text(query)
        results = []
        
        for product in self.products.values():
            score = 0
            
            # Exact matches get highest score
            if query_normalized in product.normalized_name:
                score += 10
            if query_normalized in self.normalize_text(product.brand):
                score += 8
            
            # Partial matches
            for word in query_normalized.split():
                if word in product.normalized_name:
                    score += 3
                if word in self.normalize_text(product.brand):
                    score += 2
                if any(word in self.normalize_text(cat) for cat in product.categories):
                    score += 1
            
            if score > 0:
                result = product.to_dict()
                result['search_score'] = score
                results.append(result)
        
        # Sort by score (desc) and frequency (desc)
        results.sort(key=lambda x: (x['search_score'], x['frequency']), reverse=True)
        return results[:limit]
    
    def get_products_by_location(self, location: str) -> List[dict]:
        """Get all products from a specific location"""
        product_ids = self.location_map.get(location, [])
        return [self.products[pid].to_dict() for pid in product_ids if pid in self.products]
    
    def get_location_stats(self) -> Dict[str, dict]:
        """Get statistics for each location"""
        stats = {}
        
        for location, product_ids in self.location_map.items():
            products = [self.products[pid] for pid in product_ids if pid in self.products]
            
            total_frequency = sum(p.frequency for p in products)
            avg_price = sum(p.avg_price_per_unit for p in products if p.avg_price_per_unit > 0)
            avg_price = avg_price / len(products) if products else 0
            
            brands = set(p.brand for p in products)
            categories = set()
            for p in products:
                categories.update(p.categories)
            
            stats[location] = {
                'product_count': len(products),
                'total_frequency': total_frequency,
                'avg_price': round(avg_price, 2),
                'brands': list(brands),
                'categories': list(categories)
            }
        
        return stats
    
    def save_to_file(self, filepath: str):
        """Save product database to JSON file"""
        database = {
            'products': {pid: product.to_dict() for pid, product in self.products.items()},
            'brand_stats': self.brand_stats,
            'location_stats': self.get_location_stats(),
            'price_ranges': dict(self.price_ranges),
            'summary': {
                'total_products': len(self.products),
                'total_brands': len(self.brand_stats),
                'total_locations': len(self.location_map)
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Database saved to {filepath}")

def main():
    """Build product database from parsed orders"""
    print("🏗️  Building Product Database from Parsed Screenshots...")
    
    # Load parsed orders
    try:
        with open('data/parsed_orders_final.json', 'r', encoding='utf-8') as f:
            orders_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading orders data: {e}")
        return
    
    # Build database
    db = ProductDatabase()
    db.build_from_orders(orders_data)
    
    # Save database
    db.save_to_file('data/product_database.json')
    
    # Print summary statistics
    print("\n📊 Database Summary:")
    print(f"  Products: {len(db.products)}")
    print(f"  Brands: {len(db.brand_stats)}")
    print(f"  Locations: {len(db.location_map)}")
    
    print("\n🏷️  Top 10 Brands by Product Count:")
    top_brands = sorted(db.brand_stats.items(), 
                       key=lambda x: x[1]['product_count'], 
                       reverse=True)[:10]
    
    for brand, stats in top_brands:
        print(f"  {brand}: {stats['product_count']} products, avg ${stats['avg_price']}")
    
    print("\n🔍 Sample Product Search - 'arroz':")
    results = db.search_products('arroz', limit=5)
    for result in results:
        print(f"  {result['brand']} - {result['name'][:50]}... (${result['avg_price_per_unit']})")
    
    print(f"\n✅ Product database created successfully!")

if __name__ == "__main__":
    main()