from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import PyPDF2
import re
import json
import os
import tempfile
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path

app = FastAPI(title="PDF Document AI Demo")

# Constants for serverless
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
TEMP_DIR = "/tmp" if os.path.exists("/tmp") else tempfile.gettempdir()

class AnalysisResult(BaseModel):
    filename: str
    pages: int
    text_length: int
    emails: List[str]
    phone_numbers: List[str]
    dates: List[str]
    currency_amounts: List[str]
    urls: List[str]
    key_sections: Dict[str, str]
    word_count: int
    extracted_text: Optional[str] = None

def get_sample_pdf_path():
    """Return path to sample PDF."""
    return os.path.join(os.path.dirname(__file__), "sample-invoice.pdf")

def create_sample_pdf():
    """Create a sample invoice PDF for demo purposes."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch
    
    sample_path = os.path.join(TEMP_DIR, "sample-invoice.pdf")
    
    if os.path.exists(sample_path):
        return sample_path
    
    doc = SimpleDocTemplate(sample_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Invoice header
    elements.append(Paragraph("<b>INVOICE</b>", styles['Title']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Company info
    company_info = """
    <b>TechCorp Solutions Inc.</b><br/>
    123 Business Street, Suite 100<br/>
    San Francisco, CA 94105<br/>
    Phone: +1 (555) 123-4567<br/>
    Email: billing@techcorp.example.com<br/>
    Website: https://www.techcorp.example.com
    """
    elements.append(Paragraph(company_info, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Invoice details
    invoice_details = """
    <b>Invoice Number:</b> INV-2024-001234<br/>
    <b>Invoice Date:</b> January 15, 2024<br/>
    <b>Due Date:</b> February 15, 2024<br/>
    <b>Customer ID:</b> CUST-5678
    """
    elements.append(Paragraph(invoice_details, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Bill to
    elements.append(Paragraph("<b>Bill To:</b>", styles['Heading2']))
    bill_to = """
    Acme Corporation<br/>
    456 Client Avenue<br/>
    New York, NY 10001<br/>
    Contact: john.doe@acme.example.com<br/>
    Phone: +1 (555) 987-6543
    """
    elements.append(Paragraph(bill_to, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Items table
    data = [
        ['Item', 'Description', 'Qty', 'Unit Price', 'Amount'],
        ['Software License', 'Annual Enterprise License', '1', '$12,500.00', '$12,500.00'],
        ['Support Package', 'Premium Support (12 months)', '1', '$3,000.00', '$3,000.00'],
        ['Training', 'On-site Team Training', '2', '$1,500.00', '$3,000.00'],
        ['', '', '', 'Subtotal:', '$18,500.00'],
        ['', '', '', 'Tax (8.5%):', '$1,572.50'],
        ['', '', '', '<b>Total:</b>', '<b>$20,072.50</b>'],
    ]
    
    table = Table(data, colWidths=[1.5*inch, 2.5*inch, 0.75*inch, 1.25*inch, 1.25*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -4), 1, colors.black),
        ('FONTNAME', (3, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Payment terms
    payment_terms = """
    <b>Payment Terms:</b> Net 30 days<br/>
    <b>Payment Methods:</b> Wire transfer, ACH, Check<br/>
    <b>Bank Details:</b> First National Bank, Account: 1234567890, Routing: 987654321
    """
    elements.append(Paragraph(payment_terms, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer = """
    <i>Thank you for your business!</i><br/>
    For questions about this invoice, contact: accounts@techcorp.example.com
    """
    elements.append(Paragraph(footer, styles['Normal']))
    
    doc.build(elements)
    return sample_path

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file."""
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def analyze_document(text: str, filename: str = "document.pdf") -> AnalysisResult:
    """Analyze document using regex patterns (demo mode - no AI)."""
    
    # Extract emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = list(set(re.findall(email_pattern, text)))
    
    # Extract phone numbers
    phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phone_numbers = list(set(re.findall(phone_pattern, text)))
    
    # Extract dates
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b'
    ]
    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, text, re.IGNORECASE))
    dates = list(set(dates))
    
    # Extract currency amounts
    currency_pattern = r'\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
    currency_amounts = list(set(re.findall(currency_pattern, text)))
    
    # Extract URLs
    url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
    urls = list(set(re.findall(url_pattern, text)))
    
    # Extract key sections (simple keyword-based)
    sections = {}
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['invoice', 'bill', 'receipt']):
            sections['Document Type'] = line.strip()
        elif 'total' in line_lower and any(char.isdigit() for char in line):
            sections['Total Amount'] = line.strip()
        elif any(keyword in line_lower for keyword in ['company', 'from:', 'sender']):
            sections['Company'] = line.strip()
        elif 'date' in line_lower and any(char.isdigit() for char in line):
            sections['Date Information'] = line.strip()
    
    # Word count
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)
    
    # Count pages (approximate from text)
    pages = max(1, text.count('\f') + 1)
    
    return AnalysisResult(
        filename=filename,
        pages=pages,
        text_length=len(text),
        emails=emails[:10],  # Limit results
        phone_numbers=phone_numbers[:10],
        dates=dates[:10],
        currency_amounts=currency_amounts[:10],
        urls=urls[:10],
        key_sections=sections,
        word_count=word_count,
        extracted_text=text[:1000] + "..." if len(text) > 1000 else text
    )

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF Document AI Demo</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }
            .banner {
                background: #1a202c;
                color: white;
                padding: 12px 20px;
                text-align: center;
                font-size: 14px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            }
            .banner strong { color: #fbbf24; }
            .demo-mode {
                background: #059669;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                display: inline-block;
                margin-top: 5px;
            }
            .container {
                flex: 1;
                max-width: 900px;
                margin: 40px auto;
                padding: 20px;
            }
            .card {
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 40px;
            }
            h1 {
                color: #1a202c;
                font-size: 32px;
                margin-bottom: 10px;
                text-align: center;
            }
            .subtitle {
                color: #64748b;
                text-align: center;
                margin-bottom: 30px;
                font-size: 16px;
            }
            .feature-list {
                background: #f8fafc;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 30px;
            }
            .feature-list ul {
                list-style: none;
                padding-left: 0;
            }
            .feature-list li {
                padding: 8px 0;
                color: #475569;
            }
            .feature-list li:before {
                content: "✓ ";
                color: #10b981;
                font-weight: bold;
                margin-right: 8px;
            }
            .file-input-wrapper {
                position: relative;
                overflow: hidden;
                display: inline-block;
                width: 100%;
                margin-bottom: 15px;
            }
            .file-input-wrapper input[type=file] {
                position: absolute;
                left: -9999px;
            }
            .file-input-label {
                display: block;
                padding: 20px;
                background: #f1f5f9;
                border: 2px dashed #cbd5e1;
                border-radius: 8px;
                cursor: pointer;
                text-align: center;
                transition: all 0.3s;
                color: #475569;
            }
            .file-input-label:hover {
                background: #e2e8f0;
                border-color: #667eea;
            }
            .file-name {
                margin-top: 10px;
                color: #10b981;
                font-size: 14px;
                text-align: center;
                min-height: 20px;
            }
            .button-group {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            button {
                flex: 1;
                padding: 16px 24px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
            }
            .btn-primary {
                background: #667eea;
                color: white;
            }
            .btn-primary:hover:not(:disabled) {
                background: #5568d3;
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            .btn-secondary {
                background: #10b981;
                color: white;
            }
            .btn-secondary:hover:not(:disabled) {
                background: #059669;
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(16, 185, 129, 0.3);
            }
            button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            .spinner {
                display: none;
                text-align: center;
                margin: 20px 0;
            }
            .spinner.active { display: block; }
            .spinner::after {
                content: "";
                display: inline-block;
                width: 40px;
                height: 40px;
                border: 4px solid #f3f4f6;
                border-top-color: #667eea;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .results {
                margin-top: 30px;
                display: none;
            }
            .results.active {
                display: block;
            }
            .result-section {
                background: #f8fafc;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 15px;
            }
            .result-section h3 {
                color: #1e293b;
                font-size: 18px;
                margin-bottom: 10px;
            }
            .result-item {
                background: white;
                padding: 8px 12px;
                margin: 5px 0;
                border-radius: 4px;
                font-size: 14px;
                color: #475569;
            }
            .stat-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            .stat-card {
                background: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }
            .stat-value {
                font-size: 28px;
                font-weight: bold;
                color: #667eea;
            }
            .stat-label {
                font-size: 12px;
                color: #64748b;
                margin-top: 5px;
            }
            .footer {
                background: rgba(0,0,0,0.1);
                color: white;
                text-align: center;
                padding: 20px;
                margin-top: auto;
            }
            .footer a {
                color: white;
                text-decoration: none;
                font-weight: 600;
                border-bottom: 2px solid rgba(255,255,255,0.3);
                transition: border-color 0.3s;
            }
            .footer a:hover {
                border-bottom-color: white;
            }
            .max-size {
                font-size: 12px;
                color: #64748b;
                text-align: center;
                margin-top: 5px;
            }
            code {
                background: #1e293b;
                color: #10b981;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 13px;
            }
        </style>
    </head>
    <body>
        <div class="banner">
            <strong>PDF Document AI Demo</strong> — Extract and analyze data from PDF documents
            <div class="demo-mode">Demo mode – AI responses are simulated using regex patterns</div>
        </div>
        
        <div class="container">
            <div class="card">
                <h1>📄 PDF Document Analyzer</h1>
                <p class="subtitle">Upload a PDF or try with a sample invoice</p>
                
                <div class="feature-list">
                    <strong style="color: #1a202c; display: block; margin-bottom: 10px;">✨ What this demo extracts:</strong>
                    <ul>
                        <li>Email addresses and phone numbers</li>
                        <li>Dates in multiple formats</li>
                        <li>Currency amounts and financial data</li>
                        <li>URLs and web addresses</li>
                        <li>Key document sections and metadata</li>
                        <li>Full text extraction with word count</li>
                    </ul>
                </div>
                
                <div class="upload-section">
                    <div class="file-input-wrapper">
                        <input type="file" id="fileInput" accept=".pdf" onchange="handleFileSelect(event)">
                        <label for="fileInput" class="file-input-label">
                            📁 Click to upload PDF file<br>
                            <small>or drag and drop here</small>
                        </label>
                    </div>
                    <div class="file-name" id="fileName"></div>
                    <div class="max-size">Maximum file size: 10MB</div>
                </div>
                
                <div class="button-group">
                    <button class="btn-primary" id="uploadBtn" onclick="processUpload()" disabled>
                        Analyze Uploaded PDF
                    </button>
                    <button class="btn-secondary" onclick="processSample()">
                        🎯 Try with Sample Invoice
                    </button>
                </div>
                
                <div class="spinner" id="spinner"></div>
                
                <div class="results" id="results">
                    <div class="result-section">
                        <h3>📊 Document Statistics</h3>
                        <div class="stat-grid" id="stats"></div>
                    </div>
                    
                    <div class="result-section" id="emailSection" style="display:none;">
                        <h3>📧 Email Addresses</h3>
                        <div id="emails"></div>
                    </div>
                    
                    <div class="result-section" id="phoneSection" style="display:none;">
                        <h3>📞 Phone Numbers</h3>
                        <div id="phones"></div>
                    </div>
                    
                    <div class="result-section" id="dateSection" style="display:none;">
                        <h3>📅 Dates</h3>
                        <div id="dates"></div>
                    </div>
                    
                    <div class="result-section" id="currencySection" style="display:none;">
                        <h3>💰 Currency Amounts</h3>
                        <div id="currency"></div>
                    </div>
                    
                    <div class="result-section" id="urlSection" style="display:none;">
                        <h3>🔗 URLs</h3>
                        <div id="urls"></div>
                    </div>
                    
                    <div class="result-section" id="sectionsSection" style="display:none;">
                        <h3>🔍 Key Sections</h3>
                        <div id="sections"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            View source code on <a href="https://github.com/Lt-wei/ai-solutions-portfolio" target="_blank">GitHub</a>
        </div>
        
        <script>
            let selectedFile = null;
            
            function handleFileSelect(event) {
                selectedFile = event.target.files[0];
                const fileNameDiv = document.getElementById('fileName');
                const uploadBtn = document.getElementById('uploadBtn');
                
                if (selectedFile) {
                    if (selectedFile.size > 10 * 1024 * 1024) {
                        fileNameDiv.textContent = '❌ File too large (max 10MB)';
                        fileNameDiv.style.color = '#dc2626';
                        uploadBtn.disabled = true;
                        return;
                    }
                    fileNameDiv.textContent = `✓ ${selectedFile.name}`;
                    fileNameDiv.style.color = '#10b981';
                    uploadBtn.disabled = false;
                } else {
                    fileNameDiv.textContent = '';
                    uploadBtn.disabled = true;
                }
            }
            
            async function processUpload() {
                if (!selectedFile) return;
                
                const formData = new FormData();
                formData.append('file', selectedFile);
                
                showSpinner(true);
                hideResults();
                
                try {
                    const response = await fetch('/analyze', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        displayResults(data);
                    } else {
                        const error = await response.json();
                        alert(`Error: ${error.detail || 'Analysis failed'}`);
                    }
                } catch (error) {
                    alert(`Error: ${error.message}`);
                } finally {
                    showSpinner(false);
                }
            }
            
            async function processSample() {
                showSpinner(true);
                hideResults();
                
                try {
                    const response = await fetch('/sample');
                    
                    if (response.ok) {
                        const data = await response.json();
                        displayResults(data);
                    } else {
                        const error = await response.json();
                        alert(`Error: ${error.detail || 'Analysis failed'}`);
                    }
                } catch (error) {
                    alert(`Error: ${error.message}`);
                } finally {
                    showSpinner(false);
                }
            }
            
            function displayResults(data) {
                // Show results container
                document.getElementById('results').className = 'results active';
                
                // Display stats
                const statsHTML = `
                    <div class="stat-card">
                        <div class="stat-value">${data.pages}</div>
                        <div class="stat-label">Pages</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.word_count.toLocaleString()}</div>
                        <div class="stat-label">Words</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.text_length.toLocaleString()}</div>
                        <div class="stat-label">Characters</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.emails.length}</div>
                        <div class="stat-label">Emails Found</div>
                    </div>
                `;
                document.getElementById('stats').innerHTML = statsHTML;
                
                // Display emails
                displaySection('emailSection', 'emails', data.emails);
                
                // Display phones
                displaySection('phoneSection', 'phones', data.phone_numbers);
                
                // Display dates
                displaySection('dateSection', 'dates', data.dates);
                
                // Display currency
                displaySection('currencySection', 'currency', data.currency_amounts);
                
                // Display URLs
                displaySection('urlSection', 'urls', data.urls);
                
                // Display sections
                if (Object.keys(data.key_sections).length > 0) {
                    document.getElementById('sectionsSection').style.display = 'block';
                    const sectionsHTML = Object.entries(data.key_sections)
                        .map(([key, value]) => `<div class="result-item"><strong>${key}:</strong> ${value}</div>`)
                        .join('');
                    document.getElementById('sections').innerHTML = sectionsHTML;
                } else {
                    document.getElementById('sectionsSection').style.display = 'none';
                }
            }
            
            function displaySection(sectionId, contentId, items) {
                if (items.length > 0) {
                    document.getElementById(sectionId).style.display = 'block';
                    const html = items.map(item => `<div class="result-item"><code>${item}</code></div>`).join('');
                    document.getElementById(contentId).innerHTML = html;
                } else {
                    document.getElementById(sectionId).style.display = 'none';
                }
            }
            
            function showSpinner(show) {
                document.getElementById('spinner').className = show ? 'spinner active' : 'spinner';
            }
            
            function hideResults() {
                document.getElementById('results').className = 'results';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "pdf-document-ai"}

@app.post("/analyze")
async def analyze_pdf(file: UploadFile = File(...)):
    """Analyze uploaded PDF file."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE / 1024 / 1024}MB")
    
    try:
        # Save to temp file
        temp_file = os.path.join(TEMP_DIR, f"upload_{os.urandom(8).hex()}.pdf")
        with open(temp_file, 'wb') as f:
            f.write(contents)
        
        # Extract and analyze
        text = extract_text_from_pdf(temp_file)
        result = analyze_document(text, filename=file.filename)
        
        # Cleanup
        try:
            os.remove(temp_file)
        except:
            pass
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing PDF: {str(e)}")

@app.get("/sample")
async def analyze_sample():
    """Analyze sample PDF."""
    try:
        # Create sample PDF
        sample_path = create_sample_pdf()
        
        # Extract and analyze
        text = extract_text_from_pdf(sample_path)
        result = analyze_document(text, filename="sample-invoice.pdf")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing sample: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting PDF Document AI Demo...")
    print("📄 Open http://localhost:8001 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8001)
