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
    response = requests.get(get_sheet_url())
    response.raise_for_status()
    
    df = pd.read_csv(StringIO(response.text))
    
    # Process data
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
    df['SKUs'] = pd.to_numeric(df['SKUs'], errors='coerce').fillna(0).astype(int)
    
    # Parse tiempo
    def parse_time(t):
        if pd.isna(t) or t == '': 
            return 0
        try:
            parts = str(t).split(':')
            return int(parts[0]) * 60 + int(parts[1])
        except:
            return 0
    
    df['Tiempo_mins'] = df['Tiempo'].apply(parse_time)
    
    # Filter out ignored orders for performance metrics
    df_filtered = df[df.get('Ignorar', '') != 'IGN'].copy()
    
    return df, df_filtered

def calculate_earnings(row):
    """Calculate earnings for an order"""
    skus = row.get('SKUs', 0)
    
    # Check if bipicking
    if pd.notna(row.get('Bipicking')) and row.get('Bipicking') != '':
        base = 60 * skus + 1040
    else:
        base = 75 * skus + 1300
    
    # Sunday multiplier
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
    today_all = df[df['Fecha'].dt.date == today]
    today_all['earnings'] = today_all.apply(calculate_earnings, axis=1)
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
    week_all = df[(df['Fecha'].dt.date >= week_start) & (df['Fecha'].dt.date <= today)]
    week_all['earnings'] = week_all.apply(calculate_earnings, axis=1)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
