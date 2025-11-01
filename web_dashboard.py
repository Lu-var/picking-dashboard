"""
Web Dashboard for Picking Performance Tracker
Mobile-friendly interface for viewing stats on the go
"""

from flask import Flask, render_template, jsonify
import os
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta
import json

app = Flask(__name__)

def get_sheet_url():
    url = os.environ.get("GOOGLE_SHEET_URL", "")
    if not url:
        raise RuntimeError("GOOGLE_SHEET_URL environment variable is not set")
    return url

def load_data():
    """Fetch latest data from Google Sheets"""
    response = requests.get(get_sheet_url(), timeout=10)
    response.raise_for_status()
    
    df = pd.read_csv(StringIO(response.text))
    
    # Process data
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
    df['SKUs'] = pd.to_numeric(df['SKUs'], errors='coerce').fillna(0).astype(int)
    
    # Parse tiempo (supports H:MM format like 1:20 = 1 hour 20 mins = 80 mins)
    def parse_time(t):
        if pd.isna(t) or t == '': 
            return 0
        try:
            parts = str(t).split(':')
            if len(parts) == 2:
                hours = int(parts[0])
                mins = int(parts[1])
                return hours * 60 + mins
            return 0
        except:
            return 0
    
    df['Tiempo_mins'] = df['Tiempo'].apply(parse_time)
    
    # Filter out ignored orders for performance metrics
    # Treat NaN as False (don't ignore), only filter out explicit True values
    df['Ignorar'] = df['Ignorar'].fillna(False)
    df_filtered = df[df['Ignorar'] == False].copy()
    
    return df, df_filtered

def calculate_earnings(row):
    """Calculate earnings for an order - assumes Mono picking"""
    skus = row.get('SKUs', 0)
    
    # Default to Mono pricing (75 CLP/SKU + 1300 base)
    # You can add Tipo/Bipicking columns later if needed
    base = 75 * skus + 1300
    
    # Sunday multiplier (1.2x)
    if pd.notna(row.get('Fecha')) and row['Fecha'].weekday() == 6:
        base *= 1.2
    
    return int(base)

@app.route('/')
def home():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/today')
def today_stats():
    """Get today's stats"""
    df, df_filtered = load_data()
    
    today = datetime.now().date()
    today_orders = df_filtered[df_filtered['Fecha'].dt.date == today]
    
    if len(today_orders) == 0:
        return jsonify({
            'orders': 0,
            'skus': 0,
            'time': 0,
            'speed': 0,
            'earned': 0
        })
    
    total_skus = today_orders['SKUs'].sum()
    total_time = today_orders['Tiempo_mins'].sum()
    speed = (total_skus / total_time * 60) if total_time > 0 else 0
    
    # Calculate earnings (use ALL orders including ignored)
    today_all = df[df['Fecha'].dt.date == today].copy()
    earnings = []
    for _, row in today_all.iterrows():
        earnings.append(calculate_earnings(row))
    today_all['earnings'] = earnings
    earned = today_all['earnings'].sum()
    
    return jsonify({
        'orders': len(today_orders),
        'skus': int(total_skus),
        'time': int(total_time),
        'speed': round(speed, 1),
        'earned': int(earned)
    })

@app.route('/api/week')
def week_stats():
    """Get this week's stats"""
    df, df_filtered = load_data()
    
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    week_orders = df_filtered[(df_filtered['Fecha'].dt.date >= week_start) & 
                              (df_filtered['Fecha'].dt.date <= today)]
    
    if len(week_orders) == 0:
        return jsonify({
            'orders': 0,
            'skus': 0,
            'time': 0,
            'speed': 0,
            'earned': 0
        })
    
    total_skus = week_orders['SKUs'].sum()
    total_time = week_orders['Tiempo_mins'].sum()
    speed = (total_skus / total_time * 60) if total_time > 0 else 0
    
    # Calculate earnings
    week_all = df[(df['Fecha'].dt.date >= week_start) & (df['Fecha'].dt.date <= today)].copy()
    earnings = []
    for _, row in week_all.iterrows():
        earnings.append(calculate_earnings(row))
    week_all['earnings'] = earnings
    earned = week_all['earnings'].sum()
    
    return jsonify({
        'orders': len(week_orders),
        'skus': int(total_skus),
        'time': int(total_time),
        'speed': round(speed, 1),
        'earned': int(earned)
    })

@app.route('/api/recent')
def recent_orders():
    """Get last 10 orders"""
    df, df_filtered = load_data()
    
    recent = df_filtered.nlargest(10, 'Fecha')
    
    orders = []
    for _, row in recent.iterrows():
        time_mins = row['Tiempo_mins']
        speed = (row['SKUs'] / time_mins * 60) if time_mins > 0 else 0
        
        orders.append({
            'fecha': row['Fecha'].strftime('%d/%m') if pd.notna(row['Fecha']) else '',
            'cliente': str(row.get('Cliente', ''))[:20],
            'skus': int(row['SKUs']),
            'tiempo': str(row.get('Tiempo', '')),
            'speed': round(speed, 1)
        })
    
    return jsonify(orders)

@app.route('/api/stats')
def general_stats():
    """Get general statistics"""
    df, df_filtered = load_data()
    
    total_orders = len(df_filtered)
    total_skus = df_filtered['SKUs'].sum()
    total_time = df_filtered['Tiempo_mins'].sum()
    avg_speed = (total_skus / total_time * 60) if total_time > 0 else 0
    
    # Last 2 weeks comparison
    today = datetime.now().date()
    two_weeks_ago = today - timedelta(days=14)
    four_weeks_ago = today - timedelta(days=28)
    
    recent = df_filtered[(df_filtered['Fecha'].dt.date >= two_weeks_ago) & 
                        (df_filtered['Fecha'].dt.date <= today)]
    previous = df_filtered[(df_filtered['Fecha'].dt.date >= four_weeks_ago) & 
                          (df_filtered['Fecha'].dt.date < two_weeks_ago)]
    
    recent_speed = (recent['SKUs'].sum() / recent['Tiempo_mins'].sum() * 60) if recent['Tiempo_mins'].sum() > 0 else 0
    previous_speed = (previous['SKUs'].sum() / previous['Tiempo_mins'].sum() * 60) if previous['Tiempo_mins'].sum() > 0 else 0
    
    change = ((recent_speed - previous_speed) / previous_speed * 100) if previous_speed > 0 else 0
    
    return jsonify({
        'total_orders': int(total_orders),
        'total_skus': int(total_skus),
        'avg_speed': round(avg_speed, 1),
        'recent_speed': round(recent_speed, 1),
        'previous_speed': round(previous_speed, 1),
        'change_percent': round(change, 1)
    })

@app.route('/api/month')
def month_stats():
    """Get current month stats"""
    df, df_filtered = load_data()
    
    # Current month
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1).date()
    month_orders = df_filtered[df_filtered['Fecha'].dt.date >= month_start]
    month_complete = df[df['Fecha'].dt.date >= month_start]  # For earnings
    
    total_orders = len(month_orders)
    total_skus = int(month_orders['SKUs'].sum())
    total_time = int(month_orders['Tiempo_mins'].sum())
    
    speed = (total_skus / total_time * 60) if total_time > 0 else 0
    
    # Calculate total earnings
    month_complete = month_complete.copy()
    earnings = []
    for _, row in month_complete.iterrows():
        earnings.append(calculate_earnings(row))
    month_complete['earnings'] = earnings
    total_earned = int(month_complete['earnings'].sum())
    
    return jsonify({
        'orders': total_orders,
        'skus': total_skus,
        'time': total_time,
        'speed': round(speed, 1),
        'earned': total_earned
    })

@app.route('/api/bests')
def personal_bests():
    """Get personal best stats"""
    df, df_filtered = load_data()
    
    if len(df_filtered) == 0:
        return jsonify({
            'fastest_order': None,
            'most_skus': None,
            'best_speed': None
        })
    
    # Calculate speed for each order (SKUs/hour)
    df_filtered['speed'] = df_filtered.apply(
        lambda x: round((x['SKUs'] / x['Tiempo_mins'] * 60), 1) if x['Tiempo_mins'] > 0 else 0,
        axis=1
    )
    
    # Fastest order (shortest time with at least 10 SKUs)
    big_orders = df_filtered[df_filtered['SKUs'] >= 10].copy()
    fastest = None
    if len(big_orders) > 0:
        fastest_row = big_orders.loc[big_orders['Tiempo_mins'].idxmin()]
        fastest = {
            'time': int(fastest_row['Tiempo_mins']),
            'skus': int(fastest_row['SKUs']),
            'cliente': str(fastest_row['Cliente'])[:20]
        }
    
    # Most SKUs in one order
    most_skus_row = df_filtered.loc[df_filtered['SKUs'].idxmax()]
    most_skus = {
        'skus': int(most_skus_row['SKUs']),
        'time': int(most_skus_row['Tiempo_mins']),
        'cliente': str(most_skus_row['Cliente'])[:20]
    }
    
    # Best speed (min 10 SKUs)
    best_speed_order = None
    if len(big_orders) > 0:
        best_speed_row = big_orders.loc[big_orders['speed'].idxmax()]
        best_speed_order = {
            'speed': round(best_speed_row['speed'], 1),
            'skus': int(best_speed_row['SKUs']),
            'time': int(best_speed_row['Tiempo_mins']),
            'cliente': str(best_speed_row['Cliente'])[:20]
        }
    
    return jsonify({
        'fastest_order': fastest,
        'most_skus': most_skus,
        'best_speed': best_speed_order
    })

@app.route('/api/all_time')
def all_time_stats():
    """Get all-time earnings and stats"""
    df, df_filtered = load_data()
    
    # Calculate total earnings from all orders
    df = df.copy()
    earnings = []
    for _, row in df.iterrows():
        earnings.append(calculate_earnings(row))
    df['earnings'] = earnings
    total_earned = int(df['earnings'].sum())
    
    # Total stats
    total_orders = len(df_filtered)
    total_skus = int(df_filtered['SKUs'].sum())
    total_time = int(df_filtered['Tiempo_mins'].sum())
    
    avg_speed = (total_skus / total_time * 60) if total_time > 0 else 0
    
    return jsonify({
        'total_earned': total_earned,
        'total_orders': total_orders,
        'total_skus': total_skus,
        'avg_speed': round(avg_speed, 1)
    })

@app.route('/api/records_detailed')
def records_detailed():
    """Get detailed records and analytics"""
    df, df_filtered = load_data()
    
    # Calculate speed for all orders
    df_filtered['speed'] = (df_filtered['SKUs'] / df_filtered['Tiempo_mins'] * 60).round(1)
    
    # Speed distribution by SKU ranges
    speed_by_range = {}
    ranges = [(1, 5), (6, 10), (11, 20), (21, 30), (31, 50), (51, 100)]
    
    for min_skus, max_skus in ranges:
        range_data = df_filtered[(df_filtered['SKUs'] >= min_skus) & (df_filtered['SKUs'] <= max_skus)]
        if len(range_data) > 0:
            speed_by_range[f"{min_skus}-{max_skus} SKUs"] = {
                'avg_speed': round(range_data['speed'].mean(), 1),
                'max_speed': round(range_data['speed'].max(), 1),
                'orders': len(range_data),
                'avg_time': round(range_data['Tiempo_mins'].mean(), 1)
            }
    
    # Top 10 fastest orders
    top_fast = df_filtered.nsmallest(10, 'Tiempo_mins')[['Cliente', 'SKUs', 'Tiempo_mins', 'speed']].to_dict('records')
    
    # Top 10 highest speed orders (min 10 SKUs)
    big_orders = df_filtered[df_filtered['SKUs'] >= 10]
    top_speed = big_orders.nlargest(10, 'speed')[['Cliente', 'SKUs', 'Tiempo_mins', 'speed']].to_dict('records')
    
    # Speed trends over time (last 30 days)
    recent_30 = df_filtered[df_filtered['Fecha'] >= (datetime.now() - timedelta(days=30))]
    daily_avg = recent_30.groupby(recent_30['Fecha'].dt.date)['speed'].mean().round(1)
    speed_trend = [{'date': str(date), 'speed': float(speed)} for date, speed in daily_avg.items()]
    
    # Weekly performance comparison
    weeks = []
    for i in range(4):  # Last 4 weeks
        week_start = datetime.now() - timedelta(days=(i+1)*7)
        week_end = week_start + timedelta(days=7)
        week_data = df_filtered[(df_filtered['Fecha'] >= week_start) & (df_filtered['Fecha'] < week_end)]
        
        if len(week_data) > 0:
            weeks.append({
                'week': f"Semana {4-i}",
                'orders': len(week_data),
                'avg_speed': round(week_data['speed'].mean(), 1),
                'total_skus': int(week_data['SKUs'].sum()),
                'total_time': int(week_data['Tiempo_mins'].sum())
            })
    
    return jsonify({
        'speed_by_range': speed_by_range,
        'top_fast_orders': top_fast,
        'top_speed_orders': top_speed,
        'speed_trend': speed_trend[-14:],  # Last 14 days
        'weekly_comparison': weeks
    })

@app.route('/api/products/search')
def search_products():
    """Search products in the database"""
    from flask import request
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 20))
    
    try:
        # Load product database
        with open('data/product_database.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        # Simple search through products
        results = []
        query_lower = query.lower()
        
        for product in db['products'].values():
            if (query_lower in product['name'].lower() or 
                query_lower in product['brand'].lower() or
                any(query_lower in cat.lower() for cat in product['categories'])):
                results.append(product)
        
        # Sort by frequency (most popular first)
        results.sort(key=lambda x: x['frequency'], reverse=True)
        
        return jsonify(results[:limit])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/brands')
def get_brands():
    """Get brand statistics"""
    try:
        with open('data/product_database.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        # Sort brands by product count
        brands = sorted(db['brand_stats'].items(), 
                       key=lambda x: x[1]['product_count'], 
                       reverse=True)
        
        return jsonify({
            'brands': dict(brands),
            'total_brands': len(brands)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/locations')
def get_locations():
    """Get location statistics"""
    try:
        with open('data/product_database.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        return jsonify(db['location_stats'])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/by-location')
def products_by_location():
    """Get products from a specific location"""
    from flask import request
    location = request.args.get('location', '')
    
    try:
        with open('data/product_database.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        # Find products in the specified location
        products = []
        for product in db['products'].values():
            if location in product['locations']:
                products.append(product)
        
        # Sort by frequency
        products.sort(key=lambda x: x['frequency'], reverse=True)
        
        return jsonify({
            'location': location,
            'products': products,
            'count': len(products)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/browse')
def browse_all_products():
    """Browse all products with sorting and pagination"""
    from flask import request
    
    # Get parameters
    sort_by = request.args.get('sort', 'name')  # name, brand, frequency, price
    order = request.args.get('order', 'asc')    # asc, desc
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    try:
        with open('data/product_database.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        # Convert products dict to list
        products = list(db['products'].values())
        
        # Sort products
        if sort_by == 'name':
            products.sort(key=lambda x: x['name'].lower(), reverse=(order == 'desc'))
        elif sort_by == 'brand':
            products.sort(key=lambda x: x['brand'].lower(), reverse=(order == 'desc'))
        elif sort_by == 'frequency':
            products.sort(key=lambda x: x['frequency'], reverse=(order == 'desc'))
        elif sort_by == 'price':
            products.sort(key=lambda x: x['avg_price_per_unit'], reverse=(order == 'desc'))
        
        # Paginate
        total = len(products)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_products = products[start:end]
        
        return jsonify({
            'products': paginated_products,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            },
            'sort': {
                'by': sort_by,
                'order': order
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/database')
def get_product_database():
    """Get full product database summary"""
    try:
        with open('data/product_database.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        return jsonify(db['summary'])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/layout')
def get_layout():
    """Serve darkstore layout data"""
    try:
        with open('data/darkstore_layout.json', 'r', encoding='utf-8') as f:
            layout_data = json.load(f)
        return jsonify(layout_data)
    except FileNotFoundError:
        return jsonify({'error': 'Layout file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
