"""
Parse screenshots using Google Cloud Vision OCR
Extracts: Order ID, Total SKUs, and Product Data only
"""

import os
import re
import json
from collections import defaultdict
from google.cloud import vision
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

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

def parse_text(text, filename):
    """Parse OCR text to extract order ID, total SKUs, and product data only"""
    lines = text.split('\n')
    
    data = {
        'order_id': None,
        'total_skus': None,
        'items': []
    }
    
    # Find order ID (vXXXXXXXXXXjmch-XX)
    for line in lines:
        if 'jmch' in line.lower():
            data['order_id'] = line.strip()
            break
    
    # Find total SKUs (0/20 format)
    for line in lines:
        match = re.search(r'(\d+)/(\d+)', line)
        if match:
            data['total_skus'] = int(match.group(2))
            break
    
    # Parse items - look for "Unidades: X" pattern
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Found an item
        if line.startswith('Unidades:'):
            match = re.search(r'Unidades:\s*(\d+)', line)
            if match:
                item = {'quantity': int(match.group(1))}
                
                # Brand is right before Unidades
                if i >= 1:
                    item['brand'] = lines[i - 1].strip()
                
                # Product name: collect all lines before brand until we hit a separator
                # Skip lines that are likely separators (categories, empty, timestamps)
                product_lines = []
                j = i - 2  # Start 2 lines before Unidades (skip brand)
                
                separators = ['Refrigerados', 'Congelados', 'Almacén', 'Verdulería', 
                             'Panadería', 'Hrs.', 'Prod.', 'Total disponible:', 
                             'Pickeado:', '/', 'REFRIGERADOR', 'CONGELADOR', 'PASILLO',
                             'PUERTA', 'BANDEJA', 'ESTANTE', 'Frutas y verduras',
                             'Refrigeradas', 'Pedido', 'disponible']
                
                # Also skip lines that look like UI elements (single letters, numbers, counters)
                def is_separator_or_ui(text):
                    if not text or len(text) <= 1:
                        return True
                    if any(sep in text for sep in separators):
                        return True
                    # Skip counter-like text: "0/20", "00:16", single digits/letters
                    if re.match(r'^[\d\s:/\-|]+$', text):
                        return True
                    # Skip very short text that's not likely a product name
                    if len(text) <= 2 and not text.isalpha():
                        return True
                    return False
                
                while j >= 0:
                    candidate = lines[j].strip()
                    
                    # Stop if we hit a separator, UI element, or empty line
                    if is_separator_or_ui(candidate):
                        break
                    
                    # Stop if line looks like a price (starts with $)
                    if candidate.startswith('$'):
                        break
                    
                    # Stop if line looks like order ID
                    if 'jmch' in candidate.lower():
                        break
                    
                    # This is part of the product name
                    product_lines.insert(0, candidate)
                    j -= 1
                
                # Combine product name lines
                if product_lines:
                    item['product_name'] = ' '.join(product_lines)
                elif i >= 2:
                    # Fallback: just use the line before brand
                    item['product_name'] = lines[i - 2].strip()
                
                # Price is next line
                if i + 1 < len(lines):
                    price_line = lines[i + 1].strip()
                    if price_line.startswith('$'):
                        item['price'] = price_line
                
                # Location is line after price
                if i + 2 < len(lines):
                    loc_line = lines[i + 2].strip()
                    if 'PASILLO' in loc_line and 'ESTANTE' in loc_line:
                        # Extract numbers from "PASILLO-4 | ESTANTE - 72"
                        pasillo_match = re.search(r'PASILLO[^0-9]*(\d+)', loc_line)
                        estante_match = re.search(r'ESTANTE[^0-9]*(\d+)', loc_line)
                        
                        if pasillo_match and estante_match:
                            item['location'] = f"PASILLO {pasillo_match.group(1)} ESTANTE {estante_match.group(1)}"
                
                data['items'].append(item)
        
        i += 1
    
    return data

def main(test_mode=True):
    """Parse screenshots - extracts order ID, total SKUs, and product data only"""
    console.print(Panel.fit(
        f"[bold cyan]Google Vision Screenshot Parser[/bold cyan]\n"
        f"Extracts: Order ID, Total SKUs, Product Data",
        border_style="cyan"
    ))
    
    screenshots_dir = '../data/App Order Screenshots'
    all_files = sorted([f for f in os.listdir(screenshots_dir) if f.endswith('.png')])
    
    files = all_files[:5] if test_mode else all_files
    
    console.print(f"\nProcessing {len(files)} screenshots...\n")
    
    # Group by order ID
    orders = defaultdict(list)
    
    for i, filename in enumerate(files, 1):
        filepath = os.path.join(screenshots_dir, filename)
        console.print(f"[{i}/{len(files)}] {filename}")
        
        try:
            text = ocr_screenshot(filepath)
            if text:
                data = parse_text(text, filename)
                
                if data['order_id']:
                    orders[data['order_id']].append(data)
        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")
    
    # Merge screenshots by order
    console.print(f"\n[green]Found {len(orders)} unique orders[/green]\n")
    
    merged_orders = []
    for order_id, screenshots in orders.items():
        # Combine all items from all screenshots
        all_items = []
        for screenshot in screenshots:
            all_items.extend(screenshot['items'])
        
        # Deduplicate based on product name + quantity
        unique_items = []
        seen = set()
        for item in all_items:
            key = f"{item.get('product_name', '')}_{item.get('quantity', 0)}"
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
                unique_items.append(item)
        
        
        merged = {
            'order_id': order_id,
            'total_skus': screenshots[0]['total_skus'],
            'items': unique_items
        }
        
        merged_orders.append(merged)
    
    # Display results
    table = Table(title="Parsed Orders", show_header=True)
    table.add_column("Order ID", style="cyan")
    table.add_column("Total SKUs", style="green")
    table.add_column("Items Found", style="blue")
    table.add_column("SKUs Counted", style="green")
    
    for order in merged_orders:
        skus_counted = sum(item.get('quantity', 0) for item in order['items'])
        table.add_row(
            order['order_id'],
            str(order['total_skus']),
            str(len(order['items'])),
            str(skus_counted)
        )
    
    console.print(table)
    
    # Save
    output_file = '../data/parsed_orders_test.json' if test_mode else '../data/parsed_orders_final.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_orders, f, indent=2, ensure_ascii=False)
    
    console.print(f"\n[green]Saved to: {output_file}[/green]")
    
    return merged_orders

if __name__ == "__main__":
    import sys
    
    # Check for --full flag
    test_mode = '--full' not in sys.argv
    
    try:
        orders = main(test_mode=test_mode)
        
        # Show first order details
        if orders:
            console.print("\n[cyan]Sample: First order product data[/cyan]")
            for i, item in enumerate(orders[0]['items'][:5], 1):
                console.print(f"  {i}. {item.get('product_name', 'N/A')}")
                console.print(f"     Brand: {item.get('brand', 'N/A')} | Qty: {item.get('quantity', '?')}")
                console.print(f"     Price: {item.get('price', 'N/A')} | Location: {item.get('location', 'N/A')}")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
