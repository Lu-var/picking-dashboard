import json

# Load the Excalidraw file
with open('data/Untitled-2025-10-25-2125.excalidraw', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("🚶 WALKABLE ZONES ANALYSIS")
print("=" * 60)

# Categorize all rectangles by transparency and purpose
solid_zones = []
aisle_markers = []  # 50% transparent
walls = []  # Fully transparent with borders
potential_walkways = []

for element in data['elements']:
    if element['type'] == 'rectangle':
        opacity = element.get('opacity', 100)
        stroke_color = element.get('strokeColor', 'transparent')
        fill_color = element.get('backgroundColor', 'transparent')
        width = element.get('width', 0)
        height = element.get('height', 0)
        x = element.get('x', 0)
        y = element.get('y', 0)
        
        zone = {
            'opacity': opacity,
            'stroke_color': stroke_color,
            'fill_color': fill_color,
            'width': width,
            'height': height,
            'x': x,
            'y': y,
            'size': width * height
        }
        
        if opacity == 100 and fill_color != 'transparent':
            solid_zones.append(zone)
        elif opacity == 50:
            aisle_markers.append(zone)
        elif fill_color == 'transparent' and stroke_color != 'transparent':
            walls.append(zone)

print(f"\n📊 ZONE BREAKDOWN:")
print(f"  Solid zones (storage): {len(solid_zones)}")
print(f"  Aisle markers (50% transparent): {len(aisle_markers)}")
print(f"  Walls (transparent with borders): {len(walls)}")

print("\n" + "=" * 60)
print("🚶 WALKABLE AREAS:")
print("-" * 60)

print(f"\n1. MAIN AISLES (Semi-transparent markers): {len(aisle_markers)}")
print("   These are the numbered aisles where pickers walk:")
for i, marker in enumerate(sorted(aisle_markers, key=lambda x: x['x']), 1):
    print(f"   Aisle {i}: {marker['width']:.0f} x {marker['height']:.0f} at ({marker['x']:.0f}, {marker['y']:.0f})")

print(f"\n2. WALLS/BARRIERS (Not walkable): {len(walls)}")
print("   These block movement:")
for i, wall in enumerate(walls, 1):
    print(f"   Wall {i}: {wall['width']:.0f} x {wall['height']:.0f} at ({wall['x']:.0f}, {wall['y']:.0f})")

print(f"\n3. IMPLICIT WALKWAYS:")
print("   The negative space between zones represents:")
print("   • Main walkway between top shelves and middle section")
print("   • Walkway around Frutas y Verduras area")
print("   • Path from picking area to Despacho/handoff")
print("   • Space around Mesas Embolsado")

print("\n" + "=" * 60)
print("🗺️ WALKABLE ZONE TYPES:")
print("-" * 60)
print("\n✓ EXPLICIT WALKWAYS (visible on map):")
print(f"  • 12 numbered aisles (50% transparent)")
print(f"  • Color: #475569 (slate gray)")
print(f"  • Average width: {sum(m['width'] for m in aisle_markers)/len(aisle_markers):.0f} units")
print(f"  • Location: Top section (shelves area)")

print("\n✓ IMPLICIT WALKWAYS (negative space):")
print("  • Open floor between sections")
print("  • Paths to dispatch/handoff areas")
print("  • Access routes around produce")

print("\n✗ NON-WALKABLE (barriers):")
print(f"  • {len(walls)} wall segments")
print(f"  • {len(solid_zones)} storage zones (shelves, freezers, etc.)")

print("\n" + "=" * 60)
print("💡 INTERPRETATION:")
print("-" * 60)
print("""
Your layout shows walkable zones in TWO ways:

1. EXPLICIT (50% transparent gray): The 12 numbered aisles
   - These are the main picking paths through the shelves
   - Semi-transparent so you can see both the aisle AND underlying structure

2. IMPLICIT (empty space): The open floor areas
   - Main walkway separating top from middle sections
   - Circulation space around Frutas y Verduras
   - Paths to Despacho, Uber, Retiro al Auto
   - Space around bagging tables

This is smart! It shows WHERE aisles are (for picking routes) while
keeping the floor space open and uncluttered.
""")
