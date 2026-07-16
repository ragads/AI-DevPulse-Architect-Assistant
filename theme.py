# theme.py
"""Clean modern SaaS theme.

All visual tokens live in TOKENS. The stylesheet is emitted once and every rule
reads from a CSS custom property, so light and dark come from the same source.

mode="auto"  -> light :root + a prefers-color-scheme:dark override (follows OS)
mode="light" -> light :root only
mode="dark"  -> dark :root only
"""
import streamlit as st

TOKENS = {
    "light": {
        "bg": "#F7F8FA",
        "surface": "#FFFFFF",
        "surface-2": "#F1F5F9",
        "border": "#E2E8F0",
        "border-strong": "#CBD5E1",
        "text-primary": "#0F172A",
        "text-secondary": "#475569",
        "text-muted": "#94A3B8",
        "accent": "#4F46E5",
        "accent-hover": "#4338CA",
        "accent-soft": "#EEF2FF",
        "focus-ring": "rgba(79,70,229,0.35)",
        # severity / semantic
        "critical": "#DC2626",
        "critical-soft": "#FEE2E2",
        "high": "#EA580C",
        "high-soft": "#FFEDD5",
        "medium": "#D97706",
        "medium-soft": "#FEF3C7",
        "low": "#2563EB",
        "low-soft": "#DBEAFE",
        "info": "#475569",
        "info-soft": "#F1F5F9",
        "success": "#16A34A",
        "success-soft": "#DCFCE7",
        # elevation
        "shadow-xs": "0 1px 2px rgba(16,24,40,.05)",
        "shadow-sm": "0 1px 3px rgba(16,24,40,.06), 0 1px 2px rgba(16,24,40,.04)",
        "shadow-md": "0 4px 12px rgba(16,24,40,.08)",
        "shadow-lg": "0 12px 24px rgba(16,24,40,.10)",
    },
    "dark": {
        "bg": "#0B0F1A",
        "surface": "#131926",
        "surface-2": "#1A2233",
        "border": "#232B3D",
        "border-strong": "#33405A",
        "text-primary": "#E6EAF2",
        "text-secondary": "#9BA6BC",
        "text-muted": "#6B7688",
        "accent": "#6366F1",
        "accent-hover": "#818CF8",
        "accent-soft": "rgba(99,102,241,0.14)",
        "focus-ring": "rgba(99,102,241,0.45)",
        "critical": "#F87171",
        "critical-soft": "rgba(248,113,113,0.14)",
        "high": "#FB923C",
        "high-soft": "rgba(251,146,60,0.14)",
        "medium": "#FBBF24",
        "medium-soft": "rgba(251,191,36,0.14)",
        "low": "#60A5FA",
        "low-soft": "rgba(96,165,250,0.14)",
        "info": "#94A3B8",
        "info-soft": "rgba(148,163,184,0.14)",
        "success": "#4ADE80",
        "success-soft": "rgba(74,222,128,0.14)",
        "shadow-xs": "0 1px 2px rgba(0,0,0,.3)",
        "shadow-sm": "0 1px 2px rgba(0,0,0,.4)",
        "shadow-md": "0 6px 16px rgba(0,0,0,.5)",
        "shadow-lg": "0 16px 32px rgba(0,0,0,.55)",
    },
}

# Non-color tokens are theme-independent.
STATIC_TOKENS = {
    "radius-sm": "6px",
    "radius-md": "10px",
    "radius-lg": "14px",
    "radius-full": "9999px",
    "font-ui": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    "font-mono": "'JetBrains Mono', 'SFMono-Regular', Consolas, monospace",
}

SEVERITY_LEVELS = ("critical", "high", "medium", "low", "info", "success")


def _vars(mode: str) -> str:
    """Render a token dict as CSS custom property declarations."""
    pairs = {**STATIC_TOKENS, **TOKENS[mode]}
    return "\n".join(f"    --{k}: {v};" for k, v in pairs.items())


def _token_layer(mode: str) -> str:
    if mode == "light":
        return f":root {{\n{_vars('light')}\n}}"
    if mode == "dark":
        return f":root {{\n{_vars('dark')}\n}}"
    # auto: light default + OS dark override
    return (
        f":root {{\n{_vars('light')}\n}}\n\n"
        f"@media (prefers-color-scheme: dark) {{\n"
        f"  :root {{\n{_vars('dark')}\n  }}\n}}"
    )


_STYLES = """
/* ── Base ─────────────────────────────────────────────── */
.stApp {
    background: var(--bg) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-ui) !important;
}
.block-container {
    max-width: 1160px !important;
    padding-top: 1.25rem !important;
    padding-bottom: 3rem !important;
}
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="stMainMenuButton"], [data-testid="stToolbarActions"],
[data-testid="stAppDeployButton"], [data-testid="stAppViewBlockSpacer"] {
    display: none !important;
}
/* Keep the header AND toolbar mounted. Streamlit renders the sidebar expand
   button (stExpandSidebarButton) inside stToolbar; display:none-ing the toolbar
   makes it 0x0, so a collapsed sidebar can never be reopened. Collapse the
   header to zero height instead and let the expand button escape via position:fixed. */
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
    overflow: visible !important;
}
[data-testid="stToolbar"] {
    background: transparent !important;
    padding: 0 !important;
    right: auto !important;
}
body:has(section[data-testid="stSidebar"][aria-expanded="false"])
    [data-testid="stExpandSidebarButton"]:hover { background: var(--surface-2) !important; }
/* The glyph is a Material Symbols ligature, but this button sits in <header>,
   outside .stApp, so it falls back to Inter and renders as an empty box. Draw
   the chevron with CSS instead — no icon-font dependency. */
[data-testid="stExpandSidebarButton"] span { display: none !important; }
[data-testid="stExpandSidebarButton"]::after {
    content: "»";
    color: var(--text-secondary);
    font-size: 17px; font-weight: 700; line-height: 1;
}
/* Streamlit reserves a tall empty header row for the collapse control. Kill that
   space so the logo sits at the very top, and ride the collapse toggle on the
   sidebar's right border line instead of floating above the logo. */
[data-testid="stSidebarHeader"] {
    height: 0 !important; min-height: 0 !important;
    padding: 0 !important; margin: 0 !important;
}
[data-testid="stSidebarCollapseButton"] {
    position: absolute !important;
    top: 14px !important;
    right: -11px !important;    /* offsets the sidebar's inner padding so the… */
    transform: translateX(50%) !important;   /* …button centers on the border line */
    z-index: 1200 !important;
    visibility: visible !important; opacity: 1 !important;
}
[data-testid="stSidebarCollapseButton"] button {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    width: 26px !important; height: 26px !important; min-height: 26px !important;
    padding: 0 !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stSidebarCollapseButton"] button:hover { background: var(--surface-2) !important; }
[data-testid="stSidebarCollapseButton"] button span { display: none !important; }
[data-testid="stSidebarCollapseButton"] button::after {
    content: "«"; color: var(--text-secondary);
    font-size: 15px; font-weight: 700; line-height: 1;
}
[data-testid="stSidebarCollapseButton"] button:hover::after { color: var(--text-primary); }

/* Trim the dead space Streamlit leaves above the first element. */
h1 { margin-top: 0 !important; padding-top: 0 !important; }
.block-container > div:first-child { padding-top: 0 !important; }
div[data-testid="stVerticalBlock"] { gap: 0.6rem; }

/* ── Typography ───────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-ui) !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}
h1 { font-size: 1.75rem !important; font-weight: 700 !important;
     letter-spacing: -0.02em !important; line-height: 1.2 !important; }
h2 { font-size: 1.25rem !important; letter-spacing: -0.01em !important; }
h3 { font-size: 1.0625rem !important; }
p, li, span, label, div[data-testid="stMarkdownContainer"] p {
    color: var(--text-secondary);
    font-size: 0.9375rem;
    line-height: 1.6;
}
.stCaption, [data-testid="stCaptionContainer"] p {
    color: var(--text-muted) !important;
    font-size: 0.8125rem !important;
}
.dp-overline {
    display: block;
    font-size: 0.6875rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--text-muted);
    line-height: 1.5; margin: 8px 0 12px;
}
.dp-subtitle { color: var(--text-muted); font-size: 0.8125rem; margin: 2px 0 0; }

/* ── Sidebar ──────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding-top: 8px; }

/* logo lockup */
.dp-logo-wrap {
    display: flex; align-items: center; gap: 10px; padding: 2px 6px 14px;
}
.dp-logo-mark { flex: 0 0 auto; line-height: 0; }
.dp-logo-text {
    font-size: 0.95rem; font-weight: 650; letter-spacing: -0.01em;
    color: var(--text-primary); white-space: nowrap;
}

/* ── Collapsed = a slim rail that keeps the logo, instead of vanishing ── */
section[data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 60px !important; max-width: 60px !important; width: 60px !important;
    transform: none !important; visibility: visible !important; overflow: hidden !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] .dp-logo-text,
section[data-testid="stSidebar"][aria-expanded="false"] div[role="radiogroup"],
section[data-testid="stSidebar"][aria-expanded="false"] hr,
section[data-testid="stSidebar"][aria-expanded="false"] .dp-sidebar-foot,
section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarCollapseButton"] {
    display: none !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] .dp-logo-wrap {
    justify-content: center !important;
    padding: 46px 0 6px !important;   /* clear the pinned expand button above */
}

/* The expand (») button shows ONLY when collapsed, pinned onto the rail — not
   floating in the empty content area. The sidebar sits at z-index 999991 and the
   button lives in the header (999990), so without lifting the header above the
   sidebar the rail covers the button and it can't be clicked. */
body:has(section[data-testid="stSidebar"][aria-expanded="false"])
    header[data-testid="stHeader"] { z-index: 999999 !important; }
[data-testid="stExpandSidebarButton"] { display: none !important; }
body:has(section[data-testid="stSidebar"][aria-expanded="false"])
    [data-testid="stExpandSidebarButton"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 12px !important; left: 13px !important;
    z-index: 1000 !important;
    width: 34px !important; height: 34px !important;
    align-items: center !important; justify-content: center !important;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* radio-as-nav.
   DOM per option: <label data-testid="stRadioOption" data-selected="true|false">
                     <span sr-only><input></span>
                     <div><div><div.circle/><div data-testid="stMarkdownContainer"/></div></div>
   The circle is the div immediately preceding the markdown container. */
section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 2px; }
section[data-testid="stSidebar"] label[data-testid="stRadioOption"]
    div:has(+ div[data-testid="stMarkdownContainer"]) {
    display: none !important;
}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] {
    display: flex; align-items: center; width: 100%;
    padding: 10px 12px; margin: 0;
    border-radius: var(--radius-md);
    cursor: pointer; transition: background .12s ease, color .12s ease;
    border-left: 3px solid transparent;
}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] p {
    font-size: 0.875rem !important; font-weight: 500 !important;
    color: var(--text-secondary) !important; margin: 0 !important;
}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"]:hover {
    background: var(--surface-2);
}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] {
    background: var(--accent-soft);
    border-left: 3px solid var(--accent);
}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] p {
    color: var(--accent) !important; font-weight: 600 !important;
}

/* ── Buttons ──────────────────────────────────────────── */
button[data-testid="stBaseButton-primary"] {
    background: var(--accent) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--accent) !important;
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important; font-size: 0.9rem !important;
    padding: 8px 16px !important;
    box-shadow: var(--shadow-xs) !important;
    transition: background .12s ease, box-shadow .12s ease;
}
button[data-testid="stBaseButton-primary"]:hover {
    background: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
    box-shadow: var(--shadow-sm) !important;
}
button[data-testid="stBaseButton-secondary"] {
    background: var(--surface) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    font-weight: 500 !important; font-size: 0.9rem !important;
    padding: 8px 16px !important;
    transition: background .12s ease, border-color .12s ease;
}
button[data-testid="stBaseButton-secondary"]:hover {
    background: var(--surface-2) !important;
    border-color: var(--border-strong) !important;
    color: var(--text-primary) !important;
}
button:focus-visible { outline: 3px solid var(--focus-ring) !important; outline-offset: 1px; }

/* Streamlit wraps button labels in <p>, which would otherwise inherit the
   global paragraph color and wash out the label. */
button[data-testid="stBaseButton-primary"] p,
button[data-testid="stBaseButton-primary"] span,
button[data-testid="stBaseButton-primaryFormSubmit"] p {
    color: #FFFFFF !important; font-weight: 600 !important;
}
button[data-testid="stBaseButton-secondary"] p,
button[data-testid="stBaseButton-secondary"] span,
button[data-testid="stBaseButton-secondaryFormSubmit"] p,
button[data-testid="stBaseButton-minimal"] p {
    color: var(--text-primary) !important;
}
button[disabled] p, button[disabled] span { color: var(--text-muted) !important; }
div[data-testid="stDownloadButton"] button p { color: var(--text-primary) !important; }

/* ── Inputs ───────────────────────────────────────────── */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background: var(--surface) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    font-size: 0.9rem !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: var(--text-muted) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--focus-ring) !important;
}
/* Selectbox / multiselect. The visible control is div[role="group"]; without this
   it keeps config.toml's light secondaryBackgroundColor even in dark mode. */
div[data-testid="stSelectbox"] div[role="group"],
div[data-testid="stMultiSelect"] div[role="group"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
}
div[data-testid="stSelectbox"] div[role="group"]:focus-within,
div[data-testid="stMultiSelect"] div[role="group"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--focus-ring) !important;
}
div[data-testid="stSelectbox"] input,
div[data-testid="stMultiSelect"] input,
div[data-testid="stSelectbox"] div[role="group"] > div {
    color: var(--text-primary) !important;
    background: transparent !important;
}
div[data-testid="stSelectbox"] svg,
div[data-testid="stMultiSelect"] svg { fill: var(--text-muted) !important; }

/* Dropdown menu — rendered in a portal outside .stApp, so :root vars still apply. */
div[role="listbox"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-md) !important;
}
div[role="listbox"] [role="option"], div[role="listbox"] li {
    color: var(--text-primary) !important;
    background: transparent !important;
}
div[role="listbox"] [role="option"]:hover, div[role="listbox"] li:hover {
    background: var(--surface-2) !important;
}
div[role="listbox"] [aria-selected="true"] {
    background: var(--accent-soft) !important; color: var(--accent) !important;
}

/* ── Alerts (restyled natively; no call-site changes) ────
   The painted element is stAlertContainer, which carries Streamlit's own tint and
   a dark-blue text color. stAlert is a transparent wrapper; the stAlertContent*
   nodes only identify the variant. */
div[data-testid="stAlert"] { background: transparent !important; box-shadow: none !important; }
div[data-testid="stAlertContainer"] {
    background: var(--info-soft) !important;
    border: 1px solid var(--border) !important;
    border-left: 3px solid var(--info) !important;
    border-radius: var(--radius-lg) !important;
    padding: 12px 16px !important;
}
div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {
    background: var(--success-soft) !important; border-left-color: var(--success) !important; }
div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {
    background: var(--accent-soft) !important; border-left-color: var(--accent) !important; }
div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {
    background: var(--medium-soft) !important; border-left-color: var(--medium) !important; }
div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {
    background: var(--critical-soft) !important; border-left-color: var(--critical) !important; }
div[data-testid="stAlertContainer"],
div[data-testid="stAlertContainer"] div,
div[data-testid="stAlertContainer"] p,
div[data-testid="stAlertContainer"] li,
div[data-testid="stAlertContainer"] strong {
    color: var(--text-primary) !important;
}
div[data-testid="stAlertContainer"] p { font-size: 0.875rem !important; }
div[data-testid="stAlertContainer"] [data-testid^="stAlertContent"] {
    background: transparent !important;
}
div[data-testid="stAlertContainer"] code {
    background: transparent !important; color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* ── Code ─────────────────────────────────────────────── */
code {
    background: var(--accent-soft) !important;
    color: var(--accent) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.85rem !important;
    padding: 2px 6px !important;
    border-radius: var(--radius-sm) !important;
}
pre, .stCodeBlock, div[data-testid="stCode"] > pre {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
}
pre code {
    background: transparent !important;
    color: var(--text-primary) !important;
    padding: 0 !important;
}

/* ── Expander ─────────────────────────────────────────── */
div[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: none !important;
}
div[data-testid="stExpander"] summary { color: var(--text-primary) !important; font-size: 0.9rem; }
div[data-testid="stExpander"] summary:hover { color: var(--accent) !important; }

/* ── Tabs (used only for in-section sub-nav) ──────────── */
button[data-baseweb="tab"] { color: var(--text-secondary) !important; }
button[data-baseweb="tab"][aria-selected="true"] { color: var(--accent) !important; }
div[data-baseweb="tab-highlight"] { background: var(--accent) !important; }

/* ── File uploader ────────────────────────────────────── */
section[data-testid="stFileUploaderDropzone"] {
    background: var(--surface-2) !important;
    border: 1px dashed var(--border-strong) !important;
    border-radius: var(--radius-lg) !important;
}

/* ── Cards / panels / KPI ─────────────────────────────── */
.dp-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 24px;
    box-shadow: var(--shadow-sm);
}
.dp-kpi { display: flex; flex-direction: column; gap: 8px; }
.dp-kpi-icon {
    width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;
    border-radius: var(--radius-sm); font-size: 1.05rem;
}
.dp-kpi-value { font-size: 1.75rem; font-weight: 700; color: var(--text-primary); line-height: 1.1; }
.dp-empty {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-lg); padding: 48px 24px; text-align: center;
}

/* ── Badges / chips ───────────────────────────────────── */
.dp-badge {
    display: inline-block; border-radius: var(--radius-full);
    padding: 2px 10px; font-size: 0.75rem; font-weight: 600;
    font-family: var(--font-ui);
}
.dp-chip {
    display: inline-block; border-radius: var(--radius-full);
    padding: 2px 10px; font-size: 0.72rem; font-weight: 500;
    border: 1px solid var(--border); color: var(--text-secondary);
    background: var(--surface-2);
}

/* ── Table rows ───────────────────────────────────────── */
.dp-th {
    display: flex; padding-bottom: 8px; border-bottom: 1px solid var(--border);
    font-size: 0.6875rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--text-muted);
}
table { border-color: var(--border) !important; }
thead th { color: var(--text-muted) !important; border-color: var(--border) !important; }
tbody td { color: var(--text-primary) !important; border-color: var(--border) !important; }

/* ── Floating chat widget ─────────────────────────────── */
/* Streamlit tags keyed containers with a .st-key-<key> class; we pin those. */
.st-key-dp_chat_launcher {
    position: fixed !important;
    right: 24px !important; bottom: 24px !important;
    width: 56px !important; z-index: 1000001 !important;
}
.st-key-dp_chat_launcher button {
    width: 56px !important; height: 56px !important; min-height: 56px !important;
    border-radius: 50% !important;
    background-color: var(--accent) !important; border: none !important;
    box-shadow: 0 6px 20px rgba(79,70,229,.45) !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32' fill='none'%3E%3Cpath d='M5 16 H10 L13 9 L17 23 L20 13 L22 16 H27' stroke='white' stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 30px 30px !important;
    transition: transform .12s ease, box-shadow .12s ease !important;
}
/* Hide the button's text label so only the logo shows. */
.st-key-dp_chat_launcher button * {
    font-size: 0 !important; color: transparent !important;
    width: 0 !important; height: 0 !important; overflow: hidden !important;
}
.st-key-dp_chat_launcher button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 26px rgba(79,70,229,.55) !important;
    background-color: var(--accent-hover) !important;
}

.st-key-dp_chat_panel {
    position: fixed !important;
    right: 24px !important; bottom: 92px !important;
    width: 370px !important; max-width: calc(100vw - 32px) !important;
    z-index: 1000001 !important;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    box-shadow: var(--shadow-lg) !important;
    padding: 14px 16px !important;
}
.st-key-dp_chat_scroll {
    height: 300px !important; overflow-y: auto !important;
    margin: 6px -4px 8px; padding: 0 4px;
}
.st-key-dp_chat_close button {
    background: transparent !important; border: none !important;
    color: var(--text-muted) !important; padding: 0 !important;
    min-height: 28px !important;
}
.st-key-dp_chat_close button:hover { color: var(--text-primary) !important; }
.st-key-dp_chat_panel [data-testid="stChatInput"] {
    background: var(--surface-2) !important; border-color: var(--border) !important;
}
.st-key-dp_chat_panel [data-testid="stChatInput"] textarea {
    background: transparent !important; color: var(--text-primary) !important;
}

/* ── Images (guide screenshots) ───────────────────────── */
div[data-testid="stImage"] img {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-sm) !important;
}
div[data-testid="stImage"] figcaption,
div[data-testid="stImageCaption"] {
    color: var(--text-muted) !important;
    font-size: 0.8125rem !important;
    text-align: left !important;
}

/* ── Progress / spinner ───────────────────────────────── */
div[data-testid="stProgress"] > div > div > div { background: var(--accent) !important; }

/* ── Scrollbar ────────────────────────────────────────── */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: var(--border-strong); border-radius: var(--radius-full);
    border: 2px solid var(--bg);
}
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ── Misc ─────────────────────────────────────────────── */
hr { border-color: var(--border) !important; }
a { color: var(--accent) !important; }
div[data-testid="column"] > div { gap: 0.75rem; }
"""

_FONTS = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700"
    "&family=JetBrains+Mono:wght@400;500&display=swap');"
)


def inject_theme(mode: str = "auto") -> None:
    """Inject the full stylesheet. Call exactly once per rerun, from app.py."""
    if mode not in ("auto", "light", "dark"):
        mode = "auto"
    st.markdown(
        f"<style>\n{_FONTS}\n\n{_token_layer(mode)}\n{_STYLES}\n</style>",
        unsafe_allow_html=True,
    )
