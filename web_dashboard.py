"""
Simple Picking Dashboard
Basic Flask app for viewing order data from Google Sheets
"""

from flask import Flask, render_template, jsonify, request
import os
import pandas as pd
import requests
from io import StringIO

app = Flask(__name__)

def get_sheet_url():
    url = os.environ.get("GOOGLE_SHEET_URL", "")
    if not url:
        raise RuntimeError("GOOGLE_SHEET_URL environment variable is not set")
    return url

def get_tier(sku_per_hour):
    """Classify efficiency into tiers based on SKU/hour"""
    if sku_per_hour >= 35: return 'optimal'
    if sku_per_hour >= 30: return 'excellent'
    if sku_per_hour >= 20: return 'good'
    if sku_per_hour >= 15: return 'medium'
    return 'poor'

def add_metrics(df):
    """Add calculated metrics to dataframe"""
    # Only calculate time-based metrics for non-ignored orders
    df['SKUPerHour'] = None
    df['MinPerSKU'] = None
    df['Tier'] = 'ignored'
    
    valid_mask = ~df['Ignorar']
    df.loc[valid_mask, 'SKUPerHour'] = (df.loc[valid_mask, 'SKUs'] / (df.loc[valid_mask, 'TiempoMin'] / 60)).round(1)
    df.loc[valid_mask, 'MinPerSKU'] = (df.loc[valid_mask, 'TiempoMin'] / df.loc[valid_mask, 'SKUs']).round(1)
    df.loc[valid_mask, 'Tier'] = df.loc[valid_mask, 'SKUPerHour'].apply(get_tier)
    
    return df

def load_data():
    """Fetch latest data from Google Sheets"""
    try:
        response = requests.get(get_sheet_url(), timeout=10)
        response.raise_for_status()
        
        # Ensure UTF-8 decoding
        csv_text = response.content.decode('utf-8')
        df = pd.read_csv(StringIO(csv_text))

        # Basic data processing
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
        df['SKUs'] = pd.to_numeric(df['SKUs'], errors='coerce').fillna(0).astype(int)
        
        # Handle Ignorar column (convert to boolean)
        if 'Ignorar' in df.columns:
            df['Ignorar'] = df['Ignorar'].fillna(False).astype(bool)
        else:
            df['Ignorar'] = False
        
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
        
        df['TiempoMin'] = df['Tiempo'].apply(parse_time)
        df = df[df['TiempoMin'] > 0]  # Filter out invalid times
        
        return df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/orders')
def get_orders():
    """API endpoint to get all orders with optional filtering and calculated metrics"""
    df = load_data()
    
    if df.empty:
        return jsonify({'orders': [], 'summary': {}})
    
    # Calculate metrics for all orders
    df = add_metrics(df)
    
    # Apply filters
    search = request.args.get('search', '').lower()
    limit = request.args.get('limit', 200, type=int)
    grouping = request.args.get('grouping', 'none')
    
    # Filter by search term (searches in Cliente field)
    if search:
        df = df[df['Cliente'].str.lower().str.contains(search, na=False)]
    
    # Sort by date (most recent first), handling NaT values
    df = df.sort_values('Fecha', ascending=False, na_position='last')
    
    # Calculate summary stats before limiting
    # Use all orders for counts, only non-ignored for time-based metrics
    valid_df = df[~df['Ignorar']]
    valid_count = len(valid_df)
    summary = {
        'total_orders': int(len(df)),
        'total_skus': int(df['SKUs'].sum()),
        'total_time_minutes': int(valid_df['TiempoMin'].sum()) if valid_count > 0 else 0,
        'total_time_hours': round(valid_df['TiempoMin'].sum() / 60, 1) if valid_count > 0 else 0,
        'avg_sku_per_hour': round(valid_df['SKUPerHour'].mean(), 1) if valid_count > 0 else 0,
        'avg_min_per_sku': round(valid_df['MinPerSKU'].mean(), 1) if valid_count > 0 else 0,
        'avg_time_per_order': round(valid_df['TiempoMin'].mean(), 1) if valid_count > 0 else 0
    }
    
    # Limit results
    df = df.head(limit)
    
    # Handle grouping
    if grouping == 'day' or grouping == 'month':
        df['FechaStr'] = df['Fecha'].dt.strftime('%d/%m/%Y')
        
        if grouping == 'day':
            group_key = 'FechaStr'
        else:  # month
            df['MonthKey'] = df['Fecha'].dt.strftime('%m/%Y')
            group_key = 'MonthKey'
        
        grouped_data = []
        for key, group_df in df.groupby(group_key, sort=False):
            group_orders = []
            for _, row in group_df.iterrows():
                order_dict = row.to_dict()
                # Convert datetime to string
                if isinstance(order_dict.get('Fecha'), pd.Timestamp):
                    order_dict['Fecha'] = order_dict['Fecha'].strftime('%d/%m/%Y')
                # Remove helper columns
                order_dict.pop('FechaStr', None)
                order_dict.pop('MonthKey', None)
                group_orders.append(order_dict)
            
            # Use all orders for counts, only non-ignored for time-based metrics
            valid_group = group_df[~group_df['Ignorar']]
            valid_count = len(valid_group)
            avg_sku_hour = round(valid_group['SKUPerHour'].mean(), 1) if valid_count > 0 else 0
            
            group_summary = {
                'key': key,
                'order_count': len(group_df),
                'total_skus': int(group_df['SKUs'].sum()),
                'total_time_minutes': int(valid_group['TiempoMin'].sum()) if valid_count > 0 else 0,
                'total_time_hours': round(valid_group['TiempoMin'].sum() / 60, 1) if valid_count > 0 else 0,
                'avg_sku_per_hour': avg_sku_hour,
                'avg_min_per_sku': round(valid_group['MinPerSKU'].mean(), 1) if valid_count > 0 else 0,
                'tier': get_tier(avg_sku_hour),
                'orders': group_orders
            }
            grouped_data.append(group_summary)
        
        return jsonify({'groups': grouped_data, 'summary': summary, 'grouping': grouping})
    
    # Replace NaN with None for valid JSON
    df = df.replace({pd.NA: None, pd.NaT: None})
    df = df.where(pd.notna(df), None)
    
    # Convert to records
    orders = df.to_dict('records')
    
    # Convert datetime objects to strings for JSON serialization
    for order in orders:
        if isinstance(order.get('Fecha'), pd.Timestamp):
            order['Fecha'] = order['Fecha'].strftime('%d/%m/%Y')
    
    return jsonify({'orders': orders, 'summary': summary})

@app.route('/api/quick_stats')
def get_quick_stats():
    """API endpoint for quick stats: today, this week, this month, profit"""
    df = load_data()
    
    if df.empty:
        return jsonify({})
    
    # Get current date
    today = pd.Timestamp.now().normalize()
    week_start = today - pd.Timedelta(days=today.dayofweek)  # Monday of current week
    month_start = today.replace(day=1)  # First day of current month
    
    # Calculate SKU/hour for each order
    df = add_metrics(df)
    
    # Helper to calculate period stats
    def period_stats(period_df):
        count = len(period_df)
        # Only use non-ignored orders for time-based metrics
        valid_df = period_df[~period_df['Ignorar']]
        valid_count = len(valid_df)
        return {
            'orders': count,
            'skus': int(period_df['SKUs'].sum()) if count > 0 else 0,
            'time_hours': round(valid_df['TiempoMin'].sum() / 60, 1) if valid_count > 0 else 0,
            'avg_efficiency': round(valid_df['SKUPerHour'].mean(), 1) if valid_count > 0 else 0
        }
    
    # Calculate stats for each period
    today_df = df[df['Fecha'] == today]
    week_df = df[df['Fecha'] >= week_start]
    month_df = df[df['Fecha'] >= month_start]
    
    today_stats = period_stats(today_df)
    week_stats = period_stats(week_df)
    month_stats = period_stats(month_df)
    overall_avg_efficiency = round(df['SKUPerHour'].mean(), 1)
    
    # Profit calculations based on actual rates
    # Standard order: 1300 CLP per order + 75 CLP per SKU (90 CLP on Sundays)
    # Bipicking order: 1040 CLP per order + 60 CLP per SKU (72 CLP on Sundays)
    
    def calculate_earnings(period_df):
        earnings = 0
        for _, row in period_df.iterrows():
            cliente = str(row.get('Cliente', ''))
            skus = row['SKUs']
            fecha = row['Fecha']
            
            # Check if it's a bipicking order (has (A) or (B) prefix)
            is_bipicking = '(A)' in cliente or '(B)' in cliente
            
            # Check if it's Sunday (weekday 6)
            is_sunday = fecha.weekday() == 6 if pd.notna(fecha) else False
            
            if is_bipicking:
                base_per_order = 1040
                sku_rate = 72 if is_sunday else 60
            else:
                base_per_order = 1300
                sku_rate = 90 if is_sunday else 75
            
            earnings += base_per_order + (skus * sku_rate)
        
        return int(earnings)  # Return as integer CLP
    
    # Add earnings to each period
    today_stats['earnings'] = calculate_earnings(today_df)
    week_stats['earnings'] = calculate_earnings(week_df)
    month_stats['earnings'] = calculate_earnings(month_df)
    
    stats = {
        'today': today_stats,
        'week': week_stats,
        'month': month_stats,
        'overall': {
            'avg_efficiency': overall_avg_efficiency,
            'total_orders': int(len(df)),
            'earnings': calculate_earnings(df)
        }
    }
    
    return jsonify(stats)

@app.route('/api/records')
def get_records():
    """API endpoint for personal records and achievements"""
    df = load_data()
    
    if df.empty:
        return jsonify({'error': 'No data available'})
    
    try:
        df = add_metrics(df)
        df['FechaStr'] = df['Fecha'].dt.strftime('%d/%m/%Y')
        
        # Only use non-ignored orders for efficiency-based records
        valid_df = df[~df['Ignorar']]
        
        # Best single order (fastest SKU/hour)
        best_order = valid_df.loc[valid_df['SKUPerHour'].idxmax()]
        
        # Aggregation config for groupby operations
        agg_config = {'SKUPerHour': 'mean', 'SKUs': 'sum', 'TiempoMin': 'sum', 'Cliente': 'count'}
        col_names = ['AvgSKUPerHour', 'TotalSKUs', 'TotalTime', 'OrderCount']
        
        # Best day (group by date, highest average SKU/hour) - use valid orders for efficiency
        daily_stats = valid_df.groupby('FechaStr').agg(agg_config).reset_index()
        daily_stats.columns = ['Fecha'] + col_names
        best_day = daily_stats.loc[daily_stats['AvgSKUPerHour'].idxmax()]
        most_skus_day = daily_stats.loc[daily_stats['TotalSKUs'].idxmax()]
        most_orders_day = daily_stats.loc[daily_stats['OrderCount'].idxmax()]
        
        # Best week (group by week) - use valid orders for efficiency
        valid_df['Week'] = valid_df['Fecha'].dt.to_period('W')
        weekly_stats = valid_df.groupby('Week').agg(agg_config).reset_index()
        weekly_stats.columns = ['Week'] + col_names
        if len(weekly_stats) > 0:
            best_week = weekly_stats.loc[weekly_stats['AvgSKUPerHour'].idxmax()]
            best_week_str = f"{best_week['Week'].start_time.strftime('%d/%m/%Y')} - {best_week['Week'].end_time.strftime('%d/%m/%Y')}"
        else:
            best_week = None
            best_week_str = "N/A"
        
        # Longest streak of good days (>=20 SKU/h)
        daily_stats['IsGood'] = daily_stats['AvgSKUPerHour'] >= 20
        current_streak = 0
        max_streak = 0
        for is_good in daily_stats['IsGood']:
            if is_good:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
    
        records = {
            'best_order': {
                'sku_per_hour': float(best_order['SKUPerHour']),
                'skus': int(best_order['SKUs']),
                'time': str(best_order['Tiempo']),
                'date': best_order['FechaStr'],
                'cliente': str(best_order['Cliente'])
            },
            'best_day': {
                'avg_sku_per_hour': round(best_day['AvgSKUPerHour'], 1),
                'total_skus': int(best_day['TotalSKUs']),
                'total_time': round(best_day['TotalTime'] / 60, 1),
                'order_count': int(best_day['OrderCount']),
                'date': best_day['Fecha']
            },
            'most_skus_day': {
                'total_skus': int(most_skus_day['TotalSKUs']),
                'order_count': int(most_skus_day['OrderCount']),
                'date': most_skus_day['Fecha']
            },
            'most_orders_day': {
                'order_count': int(most_orders_day['OrderCount']),
                'total_skus': int(most_orders_day['TotalSKUs']),
                'date': most_orders_day['Fecha']
            },
            'best_week': {
                'avg_sku_per_hour': round(best_week['AvgSKUPerHour'], 1) if best_week is not None else 0,
                'total_skus': int(best_week['TotalSKUs']) if best_week is not None else 0,
                'order_count': int(best_week['OrderCount']) if best_week is not None else 0,
                'week_range': best_week_str
            } if best_week is not None else None,
            'longest_streak': {
                'days': int(max_streak)
            }
        }
        
        return jsonify(records)
    except Exception as e:
        print(f"Error in /api/records: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)