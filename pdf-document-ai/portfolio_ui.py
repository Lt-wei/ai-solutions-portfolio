"""
Shared portfolio demo UI — SaaS-style dashboard shell for Leane portfolio apps.
Copied identically into each FastAPI subproject for independent Vercel deploys.
"""

from typing import Optional


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


def dashboard_page(
    *,
    page_title: str,
    product_name: str,
    badge_text: str,
    subtitle: str,
    body_html: str,
    notice_html: Optional[str] = None,
    extra_head: str = "",
) -> str:
    notice_block = ""
    if notice_html:
        notice_block = f'<div class="inline-callout">{notice_html}</div>'

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
{DASHBOARD_CSS}
    </style>
    {extra_head}
</head>
<body class="app-body">
    <header class="topbar">
        <div class="topbar-inner">
            <div class="topbar-start">
                <div class="brand-mark" aria-hidden="true">L</div>
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


# Back-compat alias used during migration
demo_page = dashboard_page

DASHBOARD_CSS = """
:root {
    --font: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --text: #0f172a;
    --text-secondary: #475569;
    --text-muted: #64748b;
    --surface: #ffffff;
    --surface-raised: #ffffff;
    --border: #e2e8f0;
    --border-subtle: #f1f5f9;
    --accent: #2563eb;
    --accent-hover: #1d4ed8;
    --accent-muted: #dbeafe;
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
        radial-gradient(ellipse 120% 80% at 50% -30%, rgba(37, 99, 235, 0.07), transparent 55%),
        linear-gradient(rgba(148, 163, 184, 0.06) 1px, transparent 1px),
        linear-gradient(90deg, rgba(148, 163, 184, 0.06) 1px, transparent 1px);
    background-size: auto, 24px 24px, 24px 24px;
    -webkit-font-smoothing: antialiased;
}

.topbar {
    position: sticky;
    top: 0;
    z-index: 50;
    height: var(--topbar-h);
    border-bottom: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.88);
    backdrop-filter: blur(10px);
}

.topbar-inner {
    max-width: 1280px;
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
    gap: 12px;
    min-width: 0;
}

.brand-mark {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: linear-gradient(145deg, #1e293b, #334155);
    color: #f8fafc;
    font-weight: 700;
    font-size: 0.875rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

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
    color: #1d4ed8;
    background: var(--accent-muted);
    border: 1px solid #bfdbfe;
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
    border: 1px solid transparent;
}

.topbar-link:hover {
    color: var(--text);
    border-color: var(--border);
    background: var(--surface);
}

.workspace {
    max-width: 1280px;
    margin: 0 auto;
    padding: 20px 20px 40px;
}

.workspace-sub {
    font-size: var(--text-sm);
    color: var(--text-muted);
    margin-bottom: 16px;
    max-width: 52rem;
}

.inline-callout {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 10px 14px;
    margin-bottom: 16px;
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
    margin-bottom: 16px;
}

@media (max-width: 900px) {
    .kpi-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 480px) {
    .kpi-strip { grid-template-columns: 1fr; }
}

.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 12px 14px;
    box-shadow: var(--shadow-sm);
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-height: 76px;
    transition: box-shadow 0.15s, border-color 0.15s;
}

.kpi-card:hover {
    box-shadow: var(--shadow-md);
    border-color: #cbd5e1;
}

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
    font-size: 1.375rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
}

.kpi-spark {
    width: 56px;
    height: 22px;
    color: var(--accent);
    opacity: 0.55;
    flex-shrink: 0;
}

.dashboard-grid {
    display: grid;
    grid-template-columns: minmax(0, 380px) minmax(0, 1fr);
    gap: 16px;
    align-items: start;
}

@media (max-width: 959px) {
    .dashboard-grid { grid-template-columns: 1fr; }
}

.panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
}

.panel-head {
    padding: 14px 16px;
    border-bottom: 1px solid var(--border-subtle);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.panel-title {
    font-size: 0.8125rem;
    font-weight: 600;
    letter-spacing: -0.01em;
}

.panel-meta {
    font-size: 0.75rem;
    color: var(--text-muted);
}

.panel-body {
    padding: 16px;
}

.panel-body.flush {
    padding: 0;
}

.upload-zone {
    border: 1px dashed #cbd5e1;
    border-radius: var(--radius);
    padding: 20px 16px;
    text-align: center;
    background: #fafbfc;
    transition: border-color 0.15s, background 0.15s;
}

.upload-zone.is-dragover,
.upload-zone:hover {
    border-color: var(--accent);
    background: #f8fafc;
}

.upload-icon {
    width: 36px;
    height: 36px;
    margin: 0 auto 10px;
    color: var(--text-muted);
}

.upload-title {
    font-size: 0.8125rem;
    font-weight: 600;
    margin-bottom: 2px;
}

.upload-hint {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-bottom: 12px;
}

.btn-file {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 7px 14px;
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--text);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    cursor: pointer;
    transition: border-color 0.15s, box-shadow 0.15s;
}

.btn-file:hover {
    border-color: #94a3b8;
}

.btn-file input {
    position: absolute;
    width: 0;
    height: 0;
    opacity: 0;
}

.file-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 12px;
    justify-content: center;
}

.file-chip {
    font-size: 0.75rem;
    padding: 4px 10px;
    border-radius: 999px;
    background: var(--border-subtle);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.field-label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin: 14px 0 6px;
}

textarea,
input[type="text"],
input[type="email"] {
    width: 100%;
    padding: 10px 11px;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: var(--text-sm);
    font-family: var(--font);
    color: var(--text);
    background: var(--surface);
    transition: border-color 0.15s, box-shadow 0.15s;
}

textarea {
    min-height: 120px;
    resize: vertical;
    font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
    font-size: 0.75rem;
    line-height: 1.5;
}

textarea:focus,
input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18);
}

.actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
}

.btn {
    font-family: var(--font);
    font-size: 0.8125rem;
    font-weight: 600;
    padding: 9px 14px;
    border-radius: 8px;
    border: 1px solid transparent;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s, box-shadow 0.15s, transform 0.1s;
}

.btn:focus-visible {
    outline: none;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25);
}

.btn:active:not(:disabled) { transform: scale(0.99); }

.btn-primary {
    background: var(--accent);
    color: #fff;
    flex: 1;
    min-width: 120px;
}

.btn-primary:hover:not(:disabled) {
    background: var(--accent-hover);
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.28);
}

.btn-secondary {
    background: var(--surface);
    color: var(--text);
    border-color: var(--border);
    font-weight: 500;
}

.btn-secondary:hover:not(:disabled) {
    border-color: #94a3b8;
    background: #f8fafc;
}

.btn-tertiary {
    background: transparent;
    color: var(--text-muted);
    border: none;
    font-weight: 500;
    padding: 9px 8px;
}

.btn-tertiary:hover { color: var(--accent); }

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.table-wrap {
    overflow: auto;
    max-height: 420px;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8125rem;
}

.data-table th,
.data-table td {
    padding: 9px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border-subtle);
    white-space: nowrap;
}

.data-table th {
    position: sticky;
    top: 0;
    background: #f8fafc;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-muted);
    z-index: 1;
}

.data-table tbody tr:nth-child(even) { background: #fafbfc; }
.data-table tbody tr:hover { background: #f1f5f9; }

.data-table .num {
    font-variant-numeric: tabular-nums;
    text-align: right;
}

.pill {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: capitalize;
}

.pill-success { background: var(--success-bg); color: #047857; border: 1px solid #a7f3d0; }
.pill-warning { background: var(--warning-bg); color: #b45309; border: 1px solid #fde68a; }
.pill-mock { background: #f1f5f9; color: #475569; border: 1px solid var(--border); }
.pill-neutral { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }

.preview-status {
    display: flex;
    align-items: center;
    gap: 8px;
}

.result-card {
    padding: 14px 16px;
    border-bottom: 1px solid var(--border-subtle);
}

.result-card:last-child { border-bottom: none; }

.result-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin-bottom: 12px;
}

.result-kv label {
    display: block;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-muted);
    margin-bottom: 2px;
}

.result-kv span {
    font-size: 0.8125rem;
    font-weight: 500;
}

.reply-block {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    line-height: 1.5;
    padding: 10px 12px;
    background: #f8fafc;
    border-radius: 8px;
    border: 1px solid var(--border-subtle);
}

.download-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px 16px;
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
    background: #fff;
}

.download-link:hover {
    background: var(--accent-muted);
}

.skeleton {
    background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
    background-size: 200% 100%;
    animation: shimmer 1.1s ease-in-out infinite;
    border-radius: 6px;
    height: 12px;
    margin: 8px 0;
}

.skeleton-row { height: 36px; margin: 0; border-radius: 0; }

@keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

.panel-loading .table-wrap { opacity: 0.45; pointer-events: none; }

.toast-error {
    font-size: var(--text-sm);
    color: #b91c1c;
    padding: 10px 14px;
    margin: 12px 16px;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
}

.bar-chart {
    display: flex;
    align-items: flex-end;
    gap: 3px;
    height: 22px;
}

.bar-chart span {
    flex: 1;
    background: var(--accent);
    opacity: 0.35;
    border-radius: 2px 2px 0 0;
    min-width: 4px;
}
"""

UPLOAD_ICON_SVG = """<svg class="upload-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true">
  <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"/>
</svg>"""
