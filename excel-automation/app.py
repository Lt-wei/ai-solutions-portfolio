from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import json
import os
import tempfile
from typing import Optional
from pathlib import Path

app = FastAPI(title="Excel Automation Demo")

# Constants for serverless
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
TEMP_DIR = "/tmp" if os.path.exists("/tmp") else tempfile.gettempdir()

class DataInput(BaseModel):
    data: list[dict]
    title: Optional[str] = "Sales Report"
    include_charts: Optional[bool] = False

def get_sample_data():
    """Get bundled sample sales data."""
    return [
        {"Product": "Laptop", "Category": "Electronics", "Units Sold": 45, "Unit Price": 899.99, "Revenue": 40499.55},
        {"Product": "Mouse", "Category": "Electronics", "Units Sold": 120, "Unit Price": 24.99, "Revenue": 2998.80},
        {"Product": "Keyboard", "Category": "Electronics", "Units Sold": 85, "Unit Price": 79.99, "Revenue": 6799.15},
        {"Product": "Monitor", "Category": "Electronics", "Units Sold": 32, "Unit Price": 299.99, "Revenue": 9599.68},
        {"Product": "Desk Chair", "Category": "Furniture", "Units Sold": 28, "Unit Price": 249.99, "Revenue": 6999.72},
        {"Product": "Standing Desk", "Category": "Furniture", "Units Sold": 15, "Unit Price": 599.99, "Revenue": 8999.85},
        {"Product": "Webcam", "Category": "Electronics", "Units Sold": 67, "Unit Price": 89.99, "Revenue": 6029.33},
        {"Product": "Headset", "Category": "Electronics", "Units Sold": 93, "Unit Price": 129.99, "Revenue": 12089.07},
    ]

def create_formatted_excel(data: list[dict], title: str = "Report") -> str:
    """Create a professionally formatted Excel file."""
    df = pd.DataFrame(data)
    
    # Create temp file
    temp_file = os.path.join(TEMP_DIR, f"report_{os.urandom(8).hex()}.xlsx")
    
    # Write to Excel with formatting
    with pd.ExcelWriter(temp_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
        
        workbook = writer.book
        worksheet = writer.sheets['Data']
        
        # Header styling
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Format headers
        for col_num, column in enumerate(df.columns, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
            
        # Format data cells
        for row in range(2, len(df) + 2):
            for col in range(1, len(df.columns) + 1):
                cell = worksheet.cell(row=row, column=col)
                cell.border = border
                
                # Format currency columns
                if 'price' in str(df.columns[col-1]).lower() or 'revenue' in str(df.columns[col-1]).lower():
                    cell.number_format = '$#,##0.00'
                # Format number columns
                elif isinstance(cell.value, (int, float)):
                    cell.number_format = '#,##0'
                    
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
            
        # Add title
        worksheet.insert_rows(1)
        worksheet.merge_cells('A1:' + get_column_letter(len(df.columns)) + '1')
        title_cell = worksheet['A1']
        title_cell.value = title
        title_cell.font = Font(size=16, bold=True, color="1F4E78")
        title_cell.alignment = Alignment(horizontal='center', vertical='center')
        worksheet.row_dimensions[1].height = 30
        
    return temp_file

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Excel Automation Demo</title>
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
            .container {
                flex: 1;
                max-width: 800px;
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
            .upload-section {
                margin: 30px 0;
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
                text-transform: none;
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
            .result {
                margin-top: 20px;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                display: none;
            }
            .result.success {
                background: #d1fae5;
                color: #065f46;
                display: block;
            }
            .result.error {
                background: #fee2e2;
                color: #991b1b;
                display: block;
            }
            .max-size {
                font-size: 12px;
                color: #64748b;
                text-align: center;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="banner">
            <strong>Excel Automation Demo</strong> — Transform data into beautifully formatted Excel reports with one click
        </div>
        
        <div class="container">
            <div class="card">
                <h1>📊 Excel Report Generator</h1>
                <p class="subtitle">Upload CSV/JSON data or try with sample sales data</p>
                
                <div class="feature-list">
                    <strong style="color: #1a202c; display: block; margin-bottom: 10px;">✨ What this demo does:</strong>
                    <ul>
                        <li>Converts CSV or JSON data to formatted Excel files</li>
                        <li>Applies professional styling (headers, borders, colors)</li>
                        <li>Auto-adjusts column widths for readability</li>
                        <li>Formats currency and numbers appropriately</li>
                        <li>Adds custom titles and branding</li>
                    </ul>
                </div>
                
                <div class="upload-section">
                    <div class="file-input-wrapper">
                        <input type="file" id="fileInput" accept=".csv,.json" onchange="handleFileSelect(event)">
                        <label for="fileInput" class="file-input-label">
                            📁 Click to upload CSV or JSON file<br>
                            <small>or drag and drop here</small>
                        </label>
                    </div>
                    <div class="file-name" id="fileName"></div>
                    <div class="max-size">Maximum file size: 5MB</div>
                </div>
                
                <div class="button-group">
                    <button class="btn-primary" id="uploadBtn" onclick="processUpload()" disabled>
                        Generate Excel from Upload
                    </button>
                    <button class="btn-secondary" onclick="processSample()">
                        🎯 Try with Sample Data
                    </button>
                </div>
                
                <div class="spinner" id="spinner"></div>
                <div class="result" id="result"></div>
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
                    if (selectedFile.size > 5 * 1024 * 1024) {
                        fileNameDiv.textContent = '❌ File too large (max 5MB)';
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
                hideResult();
                
                try {
                    const response = await fetch('/process', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const blob = await response.blob();
                        downloadFile(blob, 'report.xlsx');
                        showResult('success', '✓ Excel file generated successfully!');
                    } else {
                        const error = await response.json();
                        showResult('error', `Error: ${error.detail || 'Processing failed'}`);
                    }
                } catch (error) {
                    showResult('error', `Error: ${error.message}`);
                } finally {
                    showSpinner(false);
                }
            }
            
            async function processSample() {
                showSpinner(true);
                hideResult();
                
                try {
                    const response = await fetch('/sample');
                    
                    if (response.ok) {
                        const blob = await response.blob();
                        downloadFile(blob, 'sample_sales_report.xlsx');
                        showResult('success', '✓ Sample report generated! Check your downloads.');
                    } else {
                        const error = await response.json();
                        showResult('error', `Error: ${error.detail || 'Processing failed'}`);
                    }
                } catch (error) {
                    showResult('error', `Error: ${error.message}`);
                } finally {
                    showSpinner(false);
                }
            }
            
            function downloadFile(blob, filename) {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }
            
            function showSpinner(show) {
                document.getElementById('spinner').className = show ? 'spinner active' : 'spinner';
            }
            
            function hideResult() {
                document.getElementById('result').className = 'result';
            }
            
            function showResult(type, message) {
                const resultDiv = document.getElementById('result');
                resultDiv.className = `result ${type}`;
                resultDiv.textContent = message;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "excel-automation"}

@app.post("/process")
async def process_file(file: UploadFile = File(...)):
    """Process uploaded CSV/JSON file and return formatted Excel."""
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE / 1024 / 1024}MB")
    
    try:
        # Parse file based on extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(pd.io.common.BytesIO(contents))
            data = df.to_dict('records')
        elif file.filename.endswith('.json'):
            data = json.loads(contents)
            if not isinstance(data, list):
                raise ValueError("JSON must be an array of objects")
        else:
            raise HTTPException(status_code=400, detail="Only CSV and JSON files are supported")
        
        if not data:
            raise HTTPException(status_code=400, detail="File contains no data")
        
        # Generate Excel
        excel_file = create_formatted_excel(data, title="Data Report")
        
        return FileResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="report.xlsx"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.get("/sample")
async def get_sample():
    """Generate Excel from sample data."""
    try:
        data = get_sample_data()
        excel_file = create_formatted_excel(data, title="Sample Sales Report - Q4 2024")
        
        return FileResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="sample_sales_report.xlsx"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sample: {str(e)}")

@app.post("/api/generate")
async def generate_excel(input_data: DataInput):
    """API endpoint for programmatic Excel generation."""
    try:
        excel_file = create_formatted_excel(
            input_data.data,
            title=input_data.title
        )
        
        return FileResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="report.xlsx"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating Excel: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Excel Automation Demo...")
    print("📊 Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)
