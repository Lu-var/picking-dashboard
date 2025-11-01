"""
Test OCR on Order Info screenshots
Identifies what data can be extracted from start and completion screens
"""

import os
from google.cloud import vision
from rich.console import Console
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

def main():
    """Test OCR on first few screenshots"""
    console.print(Panel.fit(
        "[bold cyan]Order Info Screenshot OCR Test[/bold cyan]\n"
        "Testing start screen (56) and completion screen (29)",
        border_style="cyan"
    ))
    
    screenshots_dir = '../data/Order Info Screenshots'
    
    # Test: start screen (075656) and completion screen (090329)
    test_files = [
        'Screenshot_20251008-075656_Picker Up.png',  # Start screen
        'Screenshot_20251008-090329_Picker Up.png'   # Completion screen
    ]
    
    for filename in test_files:
        filepath = os.path.join(screenshots_dir, filename)
        console.print(f"\n[yellow]{'='*80}[/yellow]")
        console.print(f"[cyan]📸 {filename}[/cyan]")
        console.print(f"[yellow]{'='*80}[/yellow]\n")
        
        try:
            text = ocr_screenshot(filepath)
            if text:
                console.print(text)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    console.print("\n[green]✅ Test complete![/green]")
    console.print("\n[yellow]START screen should have:[/yellow]")
    console.print("  • Order ID (Pedido)")
    console.print("  • Cliente name")
    console.print("  • SKUs count")
    console.print("  • Unidades (units)")
    console.print("  • Fecha de entrega (date)")
    console.print("\n[yellow]COMPLETION screen should have:[/yellow]")
    console.print("  • Order ID")
    console.print("  • Time taken (Tiempo)")
    console.print("  • Final SKU count")

if __name__ == '__main__':
    main()
