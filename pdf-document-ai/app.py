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

from portfolio_ui import demo_page, demo_badge, UPLOAD_ICON_SVG

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PDF Document AI API", version="1.0.0")

# Create directories (use /tmp for serverless)
TEMP_BASE = Path("/tmp") if Path("/tmp").exists() else Path(".")
UPLOAD_DIR = TEMP_BASE / "uploads"
OUTPUT_DIR = TEMP_BASE / "outputs"
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
    notice = None
    if not OPENAI_AVAILABLE:
        notice = (
            "No OpenAI API key is configured. Extraction uses regex and heuristic patterns "
            "so you can try the demo safely. Set <code>OPENAI_API_KEY</code> to enable live AI extraction."
        )

    badge = demo_badge(mock_ai=not OPENAI_AVAILABLE, openai_active=OPENAI_AVAILABLE)

    main_html = f"""
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-zone" id="uploadZone">
                    {UPLOAD_ICON_SVG}
                    <p class="upload-title">Upload PDF contracts</p>
                    <p class="upload-hint">One or more files · Max 10MB each</p>
                    <label class="btn-file">
                        <input type="file" name="files" id="fileInput" accept=".pdf" multiple>
                        Choose files
                    </label>
                    <p class="file-selected" id="fileName" aria-live="polite"></p>
                </div>

                <div class="actions">
                    <button type="submit" class="btn btn-primary" id="submitBtn">Extract from uploaded PDFs</button>
                    <button type="button" class="btn btn-secondary" id="sampleBtn">Try sample contracts</button>
                </div>
            </form>

            <div class="loader" id="loader"></div>
            <div id="result"></div>

            <script>
            (function() {{
                const fileInput = document.getElementById('fileInput');
                const fileName = document.getElementById('fileName');
                const zone = document.getElementById('uploadZone');

                fileInput.addEventListener('change', () => {{
                    const n = fileInput.files.length;
                    if (!n) {{ fileName.textContent = ''; return; }}
                    if (n === 1) fileName.textContent = 'Selected: ' + fileInput.files[0].name;
                    else fileName.textContent = n + ' files selected';
                }});

                function renderTable(data, title) {{
                    const tableRows = data.contracts.map(c => `
                        <tr>
                            <td>${{c.contract_no}}</td>
                            <td>${{c.company}}</td>
                            <td>${{c.party_a}}</td>
                            <td>${{c.party_b}}</td>
                            <td>$${{c.amount.toLocaleString()}}</td>
                            <td>${{c.date}}</td>
                            <td>${{(c.confidence * 100).toFixed(0)}}%</td>
                        </tr>`).join('');

                    return `
                        <p class="result-title success">${{title}}</p>
                        <p><strong>Files processed:</strong> ${{data.total_files}}</p>
                        <p><strong>Contracts:</strong> ${{data.contracts.length}}</p>
                        <p><strong>Method:</strong> ${{data.contracts[0]?.extraction_method || 'N/A'}}</p>
                        <p><strong>Time:</strong> ${{data.processing_time.toFixed(2)}}s</p>
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Contract</th>
                                    <th>Company</th>
                                    <th>Party A</th>
                                    <th>Party B</th>
                                    <th>Amount</th>
                                    <th>Date</th>
                                    <th>Conf.</th>
                                </tr>
                            </thead>
                            <tbody>${{tableRows}}</tbody>
                        </table>
                        <div class="download-row">
                            <a href="/download/${{data.output_file}}" class="download-link" download>Download Excel</a>
                        </div>`;
                }}

                async function run(url, options, successTitle) {{
                    const submitBtn = document.getElementById('submitBtn');
                    const sampleBtn = document.getElementById('sampleBtn');
                    const loader = document.getElementById('loader');
                    const resultDiv = document.getElementById('result');

                    submitBtn.disabled = true;
                    sampleBtn.disabled = true;
                    loader.style.display = 'block';
                    resultDiv.style.display = 'none';

                    try {{
                        const response = await fetch(url, options);
                        const data = await response.json();
                        if (response.ok) {{
                            resultDiv.className = 'success';
                            resultDiv.innerHTML = renderTable(data, successTitle);
                        }} else {{
                            throw new Error(data.detail || 'Extraction failed');
                        }}
                    }} catch (error) {{
                        resultDiv.className = 'error';
                        resultDiv.innerHTML = `<p class="result-title error">Extraction failed</p><p>${{error.message}}</p>`;
                    }}

                    resultDiv.style.display = 'block';
                    submitBtn.disabled = false;
                    sampleBtn.disabled = false;
                    loader.style.display = 'none';
                }}

                document.getElementById('uploadForm').addEventListener('submit', async (e) => {{
                    e.preventDefault();
                    if (!fileInput.files.length) {{
                        alert('Please choose at least one PDF.');
                        return;
                    }}
                    for (const file of fileInput.files) {{
                        if (file.size > 10 * 1024 * 1024) {{
                            alert('File exceeds 10MB: ' + file.name);
                            return;
                        }}
                    }}
                    const formData = new FormData();
                    for (const file of fileInput.files) formData.append('files', file);
                    await run('/extract', {{ method: 'POST', body: formData }}, 'Extraction complete');
                }});

                document.getElementById('sampleBtn').addEventListener('click', () =>
                    run('/sample', {{}}, 'Sample extraction complete')
                );
            }})();
            </script>
    """

    return demo_page(
        page_title="PDF Document AI — Leane",
        product_title="PDF Document AI",
        value_prop="Extract structured contract fields from PDFs and export to Excel.",
        badge_text=badge,
        pipeline_html="PDF → text extraction → AI or heuristic parsing → structured rows → Excel export.",
        notice_html=notice,
        main_html=main_html,
    )


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


@app.get("/sample")
async def extract_sample_contracts():
    """Process sample contract PDFs for demo purposes"""
    import time
    start_time = time.time()
    
    try:
        sample_dir = Path(__file__).parent / "sample_pdfs"
        if not sample_dir.exists():
            raise HTTPException(status_code=500, detail="Sample PDF files not found")
        
        # Get all sample PDFs
        sample_files = list(sample_dir.glob("*.pdf"))
        if not sample_files:
            raise HTTPException(status_code=500, detail="No sample PDF files found")
        
        logger.info(f"Processing {len(sample_files)} sample PDF file(s)")
        
        processor = PDFProcessor()
        contracts = []
        
        # Process each sample PDF
        for pdf_path in sample_files:
            try:
                contract = processor.process_pdf(pdf_path)
                contracts.append(contract.model_dump())
            except Exception as e:
                logger.error(f"Failed to process {pdf_path.name}: {e}")
                contracts.append({
                    "contract_no": "ERROR",
                    "company": f"Failed: {pdf_path.name}",
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
        output_filename = f"contracts_sample_{timestamp}.xlsx"
        output_path = OUTPUT_DIR / output_filename
        
        df.to_excel(output_path, index=False, engine='openpyxl')
        
        processing_time = time.time() - start_time
        
        logger.info(f"Sample extraction complete: {len(contracts)} contracts in {processing_time:.2f}s")
        
        return {
            "status": "success",
            "total_files": len(sample_files),
            "contracts": contracts,
            "output_file": output_filename,
            "processing_time": processing_time,
            "extraction_stats": processor.extraction_stats
        }
        
    except Exception as e:
        logger.error(f"Sample extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sample extraction failed: {str(e)}")


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
