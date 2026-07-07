# pages/dashboard.py
import streamlit as st
import urllib.request
import zipfile
import io
import logging
from theme import inject_theme
from services.supabase_service import (
    get_all_files,
    save_file,
    delete_file,
    get_file_content,
    insert_file_with_chunks
)

logger = logging.getLogger("pages_data")

LANGUAGE_MAPPING = {
    "py": "python", "js": "javascript", "ts": "typescript", 
    "tsx": "typescript", "md": "markdown", "txt": "text", 
    "json": "json", "yaml": "yaml", "html": "html", "css": "css", 
    "java": "java", "go": "go", "rs": "rust"
}

def process_single_file(uploaded, file_type, client):
    try:
        content = uploaded.read().decode("utf-8", errors="ignore")
        filename = uploaded.name
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        lang = LANGUAGE_MAPPING.get(ext, "text")
        save_file(client, filename, file_type, content, lang, len(content))
        st.success(f"✓ Indexed {filename}")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to process file: {e}")

def process_pasted_text(raw_text, filename, paste_type, client):
    try:
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        lang = LANGUAGE_MAPPING.get(ext, "text")
        save_file(client, filename, paste_type, raw_text, lang, len(raw_text))
        st.success(f"✓ Indexed {filename}")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to process pasted text: {e}")

def download_and_filter_repo(repo_url: str, branch: str) -> list:
    url = repo_url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
        
    parts = url.split("github.com/")
    if len(parts) < 2:
        raise ValueError("Invalid GitHub URL. Must be like https://github.com/username/repository")
        
    repo_path = parts[1]
    zip_url = f"https://github.com/{repo_path}/archive/refs/heads/{branch}.zip"
    
    req = urllib.request.Request(
        zip_url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            zip_data = response.read()
    except Exception as e:
        if branch == "main":
            fallback_url = f"https://github.com/{repo_path}/archive/refs/heads/master.zip"
            req = urllib.request.Request(
                fallback_url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req) as response:
                zip_data = response.read()
        else:
            raise e
            
    files_list = []
    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        for name in z.namelist():
            if name.endswith("/"):
                continue
            parts = name.split("/", 1)
            clean_name = parts[1] if len(parts) > 1 else name
            
            # Skip hidden, build, cache, or binary assets
            if any(p.startswith(".") for p in clean_name.split("/")) or "node_modules/" in clean_name or "venv/" in clean_name or "__pycache__/" in clean_name:
                continue
                
            try:
                content = z.read(name)
                files_list.append({
                    "path": clean_name,
                    "content": content
                })
            except Exception:
                pass
    return files_list

def clone_and_index(repo_url, branch, client):
    try:
        progress = st.progress(0)
        status   = st.empty()
        files    = download_and_filter_repo(repo_url, branch)
        if not files:
            st.warning("No valid text files found.")
            progress.empty()
            return
            
        for i, f in enumerate(files):
            status.markdown(f'`Indexing {f["path"]}...`')
            insert_file_with_chunks(client, f)
            progress.progress((i + 1) / len(files))
        progress.empty()
        status.success(f'✓  Indexed {len(files)} files from {repo_url}')
        st.rerun()
    except Exception as ex:
        st.error(f"Failed to clone and index repository: {ex}")

def render_ingestion_tabs(client):
    tab_upload, tab_github, tab_paste = st.tabs([
        '📄  Upload File',
        '🐙  Clone GitHub Repo',
        '✍️  Paste Text',
    ])
 
    with tab_upload:
        uploaded = st.file_uploader(
            'Drop a source file, API doc, or design doc',
            type=['py','js','ts','tsx','md','txt','json','yaml','html','css','java','go','rs']
        )
        file_type = st.selectbox('File Type',
            ['source_code', 'api_doc', 'design_doc'])
        if st.button('⬆  Ingest File') and uploaded:
            process_single_file(uploaded, file_type, client)
 
    with tab_github:
        repo_url = st.text_input('GitHub URL',
            placeholder='https://github.com/owner/repo')
        branch = st.text_input('Branch', value='main')
        col_clone, col_info = st.columns([2,1])
        with col_clone:
            if st.button('⬇  Clone & Index', use_container_width=True):
                clone_and_index(repo_url, branch, client)
 
    with tab_paste:
        raw_text = st.text_area('Paste code or text', height=240)
        filename = st.text_input('Filename', placeholder='snippet.py')
        paste_type = st.selectbox('Type', ['source_code','api_doc','design_doc'])
        if st.button('⬆  Ingest Text') and raw_text and filename:
            process_pasted_text(raw_text, filename, paste_type, client)

def render_files_table(client):
    st.markdown('#### 🗄️  Indexed Files')
    search = st.text_input('', placeholder='🔍  Filter by filename...',
        label_visibility='collapsed')
    files = get_all_files(client)
    if search:
        files = [f for f in files if search.lower() in f['filename'].lower()]
    if not files:
        st.info('No files indexed yet.')
        return
        
    # Table header
    st.markdown('''
    <div style="display:flex; font-weight:700; color:#00f0ff; padding-bottom:8px; border-bottom:1px solid rgba(0,240,255,0.25); font-size:0.8rem; font-family:'Space Grotesk',sans-serif;">
        <div style="flex: 3.5;">FILENAME</div>
        <div style="flex: 1.5;">TYPE</div>
        <div style="flex: 1;">LANGUAGE</div>
        <div style="flex: 1;">SIZE</div>
        <div style="flex: 0.7; text-align: center;">DEL</div>
    </div>
    ''', unsafe_allow_html=True)
    
    for f in files:
        c1,c2,c3,c4,c5 = st.columns([3.5, 1.5, 1, 1, 0.7])
        c1.write(f['filename'])
        c2.caption(f['file_type'])
        c3.caption(f['language'] or '—')
        size_kb = f"{f['size_bytes']//1024} KB" if f.get('size_bytes') else '0 KB'
        c4.caption(size_kb)
        if c5.button('🗑️', key=f"d_{f['id']}", use_container_width=True):
            delete_file(client, f['id'])
            st.rerun()

def render(client):
    inject_theme()
    st.markdown("### 📂  Dashboard")
    render_ingestion_tabs(client)
    st.markdown("<hr style='border-color:rgba(0,240,255,0.15); margin:24px 0;'>", unsafe_allow_html=True)
    render_files_table(client)
