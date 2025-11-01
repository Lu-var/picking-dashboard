import json

# Load the Excalidraw file
with open('data/Untitled-2025-10-25-2125.excalidraw', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("🔍 AISLE MARKER ANALYSIS")
print("=" * 60)

# Find all rectangles with partial transparency
aisle_markers = []
for element in data['elements']:
    if element['type'] == 'rectangle':
        opacity = element.get('opacity', 100)
        
        # Check for partial transparency (not fully opaque, not fully transparent)
        if 0 < opacity < 100:
            stroke_color = element.get('strokeColor', 'transparent')
            fill_color = element.get('backgroundColor', 'transparent')
            width = element.get('width', 0)
            height = element.get('height', 0)
            x = element.get('x', 0)
            y = element.get('y', 0)
            
            aisle_markers.append({
                'opacity': opacity,
                'stroke_color': stroke_color,
                'fill_color': fill_color,
                'width': width,
                'height': height,
                'x': x,
                'y': y,
                'size': width * height
            })

print(f"\nFound {len(aisle_markers)} zones with partial transparency")
print("\nAISLE MARKERS:")
print("-" * 60)

# Sort by opacity for easier viewing
aisle_markers.sort(key=lambda x: x['opacity'])

for i, marker in enumerate(aisle_markers, 1):
    print(f"\nMarker {i}:")
    print(f"  Opacity: {marker['opacity']}%")
    print(f"  Size: {marker['width']:.0f} x {marker['height']:.0f} (area: {marker['size']:.0f})")
    print(f"  Position: ({marker['x']:.0f}, {marker['y']:.0f})")
    print(f"  Fill color: {marker['fill_color']}")
    print(f"  Stroke color: {marker['stroke_color']}")

# Group by opacity level
print("\n" + "=" * 60)
print("GROUPED BY OPACITY:")
print("-" * 60)

opacity_groups = {}
for marker in aisle_markers:
    opacity = marker['opacity']
    if opacity not in opacity_groups:
        opacity_groups[opacity] = []
    opacity_groups[opacity].append(marker)

for opacity in sorted(opacity_groups.keys()):
    markers = opacity_groups[opacity]
    print(f"\n{opacity}% opacity: {len(markers)} markers")
    avg_size = sum(m['size'] for m in markers) / len(markers)
    print(f"  Average size: {avg_size:.0f} sq units")
    colors = set(m['fill_color'] for m in markers)
    print(f"  Colors used: {', '.join(colors)}")

print("\n" + "=" * 60)
print("SUMMARY:")
print(f"Total aisle markers: {len(aisle_markers)}")
print(f"Opacity levels used: {len(opacity_groups)}")
print(f"Distinct opacity values: {sorted(opacity_groups.keys())}")
