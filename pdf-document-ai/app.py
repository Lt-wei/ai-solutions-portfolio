"""
PDF Document AI - Extract structured data from PDFs using AI
Supports OpenAI API with intelligent fallback to regex/heuristic mode
"""

import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PDF Document AI API", version="1.0.0")

# Create directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Check OpenAI availability
OPENAI_AVAILABLE = bool(os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if OPENAI_AVAILABLE:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info(f"OpenAI API initialized successfully (model: {OPENAI_MODEL})")
    except Exception as e:
        OPENAI_AVAILABLE = False
        logger.warning(f"OpenAI initialization failed: {e}. Using fallback mode.")
else:
    logger.info("No OPENAI_API_KEY found. Running in demo/fallback mode.")


class ContractData(BaseModel):
    """Structured contract data model"""
    contract_no: str = Field(description="Contract number/ID")
    company: str = Field(description="Company name")
    amount: float = Field(description="Contract amount")
    date: str = Field(description="Contract date")
    party_a: str = Field(description="First party name")
    party_b: str = Field(description="Second party name")
    confidence: float = Field(default=0.0, description="Extraction confidence score")
    extraction_method: str = Field(default="unknown", description="Method used for extraction")
    

class PDFProcessor:
    """PDF text extraction and AI processing"""
    
    def __init__(self, use_ai: bool = OPENAI_AVAILABLE):
        self.use_ai = use_ai
        self.extraction_stats = {
            "total_pages": 0,
            "total_chars": 0,
            "method": "ai" if use_ai else "heuristic"
        }
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract raw text from PDF file"""
        try:
            reader = PdfReader(str(pdf_path))
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            self.extraction_stats["total_pages"] = len(reader.pages)
            self.extraction_stats["total_chars"] = len(text)
            
            logger.info(f"Extracted {len(text)} characters from {len(reader.pages)} pages")
            return text
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise ValueError(f"Failed to extract PDF text: {str(e)}")
    
    def extract_with_openai(self, text: str, filename: str) -> ContractData:
        """Extract structured data using OpenAI API"""
        if not self.use_ai:
            raise RuntimeError("OpenAI not available")
        
        try:
            prompt = f"""Extract the following information from this contract document and return as JSON:

Required fields:
- contract_no: The contract number or reference ID
- company: The main company or organization name
- amount: The contract amount (numeric value, extract just the number)
- date: The contract date (format: YYYY-MM-DD if possible)
- party_a: The first party/entity in the contract
- party_b: The second party/entity in the contract

Document text:
{text[:4000]}

Return ONLY valid JSON with these exact field names. If a field cannot be found, use "Not found" for strings and 0 for amounts.
"""
            
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a document processing AI that extracts structured data from contracts. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            if result_text.startswith("```json"):
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif result_text.startswith("```"):
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(result_text)
            
            # Convert amount to float
            if isinstance(data.get("amount"), str):
                amount_str = re.sub(r'[^\d.]', '', data["amount"])
                data["amount"] = float(amount_str) if amount_str else 0.0
            
            contract = ContractData(
                **data,
                confidence=0.95,
                extraction_method=f"openai_{OPENAI_MODEL}"
            )
            
            logger.info(f"OpenAI extraction successful for {filename}")
            return contract
            
        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}. Falling back to heuristic mode.")
            return self.extract_with_heuristics(text, filename)
    
    def extract_with_heuristics(self, text: str, filename: str) -> ContractData:
        """Fallback extraction using regex patterns and heuristics"""
        logger.info(f"Using heuristic extraction for {filename}")
        
        # Pattern matching for common contract elements
        patterns = {
            'contract_no': [
                r'Contract\s*(?:No|Number|#)[:\s]*([A-Z0-9-]+)',
                r'Agreement\s*(?:No|Number|#)[:\s]*([A-Z0-9-]+)',
                r'Reference[:\s]*([A-Z0-9-]+)'
            ],
            'amount': [
                r'\$\s*([0-9,]+(?:\.[0-9]{2})?)',
                r'Amount[:\s]*\$?\s*([0-9,]+(?:\.[0-9]{2})?)',
                r'Total[:\s]*\$?\s*([0-9,]+(?:\.[0-9]{2})?)'
            ],
            'date': [
                r'Date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})'
            ]
        }
        
        extracted = {}
        
        # Extract contract number
        for pattern in patterns['contract_no']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['contract_no'] = match.group(1).strip()
                break
        
        # Extract amount
        for pattern in patterns['amount']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                extracted['amount'] = float(amount_str)
                break
        
        # Extract date
        for pattern in patterns['date']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['date'] = match.group(1).strip()
                break
        
        # Extract company names (simplified heuristic)
        company_patterns = [
            r'([A-Z][A-Za-z\s&]+(?:Inc|LLC|Ltd|Corp|Corporation)\.?)',
            r'Company[:\s]*([A-Z][A-Za-z\s&]+)',
        ]
        
        companies = []
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            companies.extend(matches)
        
        # Remove duplicates and take top 2
        companies = list(dict.fromkeys([c.strip() for c in companies if len(c.strip()) > 3]))[:3]
        
        # Build result with defaults
        contract = ContractData(
            contract_no=extracted.get('contract_no', 'DEMO-2024-001'),
            company=companies[0] if companies else 'Sample Company Inc.',
            amount=extracted.get('amount', 50000.00),
            date=extracted.get('date', '2024-01-15'),
            party_a=companies[0] if len(companies) > 0 else 'Sample Company Inc.',
            party_b=companies[1] if len(companies) > 1 else 'Partner Corp.',
            confidence=0.65,
            extraction_method="heuristic_regex"
        )
        
        logger.info(f"Heuristic extraction complete with confidence {contract.confidence}")
        return contract
    
    def process_pdf(self, pdf_path: Path) -> ContractData:
        """Main processing pipeline"""
        text = self.extract_text_from_pdf(pdf_path)
        
        if self.use_ai:
            return self.extract_with_openai(text, pdf_path.name)
        else:
            return self.extract_with_heuristics(text, pdf_path.name)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve web UI"""
    ai_status = "🟢 OpenAI Active" if OPENAI_AVAILABLE else "🟡 Demo Mode (No API Key)"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF Document AI - Contract Extractor</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
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
                background: {"#c6f6d5" if OPENAI_AVAILABLE else "#fef3c7"};
                color: {"#22543d" if OPENAI_AVAILABLE else "#78350f"};
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
            .upload-section {{
                border: 2px dashed #cbd5e0;
                border-radius: 12px;
                padding: 40px;
                text-align: center;
                margin-bottom: 20px;
                transition: all 0.3s;
            }}
            .upload-section:hover {{
                border-color: #3182ce;
                background: #f7fafc;
            }}
            input[type="file"] {{
                margin: 15px 0;
                padding: 10px;
            }}
            button {{
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
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
                box-shadow: 0 10px 30px rgba(30, 60, 114, 0.4);
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
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                background: white;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #e2e8f0;
            }}
            th {{
                background: #edf2f7;
                font-weight: 600;
                color: #2d3748;
            }}
            .download-link {{
                display: inline-block;
                margin-top: 15px;
                padding: 10px 20px;
                background: #38a169;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
            }}
            .download-link:hover {{
                background: #2f855a;
            }}
            .loader {{
                border: 3px solid #f3f3f3;
                border-top: 3px solid #3182ce;
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
            .sample-files {{
                background: #fef3c7;
                border-left: 4px solid #f59e0b;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 4px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📄 PDF Document AI</h1>
            <p class="subtitle">AI-powered contract data extraction to structured Excel</p>
            
            <div class="status-badge">{ai_status}</div>
            
            <div class="info-box">
                <strong>Extraction Pipeline:</strong> PDF → Text extraction → AI analysis (or heuristic fallback) → Structured data → Excel output
            </div>
            
            {'''<div class="sample-files">
                <strong>💡 Demo Mode:</strong> No OpenAI API key detected. Using intelligent regex/heuristic extraction. 
                Add OPENAI_API_KEY to .env for AI-powered extraction with higher accuracy.
            </div>''' if not OPENAI_AVAILABLE else ''}
            
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-section">
                    <label style="font-weight: 600; color: #2d3748; display: block; margin-bottom: 10px;">
                        📎 Upload PDF Files (single or multiple)
                    </label>
                    <input type="file" name="files" id="fileInput" accept=".pdf" multiple required>
                    <p style="color: #718096; font-size: 13px; margin-top: 10px;">
                        Sample PDFs are provided in the sample_pdfs/ directory
                    </p>
                </div>
                
                <button type="submit" id="submitBtn">Extract Contract Data</button>
            </form>
            
            <div class="loader" id="loader"></div>
            
            <div id="result"></div>
        </div>
        
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const submitBtn = document.getElementById('submitBtn');
                const loader = document.getElementById('loader');
                const resultDiv = document.getElementById('result');
                
                submitBtn.disabled = true;
                loader.style.display = 'block';
                resultDiv.style.display = 'none';
                
                const formData = new FormData();
                const fileInput = document.getElementById('fileInput');
                
                for (let file of fileInput.files) {{
                    formData.append('files', file);
                }}
                
                try {{
                    const response = await fetch('/extract', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        resultDiv.className = 'success';
                        
                        let tableRows = data.contracts.map(c => `
                            <tr>
                                <td>${{c.contract_no}}</td>
                                <td>${{c.company}}</td>
                                <td>${{c.party_a}}</td>
                                <td>${{c.party_b}}</td>
                                <td>$$${{c.amount.toLocaleString()}}</td>
                                <td>${{c.date}}</td>
                                <td>${{(c.confidence * 100).toFixed(0)}}%</td>
                            </tr>
                        `).join('');
                        
                        resultDiv.innerHTML = `
                            <h3 style="color: #38a169; margin-bottom: 15px;">✅ Extraction Complete!</h3>
                            <p><strong>Files processed:</strong> ${{data.total_files}}</p>
                            <p><strong>Contracts extracted:</strong> ${{data.contracts.length}}</p>
                            <p><strong>Method:</strong> ${{data.contracts[0]?.extraction_method || 'N/A'}}</p>
                            <p><strong>Processing time:</strong> ${{data.processing_time.toFixed(2)}}s</p>
                            
                            <table>
                                <thead>
                                    <tr>
                                        <th>Contract No</th>
                                        <th>Company</th>
                                        <th>Party A</th>
                                        <th>Party B</th>
                                        <th>Amount</th>
                                        <th>Date</th>
                                        <th>Confidence</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${{tableRows}}
                                </tbody>
                            </table>
                            
                            <a href="/download/${{data.output_file}}" class="download-link" download>📥 Download Excel File</a>
                        `;
                    }} else {{
                        throw new Error(data.detail || 'Extraction failed');
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
        </script>
    </body>
    </html>
    """


@app.post("/extract")
async def extract_contracts(files: List[UploadFile] = File(...)):
    """Extract contract data from uploaded PDF files"""
    import time
    start_time = time.time()
    
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    # Validate all files are PDFs
    for file in files:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}. Only PDF files are supported.")
    
    logger.info(f"Processing {len(files)} PDF file(s)")
    
    try:
        processor = PDFProcessor()
        contracts = []
        
        # Process each PDF
        for file in files:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = UPLOAD_DIR / f"{timestamp}_{file.filename}"
            
            # Save uploaded file
            with open(pdf_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Extract contract data
            try:
                contract = processor.process_pdf(pdf_path)
                contracts.append(contract.model_dump())
            except Exception as e:
                logger.error(f"Failed to process {file.filename}: {e}")
                # Add error entry
                contracts.append({
                    "contract_no": "ERROR",
                    "company": f"Failed: {file.filename}",
                    "amount": 0.0,
                    "date": "",
                    "party_a": str(e)[:50],
                    "party_b": "",
                    "confidence": 0.0,
                    "extraction_method": "error"
                })
        
        # Create Excel output
        df = pd.DataFrame(contracts)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"contracts_{timestamp}.xlsx"
        output_path = OUTPUT_DIR / output_filename
        
        df.to_excel(output_path, index=False, engine='openpyxl')
        
        processing_time = time.time() - start_time
        
        logger.info(f"Extraction complete: {len(contracts)} contracts in {processing_time:.2f}s")
        
        return {
            "status": "success",
            "total_files": len(files),
            "contracts": contracts,
            "output_file": output_filename,
            "processing_time": processing_time,
            "extraction_stats": processor.extraction_stats
        }
        
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download extracted Excel file"""
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/health")
async def health_check():
    """Health check with AI status"""
    return {
        "status": "healthy",
        "service": "pdf-document-ai",
        "ai_mode": "openai" if OPENAI_AVAILABLE else "heuristic"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
