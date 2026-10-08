# 🚀 AI Solutions Portfolio

Professional FastAPI demonstration projects showcasing automation and AI integration capabilities.

## Live Demos

| Project | Description | Live Demo |
|---------|-------------|-----------|
| 📊 **Excel Automation** | Transform CSV/JSON data into formatted Excel reports | **[Try it live →](LIVE_DEMO_URL_EXCEL)** |
| 📄 **PDF Document AI** | Extract and analyze data from PDF documents | **[Try it live →](LIVE_DEMO_URL_PDF)** |
| 🤖 **OpenAI API Automation** | AI-powered text processing and analysis | **[Try it live →](LIVE_DEMO_URL_API)** |

## Projects Overview

### 1. Excel Automation
Converts raw data (CSV/JSON) into professionally formatted Excel reports with automatic styling, column sizing, and number formatting.

**Features:**
- Web-based file upload interface
- One-click sample data demonstration
- Automatic formatting (headers, borders, colors)
- Currency and number formatting
- Custom report titles

[View Project →](./excel-automation/)

### 2. PDF Document AI
Extracts structured data from PDF documents including emails, phone numbers, dates, currency amounts, and key sections.

**Features:**
- PDF text extraction
- Intelligent pattern recognition
- Multi-format date detection
- Contact information extraction
- Document statistics and analysis

[View Project →](./pdf-document-ai/)

### 3. OpenAI API Automation
Demonstrates AI-powered text processing with automatic fallback to demo mode when no API key is provided.

**Features:**
- Text summarization
- Sentiment analysis
- Keyword extraction
- Multi-language translation
- Works without API keys (demo mode)
- Optional GPT-4o integration

[View Project →](./openai-api-automation/)

## Technology Stack

- **Framework**: FastAPI (Python)
- **Deployment**: Vercel Serverless Functions
- **Libraries**: pandas, openpyxl, PyPDF2, reportlab, OpenAI SDK
- **Frontend**: Modern HTML5/CSS3/JavaScript

## Quick Start (Local Development)

Each project can be run independently:

```bash
# Excel Automation
cd excel-automation
pip install -r requirements.txt
python app.py
# Open http://localhost:8000

# PDF Document AI
cd pdf-document-ai
pip install -r requirements.txt
python app.py
# Open http://localhost:8001

# OpenAI API Automation
cd openai-api-automation
pip install -r requirements.txt
python app.py
# Open http://localhost:8002
```

## Deployment to Vercel

Each project is designed to deploy as a separate Vercel project:

### 1. Excel Automation Deployment

```bash
# Via Vercel CLI
cd excel-automation
vercel --prod

# Or via Vercel Dashboard:
# - Root Directory: excel-automation
# - Framework Preset: Other
# - Build Command: (leave empty)
# - Install Command: pip install -r requirements.txt
# - Environment Variables: (none required)
```

### 2. PDF Document AI Deployment

```bash
# Via Vercel CLI
cd pdf-document-ai
vercel --prod

# Or via Vercel Dashboard:
# - Root Directory: pdf-document-ai
# - Framework Preset: Other
# - Build Command: (leave empty)
# - Install Command: pip install -r requirements.txt
# - Environment Variables: (none required)
```

### 3. OpenAI API Automation Deployment

```bash
# Via Vercel CLI
cd openai-api-automation
vercel --prod

# Or via Vercel Dashboard:
# - Root Directory: openai-api-automation
# - Framework Preset: Other
# - Build Command: (leave empty)
# - Install Command: pip install -r requirements.txt
# - Environment Variables:
#   - OPENAI_API_KEY (optional - enables real AI, works without it in demo mode)
```

## Vercel Configuration

Each project includes:
- ✅ `requirements.txt` - Python dependencies
- ✅ `vercel.json` - Function configuration (memory, timeout)
- ✅ `app.py` - FastAPI application with proper ASGI export
- ✅ `/health` - Health check endpoint

All projects work out of the box with Vercel's Python runtime.

## Key Features for Non-Technical Clients

- ✅ **One-Click Demos**: Every project has "Try with Sample Data" buttons
- ✅ **No Setup Required**: Web interfaces accessible from any browser
- ✅ **No API Keys Needed**: Demo modes work without any external services
- ✅ **Professional UI**: Modern, intuitive interfaces
- ✅ **Instant Results**: Fast processing with immediate downloads/results
- ✅ **Mobile Responsive**: Works on desktop and mobile devices

## Architecture Highlights

- **Serverless**: All projects run on Vercel's serverless infrastructure
- **Stateless**: No databases required, perfect for demos
- **File Handling**: Proper temp directory usage (`/tmp` for serverless)
- **Size Limits**: Configured within Vercel's request limits (5-10MB)
- **Error Handling**: Graceful fallbacks and user-friendly error messages
- **Demo Mode**: All projects work without external API keys

## Portfolio Use Case

These projects demonstrate:
- ✅ Full-stack Python development (FastAPI)
- ✅ Modern frontend development (vanilla JS, responsive CSS)
- ✅ Cloud deployment expertise (Vercel serverless)
- ✅ API integration (OpenAI, with fallback patterns)
- ✅ Document processing (Excel generation, PDF extraction)
- ✅ User experience design (instant demos, clear workflows)
- ✅ Production-ready code (error handling, validation, testing)

## Testing Checklist

- [x] Each app runs locally with `python app.py`
- [x] Health check endpoints respond correctly
- [x] Sample data buttons work without uploads
- [x] File uploads respect size limits
- [x] Downloads work properly
- [x] UI is mobile responsive
- [x] Error messages are user-friendly
- [x] No API keys required for basic functionality

## License

MIT - Feel free to use these projects as references for your own work.

## Contact

Built by Leane for Upwork clients and portfolio demonstration.

📧 For project inquiries, see my [Upwork profile](https://www.upwork.com/).
