from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import os
import random
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="OpenAI API Automation Demo")

# Check if OpenAI API key is available (optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_REAL_API = bool(OPENAI_API_KEY)

if USE_REAL_API:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        USE_REAL_API = False
        print("⚠️  OpenAI package not available, using demo mode")

class TextRequest(BaseModel):
    text: str
    task: str  # "summarize", "sentiment", "keywords", "translate"
    target_language: Optional[str] = "Spanish"

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = ""

# Demo mode responses (used when no API key is provided)
DEMO_RESPONSES = {
    "summarize": {
        "sample_text": "Key points: The document discusses quarterly financial results, highlighting a 15% revenue increase and successful product launch. Operating expenses were controlled, and the company expanded into new markets. Future outlook remains positive with strategic investments planned.",
        "templates": [
            "Summary: The text discusses {topic} with main points including {point1} and {point2}. Overall outlook is {sentiment}.",
            "Key takeaways: {point1}, {point2}, and {point3}. The conclusion emphasizes {conclusion}.",
        ]
    },
    "sentiment": {
        "options": ["Positive", "Negative", "Neutral", "Mixed"],
        "details": {
            "Positive": "The text conveys optimistic and favorable sentiment.",
            "Negative": "The text expresses critical or unfavorable sentiment.",
            "Neutral": "The text maintains an objective, balanced tone.",
            "Mixed": "The text contains both positive and negative elements."
        }
    },
    "keywords": {
        "sample": ["artificial intelligence", "automation", "efficiency", "innovation", "technology", "digital transformation"],
        "categories": ["Technology", "Business", "Innovation", "Strategy"]
    },
    "translate": {
        "sample_translations": {
            "Spanish": "Este es un ejemplo de traducción al español. La tecnología de IA puede traducir texto entre múltiples idiomas de manera eficiente.",
            "French": "Ceci est un exemple de traduction en français. La technologie IA peut traduire du texte entre plusieurs langues de manière efficace.",
            "German": "Dies ist ein Beispiel für eine Übersetzung ins Deutsche. KI-Technologie kann Text effizient zwischen mehreren Sprachen übersetzen.",
            "Japanese": "これは日本語への翻訳の例です。AI技術は、複数の言語間でテキストを効率的に翻訳できます。"
        }
    },
    "chat": {
        "responses": [
            "That's an interesting question! Based on typical use cases, {context}.",
            "Here's what I can tell you: {context}. Would you like more details?",
            "Great question! The key considerations are {context}.",
        ],
        "contexts": [
            "automation can significantly improve efficiency and reduce manual work",
            "AI-powered solutions are transforming how businesses operate",
            "data-driven insights help make better strategic decisions",
            "integrating APIs can streamline workflows and improve productivity"
        ]
    }
}

def generate_demo_response(task: str, text: str, **kwargs) -> dict:
    """Generate a simulated AI response for demo mode."""
    
    if task == "summarize":
        if "financial" in text.lower() or "revenue" in text.lower():
            summary = DEMO_RESPONSES["summarize"]["sample_text"]
        else:
            words = text.split()[:50]
            summary = f"Summary: {' '.join(words[:30])}... The text covers key topics and concludes with important insights."
        return {
            "task": "summarize",
            "result": summary,
            "word_count_original": len(text.split()),
            "word_count_summary": len(summary.split()),
            "demo_mode": True
        }
    
    elif task == "sentiment":
        # Simple rule-based sentiment
        positive_words = ["good", "great", "excellent", "positive", "success", "happy", "love", "best"]
        negative_words = ["bad", "poor", "terrible", "negative", "failure", "sad", "hate", "worst"]
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            sentiment = "Positive"
        elif neg_count > pos_count:
            sentiment = "Negative"
        elif pos_count == neg_count and pos_count > 0:
            sentiment = "Mixed"
        else:
            sentiment = "Neutral"
        
        return {
            "task": "sentiment",
            "result": sentiment,
            "explanation": DEMO_RESPONSES["sentiment"]["details"][sentiment],
            "confidence": round(random.uniform(0.75, 0.95), 2),
            "demo_mode": True
        }
    
    elif task == "keywords":
        # Extract potential keywords (simple approach)
        words = text.split()
        keywords = [w.strip('.,!?;:') for w in words if len(w) > 6][:8]
        
        if not keywords:
            keywords = DEMO_RESPONSES["keywords"]["sample"][:5]
        
        return {
            "task": "keywords",
            "result": keywords,
            "categories": random.sample(DEMO_RESPONSES["keywords"]["categories"], 2),
            "demo_mode": True
        }
    
    elif task == "translate":
        target_lang = kwargs.get("target_language", "Spanish")
        
        if target_lang in DEMO_RESPONSES["translate"]["sample_translations"]:
            translation = DEMO_RESPONSES["translate"]["sample_translations"][target_lang]
        else:
            translation = f"[Demo translation to {target_lang}] {text[:100]}..."
        
        return {
            "task": "translate",
            "source_language": "English",
            "target_language": target_lang,
            "result": translation,
            "demo_mode": True
        }
    
    else:
        return {
            "error": f"Unknown task: {task}",
            "demo_mode": True
        }

async def call_real_openai(task: str, text: str, **kwargs):
    """Call real OpenAI API if available."""
    try:
        if task == "summarize":
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes text concisely."},
                    {"role": "user", "content": f"Summarize this text:\n\n{text}"}
                ],
                max_tokens=150
            )
            return {
                "task": "summarize",
                "result": response.choices[0].message.content,
                "model": response.model,
                "demo_mode": False
            }
        
        elif task == "sentiment":
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a sentiment analysis expert. Respond with only: Positive, Negative, Neutral, or Mixed, followed by a brief explanation."},
                    {"role": "user", "content": f"Analyze the sentiment:\n\n{text}"}
                ],
                max_tokens=100
            )
            content = response.choices[0].message.content
            lines = content.split('\n')
            sentiment = lines[0].strip()
            explanation = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
            
            return {
                "task": "sentiment",
                "result": sentiment,
                "explanation": explanation,
                "model": response.model,
                "demo_mode": False
            }
        
        elif task == "keywords":
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract key terms and topics. Return only a comma-separated list."},
                    {"role": "user", "content": f"Extract keywords from:\n\n{text}"}
                ],
                max_tokens=100
            )
            keywords = [k.strip() for k in response.choices[0].message.content.split(',')]
            
            return {
                "task": "keywords",
                "result": keywords,
                "model": response.model,
                "demo_mode": False
            }
        
        elif task == "translate":
            target_lang = kwargs.get("target_language", "Spanish")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Translate the following text to {target_lang}."},
                    {"role": "user", "content": text}
                ],
                max_tokens=500
            )
            
            return {
                "task": "translate",
                "source_language": "English",
                "target_language": target_lang,
                "result": response.choices[0].message.content,
                "model": response.model,
                "demo_mode": False
            }
        
    except Exception as e:
        # Fall back to demo mode if API fails
        return generate_demo_response(task, text, **kwargs)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI."""
    api_status = "🟢 Live API" if USE_REAL_API else "🟡 Demo Mode"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OpenAI API Automation Demo</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }}
            .banner {{
                background: #1a202c;
                color: white;
                padding: 12px 20px;
                text-align: center;
                font-size: 14px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            }}
            .banner strong {{ color: #fbbf24; }}
            .demo-mode {{
                background: #059669;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                display: inline-block;
                margin-top: 5px;
            }}
            .api-status {{
                position: absolute;
                top: 20px;
                right: 20px;
                background: {'#10b981' if USE_REAL_API else '#f59e0b'};
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            }}
            .container {{
                flex: 1;
                max-width: 900px;
                margin: 40px auto;
                padding: 20px;
                position: relative;
            }}
            .card {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 40px;
            }}
            h1 {{
                color: #1a202c;
                font-size: 32px;
                margin-bottom: 10px;
                text-align: center;
            }}
            .subtitle {{
                color: #64748b;
                text-align: center;
                margin-bottom: 30px;
                font-size: 16px;
            }}
            .feature-list {{
                background: #f8fafc;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 30px;
            }}
            .feature-list ul {{
                list-style: none;
                padding-left: 0;
            }}
            .feature-list li {{
                padding: 8px 0;
                color: #475569;
            }}
            .feature-list li:before {{
                content: "✓ ";
                color: #10b981;
                font-weight: bold;
                margin-right: 8px;
            }}
            .input-group {{
                margin-bottom: 20px;
            }}
            label {{
                display: block;
                color: #1e293b;
                font-weight: 600;
                margin-bottom: 8px;
                font-size: 14px;
            }}
            textarea {{
                width: 100%;
                min-height: 120px;
                padding: 12px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                font-family: inherit;
                resize: vertical;
                transition: border-color 0.3s;
            }}
            textarea:focus {{
                outline: none;
                border-color: #667eea;
            }}
            select {{
                width: 100%;
                padding: 12px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                background: white;
                cursor: pointer;
            }}
            .task-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                margin-bottom: 20px;
            }}
            .task-btn {{
                padding: 16px;
                background: #f1f5f9;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s;
                text-align: center;
                font-weight: 600;
                color: #475569;
            }}
            .task-btn:hover {{
                background: #e2e8f0;
                border-color: #667eea;
                color: #667eea;
            }}
            .task-btn.active {{
                background: #667eea;
                border-color: #667eea;
                color: white;
            }}
            button.submit {{
                width: 100%;
                padding: 16px 24px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                background: #667eea;
                color: white;
            }}
            button.submit:hover:not(:disabled) {{
                background: #5568d3;
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }}
            button:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
            }}
            .spinner {{
                display: none;
                text-align: center;
                margin: 20px 0;
            }}
            .spinner.active {{ display: block; }}
            .spinner::after {{
                content: "";
                display: inline-block;
                width: 40px;
                height: 40px;
                border: 4px solid #f3f4f6;
                border-top-color: #667eea;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }}
            @keyframes spin {{
                to {{ transform: rotate(360deg); }}
            }}
            .results {{
                margin-top: 30px;
                background: #f8fafc;
                border-radius: 8px;
                padding: 20px;
                display: none;
            }}
            .results.active {{
                display: block;
            }}
            .result-header {{
                color: #1e293b;
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 15px;
            }}
            .result-content {{
                background: white;
                padding: 15px;
                border-radius: 6px;
                color: #475569;
                line-height: 1.6;
                white-space: pre-wrap;
            }}
            .result-meta {{
                margin-top: 10px;
                font-size: 12px;
                color: #64748b;
            }}
            .sample-buttons {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 10px;
                margin-bottom: 20px;
            }}
            .sample-btn {{
                padding: 10px;
                background: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                transition: all 0.3s;
            }}
            .sample-btn:hover {{
                background: #059669;
                transform: translateY(-1px);
            }}
            .footer {{
                background: rgba(0,0,0,0.1);
                color: white;
                text-align: center;
                padding: 20px;
                margin-top: auto;
            }}
            .footer a {{
                color: white;
                text-decoration: none;
                font-weight: 600;
                border-bottom: 2px solid rgba(255,255,255,0.3);
                transition: border-color 0.3s;
            }}
            .footer a:hover {{
                border-bottom-color: white;
            }}
            .translate-options {{
                display: none;
                margin-top: 15px;
            }}
            .translate-options.active {{
                display: block;
            }}
        </style>
    </head>
    <body>
        <div class="banner">
            <strong>OpenAI API Automation Demo</strong> — Intelligent text processing and analysis
            <div class="demo-mode">Demo mode – AI responses are simulated (add OPENAI_API_KEY env var for real API)</div>
        </div>
        
        <div class="container">
            <div class="api-status">{api_status}</div>
            
            <div class="card">
                <h1>🤖 AI Text Processing</h1>
                <p class="subtitle">Summarize, analyze sentiment, extract keywords, or translate text</p>
                
                <div class="feature-list">
                    <strong style="color: #1a202c; display: block; margin-bottom: 10px;">✨ What this demo does:</strong>
                    <ul>
                        <li><strong>Summarize:</strong> Generate concise summaries of long text</li>
                        <li><strong>Sentiment Analysis:</strong> Detect positive, negative, or neutral tone</li>
                        <li><strong>Keyword Extraction:</strong> Identify key terms and topics</li>
                        <li><strong>Translation:</strong> Translate text to multiple languages</li>
                    </ul>
                </div>
                
                <div class="sample-buttons">
                    <button class="sample-btn" onclick="loadSample('business')">📊 Business Report</button>
                    <button class="sample-btn" onclick="loadSample('review')">⭐ Product Review</button>
                    <button class="sample-btn" onclick="loadSample('article')">📰 News Article</button>
                    <button class="sample-btn" onclick="loadSample('email')">📧 Email Draft</button>
                </div>
                
                <div class="input-group">
                    <label for="textInput">Enter your text:</label>
                    <textarea id="textInput" placeholder="Paste any text here..."></textarea>
                </div>
                
                <div class="input-group">
                    <label>Choose a task:</label>
                    <div class="task-grid">
                        <div class="task-btn active" data-task="summarize" onclick="selectTask('summarize')">
                            📝 Summarize
                        </div>
                        <div class="task-btn" data-task="sentiment" onclick="selectTask('sentiment')">
                            😊 Sentiment
                        </div>
                        <div class="task-btn" data-task="keywords" onclick="selectTask('keywords')">
                            🔑 Keywords
                        </div>
                        <div class="task-btn" data-task="translate" onclick="selectTask('translate')">
                            🌐 Translate
                        </div>
                    </div>
                </div>
                
                <div id="translateOptions" class="translate-options">
                    <label for="targetLang">Target Language:</label>
                    <select id="targetLang">
                        <option value="Spanish">Spanish</option>
                        <option value="French">French</option>
                        <option value="German">German</option>
                        <option value="Japanese">Japanese</option>
                        <option value="Chinese">Chinese</option>
                        <option value="Italian">Italian</option>
                        <option value="Portuguese">Portuguese</option>
                    </select>
                </div>
                
                <button class="submit" onclick="processText()">🚀 Process Text</button>
                
                <div class="spinner" id="spinner"></div>
                
                <div class="results" id="results">
                    <div class="result-header" id="resultHeader"></div>
                    <div class="result-content" id="resultContent"></div>
                    <div class="result-meta" id="resultMeta"></div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            View source code on <a href="https://github.com/Lt-wei/ai-solutions-portfolio" target="_blank">GitHub</a>
        </div>
        
        <script>
            let currentTask = 'summarize';
            
            const samples = {{
                business: "Our Q4 results exceeded expectations with revenue reaching $15.2M, representing a 23% year-over-year increase. The successful launch of our new product line contributed significantly to this growth. Operating expenses were maintained at 45% of revenue, demonstrating strong cost control. We expanded into three new markets and hired 25 additional team members. Customer satisfaction scores improved to 4.7/5.0. Looking ahead, we're investing in R&D and planning strategic partnerships to drive innovation and market expansion.",
                review: "I absolutely love this product! The quality is outstanding and it exceeded all my expectations. The design is sleek and modern, and it's incredibly easy to use. Customer service was responsive and helpful when I had questions. It's definitely worth the price and I would highly recommend it to anyone considering a purchase. Five stars!",
                article: "Recent studies show that artificial intelligence is transforming industries at an unprecedented pace. Companies adopting AI technologies are seeing significant improvements in efficiency and decision-making capabilities. Machine learning algorithms can now process vast amounts of data in seconds, identifying patterns that humans might miss. However, experts caution about the ethical implications and the need for responsible AI development. The future of work will likely involve close collaboration between humans and AI systems.",
                email: "Hi team, I wanted to follow up on our project timeline discussion from yesterday's meeting. Based on the current progress, we should be able to complete Phase 1 by end of month. However, we'll need additional resources for Phase 2 to stay on schedule. Please review the updated project plan and let me know if you have any concerns. We'll have another checkpoint meeting next week. Thanks for your continued hard work on this initiative!"
            }};
            
            function selectTask(task) {{
                currentTask = task;
                document.querySelectorAll('.task-btn').forEach(btn => {{
                    btn.classList.remove('active');
                }});
                document.querySelector(`[data-task="${{task}}"]`).classList.add('active');
                
                // Show/hide translate options
                if (task === 'translate') {{
                    document.getElementById('translateOptions').classList.add('active');
                }} else {{
                    document.getElementById('translateOptions').classList.remove('active');
                }}
            }}
            
            function loadSample(type) {{
                document.getElementById('textInput').value = samples[type];
            }}
            
            async function processText() {{
                const text = document.getElementById('textInput').value.trim();
                
                if (!text) {{
                    alert('Please enter some text to process');
                    return;
                }}
                
                showSpinner(true);
                hideResults();
                
                const payload = {{
                    text: text,
                    task: currentTask
                }};
                
                if (currentTask === 'translate') {{
                    payload.target_language = document.getElementById('targetLang').value;
                }}
                
                try {{
                    const response = await fetch('/process', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(payload)
                    }});
                    
                    if (response.ok) {{
                        const data = await response.json();
                        displayResults(data);
                    }} else {{
                        const error = await response.json();
                        alert(`Error: ${{error.detail || 'Processing failed'}}`);
                    }}
                }} catch (error) {{
                    alert(`Error: ${{error.message}}`);
                }} finally {{
                    showSpinner(false);
                }}
            }}
            
            function displayResults(data) {{
                const resultsDiv = document.getElementById('results');
                const headerDiv = document.getElementById('resultHeader');
                const contentDiv = document.getElementById('resultContent');
                const metaDiv = document.getElementById('resultMeta');
                
                // Set header
                const taskNames = {{
                    summarize: '📝 Summary',
                    sentiment: '😊 Sentiment Analysis',
                    keywords: '🔑 Keywords',
                    translate: '🌐 Translation'
                }};
                headerDiv.textContent = taskNames[data.task] || 'Results';
                
                // Set content
                if (data.task === 'sentiment') {{
                    contentDiv.innerHTML = `
                        <div style="font-size: 20px; font-weight: 600; color: #667eea; margin-bottom: 10px;">
                            ${{data.result}}
                        </div>
                        <div>${{data.explanation || ''}}</div>
                        ${{data.confidence ? `<div style="margin-top: 10px;">Confidence: ${{(data.confidence * 100).toFixed(0)}}%</div>` : ''}}
                    `;
                }} else if (data.task === 'keywords') {{
                    contentDiv.innerHTML = `
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${{data.result.map(kw => `<span style="background: #667eea; color: white; padding: 6px 12px; border-radius: 16px; font-size: 13px;">${{kw}}</span>`).join('')}}
                        </div>
                        ${{data.categories ? `<div style="margin-top: 15px; color: #64748b;">Categories: ${{data.categories.join(', ')}}</div>` : ''}}
                    `;
                }} else {{
                    contentDiv.textContent = data.result;
                }}
                
                // Set metadata
                let metaText = data.demo_mode ? '⚠️  Demo mode (simulated response)' : `✓ Powered by ${{data.model}}`;
                if (data.word_count_original) {{
                    metaText += ` • Original: ${{data.word_count_original}} words → Summary: ${{data.word_count_summary}} words`;
                }}
                metaDiv.textContent = metaText;
                
                resultsDiv.classList.add('active');
            }}
            
            function showSpinner(show) {{
                document.getElementById('spinner').className = show ? 'spinner active' : 'spinner';
            }}
            
            function hideResults() {{
                document.getElementById('results').classList.remove('active');
            }}
            
            // Load default sample
            loadSample('business');
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "openai-api-automation",
        "api_mode": "real" if USE_REAL_API else "demo"
    }

@app.post("/process")
async def process_text(request: TextRequest):
    """Process text with the specified AI task."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        if USE_REAL_API:
            result = await call_real_openai(
                request.task,
                request.text,
                target_language=request.target_language
            )
        else:
            result = generate_demo_response(
                request.task,
                request.text,
                target_language=request.target_language
            )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

@app.post("/chat")
async def chat(request: ChatRequest):
    """Simple chat endpoint."""
    try:
        if USE_REAL_API:
            messages = []
            if request.context:
                messages.append({"role": "system", "content": request.context})
            messages.append({"role": "user", "content": request.message})
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=300
            )
            
            return {
                "response": response.choices[0].message.content,
                "model": response.model,
                "demo_mode": False
            }
        else:
            # Demo response
            template = random.choice(DEMO_RESPONSES["chat"]["responses"])
            context = random.choice(DEMO_RESPONSES["chat"]["contexts"])
            response = template.format(context=context)
            
            return {
                "response": response,
                "demo_mode": True
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    mode = "with OpenAI API" if USE_REAL_API else "in DEMO mode (no API key)"
    print(f"🚀 Starting OpenAI API Automation Demo {mode}...")
    print("🤖 Open http://localhost:8002 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8002)
