# services/chat_service.py
"""RAG chat grounded strictly in the ingested repository.

Retrieval is vector-first (needs a Gemini embeddings key) and falls back to
keyword matching so the chat still works with no key. Generation goes through
llm_service.generate(), so it uses whichever provider/model/key is set in Settings.

No Streamlit imports — reusable and testable on its own.
"""
import logging

from services import llm_service
from services.database_service import (
    get_all_files,
    keyword_search_chunks,
    search_chunks_vector,
)

logger = logging.getLogger("chat_service")

MAX_CONTEXT_CHUNKS = 6
MAX_HISTORY_TURNS = 6          # user+assistant messages fed back for continuity
MAX_CHUNK_CHARS = 1200
FILE_TYPES = ["source_code", "api_doc", "design_doc"]

SYSTEM = """You are a coding assistant embedded in "DevPulse Architect", answering \
questions about ONE specific codebase — the repository the user has ingested.

Rules:
- Answer ONLY from the provided context (retrieved code snippets and the file list).
- If the answer is not in the context, say so plainly: "I don't see that in the \
indexed codebase." Do not invent files, functions, or behavior.
- Do not answer questions unrelated to this codebase; steer back to it.
- Cite the files you used, e.g. `path/to/file.py`.
- Be concise and concrete. Use markdown and fenced code blocks for code."""


class NoRepositoryIndexed(RuntimeError):
    """Raised when there is nothing to chat about yet."""


def retrieve(question: str, k: int = MAX_CONTEXT_CHUNKS) -> list:
    """Vector search first; keyword fallback when embeddings are unavailable."""
    hits = search_chunks_vector(question, limit=k, file_types=FILE_TYPES)
    if hits:
        return hits
    return keyword_search_chunks(question, limit=k)


def _format_context(chunks: list, files: list) -> str:
    catalog = ", ".join(sorted(f["filename"] for f in files)[:60])
    parts = [f"Indexed files: {catalog}"]
    if len(files) > 60:
        parts[0] += f" (+{len(files) - 60} more)"
    if chunks:
        parts.append("\nRelevant snippets:")
        for i, c in enumerate(chunks, 1):
            body = (c.get("content") or "")[:MAX_CHUNK_CHARS]
            parts.append(f"\n[{i}] {c.get('filename', '?')}\n{body}")
    else:
        parts.append("\n(No snippet matched the question directly — rely on the "
                     "file list above and say if the detail isn't available.)")
    return "\n".join(parts)


def _format_history(history: list) -> str:
    turns = [m for m in history if m.get("role") in ("user", "assistant")]
    turns = turns[-MAX_HISTORY_TURNS:]
    if not turns:
        return ""
    lines = ["Conversation so far:"]
    for m in turns:
        who = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{who}: {m['content']}")
    return "\n".join(lines) + "\n"


def answer(history: list, question: str):
    """Return (answer_text, sources) for one turn. Raises if nothing is indexed."""
    files = get_all_files()
    if not files:
        raise NoRepositoryIndexed(
            "No repository is indexed yet. Ingest one first, then ask about it."
        )

    chunks = retrieve(question)
    context = _format_context(chunks, files)
    history_block = _format_history(history)

    prompt = (
        f"{history_block}"
        f"--- CODEBASE CONTEXT ---\n{context}\n\n"
        f"--- QUESTION ---\n{question}"
    )
    text = llm_service.generate(SYSTEM, prompt)

    # Distinct source filenames, preserving retrieval order.
    sources = list(dict.fromkeys(c.get("filename") for c in chunks if c.get("filename")))
    return text, sources
