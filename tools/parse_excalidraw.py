"""
Parse Excalidraw layout file and extract zone information
"""
import json
import sys
from pathlib import Path

# Color to zone type mapping
COLOR_MAP = {
    '#f59e0b': 'dry_shelves',
    '#10b981': 'produce',
    '#06b6d4': 'fridges',
    '#3b82f6': 'freezers',
    '#22c55e': 'chilled_produce',
    '#14b8a6': 'prepared_meals',
    '#ef4444': 'cecineria',
    '#8b5cf6': 'frontera',
    '#0ea5e9': 'ice_dispenser',
    '#64748b': 'bagging',
    '#a855f7': 'backpacks',
    '#fb923c': 'handoff',
    '#475569': 'aisle',
    '#1e293b': 'wall',
}

def parse_excalidraw(excalidraw_path):
    """Parse Excalidraw JSON and extract zones"""
    with open(excalidraw_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    zones = []
    aisles = []
    texts = {}
    
    # First pass: collect all text elements
    for element in data.get('elements', []):
        if element.get('type') == 'text':
            texts[element['id']] = {
                'text': element.get('text', ''),
                'x': element.get('x', 0),
                'y': element.get('y', 0)
            }
    
    # Second pass: process rectangles
    for element in data.get('elements', []):
        if element.get('type') != 'rectangle':
            continue
        
        # Get element properties
        elem_id = element.get('id')
        x = element.get('x', 0)
        y = element.get('y', 0)
        width = element.get('width', 0)
        height = element.get('height', 0)
        bg_color = element.get('backgroundColor', 'transparent')
        
        # Skip transparent elements (floor)
        if bg_color == 'transparent':
            continue
        
        # Find zone type by color
        zone_type = COLOR_MAP.get(bg_color, 'unknown')
        
        # Find associated text label
        label = None
        bound_elements = element.get('boundElements')
        if bound_elements:
            for bound in bound_elements:
                if bound.get('type') == 'text':
                    text_id = bound.get('id')
                    if text_id in texts:
                        label = texts[text_id]['text'].strip()
                        break
        
        # If no bound text, find nearest text
        if not label:
            center_x = x + width / 2
            center_y = y + height / 2
            min_dist = float('inf')
            nearest_text = None
            
            for text_id, text_data in texts.items():
                tx = text_data['x']
                ty = text_data['y']
                dist = ((tx - center_x) ** 2 + (ty - center_y) ** 2) ** 0.5
                
                # Only consider texts within the rectangle or very close
                if dist < min_dist and dist < max(width, height):
                    min_dist = dist
                    nearest_text = text_data['text'].strip()
            
            label = nearest_text
        
        zone_info = {
            'id': elem_id,
            'x': round(x, 2),
            'y': round(y, 2),
            'width': round(width, 2),
            'height': round(height, 2),
            'color': bg_color,
            'zone_type': zone_type,
            'label': label
        }
        
        # Separate aisles from zones
        if zone_type == 'aisle':
            aisles.append(zone_info)
        else:
            zones.append(zone_info)
    
    return {
        'zones': zones,
        'aisles': aisles,
        'metadata': {
            'total_zones': len(zones),
            'total_aisles': len(aisles),
            'source_file': str(excalidraw_path)
        }
    }

def main():
    # Find the excalidraw file
    data_dir = Path(__file__).parent.parent / 'data'
    excalidraw_file = data_dir / 'Untitled-2025-10-25-2125.excalidraw'
    
    if not excalidraw_file.exists():
        print(f"Error: Excalidraw file not found at {excalidraw_file}")
        sys.exit(1)
    
    print(f"Parsing {excalidraw_file.name}...")
    layout_data = parse_excalidraw(excalidraw_file)
    
    # Save to JSON
    output_file = data_dir / 'darkstore_layout.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(layout_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Parsed {layout_data['metadata']['total_zones']} zones")
    print(f"✅ Parsed {layout_data['metadata']['total_aisles']} aisles")
    print(f"✅ Saved to {output_file}")
    
    # Print summary by zone type
    zone_types = {}
    for zone in layout_data['zones']:
        zt = zone['zone_type']
        zone_types[zt] = zone_types.get(zt, 0) + 1
    
    print("\n📊 Zone Summary:")
    for zone_type, count in sorted(zone_types.items()):
        print(f"  {zone_type}: {count}")

if __name__ == '__main__':
    main()
