import json

# Load the Excalidraw file
with open('c:/Dev/Picking/data/Untitled-2025-10-25-2125.excalidraw', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find transparent rectangles
transparent = [e for e in data['elements'] if e.get('type') == 'rectangle' and e.get('backgroundColor') == 'transparent']

print(f"\n🔍 TRANSPARENT ZONES ANALYSIS")
print(f"=" * 60)
print(f"\nFound {len(transparent)} transparent rectangles")
print(f"\nThese could be:")
print(f"  - Floor areas (where you walk)")
print(f"  - Walls/borders")
print(f"  - Background elements")

print(f"\n📐 TRANSPARENT ZONE COORDINATES:")
for i, zone in enumerate(transparent, 1):
    x = zone.get('x', 0)
    y = zone.get('y', 0)
    w = zone.get('width', 0)
    h = zone.get('height', 0)
    print(f"\n  Zone {i}:")
    print(f"    Position: ({x}, {y})")
    print(f"    Size: {w} x {h}")
    print(f"    Area: {w * h:.0f} sq units")
    
    # Try to determine if it's likely floor or wall based on size
    if w > 500 or h > 500:
        print(f"    → Likely: FLOOR (large area)")
    elif w < 100 and h < 100:
        print(f"    → Likely: Small element")
    else:
        print(f"    → Likely: WALL/BORDER (medium strip)")

# Now let's look at the overall layout bounds
all_rects = [e for e in data['elements'] if e.get('type') == 'rectangle']
if all_rects:
    min_x = min(e.get('x', 0) for e in all_rects)
    max_x = max(e.get('x', 0) + e.get('width', 0) for e in all_rects)
    min_y = min(e.get('y', 0) for e in all_rects)
    max_y = max(e.get('y', 0) + e.get('height', 0) for e in all_rects)
    
    print(f"\n📏 OVERALL LAYOUT BOUNDS:")
    print(f"  X range: {min_x} to {max_x} (width: {max_x - min_x})")
    print(f"  Y range: {min_y} to {max_y} (height: {max_y - min_y})")

print(f"\n" + "=" * 60)
print(f"\n💡 RECOMMENDATION:")
print(f"  If transparent zones are FLOOR:")
print(f"    → Keep them transparent or use light gray #f8fafc")
print(f"  If transparent zones are WALLS:")
print(f"    → Change to dark #1e293b or #475569")
print(f"")
