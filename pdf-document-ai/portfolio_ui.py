"""
Shared portfolio demo UI — Leane brand + per-product themes.
Copied identically into each FastAPI subproject for independent Vercel deploys.
"""

from typing import Optional

THEMES = ("excel", "pdf", "inquiry")


def demo_badge(
    *,
    mock_ai: bool = False,
    openai_active: bool = False,
    sample_only: bool = False,
) -> str:
    if sample_only:
        return "Live demo · sample data"
    if openai_active:
        return "Live demo · OpenAI"
    if mock_ai:
        return "Live demo · mock AI"
    return "Live demo · sample data"


def sparkline_svg(points: str = "2,11 7,8 12,9 17,5 22,7 26,3") -> str:
    return f"""<svg class="kpi-spark" viewBox="0 0 28 14" aria-hidden="true">
  <polyline fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
    points="{points}" />
</svg>"""


PRODUCT_MARKS = {
    "excel": """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 3v18"/></svg>""",
    "pdf": """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
      <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v6h6"/></svg>""",
    "inquiry": """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
      <path d="M4 5h16v11H7l-3 3V5z"/><path d="M8 10h8M8 13h5"/></svg>""",
}


def dashboard_page(
    *,
    page_title: str,
    product_name: str,
    badge_text: str,
    subtitle: str,
    body_html: str,
    theme: str,
    notice_html: Optional[str] = None,
    extra_head: str = "",
) -> str:
    if theme not in THEMES:
        raise ValueError(f"Unknown theme: {theme}")

    notice_block = ""
    if notice_html:
        notice_block = f'<div class="inline-callout">{notice_html}</div>'

    mark = PRODUCT_MARKS[theme]

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
{THEME_CSS[theme]}
    </style>
    {extra_head}
</head>
<body class="app-body theme-{theme}">
    <header class="topbar">
        <div class="topbar-inner">
            <div class="topbar-start">
                <div class="brand-mark" aria-hidden="true">L</div>
                <div class="product-mark">{mark}</div>
                <div class="topbar-titles">
                    <span class="topbar-product">{product_name}</span>
                    <span class="topbar-badge">{badge_text}</span>
                </div>
            </div>
            <div class="topbar-end">
                <a class="topbar-link" href="https://github.com/Lt-wei/ai-solutions-portfolio" target="_blank" rel="noopener noreferrer">GitHub</a>
            </div>
        </div>
    </header>

    <main class="workspace">
        <p class="workspace-sub">{subtitle}</p>
        {notice_block}
        {body_html}
    </main>
</body>
</html>"""


demo_page = dashboard_page

BASE_CSS = """
:root {
    --font: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --text: #0f172a;
    --text-secondary: #475569;
    --text-muted: #64748b;
    --surface: #ffffff;
    --border: #e2e8f0;
    --border-subtle: #f1f5f9;
    --accent: #2563eb;
    --accent-hover: #1d4ed8;
    --accent-muted: #dbeafe;
    --accent-ring: rgba(37, 99, 235, 0.18);
    --success: #059669;
    --success-bg: #ecfdf5;
    --warning: #d97706;
    --warning-bg: #fffbeb;
    --radius: 10px;
    --radius-lg: 12px;
    --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
    --shadow-md: 0 4px 16px rgba(15, 23, 42, 0.06);
    --topbar-h: 52px;
    --text-sm: 0.8125rem;
    --text-base: 0.875rem;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

.app-body {
    font-family: var(--font);
    font-size: var(--text-base);
    color: var(--text);
    line-height: 1.45;
    min-height: 100vh;
    background-color: #f8fafc;
    background-image:
        radial-gradient(ellipse 120% 80% at 50% -30%, rgba(37, 99, 235, 0.06), transparent 55%),
        linear-gradient(rgba(148, 163, 184, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(148, 163, 184, 0.05) 1px, transparent 1px);
    background-size: auto, 24px 24px, 24px 24px;
    -webkit-font-smoothing: antialiased;
}

.topbar {
    position: sticky;
    top: 0;
    z-index: 50;
    height: var(--topbar-h);
    border-bottom: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
}

.topbar-inner {
    max-width: 1320px;
    margin: 0 auto;
    height: 100%;
    padding: 0 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}

.topbar-start {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
}

.brand-mark {
    width: 28px;
    height: 28px;
    border-radius: 7px;
    background: #0f172a;
    color: #f8fafc;
    font-weight: 700;
    font-size: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.product-mark {
    width: 28px;
    height: 28px;
    color: var(--accent);
    flex-shrink: 0;
}

.product-mark svg { width: 100%; height: 100%; }

.topbar-titles {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    min-width: 0;
}

.topbar-product {
    font-weight: 600;
    font-size: 0.9375rem;
    letter-spacing: -0.02em;
}

.topbar-badge {
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--accent);
    background: var(--accent-muted);
    border: 1px solid color-mix(in srgb, var(--accent) 25%, white);
    padding: 3px 8px;
    border-radius: 999px;
}

.topbar-link {
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-muted);
    text-decoration: none;
    padding: 6px 10px;
    border-radius: 6px;
}

.topbar-link:hover { color: var(--accent); background: var(--accent-muted); }

.workspace {
    max-width: 1320px;
    margin: 0 auto;
    padding: 18px 20px 40px;
}

.workspace-sub {
    font-size: var(--text-sm);
    color: var(--text-muted);
    margin-bottom: 14px;
    max-width: 52rem;
}

.inline-callout {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 9px 12px;
    margin-bottom: 14px;
    box-shadow: var(--shadow-sm);
}

.inline-callout code {
    font-size: 0.75rem;
    background: var(--border-subtle);
    padding: 1px 5px;
    border-radius: 4px;
}

.kpi-strip {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 14px;
}

@media (max-width: 900px) { .kpi-strip { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 480px) { .kpi-strip { grid-template-columns: 1fr; } }

.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 12px 14px;
    box-shadow: var(--shadow-sm);
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-height: 72px;
    transition: box-shadow 0.15s, border-color 0.15s;
}

.kpi-card:hover { box-shadow: var(--shadow-md); border-color: #cbd5e1; }

.kpi-label {
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-muted);
}

.kpi-row {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 8px;
}

.kpi-value {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
    color: var(--text);
}

.kpi-spark {
    width: 52px;
    height: 20px;
    color: var(--accent);
    opacity: 0.45;
    flex-shrink: 0;
}

.dashboard-grid {
    display: grid;
    grid-template-columns: minmax(280px, 380px) minmax(0, 1fr);
    gap: 14px;
    align-items: start;
}

@media (max-width: 959px) { .dashboard-grid { grid-template-columns: 1fr; } }

.data-table th { background: #f8fafc; }
.data-table tbody tr:nth-child(even) { background: #fafbfc; }
.data-table tbody tr:hover { background: #f1f5f9; }

.btn:focus-visible {
    outline: none;
    box-shadow: 0 0 0 3px var(--accent-ring);
}

.panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
}

.panel-head {
    padding: 12px 14px;
    border-bottom: 1px solid var(--border-subtle);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.panel-title { font-size: 0.8125rem; font-weight: 600; }
.panel-meta { font-size: 0.75rem; color: var(--text-muted); }
.panel-body { padding: 14px; }
.panel-body.flush { padding: 0; }

.upload-zone {
    border: 1px dashed color-mix(in srgb, var(--accent) 35%, #cbd5e1);
    border-radius: var(--radius);
    padding: 18px 14px;
    text-align: center;
    background: color-mix(in srgb, var(--accent-muted) 40%, white);
    transition: border-color 0.15s, background 0.15s;
}

.upload-zone.is-dragover,
.upload-zone:hover {
    border-color: var(--accent);
    background: var(--accent-muted);
}

.upload-icon { width: 34px; height: 34px; margin: 0 auto 8px; color: var(--text-muted); }
.upload-title { font-size: 0.8125rem; font-weight: 600; }
.upload-hint { font-size: 0.75rem; color: var(--text-muted); margin: 4px 0 10px; }

.btn-file {
    display: inline-flex;
    padding: 7px 14px;
    font-size: 0.8125rem;
    font-weight: 500;
    border: 1px solid var(--border);
    border-radius: 8px;
    cursor: pointer;
    background: var(--surface);
}

.btn-file input { position: absolute; width: 0; height: 0; opacity: 0; }

.file-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; justify-content: center; }
.file-chip {
    font-size: 0.75rem;
    padding: 4px 10px;
    border-radius: 999px;
    background: var(--border-subtle);
    border: 1px solid var(--border);
}

.field-label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin: 12px 0 6px;
}

textarea, input[type="text"], input[type="email"] {
    width: 100%;
    padding: 10px 11px;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: var(--text-sm);
    font-family: var(--font);
}

textarea { min-height: 100px; resize: vertical; }
textarea:focus, input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-ring);
}

.actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }

.btn {
    font-family: var(--font);
    font-size: 0.8125rem;
    font-weight: 600;
    padding: 9px 14px;
    border-radius: 8px;
    border: 1px solid transparent;
    cursor: pointer;
}

.btn-primary { background: var(--accent); color: #fff; flex: 1; min-width: 110px; }
.btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
.btn-secondary { background: var(--surface); border-color: var(--border); font-weight: 500; }
.btn-tertiary { background: transparent; color: var(--text-muted); border: none; font-weight: 500; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.table-wrap { overflow: auto; max-height: 460px; }

.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8125rem;
}

.data-table th, .data-table td {
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-subtle);
}

.data-table th {
    position: sticky;
    top: 0;
    z-index: 1;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-muted);
}

.data-table .num { font-variant-numeric: tabular-nums; text-align: right; }

.pill {
    display: inline-flex;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: capitalize;
}

.pill-success { background: var(--success-bg); color: #047857; border: 1px solid #a7f3d0; }
.pill-warning { background: var(--warning-bg); color: #b45309; border: 1px solid #fde68a; }
.pill-mock { background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }
.pill-neutral { background: var(--accent-muted); color: var(--accent); border: 1px solid color-mix(in srgb, var(--accent) 30%, white); }

.download-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 10px 14px;
    border-top: 1px solid var(--border-subtle);
    background: #fafbfc;
}

.download-link {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--accent);
    text-decoration: none;
    padding: 6px 10px;
    border-radius: 6px;
    border: 1px solid var(--accent-muted);
}

.toast-error {
    font-size: var(--text-sm);
    color: #b91c1c;
    padding: 10px 14px;
    margin: 12px;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
}

.panel-loading .table-wrap { opacity: 0.45; pointer-events: none; }

.progress-bar {
    height: 6px;
    background: var(--border-subtle);
    border-radius: 999px;
    overflow: hidden;
    min-width: 64px;
}

.progress-bar span {
    display: block;
    height: 100%;
    background: var(--accent);
    border-radius: 999px;
}

.progress-bar--doc span { background: #6366f1; }
"""

THEME_CSS = {
    "excel": """
/* Layout: sheet workbench — accent stays brand blue; teal only on clean hints */
.pipeline-stepper {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 14px;
    font-size: 0.75rem;
}

.pipeline-stepper .step {
    padding: 5px 10px;
    border-radius: 999px;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text-muted);
    font-weight: 500;
}

.pipeline-stepper .step.active {
    background: var(--accent-muted);
    border-color: #93c5fd;
    color: #1d4ed8;
    font-weight: 600;
}

.pipeline-stepper .step.done {
    background: #ecfdf5;
    border-color: #a7f3d0;
    color: #0f766e;
}

.pipeline-stepper .chev { color: #94a3b8; font-size: 0.65rem; }

.excel-layout {
    display: grid;
    grid-template-columns: minmax(0, 1.65fr) minmax(280px, 360px);
    gap: 14px;
    align-items: start;
}

@media (max-width: 959px) { .excel-layout { grid-template-columns: 1fr; } }

.theme-excel .data-table.sheet-grid th,
.theme-excel .data-table.sheet-grid td {
    border-right: 1px solid #e2e8f0;
    border-bottom: 1px solid #e2e8f0;
}

.theme-excel .data-table.sheet-grid th { background: #f8fafc; top: 0; }
.theme-excel .data-table.sheet-grid tbody tr.row-cleaned { background: #f0fdf4; }
.theme-excel .data-table.sheet-grid tbody tr.row-cleaned:hover { background: #ecfdf5; }

.col-chips { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
.col-chip {
    font-size: 0.625rem;
    padding: 2px 6px;
    border-radius: 4px;
    background: #e2e8f0;
    color: #475569;
    font-weight: 600;
    text-transform: uppercase;
}
""",
    "pdf": """
/* Document pipeline — indigo only on doc icons + confidence bars */
.pdf-kpi-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: #eef2ff;
    color: #6366f1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    vertical-align: middle;
    margin-right: 8px;
}

.pdf-kpi-icon svg { width: 18px; height: 18px; }

.pdf-kpi-row { display: flex; align-items: center; }

.pdf-layout {
    display: grid;
    grid-template-columns: minmax(240px, 300px) minmax(0, 1fr);
    gap: 14px;
    align-items: start;
}

@media (max-width: 959px) { .pdf-layout { grid-template-columns: 1fr; } }

.doc-stack { display: flex; flex-direction: column; gap: 10px; }

.doc-card {
    display: flex;
    gap: 10px;
    padding: 10px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: #fafafa;
    cursor: default;
}

.doc-card.active { border-color: var(--accent); background: #f8fafc; box-shadow: var(--shadow-sm); }

.doc-thumb {
    width: 48px;
    height: 62px;
    border-radius: 4px;
    background: linear-gradient(180deg, #fff 0%, #e2e8f0 100%);
    border: 1px solid #cbd5e1;
    position: relative;
    flex-shrink: 0;
}

.doc-thumb::after {
    content: '';
    position: absolute;
    top: 8px;
    left: 8px;
    right: 8px;
    height: 3px;
    background: #cbd5e1;
    box-shadow: 0 8px 0 #e2e8f0, 0 16px 0 #e2e8f0;
}

.doc-meta { min-width: 0; }
.doc-meta .name { font-size: 0.75rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.doc-meta .pages { font-size: 0.6875rem; color: var(--text-muted); }

.theme-pdf .fields-table td.conf-cell { min-width: 100px; }
""",
    "inquiry": """
/* Support desk — coral only on high-priority + subtle queue selection hint */
.inquiry-layout {
    display: grid;
    grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
    gap: 14px;
    align-items: stretch;
}

@media (max-width: 959px) { .inquiry-layout { grid-template-columns: 1fr; } }

.ticket-list { list-style: none; max-height: 320px; overflow: auto; }

.ticket-item {
    padding: 12px 14px;
    border-bottom: 1px solid var(--border-subtle);
    cursor: pointer;
    transition: background 0.12s;
}

.ticket-item:hover { background: #f8fafc; }
.ticket-item.selected {
    background: #f8fafc;
    border-left: 3px solid var(--accent);
    padding-left: 11px;
}

.ticket-item .row1 { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 4px; }
.ticket-item .tid { font-size: 0.75rem; font-weight: 700; color: var(--text); }
.ticket-item .snippet { font-size: 0.75rem; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.tag {
    font-size: 0.625rem;
    font-weight: 700;
    text-transform: uppercase;
    padding: 2px 6px;
    border-radius: 4px;
    letter-spacing: 0.03em;
}

.tag-sales { background: #dbeafe; color: #1d4ed8; }
.tag-billing { background: #fce7f3; color: #be185d; }
.tag-technical { background: #e0e7ff; color: #4338ca; }
.tag-support { background: #d1fae5; color: #047857; }
.tag-general { background: #f1f5f9; color: #475569; }

.priority-high, .priority-urgent {
    background: #fff7ed;
    color: #c2410c;
    border: 1px solid #fed7aa;
}

.priority-medium { background: var(--accent-muted); color: #1d4ed8; border: 1px solid #bfdbfe; }
.priority-low { background: #f1f5f9; color: #64748b; border: 1px solid var(--border); }

.reply-bubble {
    margin-top: 12px;
    padding: 14px 16px;
    background: #f8fafc;
    border: 1px solid var(--border);
    border-radius: 12px 12px 12px 4px;
    font-size: var(--text-sm);
    color: var(--text-secondary);
    line-height: 1.55;
}

.compose-box {
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px dashed var(--border);
}

.triage-header {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin-bottom: 12px;
}
""",
}

UPLOAD_ICON_SVG = """<svg class="upload-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true">
  <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"/>
</svg>"""

PDF_DOC_ICON = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/></svg>"""
