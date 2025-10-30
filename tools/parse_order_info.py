"""
Parse Order Info screenshots
Extracts: Order ID, Cliente, SKUs, Tiempo from start and completion screens
Handles both mono-picking and bi-picking orders
"""

import os
import re
from datetime import datetime
from google.cloud import vision
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def extract_date_from_filename(filename):
    """Extract date from screenshot filename: Screenshot_20251008-075656_Picker Up.png"""
    match = re.search(r'Screenshot_(\d{8})', filename)
    if match:
        date_str = match.group(1)
        # Convert YYYYMMDD to DD/M/YYYY format (match sheet format)
        dt = datetime.strptime(date_str, '%Y%m%d')
        return dt.strftime('%d/%m/%Y')
    return None

def ocr_screenshot(image_path):
    """Get full text from screenshot using Google Vision"""
    client = vision.ImageAnnotatorClient()
    
    with open(image_path, 'rb') as f:
        content = f.read()
    
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    
    if response.error.message:
        raise Exception(f'{response.error.message}')
    
    if response.text_annotations:
        return response.text_annotations[0].description
    
    return None

def parse_start_screen(text):
    """Parse START screen - extract order ID, cliente, SKUs"""
    lines = text.split('\n')
    
    data = {
        'order_id': None,
        'cliente': None,
        'skus': None,
        'unidades': None
    }
    
    # Find order ID (vXXXXXXXXXXjmch-XX)
    for line in lines:
        if 'jmch' in line.lower():
            data['order_id'] = line.strip()
            break
    
    # Find cliente name (look for name before "Pedido:")
    for i, line in enumerate(lines):
        if 'Pedido:' in line and i > 0:
            # Name is a few lines before "Pedido:"
            for j in range(max(0, i-5), i):
                candidate = lines[j].strip()
                # Skip single letters (A, B markers) and short text
                if len(candidate) > 3 and not candidate in ['Chat', 'Llamar', 'Contacto', 'LTE']:
                    # Check if it looks like a name (multiple words)
                    if ' ' in candidate or len(candidate.split()) >= 2:
                        data['cliente'] = candidate
                        break
            break
    
    # Find SKUs count
    for i, line in enumerate(lines):
        if "SKU's:" in line or "SKU's" in line:
            if i + 1 < len(lines):
                try:
                    data['skus'] = int(lines[i + 1].strip())
                except ValueError:
                    pass
            break
    
    # Find Unidades
    for i, line in enumerate(lines):
        if 'Unidades:' in line:
            if i + 1 < len(lines):
                try:
                    data['unidades'] = int(lines[i + 1].strip())
                except ValueError:
                    pass
            break
    
    return data

def parse_completion_screen(text):
    """Parse COMPLETION screen - extract order ID, tiempo, productos"""
    lines = text.split('\n')
    
    orders = []
    current_order = None
    
    # Look for "Detalle Pedido [Name]" to identify orders
    for i, line in enumerate(lines):
        if 'Detalle Pedido' in line:
            # New order found
            if current_order:
                orders.append(current_order)
            
            # Extract cliente name from "Detalle Pedido [Name]"
            cliente = line.replace('Detalle Pedido', '').strip()
            
            current_order = {
                'order_id': None,
                'cliente': cliente,
                'productos_solicitados': None,
                'pickeados': None,
                'tiempo': None
            }
        
        # Extract order ID
        if current_order and 'jmch' in line.lower():
            current_order['order_id'] = line.strip()
        
        # Extract productos solicitados
        if current_order and 'Productos solicitados' in line:
            if i + 1 < len(lines):
                try:
                    current_order['productos_solicitados'] = int(lines[i + 1].strip())
                except ValueError:
                    pass
        
        # Extract pickeados
        if current_order and 'Pickeados' in line:
            if i + 1 < len(lines):
                try:
                    current_order['pickeados'] = int(lines[i + 1].strip())
                except ValueError:
                    pass
        
        # Extract tiempo (formato: "1:07 horas" o "0:45 minutos")
        if current_order and 'Tiempo total de picking' in line:
            if i + 1 < len(lines):
                tiempo_text = lines[i + 1].strip()
                # Parse "1:07 horas" -> 67 minutes
                match = re.search(r'(\d+):(\d+)', tiempo_text)
                if match:
                    hours = int(match.group(1))
                    minutes = int(match.group(2))
                    current_order['tiempo'] = hours * 60 + minutes
    
    if current_order:
        orders.append(current_order)
    
    return orders

def main():
    """Parse all order info screenshots"""
    console.print(Panel.fit(
        "[bold cyan]Order Info Screenshot Parser[/bold cyan]\n"
        "Extracts: Order ID, Cliente, SKUs, Tiempo, Fecha",
        border_style="cyan"
    ))
    
    screenshots_dir = '../data/Order Info Screenshots'
    all_files = sorted([f for f in os.listdir(screenshots_dir) if f.endswith('.png')])
    
    console.print(f"\nProcessing {len(all_files)} screenshots...\n")
    
    orders = {}
    screenshot_dates = {}  # Track dates from filenames
    
    for i, filename in enumerate(all_files, 1):
        filepath = os.path.join(screenshots_dir, filename)
        console.print(f"[{i}/{len(all_files)}] {filename}")
        
        # Extract date from filename
        fecha = extract_date_from_filename(filename)
        
        try:
            text = ocr_screenshot(filepath)
            if not text:
                continue
            
            # Determine if start or completion screen
            if 'Resumen de pedido' in text or 'Tiempo total de picking' in text:
                # Completion screen
                completed_orders = parse_completion_screen(text)
                for order in completed_orders:
                    order_id = order['order_id']
                    if order_id:
                        if order_id not in orders:
                            orders[order_id] = {}
                        orders[order_id].update(order)
                        # Save date from filename
                        if fecha:
                            screenshot_dates[order_id] = fecha
            else:
                # Start screen
                start_data = parse_start_screen(text)
                order_id = start_data['order_id']
                if order_id:
                    if order_id not in orders:
                        orders[order_id] = {}
                    orders[order_id].update(start_data)
                    # Save date from filename
                    if fecha:
                        screenshot_dates[order_id] = fecha
        
        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")
    
    # Add dates to orders
    for order_id, fecha in screenshot_dates.items():
        if order_id in orders:
            orders[order_id]['fecha'] = fecha
    
    # Convert to list
    orders_list = list(orders.values())
    
    console.print(f"\n[green]Found {len(orders_list)} orders[/green]\n")
    
    # Display results
    table = Table(title="Parsed Orders", show_header=True)
    table.add_column("Fecha", style="yellow")
    table.add_column("Cliente", style="cyan", width=20)
    table.add_column("SKUs", style="green")
    table.add_column("Tiempo (min)", style="magenta")
    
    for order in orders_list:
        table.add_row(
            order.get('fecha', 'N/A'),
            order.get('cliente', 'N/A')[:20],
            str(order.get('skus') or order.get('productos_solicitados', 'N/A')),
            str(order.get('tiempo', 'N/A'))
        )
    
    console.print(table)
    
    # Save to JSON
    import json
    output_file = '../data/parsed_order_info.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(orders_list, f, indent=2, ensure_ascii=False)
    
    console.print(f"\n[green]✅ Saved to: {output_file}[/green]")
    
    return orders_list

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
