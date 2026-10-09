"""
Excel/CSV Data Processing Automation
FastAPI backend for automated data cleaning, deduplication, and transformation
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from portfolio_ui import demo_page, demo_badge, UPLOAD_ICON_SVG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Excel Automation API", version="1.0.0")

# Create necessary directories (use /tmp for serverless)
TEMP_BASE = Path("/tmp") if Path("/tmp").exists() else Path(".")
UPLOAD_DIR = TEMP_BASE / "uploads"
OUTPUT_DIR = TEMP_BASE / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


class ExcelProcessor:
    """Core data processing pipeline"""
    
    def __init__(self, df: pd.DataFrame, rules: Optional[dict] = None):
        self.df = df.copy()
        self.rules = rules or {}
        self.report = {
            "original_rows": len(df),
            "original_columns": len(df.columns),
            "steps": [],
            "timestamp": datetime.now().isoformat()
        }
    
    def clean_data(self):
        """Remove empty rows and standardize data"""
        before = len(self.df)
        
        # Remove completely empty rows
        self.df.dropna(how='all', inplace=True)
        
        # Strip whitespace from string columns
        for col in self.df.select_dtypes(include=['object']).columns:
            self.df[col] = self.df[col].astype(str).str.strip()
            self.df[col].replace('nan', '', inplace=True)
        
        removed = before - len(self.df)
        self.report["steps"].append({
            "step": "clean_data",
            "rows_removed": removed,
            "rows_remaining": len(self.df)
        })
        logger.info(f"Cleaned data: removed {removed} empty rows")
        return self
    
    def deduplicate(self):
        """Remove duplicate rows"""
        before = len(self.df)
        subset_cols = self.rules.get("dedupe_columns", None)
        
        self.df.drop_duplicates(subset=subset_cols, inplace=True)
        
        removed = before - len(self.df)
        self.report["steps"].append({
            "step": "deduplicate",
            "duplicates_removed": removed,
            "rows_remaining": len(self.df)
        })
        logger.info(f"Removed {removed} duplicate rows")
        return self
    
    def transform_fields(self):
        """Apply field transformations based on rules"""
        transformations = self.rules.get("transformations", {})
        
        for col, transform_type in transformations.items():
            if col not in self.df.columns:
                continue
                
            if transform_type == "uppercase":
                self.df[col] = self.df[col].astype(str).str.upper()
            elif transform_type == "lowercase":
                self.df[col] = self.df[col].astype(str).str.lower()
            elif transform_type == "title":
                self.df[col] = self.df[col].astype(str).str.title()
            elif transform_type == "numeric":
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        self.report["steps"].append({
            "step": "transform_fields",
            "transformations_applied": len(transformations)
        })
        logger.info(f"Applied {len(transformations)} field transformations")
        return self
    
    def apply_rules(self):
        """Apply custom business rules"""
        filters = self.rules.get("filters", {})
        
        for col, condition in filters.items():
            if col not in self.df.columns:
                continue
            
            before = len(self.df)
            
            if condition.get("min_value"):
                self.df = self.df[pd.to_numeric(self.df[col], errors='coerce') >= condition["min_value"]]
            
            if condition.get("max_value"):
                self.df = self.df[pd.to_numeric(self.df[col], errors='coerce') <= condition["max_value"]]
            
            if condition.get("exclude_values"):
                self.df = self.df[~self.df[col].isin(condition["exclude_values"])]
            
            removed = before - len(self.df)
            if removed > 0:
                self.report["steps"].append({
                    "step": f"apply_filter_{col}",
                    "rows_filtered": removed
                })
        
        logger.info(f"Applied business rules, {len(self.df)} rows remaining")
        return self
    
    def get_processed_data(self):
        """Return processed dataframe and report"""
        self.report["final_rows"] = len(self.df)
        self.report["final_columns"] = len(self.df.columns)
        return self.df, self.report


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI"""
    main_html = f"""
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-zone" id="uploadZone">
                    {UPLOAD_ICON_SVG}
                    <p class="upload-title">Upload Excel or CSV</p>
                    <p class="upload-hint">Single file · Max 10MB</p>
                    <label class="btn-file">
                        <input type="file" name="file" id="fileInput" accept=".xlsx,.xls,.csv">
                        Choose file
                    </label>
                    <p class="file-selected" id="fileName" aria-live="polite"></p>
                </div>

                <label class="section-label" for="rulesInput">Processing rules (optional JSON)</label>
                <textarea name="rules" id="rulesInput" placeholder='{{
  "dedupe_columns": ["email"],
  "transformations": {{
    "name": "title",
    "email": "lowercase"
  }},
  "filters": {{
    "age": {{"min_value": 18}}
  }}
}}'></textarea>

                <div class="actions">
                    <button type="submit" class="btn btn-primary" id="submitBtn">Process uploaded file</button>
                    <button type="button" class="btn btn-secondary" id="sampleBtn">Try sample data</button>
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
                    const f = fileInput.files[0];
                    fileName.textContent = f ? 'Selected: ' + f.name : '';
                }});

                ['dragenter', 'dragover'].forEach(ev => zone.addEventListener(ev, e => {{
                    e.preventDefault();
                    zone.classList.add('is-dragover');
                }}));
                ['dragleave', 'drop'].forEach(ev => zone.addEventListener(ev, e => {{
                    e.preventDefault();
                    zone.classList.remove('is-dragover');
                }}));
                zone.addEventListener('drop', e => {{
                    if (e.dataTransfer.files.length) {{
                        fileInput.files = e.dataTransfer.files;
                        fileInput.dispatchEvent(new Event('change'));
                    }}
                }});

                function renderSuccess(data, title) {{
                    return `
                        <p class="result-title success">${{title}}</p>
                        <p><strong>Rows:</strong> ${{data.report.original_rows}} → ${{data.report.final_rows}}</p>
                        <p><strong>Time:</strong> ${{data.processing_time.toFixed(3)}}s</p>
                        <pre class="result-json">${{JSON.stringify(data.report, null, 2)}}</pre>
                        <div class="download-row">
                            <a href="/download/${{data.output_file}}" class="download-link" download>Download Excel</a>
                            <a href="/download/${{data.report_file}}" class="download-link alt" download>Download report</a>
                        </div>`;
                }}

                function renderError(msg) {{
                    return `<p class="result-title error">Processing failed</p><p>${{msg}}</p>`;
                }}

                async function runRequest(url, options, successTitle) {{
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
                            resultDiv.innerHTML = renderSuccess(data, successTitle);
                        }} else {{
                            throw new Error(data.detail || 'Processing failed');
                        }}
                    }} catch (error) {{
                        resultDiv.className = 'error';
                        resultDiv.innerHTML = renderError(error.message);
                    }}

                    resultDiv.style.display = 'block';
                    submitBtn.disabled = false;
                    sampleBtn.disabled = false;
                    loader.style.display = 'none';
                }}

                document.getElementById('uploadForm').addEventListener('submit', async (e) => {{
                    e.preventDefault();
                    const fileInput = document.getElementById('fileInput');
                    if (!fileInput.files[0]) {{
                        alert('Please choose a file to upload.');
                        return;
                    }}
                    if (fileInput.files[0].size > 10 * 1024 * 1024) {{
                        alert('File size exceeds the 10MB limit.');
                        return;
                    }}
                    const formData = new FormData();
                    const rulesInput = document.getElementById('rulesInput');
                    formData.append('file', fileInput.files[0]);
                    if (rulesInput.value.trim()) formData.append('rules', rulesInput.value);
                    await runRequest('/process', {{ method: 'POST', body: formData }}, 'Processing complete');
                }});

                document.getElementById('sampleBtn').addEventListener('click', () =>
                    runRequest('/sample', {{}}, 'Sample run complete')
                );
            }})();
            </script>
    """

    return demo_page(
        page_title="Excel Data Processing — Leane",
        product_title="Excel Data Processing",
        value_prop="Automated cleaning, deduplication, and transformation for spreadsheet workflows.",
        badge_text=demo_badge(sample_only=True),
        pipeline_html="Clean empty rows → deduplicate → transform fields → apply rules → export with report.",
        main_html=main_html,
    )


@app.post("/process")
async def process_excel(
    file: UploadFile = File(...),
    rules: Optional[str] = Form(None)
):
    """Process uploaded Excel/CSV file through the data pipeline"""
    import time
    start_time = time.time()
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Only Excel (.xlsx, .xls) and CSV files are supported")
    
    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_path = UPLOAD_DIR / f"{timestamp}_{file.filename}"
    
    with open(input_path, "wb") as f:
        content = await file.read()
        # Check file size (10MB limit for serverless)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File size exceeds 10MB limit")
        f.write(content)
    
    logger.info(f"File uploaded: {input_path}")
    
    try:
        # Parse rules if provided
        rules_dict = {}
        if rules:
            try:
                rules_dict = json.loads(rules)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in rules")
        
        # Read file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(input_path)
        else:
            df = pd.read_excel(input_path)
        
        # Process through pipeline
        processor = ExcelProcessor(df, rules_dict)
        processed_df, report = (
            processor
            .clean_data()
            .deduplicate()
            .transform_fields()
            .apply_rules()
            .get_processed_data()
        )
        
        # Save outputs
        output_filename = f"processed_{timestamp}.xlsx"
        output_path = OUTPUT_DIR / output_filename
        processed_df.to_excel(output_path, index=False, engine='openpyxl')
        
        report_filename = f"report_{timestamp}.json"
        report_path = OUTPUT_DIR / report_filename
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Processing complete: {len(processed_df)} rows output")
        
        return {
            "status": "success",
            "output_file": output_filename,
            "report_file": report_filename,
            "report": report,
            "processing_time": processing_time
        }
        
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download processed files"""
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/sample")
async def process_sample():
    """Process sample data for demo purposes"""
    import time
    start_time = time.time()
    
    try:
        # Load sample file and rules
        sample_file_path = Path(__file__).parent / "sample_inputs" / "customers_raw.xlsx"
        sample_rules_path = Path(__file__).parent / "sample_inputs" / "rules.json"
        
        if not sample_file_path.exists():
            raise HTTPException(status_code=500, detail="Sample data files not found")
        
        # Read sample data
        df = pd.read_excel(sample_file_path)
        
        # Read sample rules
        with open(sample_rules_path, "r") as f:
            rules_dict = json.load(f)
        
        # Process through pipeline
        processor = ExcelProcessor(df, rules_dict)
        processed_df, report = (
            processor
            .clean_data()
            .deduplicate()
            .transform_fields()
            .apply_rules()
            .get_processed_data()
        )
        
        # Save outputs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"processed_sample_{timestamp}.xlsx"
        output_path = OUTPUT_DIR / output_filename
        processed_df.to_excel(output_path, index=False, engine='openpyxl')
        
        report_filename = f"report_sample_{timestamp}.json"
        report_path = OUTPUT_DIR / report_filename
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Sample processing complete: {len(processed_df)} rows output")
        
        return {
            "status": "success",
            "output_file": output_filename,
            "report_file": report_filename,
            "report": report,
            "processing_time": processing_time
        }
        
    except Exception as e:
        logger.error(f"Sample processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sample processing failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "excel-automation"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
