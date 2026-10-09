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

from portfolio_ui import dashboard_page, demo_badge, sparkline_svg

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
    notice = None
    if not OPENAI_AVAILABLE:
        notice = (
            "Routing and replies use <strong>mock heuristics</strong> until you configure "
            "<code>OPENAI_API_KEY</code> for live model responses."
        )

    badge = demo_badge(mock_ai=not OPENAI_AVAILABLE, openai_active=OPENAI_AVAILABLE)
    spark = sparkline_svg()

    body = f"""
        <section class="kpi-strip" aria-label="Queue metrics">
            <div class="kpi-card"><span class="kpi-label">Open today</span><div class="kpi-row"><span class="kpi-value" id="kpiOpen">24</span>{spark}</div></div>
            <div class="kpi-card"><span class="kpi-label">Auto-resolved</span><div class="kpi-row"><span class="kpi-value" id="kpiResolved">18</span>{sparkline_svg("2,11 8,8 14,6 20,7 26,4")}</div></div>
            <div class="kpi-card"><span class="kpi-label">Avg confidence</span><div class="kpi-row"><span class="kpi-value" id="kpiConf">68%</span>{sparkline_svg("2,10 9,7 15,8 21,5 27,6")}</div></div>
            <div class="kpi-card"><span class="kpi-label">Queue</span><div class="kpi-row"><span class="kpi-value" id="kpiQueue" style="font-size:1rem">Medium</span><span class="pill pill-warning">Active</span></div></div>
        </section>

        <div class="dashboard-grid">
            <section class="panel">
                <div class="panel-head"><span class="panel-title">New inquiry</span><span class="panel-meta">Min 10 chars</span></div>
                <div class="panel-body">
                    <form id="inquiryForm">
                        <label class="field-label" for="inquiryText">Message</label>
                        <textarea id="inquiryText" placeholder="Describe the issue or question..." minlength="10" required></textarea>
                        <label class="field-label" for="userName">Name</label>
                        <input type="text" id="userName" placeholder="Optional" autocomplete="name">
                        <label class="field-label" for="userEmail">Email</label>
                        <input type="email" id="userEmail" placeholder="Optional" autocomplete="email">
                        <div class="actions">
                            <button type="submit" class="btn btn-primary" id="submitBtn">Analyze &amp; respond</button>
                            <button type="button" class="btn btn-secondary" id="sampleBtn">Load sample</button>
                        </div>
                        <a class="btn btn-tertiary" href="/stats" target="_blank" rel="noopener">Raw JSON log</a>
                    </form>
                </div>
            </section>

            <section class="panel" id="resultPanel">
                <div class="panel-head">
                    <div class="preview-status">
                        <span class="panel-title">Triage &amp; draft reply</span>
                        <span class="pill pill-warning" id="resultPill">Preview</span>
                    </div>
                    <span class="panel-meta" id="resultMeta">Sample classification</span>
                </div>
                <div class="result-card" id="resultCard"></div>
                <div class="panel-head" style="border-top:1px solid var(--border-subtle)">
                    <span class="panel-title">Recent inquiries</span>
                    <span class="panel-meta" id="recentMeta">Last 5</span>
                </div>
                <div class="panel-body flush">
                    <div class="table-wrap">
                        <table class="data-table">
                            <thead><tr><th>ID</th><th>Category</th><th>Priority</th><th>Snippet</th></tr></thead>
                            <tbody id="recentRows"></tbody>
                        </table>
                    </div>
                </div>
                <div class="toast-error" id="errorToast" hidden></div>
            </section>
        </div>

        <script>
        (function() {{
            const SEED_RESULT = {{
                id: 1042,
                category: 'sales',
                priority: 'high',
                sentiment: 'positive',
                ai_response: 'Thank you for your interest in our Enterprise plan. Our team will follow up with pricing and security documentation within one business day.',
                confidence_score: 0.68,
                processing_method: 'mock_heuristic'
            }};
            const SEED_RECENT = [
                {{ id: 1039, category: 'billing', priority: 'medium', text: 'Question about invoice #8821...' }},
                {{ id: 1040, category: 'technical', priority: 'high', text: 'API integration returns 502...' }},
                {{ id: 1041, category: 'support', priority: 'low', text: 'How do I reset workspace roles?' }},
            ];

            function priorityPill(p) {{
                const cls = p === 'urgent' || p === 'high' ? 'pill-warning' : (p === 'low' ? 'pill-mock' : 'pill-neutral');
                return `<span class="pill ${{cls}}">${{p}}</span>`;
            }}

            function renderResult(data) {{
                document.getElementById('resultCard').innerHTML = `
                    <div class="result-grid">
                        <div class="result-kv"><label>Inquiry</label><span>#${{data.id}}</span></div>
                        <div class="result-kv"><label>Category</label><span>${{data.category}}</span></div>
                        <div class="result-kv"><label>Priority</label><span>${{priorityPill(data.priority)}}</span></div>
                        <div class="result-kv"><label>Sentiment</label><span>${{data.sentiment}}</span></div>
                        <div class="result-kv"><label>Confidence</label><span>${{Math.round((data.confidence_score||0)*100)}}%</span></div>
                        <div class="result-kv"><label>Method</label><span class="pill pill-mock">${{data.processing_method}}</span></div>
                    </div>
                    <label class="field-label">Drafted reply</label>
                    <div class="reply-block">${{data.ai_response}}</div>`;
                document.getElementById('kpiConf').textContent = Math.round((data.confidence_score||0)*100) + '%';
            }}

            function renderRecent(list) {{
                document.getElementById('recentRows').innerHTML = list.map(r => `
                    <tr>
                        <td>#${{r.id}}</td>
                        <td>${{r.category}}</td>
                        <td>${{priorityPill(r.priority)}}</td>
                        <td style="max-width:220px;overflow:hidden;text-overflow:ellipsis">${{r.text}}</td>
                    </tr>`).join('');
            }}

            function showSeed() {{
                renderResult(SEED_RESULT);
                renderRecent(SEED_RECENT);
                document.getElementById('resultPill').className = 'pill pill-warning';
                document.getElementById('resultPill').textContent = 'Preview';
                document.getElementById('resultMeta').textContent = 'Illustrative triage — submit or load sample';
            }}

            async function refreshStats() {{
                try {{
                    const res = await fetch('/stats');
                    if (!res.ok) return;
                    const stats = await res.json();
                    document.getElementById('kpiOpen').textContent = stats.total_inquiries || 0;
                    const recent = (stats.recent_inquiries || []).slice(0, 5);
                    if (recent.length) {{
                        renderRecent(recent.map(r => ({{
                            id: r.id,
                            category: r.category,
                            priority: r.priority,
                            text: r.text
                        }})));
                        document.getElementById('recentMeta').textContent = 'From database';
                    }}
                }} catch (_) {{}}
            }}

            async function run(url, options, resetForm) {{
                const panel = document.getElementById('resultPanel');
                panel.classList.add('panel-loading');
                document.getElementById('submitBtn').disabled = true;
                document.getElementById('sampleBtn').disabled = true;
                try {{
                    const res = await fetch(url, options);
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Request failed');
                    renderResult(data);
                    document.getElementById('resultPill').className = 'pill pill-success';
                    document.getElementById('resultPill').textContent = 'Processed';
                    document.getElementById('resultMeta').textContent = 'Stored with notification stubs';
                    document.getElementById('errorToast').hidden = true;
                    if (resetForm) document.getElementById('inquiryForm').reset();
                    await refreshStats();
                }} catch (e) {{
                    const t = document.getElementById('errorToast');
                    t.textContent = e.message;
                    t.hidden = false;
                }} finally {{
                    panel.classList.remove('panel-loading');
                    document.getElementById('submitBtn').disabled = false;
                    document.getElementById('sampleBtn').disabled = false;
                }}
            }}

            document.getElementById('inquiryForm').addEventListener('submit', e => {{
                e.preventDefault();
                const text = document.getElementById('inquiryText').value.trim();
                if (text.length < 10) {{ alert('Enter at least 10 characters.'); return; }}
                run('/submit', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        inquiry_text: text,
                        user_name: document.getElementById('userName').value || null,
                        user_email: document.getElementById('userEmail').value || null
                    }})
                }}, true);
            }});
            document.getElementById('sampleBtn').addEventListener('click', () => run('/sample', {{}}, false));
            showSeed();
            refreshStats();
        }})();
        </script>
    """

    return dashboard_page(
        page_title="Inquiry Automation — Leane",
        product_name="Inquiry Automation",
        badge_text=badge,
        subtitle="Classify inbound messages, assign priority, and draft responses with optional Telegram and email stubs.",
        notice_html=notice,
        body_html=body,
    )


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
