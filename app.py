# app.py
import importlib

import streamlit as st
from dotenv import load_dotenv

st.set_page_config(
    page_title="DevPulse Architect",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# .env is the local fallback; on Render the real env vars are already present.
load_dotenv()

from services import llm_service  # noqa: E402
from theme import inject_theme  # noqa: E402

# Session-state keys override the environment for this process. Must run before
# any module calls os.getenv("<PROVIDER>_API_KEY").
llm_service.export_keys_to_env()

inject_theme(st.session_state.get("ui_theme", "auto"))


# ── Router ──────────────────────────────────────────────────────────────
# Order matters: the first entry is the landing section on a fresh session.
SECTIONS = {
    "Ingest Repository": ("pages.dashboard", "render_ingestion_section"),
    "Overview": ("pages.dashboard", "render_overview"),
    "Project Overview": ("pages.dashboard", "render_project_overview"),
    "Security Audit": ("pages.security_audit", "render_security_audit"),
    "Static Preview": ("pages.dashboard", "render_static_preview"),
    "Indexed Files": ("pages.dashboard", "render_files_table"),
    "Guide": ("pages.guide", "render_guide"),
    "Settings": ("pages.dashboard", "render_settings"),
}

ICONS = {
    "Ingest Repository": "↓",
    "Overview": "◔",
    "Project Overview": "◇",
    "Security Audit": "⛨",
    "Static Preview": "▣",
    "Indexed Files": "☰",
    "Guide": "?",
    "Settings": "⚙",
}


with st.sidebar:
    st.markdown(
        """
        <div class="dp-logo-wrap">
          <div class="dp-logo-mark">
            <svg width="30" height="30" viewBox="0 0 32 32" fill="none"
                 xmlns="http://www.w3.org/2000/svg" aria-label="DevPulse Architect">
              <defs>
                <linearGradient id="dpg" x1="4" y1="2" x2="28" y2="30"
                    gradientUnits="userSpaceOnUse">
                  <stop stop-color="#818CF8"/><stop offset="1" stop-color="#4F46E5"/>
                </linearGradient>
              </defs>
              <path d="M16 1.8 L28.3 9 L28.3 23 L16 30.2 L3.7 23 L3.7 9 Z"
                    fill="url(#dpg)"/>
              <path d="M6.5 16.5 H10 L12.3 10.5 L15.8 22 L18.6 13.5 L20.2 16.5 H25.5"
                    stroke="#fff" stroke-width="1.9"
                    stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="dp-logo-text">DevPulse Architect</div>
        </div>""",
        unsafe_allow_html=True,
    )

    choice = st.radio(
        "Navigation",
        list(SECTIONS.keys()),
        format_func=lambda s: f"{ICONS[s]}   {s}",
        label_visibility="collapsed",
    )

    # Footer as ONE html block so the collapsed rail can hide it as a unit.
    _provider = llm_service.active_provider()
    _key, _source = llm_service.resolve_key(_provider)
    if _source == "none":
        _status = ('<div style="color:var(--medium);font-size:0.75rem;">'
                   "⚠ No API key — set one in Settings</div>")
    else:
        _status = (
            f'<div style="color:var(--text-muted);font-size:0.75rem;">'
            f'{llm_service.PROVIDERS[_provider]["label"]}<br>'
            f'<span style="opacity:.7">{llm_service.active_model(_provider)}</span></div>'
        )
    st.markdown(
        f"""
        <div class="dp-sidebar-foot">
          <hr style="margin:16px 0 12px">
          {_status}
          <div style="height:8px"></div>
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="width:6px;height:6px;border-radius:50%;
                background:var(--success);display:inline-block;"></span>
            <span style="color:var(--text-muted);font-size:0.75rem;">Local SQLite</span>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )


_module_name, _fn_name = SECTIONS[choice]
try:
    _render = getattr(importlib.import_module(_module_name), _fn_name)
    _render()
except Exception as exc:  # noqa: BLE001 - top-level UI boundary
    st.error(f"Failed to render **{choice}**: {exc}")
    st.exception(exc)

# Floating chat launcher + panel, present on every page.
from components.chat_widget import render_chat_widget  # noqa: E402

render_chat_widget()
