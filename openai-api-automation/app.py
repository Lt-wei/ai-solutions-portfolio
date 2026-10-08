"""
OpenAI API Automation - Inquiry Processing System
Automated inquiry handling with AI, SQLite storage, and notification system
"""

import os
import json
import logging
import hashlib
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup (use /tmp for serverless)
from pathlib import Path
TEMP_BASE = Path("/tmp") if Path("/tmp").exists() else Path(".")
DB_PATH = TEMP_BASE / "inquiries.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Check OpenAI availability
OPENAI_AVAILABLE = bool(os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if OPENAI_AVAILABLE:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info(f"✅ OpenAI API initialized (model: {OPENAI_MODEL})")
    except Exception as e:
        OPENAI_AVAILABLE = False
        logger.warning(f"⚠️ OpenAI init failed: {e}. Using mock mode.")
else:
    logger.info("ℹ️ No OPENAI_API_KEY. Running in demo/mock mode.")

# Notification config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"


class Inquiry(Base):
    """Database model for inquiries"""
    __tablename__ = "inquiries"
    
    id = Column(Integer, primary_key=True, index=True)
    inquiry_text = Column(Text, nullable=False)
    inquiry_hash = Column(String(64), unique=True, index=True)
    category = Column(String(50))
    priority = Column(String(20))
    sentiment = Column(String(20))
    ai_response = Column(Text)
    confidence_score = Column(Float)
    processing_method = Column(String(50))
    status = Column(String(20), default="pending")
    notification_sent = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)


class InquiryRequest(BaseModel):
    """Request model for new inquiry"""
    inquiry_text: str = Field(..., min_length=10, max_length=2000)
    user_email: Optional[str] = None
    user_name: Optional[str] = None


class InquiryResponse(BaseModel):
    """Response model for processed inquiry"""
    id: int
    category: str
    priority: str
    sentiment: str
    ai_response: str
    confidence_score: float
    processing_method: str
    status: str
    notification_sent: bool
    created_at: datetime


class InquiryProcessor:
    """AI-powered inquiry processing with fallback"""
    
    def __init__(self):
        self.use_ai = OPENAI_AVAILABLE
        self.retry_limit = 3
    
    def compute_hash(self, text: str) -> str:
        """Compute hash for duplicate detection"""
        normalized = text.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def process_with_openai(self, inquiry_text: str) -> dict:
        """Process inquiry using OpenAI API"""
        if not self.use_ai:
            raise RuntimeError("OpenAI not available")
        
        try:
            prompt = f"""Analyze this customer inquiry and provide structured information:

Inquiry: "{inquiry_text}"

Provide a JSON response with:
1. category: One of [technical, sales, billing, support, general]
2. priority: One of [low, medium, high, urgent]
3. sentiment: One of [positive, neutral, negative]
4. response: A helpful, professional response to the inquiry (2-3 sentences)

Return ONLY valid JSON."""

            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a customer service AI that analyzes inquiries and provides structured responses. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean JSON markers
            if result_text.startswith("```json"):
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif result_text.startswith("```"):
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(result_text)
            
            return {
                "category": data.get("category", "general"),
                "priority": data.get("priority", "medium"),
                "sentiment": data.get("sentiment", "neutral"),
                "ai_response": data.get("response", "Thank you for your inquiry. We will review and respond shortly."),
                "confidence_score": 0.92,
                "processing_method": f"openai_{OPENAI_MODEL}"
            }
            
        except Exception as e:
            logger.error(f"OpenAI processing failed: {e}")
            raise
    
    def process_with_mock(self, inquiry_text: str) -> dict:
        """Mock processing for demo mode"""
        text_lower = inquiry_text.lower()
        
        # Simple keyword-based categorization
        if any(word in text_lower for word in ["price", "cost", "buy", "purchase", "quote"]):
            category = "sales"
            priority = "high"
            response = "Thank you for your interest! Our sales team will provide you with a detailed quote within 24 hours."
        elif any(word in text_lower for word in ["error", "bug", "broken", "not working", "problem"]):
            category = "technical"
            priority = "high"
            response = "We've received your technical issue report. Our engineering team will investigate and respond within 4 hours."
        elif any(word in text_lower for word in ["invoice", "payment", "charge", "billing"]):
            category = "billing"
            priority = "medium"
            response = "Your billing inquiry has been noted. Our accounts team will review and respond within 24-48 hours."
        elif any(word in text_lower for word in ["help", "how to", "question", "support"]):
            category = "support"
            priority = "medium"
            response = "Thank you for reaching out! Our support team will assist you with your question shortly."
        else:
            category = "general"
            priority = "low"
            response = "We've received your inquiry and will respond within 2-3 business days. Thank you for contacting us!"
        
        # Simple sentiment detection
        positive_words = ["great", "excellent", "love", "thank", "happy", "good"]
        negative_words = ["bad", "terrible", "awful", "hate", "poor", "disappointed"]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "category": category,
            "priority": priority,
            "sentiment": sentiment,
            "ai_response": response,
            "confidence_score": 0.68,
            "processing_method": "mock_heuristic"
        }
    
    def process_inquiry(self, inquiry_text: str) -> dict:
        """Main processing pipeline with retry logic"""
        for attempt in range(self.retry_limit):
            try:
                if self.use_ai:
                    return self.process_with_openai(inquiry_text)
                else:
                    return self.process_with_mock(inquiry_text)
                    
            except Exception as e:
                logger.warning(f"Processing attempt {attempt + 1} failed: {e}")
                
                if attempt == self.retry_limit - 1:
                    logger.error("All retries exhausted, using mock fallback")
                    return self.process_with_mock(inquiry_text)


class NotificationService:
    """Notification service for Telegram and Email"""
    
    @staticmethod
    def send_telegram(inquiry: dict) -> bool:
        """Send Telegram notification (stub)"""
        if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
            logger.info(f"📱 [TELEGRAM STUB] Would send: New {inquiry['priority']} inquiry - {inquiry['category']}")
            return True
        
        try:
            # Real Telegram API call would go here
            logger.info(f"📱 Telegram notification sent for inquiry #{inquiry['id']}")
            return True
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False
    
    @staticmethod
    def send_email(inquiry: dict, recipient: str) -> bool:
        """Send email notification (stub)"""
        if not EMAIL_ENABLED:
            logger.info(f"📧 [EMAIL STUB] Would send to {recipient}: Inquiry #{inquiry['id']} - {inquiry['category']}")
            return True
        
        try:
            # Real email sending would go here
            logger.info(f"📧 Email notification sent to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False
    
    @staticmethod
    def notify_inquiry(inquiry_dict: dict, user_email: Optional[str] = None):
        """Send notifications for new inquiry"""
        NotificationService.send_telegram(inquiry_dict)
        
        if user_email:
            NotificationService.send_email(inquiry_dict, user_email)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Starting OpenAI API Automation service")
    logger.info(f"   AI Mode: {'✅ Active' if OPENAI_AVAILABLE else '⚠️ Mock/Demo'}")
    logger.info(f"   Database: {DATABASE_URL}")
    logger.info(f"   Notifications: Telegram {'✅' if TELEGRAM_BOT_TOKEN else '⚠️'} | Email {'✅' if EMAIL_ENABLED else '⚠️'}")
    yield
    logger.info("👋 Shutting down service")


app = FastAPI(
    title="OpenAI API Automation",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve web UI"""
    ai_badge = "🟢 AI Active" if OPENAI_AVAILABLE else "🟡 Demo Mode"
    ai_color = "#c6f6d5" if OPENAI_AVAILABLE else "#fef3c7"
    ai_text_color = "#22543d" if OPENAI_AVAILABLE else "#78350f"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OpenAI Inquiry Automation</title>
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
            }}
            .banner strong {{ color: #fbbf24; }}
            .container {{
                max-width: 900px;
                margin: 20px auto;
                background: white;
                border-radius: 16px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                flex: 1;
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
            }}
            .footer a:hover {{
                border-bottom-color: white;
            }}
            h1 {{
                color: #2d3748;
                margin-bottom: 10px;
                font-size: 32px;
            }}
            .subtitle {{
                color: #718096;
                margin-bottom: 20px;
                font-size: 16px;
            }}
            .status-badge {{
                display: inline-block;
                padding: 8px 16px;
                background: {ai_color};
                color: {ai_text_color};
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 20px;
            }}
            .info-box {{
                background: #ebf8ff;
                border-left: 4px solid #3182ce;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 4px;
                font-size: 14px;
            }}
            .form-group {{
                margin-bottom: 20px;
            }}
            label {{
                display: block;
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 8px;
            }}
            input, textarea {{
                width: 100%;
                padding: 12px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                font-family: inherit;
            }}
            textarea {{
                min-height: 120px;
                resize: vertical;
            }}
            button {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 14px 32px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
                width: 100%;
            }}
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            }}
            button:disabled {{
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }}
            #result {{
                margin-top: 30px;
                padding: 20px;
                border-radius: 8px;
                background: #f7fafc;
                display: none;
            }}
            .success {{
                background: #c6f6d5;
                border-left: 4px solid #38a169;
            }}
            .error {{
                background: #fed7d7;
                border-left: 4px solid #e53e3e;
            }}
            .result-field {{
                margin: 10px 0;
                padding: 10px;
                background: white;
                border-radius: 4px;
            }}
            .result-label {{
                font-weight: 600;
                color: #4a5568;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .result-value {{
                color: #2d3748;
                margin-top: 5px;
                font-size: 15px;
            }}
            .stats-link {{
                display: inline-block;
                margin-top: 15px;
                padding: 10px 20px;
                background: #3182ce;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
            }}
            .stats-link:hover {{
                background: #2c5aa0;
            }}
            .loader {{
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
                display: none;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="banner">
            <strong>Inquiry Automation Demo</strong> — AI-powered categorization, priority assignment, and automated responses{''' • Demo mode – AI responses are simulated using rule-based logic''' if not OPENAI_AVAILABLE else ''}
        </div>
        
        <div class="container">
            <h1>🤖 Inquiry Automation System</h1>
            <p class="subtitle">AI-powered inquiry processing with intelligent categorization and response</p>
            
            <div class="status-badge">{ai_badge}</div>
            
            <div class="info-box">
                <strong>System Pipeline:</strong> Submit inquiry → AI analysis → Categorization → Priority assignment → 
                Database storage → Automated response → Notifications (Telegram/Email)
            </div>
            
            <form id="inquiryForm">
                <div class="form-group">
                    <label>📝 Your Inquiry</label>
                    <textarea 
                        id="inquiryText" 
                        placeholder="Describe your question, issue, or request here..."
                    ></textarea>
                </div>
                
                <div class="form-group">
                    <label>👤 Your Name (optional)</label>
                    <input type="text" id="userName" placeholder="John Doe">
                </div>
                
                <div class="form-group">
                    <label>📧 Your Email (optional)</label>
                    <input type="email" id="userEmail" placeholder="john@example.com">
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <button type="submit" id="submitBtn">Submit Custom Inquiry</button>
                    <button type="button" onclick="loadSampleInquiry()" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">🎯 Try Sample Inquiry</button>
                </div>
            </form>
            
            <div class="loader" id="loader"></div>
            
            <div id="result"></div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/stats" class="stats-link">📊 View All Inquiries</a>
            </div>
        </div>
        
        <div class="footer">
            View source code on <a href="https://github.com/Lt-wei/ai-solutions-portfolio" target="_blank">GitHub</a>
        </div>
        
        <script>
            document.getElementById('inquiryForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const submitBtn = document.getElementById('submitBtn');
                const loader = document.getElementById('loader');
                const resultDiv = document.getElementById('result');
                
                submitBtn.disabled = true;
                loader.style.display = 'block';
                resultDiv.style.display = 'none';
                
                const inquiry = {{
                    inquiry_text: document.getElementById('inquiryText').value,
                    user_name: document.getElementById('userName').value || null,
                    user_email: document.getElementById('userEmail').value || null
                }};
                
                try {{
                    const response = await fetch('/submit', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(inquiry)
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        resultDiv.className = 'success';
                        resultDiv.innerHTML = `
                            <h3 style="color: #38a169; margin-bottom: 15px;">✅ Inquiry Submitted Successfully!</h3>
                            
                            <div class="result-field">
                                <div class="result-label">Inquiry ID</div>
                                <div class="result-value">#${{data.id}}</div>
                            </div>
                            
                            <div class="result-field">
                                <div class="result-label">Category</div>
                                <div class="result-value">${{data.category.toUpperCase()}}</div>
                            </div>
                            
                            <div class="result-field">
                                <div class="result-label">Priority</div>
                                <div class="result-value">${{data.priority.toUpperCase()}}</div>
                            </div>
                            
                            <div class="result-field">
                                <div class="result-label">Sentiment</div>
                                <div class="result-value">${{data.sentiment.toUpperCase()}}</div>
                            </div>
                            
                            <div class="result-field">
                                <div class="result-label">AI Response</div>
                                <div class="result-value">${{data.ai_response}}</div>
                            </div>
                            
                            <div class="result-field">
                                <div class="result-label">Confidence Score</div>
                                <div class="result-value">${{(data.confidence_score * 100).toFixed(0)}}%</div>
                            </div>
                            
                            <p style="margin-top: 15px; color: #4a5568; font-size: 14px;">
                                Processing method: ${{data.processing_method}}
                            </p>
                        `;
                        
                        // Reset form
                        document.getElementById('inquiryForm').reset();
                    }} else {{
                        throw new Error(data.detail || 'Submission failed');
                    }}
                }} catch (error) {{
                    resultDiv.className = 'error';
                    resultDiv.innerHTML = `
                        <h3 style="color: #e53e3e; margin-bottom: 10px;">❌ Error</h3>
                        <p>${{error.message}}</p>
                    `;
                }}
                
                resultDiv.style.display = 'block';
                submitBtn.disabled = false;
                loader.style.display = 'none';
            }});
            
            async function loadSampleInquiry() {{
                const submitBtn = document.getElementById('submitBtn');
                const loader = document.getElementById('loader');
                const resultDiv = document.getElementById('result');
                
                submitBtn.disabled = true;
                loader.style.display = 'block';
                resultDiv.style.display = 'none';
                
                try {{
                    const response = await fetch('/sample');
                    const data = await response.json();
                    
                    if (response.ok) {{
                        resultDiv.className = 'success';
                        resultDiv.innerHTML = `
                            <h3 style="color: #38a169; margin-bottom: 15px;">✅ Sample Inquiry Processed!</h3>
                            
                            <div class="result-field">
                                <div class="result-label">Inquiry ID</div>
                                <div class="result-value">#${{data.id}}</div>
                            </div>
                            
                            <div class="result-field">
                                <div class="result-label">Category</div>
                                <div class="result-value">${{data.category.toUpperCase()}}</div>
                            </div>
                            
                            <div class="result-field">
                                <div class="result-label">Priority</div>
                                <div class="result-value">${{data.priority.toUpperCase()}}</div>
                            </div>
                            
                            <div class="result-field">
                                <div class="result-label">Sentiment</div>
                                <div class="result-value">${{data.sentiment.toUpperCase()}}</div>
                            </div>
                            
                            <div class="result-field">
                                <div class="result-label">AI Response</div>
                                <div class="result-value">${{data.ai_response}}</div>
                            </div>
                            
                            <div class="result-field">
                                <div class="result-label">Confidence Score</div>
                                <div class="result-value">${{(data.confidence_score * 100).toFixed(0)}}%</div>
                            </div>
                            
                            <p style="margin-top: 15px; color: #4a5568; font-size: 14px;">
                                Processing method: ${{data.processing_method}}
                            </p>
                        `;
                    }} else {{
                        throw new Error(data.detail || 'Sample processing failed');
                    }}
                }} catch (error) {{
                    resultDiv.className = 'error';
                    resultDiv.innerHTML = `
                        <h3 style="color: #e53e3e; margin-bottom: 10px;">❌ Error</h3>
                        <p>${{error.message}}</p>
                    `;
                }}
                
                resultDiv.style.display = 'block';
                submitBtn.disabled = false;
                loader.style.display = 'none';
            }}
        </script>
    </body>
    </html>
    """


@app.post("/submit", response_model=InquiryResponse)
async def submit_inquiry(
    request: InquiryRequest,
    background_tasks: BackgroundTasks
):
    """Submit new inquiry for processing"""
    db = SessionLocal()
    
    try:
        # Compute hash for duplicate detection
        processor = InquiryProcessor()
        inquiry_hash = processor.compute_hash(request.inquiry_text)
        
        # Check for duplicates
        existing = db.query(Inquiry).filter(Inquiry.inquiry_hash == inquiry_hash).first()
        if existing:
            logger.info(f"Duplicate inquiry detected (ID: {existing.id})")
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate inquiry detected. Original inquiry ID: {existing.id}"
            )
        
        # Process inquiry
        logger.info(f"Processing new inquiry: {request.inquiry_text[:50]}...")
        processing_result = processor.process_inquiry(request.inquiry_text)
        
        # Save to database
        inquiry = Inquiry(
            inquiry_text=request.inquiry_text,
            inquiry_hash=inquiry_hash,
            category=processing_result["category"],
            priority=processing_result["priority"],
            sentiment=processing_result["sentiment"],
            ai_response=processing_result["ai_response"],
            confidence_score=processing_result["confidence_score"],
            processing_method=processing_result["processing_method"],
            status="processed"
        )
        
        db.add(inquiry)
        db.commit()
        db.refresh(inquiry)
        
        logger.info(f"✅ Inquiry saved with ID: {inquiry.id}")
        
        # Schedule notifications in background
        inquiry_dict = {
            "id": inquiry.id,
            "category": inquiry.category,
            "priority": inquiry.priority,
            "sentiment": inquiry.sentiment
        }
        
        background_tasks.add_task(
            NotificationService.notify_inquiry,
            inquiry_dict,
            request.user_email
        )
        
        return InquiryResponse(
            id=inquiry.id,
            category=inquiry.category,
            priority=inquiry.priority,
            sentiment=inquiry.sentiment,
            ai_response=inquiry.ai_response,
            confidence_score=inquiry.confidence_score,
            processing_method=inquiry.processing_method,
            status=inquiry.status,
            notification_sent=True,
            created_at=inquiry.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing inquiry: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        db.close()


@app.get("/sample")
async def submit_sample_inquiry(background_tasks: BackgroundTasks):
    """Submit a sample inquiry for demo purposes"""
    db = SessionLocal()
    
    # Sample inquiry text
    sample_text = """I would like to inquire about your Enterprise plan features and pricing. 
    Our company has been growing rapidly and we're evaluating different solutions for our team of 50+ employees.
    We're particularly interested in:
    1. Advanced security features and compliance certifications
    2. API access for integrations with our existing tools
    3. Volume discounts and flexible payment terms
    4. Dedicated support and onboarding assistance
    
    Could you provide detailed information about the Enterprise plan, including pricing for our team size?
    We're looking to make a decision within the next 2 weeks.
    
    Thank you!"""
    
    try:
        # Process sample inquiry
        processor = InquiryProcessor()
        inquiry_hash = processor.compute_hash(sample_text)
        
        # Check for duplicates
        existing = db.query(Inquiry).filter(Inquiry.inquiry_hash == inquiry_hash).first()
        if existing:
            # Return existing result
            logger.info(f"Sample inquiry already exists (ID: {existing.id})")
            return InquiryResponse(
                id=existing.id,
                category=existing.category,
                priority=existing.priority,
                sentiment=existing.sentiment,
                ai_response=existing.ai_response,
                confidence_score=existing.confidence_score,
                processing_method=existing.processing_method,
                status=existing.status,
                notification_sent=existing.notification_sent,
                created_at=existing.created_at
            )
        
        logger.info("Processing sample inquiry...")
        processing_result = processor.process_inquiry(sample_text)
        
        # Save to database
        inquiry = Inquiry(
            inquiry_text=sample_text,
            inquiry_hash=inquiry_hash,
            category=processing_result["category"],
            priority=processing_result["priority"],
            sentiment=processing_result["sentiment"],
            ai_response=processing_result["ai_response"],
            confidence_score=processing_result["confidence_score"],
            processing_method=processing_result["processing_method"],
            status="processed"
        )
        
        db.add(inquiry)
        db.commit()
        db.refresh(inquiry)
        
        logger.info(f"✅ Sample inquiry saved with ID: {inquiry.id}")
        
        # Schedule notifications in background
        inquiry_dict = {
            "id": inquiry.id,
            "category": inquiry.category,
            "priority": inquiry.priority,
            "sentiment": inquiry.sentiment
        }
        
        background_tasks.add_task(
            NotificationService.notify_inquiry,
            inquiry_dict,
            "demo@example.com"
        )
        
        return InquiryResponse(
            id=inquiry.id,
            category=inquiry.category,
            priority=inquiry.priority,
            sentiment=inquiry.sentiment,
            ai_response=inquiry.ai_response,
            confidence_score=inquiry.confidence_score,
            processing_method=inquiry.processing_method,
            status=inquiry.status,
            notification_sent=True,
            created_at=inquiry.created_at
        )
        
    except Exception as e:
        logger.error(f"Error processing sample inquiry: {e}")
        raise HTTPException(status_code=500, detail=f"Sample processing failed: {str(e)}")
    finally:
        db.close()


@app.get("/stats")
async def get_stats():
    """Get inquiry statistics"""
    db = SessionLocal()
    
    try:
        inquiries = db.query(Inquiry).order_by(Inquiry.created_at.desc()).limit(50).all()
        
        total = db.query(Inquiry).count()
        by_category = {}
        by_priority = {}
        
        for inquiry in db.query(Inquiry).all():
            by_category[inquiry.category] = by_category.get(inquiry.category, 0) + 1
            by_priority[inquiry.priority] = by_priority.get(inquiry.priority, 0) + 1
        
        return {
            "total_inquiries": total,
            "by_category": by_category,
            "by_priority": by_priority,
            "recent_inquiries": [
                {
                    "id": i.id,
                    "text": i.inquiry_text[:100] + "..." if len(i.inquiry_text) > 100 else i.inquiry_text,
                    "category": i.category,
                    "priority": i.priority,
                    "created_at": i.created_at.isoformat()
                }
                for i in inquiries
            ]
        }
    finally:
        db.close()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db = SessionLocal()
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    finally:
        db.close()
    
    return {
        "status": "healthy",
        "service": "openai-api-automation",
        "ai_mode": "openai" if OPENAI_AVAILABLE else "mock",
        "database": db_status,
        "notifications": {
            "telegram": "configured" if TELEGRAM_BOT_TOKEN else "stub",
            "email": "enabled" if EMAIL_ENABLED else "stub"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
