# 📊 Excel Automation Demo

**[Live Demo →](LIVE_DEMO_URL_EXCEL)**

Transform raw data (CSV/JSON) into professionally formatted Excel reports with custom styling, auto-sized columns, and proper number formatting.

## Screenshots

![Excel Automation Demo](docs/excel-demo.png)
*Web interface with sample data and upload options*

![Generated Excel Report](docs/excel-output.png)
*Example of generated Excel file with formatting*

## Features

- 📁 **File Upload**: Process CSV or JSON files (up to 5MB)
- 🎯 **One-Click Demo**: Try with pre-loaded sample sales data
- 🎨 **Professional Formatting**: 
  - Styled headers with colors and borders
  - Auto-adjusted column widths
  - Currency and number formatting
  - Custom report titles
- 🌐 **Web Interface**: Simple, modern UI - no coding required
- ⚡ **Fast Processing**: Serverless architecture for instant results

## What It Does

This demo showcases automated Excel report generation:

1. Upload your CSV or JSON data file
2. Click "Try with Sample Data" to see it work instantly
3. Download a professionally formatted Excel file
4. All formatting applied automatically (headers, borders, number formats, column widths)

Perfect for:
- Sales reports
- Inventory tracking
- Financial summaries
- Data exports
- Client deliverables

## Technical Details

- **Framework**: FastAPI (Python)
- **Libraries**: pandas, openpyxl
- **Deployment**: Vercel Serverless Functions
- **Max File Size**: 5MB
- **Supported Formats**: CSV, JSON

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Open in browser
http://localhost:8000
```

## API Usage

### Endpoint: POST `/api/generate`

```python
import requests

data = {
    "data": [
        {"Product": "Laptop", "Units": 45, "Revenue": 40499.55},
        {"Product": "Mouse", "Units": 120, "Revenue": 2998.80}
    ],
    "title": "Monthly Sales Report"
}

response = requests.post("http://localhost:8000/api/generate", json=data)
with open("report.xlsx", "wb") as f:
    f.write(response.content)
```

## Sample Data

The demo includes realistic sample sales data:
- 8 products across Electronics and Furniture categories
- Unit quantities, prices, and calculated revenue
- Demonstrates currency formatting and calculations

## License

MIT
