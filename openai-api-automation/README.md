# 🤖 OpenAI API Automation Demo

**[Live Demo →](LIVE_DEMO_URL_API)**

Automate intelligent text processing with AI — summarize documents, analyze sentiment, extract keywords, and translate between languages.

## Screenshots

![OpenAI Demo Interface](docs/openai-demo.png)
*Task selection and sample data options*

![Processing Results](docs/openai-results.png)
*AI-generated summary and analysis*

## Features

- 📝 **Text Summarization**: Generate concise summaries of long documents
- 😊 **Sentiment Analysis**: Detect positive, negative, neutral, or mixed sentiment
- 🔑 **Keyword Extraction**: Identify key terms and topics automatically
- 🌐 **Translation**: Translate text to Spanish, French, German, Japanese, and more
- 🎯 **Sample Data**: Try pre-loaded examples (business reports, reviews, articles, emails)
- 🌐 **Web Interface**: No coding required
- ⚡ **Fast Processing**: Instant results

## What It Does

This demo showcases AI-powered text processing automation:

1. **Demo Mode** (default): Uses intelligent regex patterns and rule-based processing
2. **Live API Mode** (optional): Set `OPENAI_API_KEY` environment variable to use real GPT models

**Demo mode is free and requires no API keys** — perfect for portfolio demonstrations.

Perfect for:
- Content summarization
- Customer feedback analysis
- Document processing automation
- Multi-language communication
- Content classification
- Business intelligence

## Technical Details

- **Framework**: FastAPI (Python)
- **AI Integration**: OpenAI API (optional)
- **Deployment**: Vercel Serverless Functions
- **Fallback**: Intelligent demo mode when no API key provided
- **Models**: GPT-4o-mini (when API key present)

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run in demo mode (no API key needed)
python app.py

# Or run with real OpenAI API
export OPENAI_API_KEY="your-key-here"
python app.py

# Open in browser
http://localhost:8002
```

## API Usage

### Endpoint: POST `/process`

```python
import requests

data = {
    "text": "Your text here...",
    "task": "summarize"  # or "sentiment", "keywords", "translate"
}

response = requests.post("http://localhost:8002/process", json=data)
result = response.json()
print(result["result"])
```

### Translation Example

```python
data = {
    "text": "Hello, how are you?",
    "task": "translate",
    "target_language": "Spanish"
}

response = requests.post("http://localhost:8002/process", json=data)
print(response.json()["result"])  # "Hola, ¿cómo estás?"
```

## Demo vs Live Mode

| Feature | Demo Mode | Live API Mode |
|---------|-----------|---------------|
| Cost | Free | Pay-per-use |
| API Key Required | No | Yes |
| Response Quality | Rule-based | GPT-4o-mini |
| Speed | Instant | ~1-3 seconds |
| Accuracy | Good for demos | Production-ready |

## Environment Variables

- `OPENAI_API_KEY` (optional): Enable real OpenAI API processing

When deployed to Vercel without this variable, the app runs in demo mode automatically.

## Sample Data Included

- **Business Report**: Quarterly results with financial metrics
- **Product Review**: Customer feedback example
- **News Article**: Technology news sample
- **Email Draft**: Professional communication example

## Supported Languages for Translation

Spanish, French, German, Japanese, Chinese, Italian, Portuguese, and more.

## License

MIT
