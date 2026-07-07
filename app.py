# app.py
import streamlit as st
import importlib
from theme import inject_theme
from services.supabase_service import get_client

st.set_page_config(
    page_title='AI Engineer Assistant',
    page_icon='⧡',
    layout='wide',
    initial_sidebar_state='expanded'
)

inject_theme()
client = get_client()   # None = SQLite fallback

PAGES = {
    '📂  Dashboard':     'pages.dashboard',
}

with st.sidebar:
    # Logo — NO subtitle
    st.markdown('''
    <div style="padding:24px 20px 12px; text-align:center;">
      <div style="font-family:'Orbitron',sans-serif;
          font-size:1.1rem; color:#00f0ff;
          letter-spacing:0.1em; font-weight:700;">⧡ AI Engineer</div>
    </div>''', unsafe_allow_html=True)

    st.markdown('<hr style="border-color:rgba(0,240,255,0.15);margin:0 0 12px">',
        unsafe_allow_html=True)

    page = st.radio('', list(PAGES.keys()), label_visibility='collapsed', key='nav_radio')

    # Connection status at bottom of sidebar
    st.markdown('<div style="flex:1"></div>', unsafe_allow_html=True)
    status_color = '#00f0ff' if client else '#f59e0b'
    status_text  = 'Supabase Connected' if client else 'Local SQLite Fallback'
    st.markdown(f'''
    <div style="margin-top:auto; padding:16px 12px 8px;">
      <div style="font-size:0.65rem; color:#7ea8c9;
          letter-spacing:0.1em; text-transform:uppercase;
          margin-bottom:8px;">⚡ Connection Status</div>
      <div style="background:rgba(10,20,45,0.8);
          border:1px solid {status_color}44;
          border-left:3px solid {status_color};
          border-radius:8px; padding:10px 12px;">
        <div style="color:{status_color}; font-weight:700;
            font-size:0.82rem;">{status_text}</div>
      </div>
    </div>''', unsafe_allow_html=True)

# Route to selected page
mod = importlib.import_module(PAGES[page])
mod.render(client)
