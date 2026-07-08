# app.py
import streamlit as st
import importlib
from theme import inject_theme

st.set_page_config(
    page_title='DevPulse Architect',
    page_icon='⧡',
    layout='wide',
    initial_sidebar_state='expanded'
)

inject_theme()

PAGES = {
    '📂  Dashboard':     'pages.dashboard',
}

with st.sidebar:
    # Logo — NO subtitle
    st.markdown('''
    <div style="padding:24px 20px 12px; text-align:center;">
      <div style="font-family:'Orbitron',sans-serif;
          font-size:1.1rem; color:#00f0ff;
          letter-spacing:0.1em; font-weight:700;">⧡ DevPulse Architect</div>
    </div>''', unsafe_allow_html=True)

    st.markdown('<hr style="border-color:rgba(0,240,255,0.15);margin:0 0 12px">',
        unsafe_allow_html=True)

    page = st.radio('', list(PAGES.keys()), label_visibility='collapsed', key='nav_radio')

# Route to selected page
mod = importlib.import_module(PAGES[page])
mod.render()
