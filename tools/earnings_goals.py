"""
Earnings Goal Tracker - Set and track earnings goals
"""

import json
import os
import pandas as pd
import requests
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich import box
import sys

console = Console()

# Default goals (can be customized)
GOALS = {
    "daily": 15000,      # 15,000 CLP per day
    "weekly": 75000,     # 75,000 CLP per week
    "monthly": 300000,   # 300,000 CLP per month
}

def load_data():
    """Load data from Google Sheets"""
    try:
        sheet_url = os.environ.get("GOOGLE_SHEET_URL", "")
        if not sheet_url:
            raise RuntimeError("GOOGLE_SHEET_URL environment variable is not set")
        
        response = requests.get(sheet_url)
        response.raise_for_status()
        
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        # Process
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
        df['SKUs'] = pd.to_numeric(df['SKUs'], errors='coerce').fillna(0).astype(int)
        
        def parse_time(t):
            if pd.isna(t) or t == '': return 0
            try:
                parts = str(t).split(':')
                return int(parts[0]) * 60 + int(parts[1]) if len(parts) == 2 else 0
            except: return 0
        
        df['Tiempo_Minutos'] = df['Tiempo'].apply(parse_time)
        
        # Earnings
        def calc_earnings(row):
            skus = row['SKUs']
            is_bi = pd.notna(row.get('Bipicking')) and str(row.get('Bipicking')).strip() not in ['', 'SKU Bi']
            is_sunday = pd.to_datetime(row['Fecha']).dayofweek == 6 if pd.notna(row['Fecha']) else False
            
            rate = 60 if is_bi else 75
            if is_sunday:
                rate *= 1.2
            bonus = 1040 if is_bi else 1300
            
            return int(skus * rate + bonus)
        
        df['Earnings'] = df.apply(calc_earnings, axis=1)
        
        # Handle Ignorar - keep all for earnings calculations
        if 'Ignorar' in df.columns:
            df['Ignorar'] = df['Ignorar'].fillna(False).astype(bool)
        
        return df.sort_values('Fecha')
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None

def show_goal_progress(df):
    """Show progress toward goals"""
    today = datetime.now()
    
    # Today
    today_orders = df[df['Fecha'].dt.date == today.date()]
    today_earned = today_orders['Earnings'].sum() if len(today_orders) > 0 else 0
    
    # This week
    week_start = today - timedelta(days=today.weekday())
    week_orders = df[df['Fecha'] >= week_start]
    week_earned = week_orders['Earnings'].sum()
    
    # This month
    month_start = today.replace(day=1)
    month_orders = df[df['Fecha'] >= month_start]
    month_earned = month_orders['Earnings'].sum()
    
    console.print(Panel.fit(
        "[bold cyan]🎯 EARNINGS GOALS TRACKER[/bold cyan]",
        border_style="cyan"
    ))
    
    # Progress bars
    goals = [
        ("📅 Today", today_earned, GOALS['daily']),
        ("📅 This Week", week_earned, GOALS['weekly']),
        ("📅 This Month", month_earned, GOALS['monthly']),
    ]
    
    for name, earned, goal in goals:
        progress_pct = (earned / goal * 100) if goal > 0 else 0
        remaining = goal - earned
        
        # Determine color
        if progress_pct >= 100:
            color = "green"
            status = "✓ ACHIEVED!"
        elif progress_pct >= 75:
            color = "yellow"
            status = f"${remaining:,} to go"
        else:
            color = "cyan"
            status = f"${remaining:,} to go"
        
        # Progress bar
        bar_length = 30
        filled = int(bar_length * min(progress_pct / 100, 1))
        bar = "█" * filled + "░" * (bar_length - filled)
        
        console.print(f"\n{name}")
        console.print(f"[{color}]{bar}[/{color}] {progress_pct:.0f}%")
        console.print(f"${earned:,} / ${goal:,} CLP - {status}")
    
    console.print()

def show_what_if(df):
    """Show what-if scenarios to reach goals"""
    today = datetime.now()
    
    # Recent avg performance
    two_weeks_ago = today - timedelta(days=14)
    recent = df[df['Fecha'] >= two_weeks_ago]
    
    if len(recent) == 0:
        return
    
    avg_earnings_per_order = recent['Earnings'].mean()
    avg_time_per_order = recent['Tiempo_Minutos'].mean()
    
    console.print(Panel.fit(
        "[bold yellow]💡 HOW TO REACH YOUR GOALS[/bold yellow]",
        border_style="yellow"
    ))
    
    # Daily goal
    console.print(f"\n[bold]To earn ${GOALS['daily']:,} CLP per day:[/bold]")
    orders_needed_daily = GOALS['daily'] / avg_earnings_per_order
    time_needed_daily = orders_needed_daily * avg_time_per_order
    console.print(f"  • Complete [cyan]{orders_needed_daily:.1f} orders[/cyan]")
    console.print(f"  • Work approximately [cyan]{time_needed_daily / 60:.1f} hours[/cyan]")
    console.print(f"  • At your current avg of [green]${avg_earnings_per_order:,.0f}[/green] per order")
    
    # Weekly goal
    console.print(f"\n[bold]To earn ${GOALS['weekly']:,} CLP per week:[/bold]")
    orders_needed_weekly = GOALS['weekly'] / avg_earnings_per_order
    orders_per_day = orders_needed_weekly / 5  # 5 working days
    console.print(f"  • Complete [cyan]{orders_needed_weekly:.0f} orders[/cyan] total")
    console.print(f"  • That's [cyan]{orders_per_day:.1f} orders per day[/cyan]")
    console.print(f"  • About [cyan]{(orders_per_day * avg_time_per_order) / 60:.1f} hours daily[/cyan]")
    
    # Monthly goal
    console.print(f"\n[bold]To earn ${GOALS['monthly']:,} CLP per month:[/bold]")
    orders_needed_monthly = GOALS['monthly'] / avg_earnings_per_order
    orders_per_day_monthly = orders_needed_monthly / 22  # ~22 working days
    console.print(f"  • Complete [cyan]{orders_needed_monthly:.0f} orders[/cyan] total")
    console.print(f"  • That's [cyan]{orders_per_day_monthly:.1f} orders per day[/cyan]")
    console.print(f"  • About [cyan]{(orders_per_day_monthly * avg_time_per_order) / 60:.1f} hours daily[/cyan]")
    
    console.print()

def show_streak_info(df):
    """Show working streak and consistency"""
    # Get unique working days
    working_days = df['Fecha'].dt.date.unique()
    working_days = sorted([d for d in working_days if pd.notna(d)])
    
    if len(working_days) == 0:
        return
    
    console.print(Panel.fit(
        "[bold magenta]🔥 CONSISTENCY TRACKER[/bold magenta]",
        border_style="magenta"
    ))
    
    total_days = len(working_days)
    first_day = working_days[0]
    last_day = working_days[-1]
    calendar_days = (last_day - first_day).days + 1
    
    consistency = (total_days / calendar_days * 100) if calendar_days > 0 else 0
    
    console.print(f"\n  📅 Days worked: [green]{total_days}[/green]")
    console.print(f"  📊 Consistency: [cyan]{consistency:.0f}%[/cyan] ({total_days} of {calendar_days} days)")
    console.print(f"  🗓️  First shift: {first_day.strftime('%d/%m/%Y')}")
    console.print(f"  🗓️  Latest shift: {last_day.strftime('%d/%m/%Y')}")
    
    # Days since last work
    days_since_last = (datetime.now().date() - last_day).days
    if days_since_last == 0:
        console.print(f"  ✨ [green]Worked today![/green]")
    elif days_since_last == 1:
        console.print(f"  ⏰ Last worked yesterday")
    else:
        console.print(f"  ⏰ Last worked {days_since_last} days ago")
    
    console.print()

def customize_goals():
    """Interactive goal setting"""
    console.print(Panel.fit(
        "[bold cyan]⚙️  CUSTOMIZE YOUR GOALS[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print("\nCurrent goals:")
    console.print(f"  Daily: ${GOALS['daily']:,} CLP")
    console.print(f"  Weekly: ${GOALS['weekly']:,} CLP")
    console.print(f"  Monthly: ${GOALS['monthly']:,} CLP")
    
    console.print("\n[dim]To customize goals, edit the GOALS dictionary in earnings_goals.py[/dim]\n")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--set-goals":
        customize_goals()
        return
    
    console.print("[yellow]📊 Loading data...[/yellow]")
    df = load_data()
    
    if df is None or len(df) == 0:
        console.print("[red]Failed to load data[/red]")
        return
    
    console.print(f"[green]✓ {len(df)} orders loaded[/green]\n")
    
    show_goal_progress(df)
    show_what_if(df)
    show_streak_info(df)
    
    console.print("[dim]💡 Tip: Edit goals in earnings_goals.py to match your targets[/dim]")

if __name__ == "__main__":
    main()
