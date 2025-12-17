# Picking Dashboard

A simple, mobile-friendly dashboard for tracking order picking data from Google Sheets.

## Features

- 📱 **Mobile-responsive design** - Works great on phones and tablets
- ☁️ **Google Sheets integration** - Real-time data from your spreadsheet
- 📊 **Basic statistics** - Total orders, SKUs, time tracking
- 🔄 **Auto-refresh** - Updates every 5 minutes automatically

## Tech Stack

- **Backend**: Flask (Python web framework)
- **Frontend**: Vanilla JavaScript + CSS
- **Data Source**: Google Sheets CSV export
- **Styling**: Modern dark theme with gradients

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the dashboard:**
   ```bash
   python web_dashboard.py
   ```

3. **Access the dashboard:**
   - Open http://localhost:5000 in your browser
   - Or access from mobile using your computer's IP address

## Data Sources

- **Google Sheets**: Live order data from your picking spreadsheet
- **Google Cloud Vision**: Key file available for future OCR features
- **Screenshots**: Folder structure maintained for manual processing

## Project Structure

```
📦 Picking Dashboard
├── 🌐 web_dashboard.py          # Flask backend
├── 📁 templates/
│   └── index.html               # Mobile dashboard UI
├── 📁 data/
│   ├── google-vision-key.json   # Cloud Vision API credentials
│   ├── orders_latest.json       # Local order backup
│   ├── App Order Screenshots/   # Screenshot storage
│   └── Order Info Screenshots/  # Additional screenshots
└── 📄 requirements.txt          # Python dependencies
```

## Clean & Simple

This version focuses on the essentials:
- ✅ Basic order tracking and statistics
- ✅ Clean, fast mobile interface  
- ✅ Reliable Google Sheets integration
- ❌ No complex analytics (removed)
- ❌ No automated tools (removed)
- ❌ No warehouse mapping (removed)

Perfect for daily order tracking without complexity!