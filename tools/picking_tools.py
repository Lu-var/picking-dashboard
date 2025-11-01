"""
Jumbo Picking Tools - Main Menu
Quick access to all performance tools
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import subprocess
import sys

console = Console()

def show_menu():
    """Display main menu"""
    console.clear()
    
    console.print(Panel.fit(
        "[bold cyan]🛠️  JUMBO PICKING TOOLS[/bold cyan]\n"
        "[dim]Performance Analysis & Earnings Tracking[/dim]",
        border_style="cyan"
    ))
    
    table = Table(show_header=False, box=box.ROUNDED, border_style="blue")
    table.add_column("Key", style="cyan bold", width=3)
    table.add_column("Tool", style="white")
    table.add_column("Description", style="dim")
    
    table.add_row("1", "Quick Stats", "Today's summary & recent orders")
    table.add_row("2", "Full Analysis", "Complete performance report")
    table.add_row("3", "Earnings Goals", "Track progress toward goals")
    table.add_row("4", "View All Data", "Show all order data")
    table.add_row("", "", "")
    table.add_row("q", "Quit", "Exit menu")
    
    console.print(table)
    console.print()

def run_tool(choice):
    """Run selected tool"""
    import os
    
    tools = {
        "1": ("quick_stats.py", "Quick Stats"),
        "2": ("performance_analyzer.py", "Performance Analyzer"),
        "3": ("earnings_goals.py", "Earnings Goals"),
        "4": ("view_data.py", "Data Viewer"),
    }
    
    if choice in tools:
        script, name = tools[choice]
        console.print(f"\n[yellow]Running {name}...[/yellow]\n")
        
        # Get script path relative to this file
        script_path = os.path.join(os.path.dirname(__file__), script)
        
        try:
            subprocess.run([sys.executable, script_path])
        except FileNotFoundError:
            console.print(f"[red]Error: {script} not found[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        
        console.print(f"\n[dim]Press Enter to return to menu...[/dim]")
        input()
        return True
    
    return False

def main():
    """Main menu loop"""
    while True:
        show_menu()
        
        choice = console.input("[cyan]Select tool (1-4, q to quit): [/cyan]").strip().lower()
        
        if choice == 'q':
            console.print("\n[green]Thanks for using Jumbo Picking Tools! 👋[/green]\n")
            break
        
        if not run_tool(choice):
            if choice:
                console.print(f"\n[red]Invalid choice: {choice}[/red]")
                console.print("[dim]Press Enter to continue...[/dim]")
                input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted. Goodbye! 👋[/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
