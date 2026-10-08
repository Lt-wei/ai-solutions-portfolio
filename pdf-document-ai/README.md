# 📄 PDF Document AI Demo

**[Live Demo →](LIVE_DEMO_URL_PDF)**

Extract and analyze data from PDF documents automatically — find emails, phone numbers, dates, currency amounts, and more using intelligent pattern recognition.

## Screenshots

![PDF Analyzer Interface](docs/pdf-demo.png)
*Upload interface with sample invoice option*

![Analysis Results](docs/pdf-results.png)
*Extracted data displayed in organized sections*

## Features

- 📁 **PDF Upload**: Process any PDF document (up to 10MB)
- 🎯 **One-Click Demo**: Try with pre-generated sample invoice
- 🔍 **Smart Extraction**:
  - Email addresses
  - Phone numbers (multiple formats)
  - Dates (various formats)
  - Currency amounts
  - URLs and web addresses
  - Key document sections
- 📊 **Document Statistics**: Page count, word count, character analysis
- 🌐 **Web Interface**: No coding required
- ⚡ **Fast Processing**: Instant results on serverless infrastructure

## What It Does

This demo showcases automated PDF document analysis:

1. Upload any PDF document (invoices, contracts, reports, etc.)
2. Click "Try with Sample Invoice" to see instant results
3. View extracted data organized by type
4. Get document statistics and metadata
5. No API keys or external services required

**Demo Mode**: Uses regex pattern matching to extract structured data. For production use cases, this could be enhanced with ML models or GPT-based extraction.

Perfect for:
- Invoice processing
- Contract analysis
- Document data extraction
- Form processing
- Receipt scanning
- Business document automation

## Technical Details

- **Framework**: FastAPI (Python)
- **Libraries**: PyPDF2, reportlab (for sample generation), regex
- **Deployment**: Vercel Serverless Functions
- **Max File Size**: 10MB
- **Processing**: Text extraction + pattern matching (no external APIs)

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Open in browser
http://localhost:8001
```

## API Usage

### Endpoint: POST `/analyze`

```python
import requests

with open("invoice.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post("http://localhost:8001/analyze", files=files)
    data = response.json()
    
print(f"Found {len(data['emails'])} emails")
print(f"Found {data['word_count']} words")
```

## Sample Data

The demo generates a realistic sample invoice containing:
- Company information with contact details
- Invoice numbering and dates
- Line items with pricing
- Tax calculations
- Payment terms and bank details
- Multiple data types for extraction demonstration

## Extraction Capabilities

| Data Type | Detection Method | Example |
|-----------|------------------|---------|
| Emails | Regex pattern | name@example.com |
| Phone Numbers | Multiple formats | +1 (555) 123-4567 |
| Dates | Various formats | January 15, 2024 |
| Currency | USD amounts | $12,500.00 |
| URLs | Web addresses | https://example.com |

## License

MIT
