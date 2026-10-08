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
from fastapi.staticfiles import StaticFiles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Excel Automation API", version="1.0.0")

# Create necessary directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
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
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Excel Automation - Data Processing Pipeline</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #2d3748;
                margin-bottom: 10px;
                font-size: 32px;
            }
            .subtitle {
                color: #718096;
                margin-bottom: 30px;
                font-size: 16px;
            }
            .upload-section {
                border: 2px dashed #cbd5e0;
                border-radius: 12px;
                padding: 30px;
                margin-bottom: 20px;
                text-align: center;
                transition: all 0.3s;
            }
            .upload-section:hover {
                border-color: #667eea;
                background: #f7fafc;
            }
            input[type="file"] {
                margin: 15px 0;
                padding: 10px;
            }
            textarea {
                width: 100%;
                min-height: 150px;
                padding: 15px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                margin-bottom: 20px;
                resize: vertical;
            }
            button {
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
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            #result {
                margin-top: 30px;
                padding: 20px;
                border-radius: 8px;
                background: #f7fafc;
                display: none;
            }
            .success {
                background: #c6f6d5;
                border-left: 4px solid #38a169;
            }
            .error {
                background: #fed7d7;
                border-left: 4px solid #e53e3e;
            }
            pre {
                background: #2d3748;
                color: #e2e8f0;
                padding: 15px;
                border-radius: 6px;
                overflow-x: auto;
                margin-top: 10px;
                font-size: 12px;
            }
            .download-link {
                display: inline-block;
                margin-top: 15px;
                padding: 10px 20px;
                background: #38a169;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
            }
            .download-link:hover {
                background: #2f855a;
            }
            .info-box {
                background: #ebf8ff;
                border-left: 4px solid #3182ce;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            .loader {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
                display: none;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Excel Data Processing</h1>
            <p class="subtitle">Automated cleaning, deduplication, and transformation pipeline</p>
            
            <div class="info-box">
                <strong>Pipeline steps:</strong> Clean empty rows → Remove duplicates → Transform fields → Apply business rules → Generate report
            </div>
            
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-section">
                    <label style="font-weight: 600; color: #2d3748; display: block; margin-bottom: 10px;">
                        📁 Upload Excel/CSV File *
                    </label>
                    <input type="file" name="file" id="fileInput" accept=".xlsx,.xls,.csv" required>
                </div>
                
                <label style="font-weight: 600; color: #2d3748; display: block; margin-bottom: 10px;">
                    ⚙️ Processing Rules (Optional JSON)
                </label>
                <textarea name="rules" id="rulesInput" placeholder='{
  "dedupe_columns": ["email"],
  "transformations": {
    "name": "title",
    "email": "lowercase"
  },
  "filters": {
    "age": {"min_value": 18}
  }
}'></textarea>
                
                <button type="submit" id="submitBtn">Process Data</button>
            </form>
            
            <div class="loader" id="loader"></div>
            
            <div id="result"></div>
        </div>
        
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const submitBtn = document.getElementById('submitBtn');
                const loader = document.getElementById('loader');
                const resultDiv = document.getElementById('result');
                
                submitBtn.disabled = true;
                loader.style.display = 'block';
                resultDiv.style.display = 'none';
                
                const formData = new FormData();
                const fileInput = document.getElementById('fileInput');
                const rulesInput = document.getElementById('rulesInput');
                
                formData.append('file', fileInput.files[0]);
                if (rulesInput.value.trim()) {
                    formData.append('rules', rulesInput.value);
                }
                
                try {
                    const response = await fetch('/process', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        resultDiv.className = 'success';
                        resultDiv.innerHTML = `
                            <h3 style="color: #38a169; margin-bottom: 15px;">✅ Processing Complete!</h3>
                            <p><strong>Processed:</strong> ${data.report.original_rows} → ${data.report.final_rows} rows</p>
                            <p><strong>Time:</strong> ${data.processing_time.toFixed(3)}s</p>
                            <pre>${JSON.stringify(data.report, null, 2)}</pre>
                            <a href="/download/${data.output_file}" class="download-link" download>📥 Download Processed Excel</a>
                            <a href="/download/${data.report_file}" class="download-link" download style="background: #3182ce; margin-left: 10px;">📄 Download Report</a>
                        `;
                    } else {
                        throw new Error(data.detail || 'Processing failed');
                    }
                } catch (error) {
                    resultDiv.className = 'error';
                    resultDiv.innerHTML = `
                        <h3 style="color: #e53e3e; margin-bottom: 10px;">❌ Error</h3>
                        <p>${error.message}</p>
                    `;
                }
                
                resultDiv.style.display = 'block';
                submitBtn.disabled = false;
                loader.style.display = 'none';
            });
        </script>
    </body>
    </html>
    """


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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "excel-automation"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
