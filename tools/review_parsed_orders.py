"""
Interactive review tool for parsed screenshot data.
Shows screenshot images alongside parsed data for easy correction.
"""

import json
import os
from pathlib import Path
from PIL import Image
import sys

def load_parsed_orders():
    """Load the parsed orders JSON"""
    json_path = Path(__file__).parent.parent / 'data' / 'parsed_orders_final.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_parsed_orders(orders):
    """Save the corrected parsed orders"""
    json_path = Path(__file__).parent.parent / 'data' / 'parsed_orders_final.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)
    print("\n✅ Saved changes to parsed_orders_final.json")

def get_screenshot_path(filename):
    """Convert old or new screenshot filename to path"""
    screenshots_dir = Path(__file__).parent.parent / 'data' / 'App Order Screenshots'
    
    # If it's old format, convert to new
    if filename.startswith('Screenshot_'):
        # Screenshot_20251022-080823_Picker Up.png -> 20251022_080823.png
        import re
        match = re.search(r'(\d{8})-(\d{6})', filename)
        if match:
            new_filename = f"{match.group(1)}_{match.group(2)}.png"
            return screenshots_dir / new_filename
    
    return screenshots_dir / filename

def show_order_review(order, order_num, total_orders):
    """Display order info and allow corrections"""
    print("\n" + "="*80)
    print(f"📦 ORDER {order_num}/{total_orders}: {order['order_id']}")
    print("="*80)
    print(f"📅 Date: {order['date']}")
    print(f"📸 Screenshots: {order['screenshots_count']}")
    print(f"📊 Total SKUs: {order['total_skus']} | Found: {order['skus_counted']}")
    
    # Show items
    print(f"\n📝 ITEMS ({len(order['items'])}):")
    for idx, item in enumerate(order['items'], 1):
        print(f"\n  [{idx}] {item.get('product_name', 'MISSING NAME')}")
        print(f"      Brand: {item.get('brand', 'MISSING')}")
        print(f"      Qty: {item.get('quantity', 'MISSING')}")
        print(f"      Price: {item.get('price', 'MISSING')}")
        print(f"      Location: {item.get('location', 'MISSING')}")

def open_screenshots_for_order(order):
    """Open all screenshots for an order"""
    screenshots_dir = Path(__file__).parent.parent / 'data' / 'App Order Screenshots'
    
    # Get all screenshots that match this order
    order_date = order['date'].replace('/', '')  # 22/10/2025 -> 22102025
    # Convert to YYYYMMDD format
    day, month, year = order_date[0:2], order_date[2:4], order_date[4:]
    date_str = f"{year}{month}{day}"  # 20251022
    
    # Find all screenshots for this date
    matching_screenshots = sorted([f for f in os.listdir(screenshots_dir) 
                                  if f.startswith(date_str) and f.endswith('.png')])
    
    if not matching_screenshots:
        print(f"\n⚠️  No screenshots found for date {date_str}")
        return
    
    print(f"\n🖼️  Opening {len(matching_screenshots)} screenshots for {order['date']}...")
    print(f"   Look for order ID: {order['order_id']}")
    
    # Open screenshots in default image viewer
    for screenshot in matching_screenshots[:order['screenshots_count']]:
        screenshot_path = screenshots_dir / screenshot
        if screenshot_path.exists():
            os.startfile(screenshot_path)
        else:
            print(f"   ⚠️  Not found: {screenshot}")

def edit_item(item):
    """Interactive item editor"""
    print("\n" + "-"*60)
    print("EDITING ITEM")
    print("-"*60)
    print(f"Current: {item.get('product_name', 'MISSING')}")
    print(f"Brand: {item.get('brand', 'MISSING')}")
    print(f"Qty: {item.get('quantity', 'MISSING')}")
    print(f"Price: {item.get('price', 'MISSING')}")
    print(f"Location: {item.get('location', 'MISSING')}")
    
    print("\nLeave blank to keep current value")
    
    new_name = input("Product name: ").strip()
    if new_name:
        item['product_name'] = new_name
    
    new_brand = input("Brand: ").strip()
    if new_brand:
        item['brand'] = new_brand
    
    new_qty = input("Quantity: ").strip()
    if new_qty:
        try:
            item['quantity'] = int(new_qty)
        except ValueError:
            print("⚠️  Invalid quantity, keeping original")
    
    new_price = input("Price (e.g., $1.790 ($1790 uni)): ").strip()
    if new_price:
        item['price'] = new_price
    
    new_location = input("Location (e.g., PASILLO 4 ESTANTE 72): ").strip()
    if new_location:
        item['location'] = new_location
    
    print("\n✅ Item updated")
    return item

def main():
    """Main review loop"""
    print("="*80)
    print(" 📋 PARSED ORDERS REVIEW TOOL")
    print("="*80)
    
    orders = load_parsed_orders()
    print(f"\nLoaded {len(orders)} orders")
    
    current_order = 0
    modified = False
    
    while True:
        order = orders[current_order]
        show_order_review(order, current_order + 1, len(orders))
        
        print("\n" + "-"*80)
        print("COMMANDS:")
        print("  [v] View screenshots for this order")
        print("  [e<num>] Edit item (e.g., 'e1' to edit item 1)")
        print("  [d<num>] Delete item (e.g., 'd5' to delete item 5)")
        print("  [n] Next order")
        print("  [p] Previous order")
        print("  [s] Save and exit")
        print("  [q] Quit without saving")
        print("-"*80)
        
        cmd = input("\nCommand: ").strip().lower()
        
        if cmd == 'v':
            open_screenshots_for_order(order)
        
        elif cmd.startswith('e') and len(cmd) > 1:
            try:
                item_num = int(cmd[1:]) - 1
                if 0 <= item_num < len(order['items']):
                    order['items'][item_num] = edit_item(order['items'][item_num])
                    modified = True
                else:
                    print(f"⚠️  Invalid item number. Must be 1-{len(order['items'])}")
            except ValueError:
                print("⚠️  Invalid command format. Use 'e1', 'e2', etc.")
        
        elif cmd.startswith('d') and len(cmd) > 1:
            try:
                item_num = int(cmd[1:]) - 1
                if 0 <= item_num < len(order['items']):
                    deleted_item = order['items'].pop(item_num)
                    print(f"\n🗑️  Deleted: {deleted_item.get('product_name', 'MISSING')}")
                    modified = True
                else:
                    print(f"⚠️  Invalid item number. Must be 1-{len(order['items'])}")
            except ValueError:
                print("⚠️  Invalid command format. Use 'd1', 'd2', etc.")
        
        elif cmd == 'n':
            if current_order < len(orders) - 1:
                current_order += 1
            else:
                print("⚠️  Already at last order")
        
        elif cmd == 'p':
            if current_order > 0:
                current_order -= 1
            else:
                print("⚠️  Already at first order")
        
        elif cmd == 's':
            if modified:
                save_parsed_orders(orders)
            print("\n👋 Goodbye!")
            break
        
        elif cmd == 'q':
            if modified:
                confirm = input("\n⚠️  You have unsaved changes. Quit anyway? (y/n): ")
                if confirm.lower() != 'y':
                    continue
            print("\n👋 Goodbye!")
            break
        
        else:
            print("⚠️  Unknown command")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        sys.exit(0)
