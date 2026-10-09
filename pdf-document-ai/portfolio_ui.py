"""
Shared portfolio demo UI — Leane branding, consistent layout and tokens.
Copied to each FastAPI subproject for independent Vercel deploys.
"""

from typing import Optional


def demo_badge(
    *,
    mock_ai: bool = False,
    openai_active: bool = False,
    sample_only: bool = False,
) -> str:
    """Return badge label text for the demo header."""
    if sample_only:
        return "Live Demo · sample data"
    if openai_active:
        return "Live Demo · OpenAI connected"
    if mock_ai:
        return "Live Demo · Mock AI / sample data"
    return "Live Demo · sample data"


def demo_page(
    *,
    page_title: str,
    product_title: str,
    value_prop: str,
    badge_text: str,
    main_html: str,
    pipeline_html: Optional[str] = None,
    notice_html: Optional[str] = None,
    extra_head: str = "",
) -> str:
    """Wrap demo content in the shared page shell."""
    pipeline_block = ""
    if pipeline_html:
        pipeline_block = f'<p class="pipeline-note">{pipeline_html}</p>'

    notice_block = ""
    if notice_html:
        notice_block = f'<div class="demo-notice">{notice_html}</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{page_title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
{BASE_CSS}
    </style>
    {extra_head}
</head>
<body>
    <div class="page">
        <header class="site-header">
            <div class="site-header-inner">
                <span class="brand">Leane</span>
                <span class="brand-sep">·</span>
                <span class="brand-tag">Portfolio demo</span>
            </div>
        </header>

        <main class="main">
            <article class="card">
                <div class="card-head">
                    <span class="badge">{badge_text}</span>
                    <h1>{product_title}</h1>
                    <p class="value-prop">{value_prop}</p>
                    {pipeline_block}
                    {notice_block}
                </div>
                <div class="card-body">
                    {main_html}
                </div>
            </article>
        </main>

        <footer class="site-footer">
            <a href="https://github.com/Lt-wei/ai-solutions-portfolio" target="_blank" rel="noopener noreferrer">View source on GitHub</a>
        </footer>
    </div>
</body>
</html>"""


BASE_CSS = """
:root {
    --bg: #f3f4f6;
    --surface: #ffffff;
    --text: #111827;
    --text-muted: #6b7280;
    --border: #e5e7eb;
    --border-strong: #d1d5db;
    --accent: #2563eb;
    --accent-hover: #1d4ed8;
    --accent-soft: #eff6ff;
    --success-bg: #ecfdf5;
    --success-border: #10b981;
    --error-bg: #fef2f2;
    --error-border: #ef4444;
    --radius: 12px;
    --radius-sm: 8px;
    --shadow: 0 1px 2px rgba(0,0,0,0.04), 0 8px 24px rgba(17,24,39,0.06);
    --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: var(--font);
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
}

.page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.site-header {
    border-bottom: 1px solid var(--border);
    background: var(--surface);
}

.site-header-inner {
    max-width: 720px;
    margin: 0 auto;
    padding: 14px 20px;
    font-size: 13px;
    color: var(--text-muted);
}

.brand {
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.02em;
}

.brand-sep { margin: 0 6px; opacity: 0.5; }

.brand-tag { font-weight: 500; }

.main {
    flex: 1;
    padding: 32px 20px 48px;
}

.card {
    max-width: 720px;
    margin: 0 auto;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    overflow: hidden;
}

.card-head {
    padding: 28px 28px 0;
}

.card-body {
    padding: 24px 28px 32px;
}

.badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #1e40af;
    background: var(--accent-soft);
    border: 1px solid #bfdbfe;
    padding: 5px 10px;
    border-radius: 999px;
    margin-bottom: 16px;
}

h1 {
    font-size: 1.625rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1.25;
    margin-bottom: 8px;
}

.value-prop {
    font-size: 0.9375rem;
    color: var(--text-muted);
    max-width: 42em;
}

.pipeline-note {
    margin-top: 16px;
    font-size: 0.8125rem;
    color: var(--text-muted);
    padding: 12px 14px;
    background: #f9fafb;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    line-height: 1.45;
}

.demo-notice {
    margin-top: 12px;
    font-size: 0.8125rem;
    color: #92400e;
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: var(--radius-sm);
    padding: 12px 14px;
    line-height: 1.45;
}

.section-label {
    display: block;
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 8px;
}

.upload-zone {
    border: 1px dashed var(--border-strong);
    border-radius: var(--radius);
    padding: 28px 20px;
    text-align: center;
    background: #fafafa;
    transition: border-color 0.15s, background 0.15s;
    margin-bottom: 20px;
}

.upload-zone:hover,
.upload-zone.is-dragover {
    border-color: var(--accent);
    background: var(--accent-soft);
}

.upload-icon {
    width: 40px;
    height: 40px;
    margin: 0 auto 12px;
    color: var(--text-muted);
}

.upload-title {
    font-size: 0.9375rem;
    font-weight: 600;
    margin-bottom: 4px;
}

.upload-hint {
    font-size: 0.8125rem;
    color: var(--text-muted);
    margin-bottom: 16px;
}

.btn-file {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 8px 16px;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text);
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: border-color 0.15s, box-shadow 0.15s;
}

.btn-file:hover {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.btn-file input[type="file"] {
    position: absolute;
    width: 0;
    height: 0;
    opacity: 0;
    overflow: hidden;
}

.file-selected {
    margin-top: 12px;
    font-size: 0.8125rem;
    color: var(--text-muted);
    word-break: break-all;
}

textarea,
input[type="text"],
input[type="email"] {
    width: 100%;
    padding: 11px 12px;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    font-size: 0.875rem;
    font-family: var(--font);
    color: var(--text);
    transition: border-color 0.15s, box-shadow 0.15s;
}

textarea {
    min-height: 140px;
    resize: vertical;
    font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
    font-size: 0.8125rem;
    line-height: 1.5;
}

textarea:focus,
input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

.form-group { margin-bottom: 20px; }

.actions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 8px;
}

.btn {
    flex: 1;
    min-width: 140px;
    padding: 12px 20px;
    font-size: 0.9375rem;
    font-weight: 600;
    font-family: var(--font);
    border-radius: var(--radius-sm);
    border: none;
    cursor: pointer;
    transition: background 0.15s, box-shadow 0.15s, transform 0.1s;
}

.btn:active:not(:disabled) { transform: scale(0.99); }

.btn-primary {
    background: var(--accent);
    color: #fff;
}

.btn-primary:hover:not(:disabled) {
    background: var(--accent-hover);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
}

.btn-secondary {
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--border-strong);
    font-weight: 500;
}

.btn-secondary:hover:not(:disabled) {
    border-color: var(--text-muted);
    background: #f9fafb;
}

.btn:disabled {
    opacity: 0.55;
    cursor: not-allowed;
}

.loader {
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    width: 32px;
    height: 32px;
    animation: spin 0.7s linear infinite;
    margin: 24px auto;
    display: none;
}

@keyframes spin { to { transform: rotate(360deg); } }

#result {
    margin-top: 24px;
    padding: 20px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
    background: #f9fafb;
    display: none;
    font-size: 0.875rem;
}

#result.success {
    background: var(--success-bg);
    border-color: #a7f3d0;
}

#result.error {
    background: var(--error-bg);
    border-color: #fecaca;
}

.result-title {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 12px;
}

.result-title.success { color: #047857; }
.result-title.error { color: #b91c1c; }

pre.result-json {
    background: #1f2937;
    color: #e5e7eb;
    padding: 14px;
    border-radius: var(--radius-sm);
    overflow-x: auto;
    margin-top: 12px;
    font-size: 0.75rem;
    line-height: 1.45;
}

.download-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 16px;
}

.download-link {
    display: inline-flex;
    align-items: center;
    padding: 9px 16px;
    font-size: 0.875rem;
    font-weight: 600;
    color: #fff;
    background: #059669;
    text-decoration: none;
    border-radius: var(--radius-sm);
    transition: background 0.15s;
}

.download-link:hover { background: #047857; }

.download-link.alt {
    background: var(--accent);
}

.download-link.alt:hover { background: var(--accent-hover); }

table.data-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 16px;
    font-size: 0.8125rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    overflow: hidden;
}

.data-table th,
.data-table td {
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid var(--border);
}

.data-table th {
    background: #f9fafb;
    font-weight: 600;
    color: var(--text-muted);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.data-table tr:last-child td { border-bottom: none; }

.result-field {
    margin: 10px 0;
    padding: 12px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
}

.result-label {
    font-weight: 600;
    color: var(--text-muted);
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.result-value {
    color: var(--text);
    margin-top: 4px;
    font-size: 0.9375rem;
}

.meta-line {
    margin-top: 12px;
    color: var(--text-muted);
    font-size: 0.8125rem;
}

.link-quiet {
    display: inline-block;
    margin-top: 24px;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--accent);
    text-decoration: none;
}

.link-quiet:hover { text-decoration: underline; }

.site-footer {
    text-align: center;
    padding: 20px;
    font-size: 0.8125rem;
    color: var(--text-muted);
    border-top: 1px solid var(--border);
    background: var(--surface);
}

.site-footer a {
    color: var(--text-muted);
    text-decoration: none;
    font-weight: 500;
}

.site-footer a:hover {
    color: var(--accent);
}
"""

# Shared inline SVG for upload zones
UPLOAD_ICON_SVG = """<svg class="upload-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true">
  <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"/>
</svg>"""
