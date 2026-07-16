# components/chat_widget.py
"""Floating chat launcher + popup panel, rendered globally on every page.

A round logo button sits bottom-right; clicking it toggles a small chat panel.
The chat is grounded in the ingested repository (services/chat_service) and uses
the provider/model configured in Settings. Positioning is done in theme.py via the
`.st-key-dp_chat_*` classes Streamlit puts on keyed containers.
"""
import html

import streamlit as st

from services import chat_service, llm_service
from services.database_service import get_all_files


def _bubble(role: str, text: str, sources=None):
    side = "flex-end" if role == "user" else "flex-start"
    bg = "var(--accent)" if role == "user" else "var(--surface-2)"
    fg = "#ffffff" if role == "user" else "var(--text-primary)"
    src = ""
    if sources:
        chips = " ".join(f"<code>{html.escape(s)}</code>" for s in sources)
        src = (f'<div style="font-size:0.68rem;color:var(--text-muted);'
               f'margin-top:4px;">{chips}</div>')
    st.markdown(
        f'<div style="display:flex;justify-content:{side};margin:6px 0;">'
        f'<div style="max-width:85%;background:{bg};color:{fg};'
        f'padding:8px 12px;border-radius:12px;font-size:0.85rem;line-height:1.5;">'
        f'{html.escape(text)}{src}</div></div>',
        unsafe_allow_html=True,
    )


def render_chat_widget():
    st.session_state.setdefault("chat_open", False)
    st.session_state.setdefault("chat_history", [])

    # ── Launcher (round logo button, bottom-right) ───────────────────
    with st.container(key="dp_chat_launcher"):
        if st.button("chat", key="dp_chat_toggle", help="Chat with this repository"):
            st.session_state["chat_open"] = not st.session_state["chat_open"]
            st.rerun()

    if not st.session_state["chat_open"]:
        return

    # ── Panel ────────────────────────────────────────────────────────
    with st.container(key="dp_chat_panel"):
        head = st.columns([5, 1])
        with head[0]:
            st.markdown(
                '<div style="font-weight:650;color:var(--text-primary);'
                'font-size:0.95rem;padding-top:4px;">Repo Chat</div>',
                unsafe_allow_html=True,
            )
        with head[1]:
            if st.button("✕", key="dp_chat_close"):
                st.session_state["chat_open"] = False
                st.rerun()

        if not get_all_files():
            st.caption("Ingest a repository first, then ask about it here.")
            return

        if llm_service.resolve_key()[0] is None:
            st.caption("Set an API key in Settings to enable chat.")
            return

        st.caption(
            f"{llm_service.PROVIDERS[llm_service.active_provider()]['label']} · "
            f"`{llm_service.active_model()}`"
        )

        history = st.session_state["chat_history"]
        with st.container(key="dp_chat_scroll"):
            if not history:
                st.markdown(
                    '<div style="color:var(--text-muted);font-size:0.8rem;'
                    'padding:8px 2px;">Ask about the indexed code — e.g. '
                    '"what does this project do?" or "where is auth handled?"</div>',
                    unsafe_allow_html=True,
                )
            for m in history:
                _bubble(m["role"], m["content"], m.get("sources"))

        prompt = st.chat_input("Ask about this codebase…", key="dp_chat_input")
        if prompt:
            history.append({"role": "user", "content": prompt})
            try:
                text, sources = chat_service.answer(history, prompt)
            except chat_service.NoRepositoryIndexed as e:
                text, sources = str(e), []
            except llm_service.LLMNotConfigured as e:
                text, sources = str(e), []
            except Exception as e:  # noqa: BLE001
                text, sources = f"Something went wrong: {e}", []
            history.append({"role": "assistant", "content": text, "sources": sources})
            st.rerun()
