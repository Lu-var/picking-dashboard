import json

# Load the Excalidraw file
with open('c:/Dev/Picking/data/Untitled-2025-10-25-2125.excalidraw', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Analyze elements
rectangles = [e for e in data['elements'] if e.get('type') == 'rectangle']
texts = [e for e in data['elements'] if e.get('type') == 'text']

print(f"\n📊 EXCALIDRAW LAYOUT ANALYSIS")
print(f"=" * 50)
print(f"\n📦 Total elements: {len(data['elements'])}")
print(f"  - Rectangles: {len(rectangles)}")
print(f"  - Text labels: {len(texts)}")

# Color distribution
print(f"\n🎨 COLOR DISTRIBUTION:")
colors = {}
for e in rectangles:
    color = e.get('backgroundColor', 'none')
    colors[color] = colors.get(color, 0) + 1

for color, count in sorted(colors.items(), key=lambda x: x[1], reverse=True):
    if color != 'transparent':
        print(f"  {color}: {count} zones")

# Text labels
if texts:
    print(f"\n🏷️  TEXT LABELS:")
    for t in texts[:30]:
        text_content = t.get('text', '')
        x, y = t.get('x', 0), t.get('y', 0)
        print(f"  - '{text_content}' at ({x}, {y})")
else:
    print(f"\n⚠️  NO TEXT LABELS FOUND")
    print(f"   Consider adding numbered labels to identify zones!")

# Check for bound elements
print(f"\n🔗 BOUND ELEMENTS:")
bound_count = sum(1 for e in rectangles if e.get('boundElements'))
print(f"  Rectangles with bound text: {bound_count}")

print(f"\n" + "=" * 50)
