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
from portfolio_ui import dashboard_page, demo_badge, UPLOAD_ICON_SVG, sparkline_svg

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


def _preview_payload(df: pd.DataFrame, limit: int = 10) -> dict:
    """First rows for dashboard preview (additive API field)."""
    slice_df = df.head(limit)
    return {
        "columns": [str(c) for c in slice_df.columns],
        "rows": slice_df.fillna("").astype(str).to_dict(orient="records"),
    }


def _duplicates_removed(report: dict) -> int:
    for step in report.get("steps", []):
        if step.get("step") == "deduplicate":
            return int(step.get("duplicates_removed", 0))
    return 0


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI"""
    spark = sparkline_svg()
    body = f"""
        <section class="kpi-strip" aria-label="Pipeline metrics">
            <div class="kpi-card"><span class="kpi-label">Total rows</span><div class="kpi-row"><span class="kpi-value" id="kpiTotal">10,248</span>{spark}</div></div>
            <div class="kpi-card"><span class="kpi-label">Cleaned</span><div class="kpi-row"><span class="kpi-value" id="kpiCleaned">9,892</span>{sparkline_svg("2,10 8,7 14,8 20,5 26,6")}</div></div>
            <div class="kpi-card"><span class="kpi-label">Duplicates removed</span><div class="kpi-row"><span class="kpi-value" id="kpiDupes">312</span>{sparkline_svg("2,12 9,9 16,10 22,4 26,5")}</div></div>
            <div class="kpi-card"><span class="kpi-label">Columns</span><div class="kpi-row"><span class="kpi-value" id="kpiCols">12</span><div class="bar-chart" aria-hidden="true"><span style="height:40%"></span><span style="height:70%"></span><span style="height:55%"></span><span style="height:90%"></span><span style="height:65%"></span></div></div></div>
        </section>

        <div class="dashboard-grid">
            <section class="panel" aria-label="Controls">
                <div class="panel-head"><span class="panel-title">Import & rules</span><span class="panel-meta">Max 10MB</span></div>
                <div class="panel-body">
                    <form id="uploadForm" enctype="multipart/form-data">
                        <div class="upload-zone" id="uploadZone">
                            {UPLOAD_ICON_SVG}
                            <p class="upload-title">Drop Excel or CSV</p>
                            <p class="upload-hint">or browse a single workbook</p>
                            <label class="btn-file"><input type="file" name="file" id="fileInput" accept=".xlsx,.xls,.csv">Browse files</label>
                            <div class="file-chips" id="fileChips" aria-live="polite"></div>
                        </div>
                        <label class="field-label" for="rulesInput">Processing rules (JSON)</label>
                        <textarea id="rulesInput" name="rules" placeholder='{{"dedupe_columns":["email"]}}'></textarea>
                        <div class="actions">
                            <button type="submit" class="btn btn-primary" id="submitBtn">Run pipeline</button>
                            <button type="button" class="btn btn-secondary" id="sampleBtn">Load sample</button>
                        </div>
                        <button type="button" class="btn btn-tertiary" id="resetPreviewBtn">Reset preview</button>
                    </form>
                </div>
            </section>

            <section class="panel" id="previewPanel" aria-label="Live preview">
                <div class="panel-head">
                    <div class="preview-status">
                        <span class="panel-title">Output preview</span>
                        <span class="pill pill-warning" id="previewPill">Sample</span>
                    </div>
                    <span class="panel-meta" id="previewMeta">Showing illustrative rows</span>
                </div>
                <div class="panel-body flush panel-loading" id="previewBody">
                    <div class="table-wrap">
                        <table class="data-table" id="previewTable">
                            <thead id="previewHead"></thead>
                            <tbody id="previewBodyRows"></tbody>
                        </table>
                    </div>
                </div>
                <div class="download-bar" id="downloadBar" hidden>
                    <a href="#" class="download-link" id="dlExcel" download>Export Excel</a>
                    <a href="#" class="download-link" id="dlReport" download>Processing report</a>
                </div>
                <div id="errorToast" class="toast-error" hidden></div>
            </section>
        </div>

        <script>
        (function() {{
            const SEED = {{
                columns: ['customer_id', 'name', 'email', 'region', 'status'],
                rows: [
                    {{ customer_id: 'C-1042', name: 'Ava Chen', email: 'ava.chen@acme.io', region: 'West', status: 'Active' }},
                    {{ customer_id: 'C-1043', name: 'Marcus Lee', email: 'marcus.lee@northwind.co', region: 'East', status: 'Active' }},
                    {{ customer_id: 'C-1044', name: 'Sofia Patel', email: 'sofia@brightlabs.com', region: 'EU', status: 'Review' }},
                    {{ customer_id: 'C-1045', name: 'James Ortiz', email: 'j.ortiz@harbor.dev', region: 'West', status: 'Active' }},
                    {{ customer_id: 'C-1046', name: 'Emily Ross', email: 'emily.ross@stripe.example', region: 'East', status: 'Churn risk' }},
                ]
            }};

            const fileInput = document.getElementById('fileInput');
            const fileChips = document.getElementById('fileChips');
            const zone = document.getElementById('uploadZone');
            const previewPanel = document.getElementById('previewPanel');
            const previewPill = document.getElementById('previewPill');
            const previewMeta = document.getElementById('previewMeta');
            const downloadBar = document.getElementById('downloadBar');
            const errorToast = document.getElementById('errorToast');

            function renderTable(columns, rows) {{
                document.getElementById('previewHead').innerHTML =
                    '<tr>' + columns.map(c => `<th>${{c}}</th>`).join('') + '</tr>';
                document.getElementById('previewBodyRows').innerHTML = rows.map(row =>
                    '<tr>' + columns.map(c => `<td>${{row[c] ?? ''}}</td>`).join('') + '</tr>'
                ).join('');
            }}

            function setKpis(total, cleaned, dupes, cols) {{
                const fmt = n => Number(n).toLocaleString();
                document.getElementById('kpiTotal').textContent = fmt(total);
                document.getElementById('kpiCleaned').textContent = fmt(cleaned);
                document.getElementById('kpiDupes').textContent = fmt(dupes);
                document.getElementById('kpiCols').textContent = fmt(cols);
            }}

            function showSeed() {{
                renderTable(SEED.columns, SEED.rows);
                setKpis(10248, 9892, 312, 12);
                previewPill.className = 'pill pill-warning';
                previewPill.textContent = 'Sample';
                previewMeta.textContent = 'Illustrative cleaned rows — run pipeline for live data';
                downloadBar.hidden = true;
                errorToast.hidden = true;
            }}

            function setLoading(on) {{
                previewPanel.classList.toggle('panel-loading', on);
                document.getElementById('submitBtn').disabled = on;
                document.getElementById('sampleBtn').disabled = on;
            }}

            function applyResult(data) {{
                const report = data.report;
                setKpis(report.original_rows, report.final_rows, data.duplicates_removed ?? 0, report.final_columns);
                if (data.preview) renderTable(data.preview.columns, data.preview.rows);
                previewPill.className = 'pill pill-success';
                previewPill.textContent = 'Success';
                previewMeta.textContent = `Processed in ${{data.processing_time.toFixed(2)}}s · ${{report.final_rows}} rows export-ready`;
                document.getElementById('dlExcel').href = '/download/' + data.output_file;
                document.getElementById('dlReport').href = '/download/' + data.report_file;
                downloadBar.hidden = false;
                errorToast.hidden = true;
            }}

            fileInput.addEventListener('change', () => {{
                fileChips.innerHTML = '';
                const f = fileInput.files[0];
                if (f) fileChips.innerHTML = `<span class="file-chip">${{f.name}}</span>`;
            }});

            ['dragenter','dragover'].forEach(ev => zone.addEventListener(ev, e => {{ e.preventDefault(); zone.classList.add('is-dragover'); }}));
            ['dragleave','drop'].forEach(ev => zone.addEventListener(ev, e => {{ e.preventDefault(); zone.classList.remove('is-dragover'); }}));
            zone.addEventListener('drop', e => {{
                if (e.dataTransfer.files.length) {{
                    fileInput.files = e.dataTransfer.files;
                    fileInput.dispatchEvent(new Event('change'));
                }}
            }});

            async function run(url, options) {{
                setLoading(true);
                try {{
                    const response = await fetch(url, options);
                    const data = await response.json();
                    if (!response.ok) throw new Error(data.detail || 'Processing failed');
                    applyResult(data);
                }} catch (err) {{
                    errorToast.textContent = err.message;
                    errorToast.hidden = false;
                }} finally {{
                    setLoading(false);
                }}
            }}

            document.getElementById('uploadForm').addEventListener('submit', e => {{
                e.preventDefault();
                if (!fileInput.files[0]) {{ alert('Choose a file first.'); return; }}
                if (fileInput.files[0].size > 10 * 1024 * 1024) {{ alert('File exceeds 10MB.'); return; }}
                const fd = new FormData();
                fd.append('file', fileInput.files[0]);
                const rules = document.getElementById('rulesInput').value.trim();
                if (rules) fd.append('rules', rules);
                run('/process', {{ method: 'POST', body: fd }});
            }});

            document.getElementById('sampleBtn').addEventListener('click', () => run('/sample', {{}}));
            document.getElementById('resetPreviewBtn').addEventListener('click', showSeed);
            showSeed();
        }})();
        </script>
    """

    return dashboard_page(
        page_title="Excel Data Processing — Leane",
        product_name="Excel Data Processing",
        badge_text=demo_badge(sample_only=True),
        subtitle="Clean, dedupe, and transform spreadsheet data with configurable rules and export-ready output.",
        body_html=body,
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
            "processing_time": processing_time,
            "preview": _preview_payload(processed_df),
            "duplicates_removed": _duplicates_removed(report),
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
            "processing_time": processing_time,
            "preview": _preview_payload(processed_df),
            "duplicates_removed": _duplicates_removed(report),
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
