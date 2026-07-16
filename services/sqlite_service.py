# services/sqlite_service.py
import os
import re
import json
import sqlite3
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from services.similarity_service import cosine_similarity

logger = logging.getLogger("sqlite_service")

SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assistant.db")

def init_sqlite():
    """Initializes SQLite database tables and schema."""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        # Files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assistant_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_type TEXT CHECK (file_type IN ('source_code','api_doc','design_doc')),
                content TEXT,
                language TEXT,
                size_bytes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Chunks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assistant_file_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL REFERENCES assistant_files(id) ON DELETE CASCADE,
                chunk_index INTEGER,
                content TEXT,
                embedding TEXT, -- JSON array string
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Queries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assistant_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                plan TEXT,
                retrieved_files TEXT, -- JSON array string
                answer TEXT,
                agent_trace TEXT, -- JSON string
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Security audit reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assistant_audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_name TEXT,
                summary TEXT,        -- JSON {counts, score, grade}
                findings TEXT,       -- JSON array
                score INTEGER,
                grade TEXT,
                files_scanned INTEGER,
                files_skipped TEXT,  -- JSON array
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to initialize SQLite: {e}")

# Run init
init_sqlite()

def get_file_count() -> int:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM assistant_files")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"SQLite file count failed: {e}")
        return 0

def get_chunk_count() -> int:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM assistant_file_chunks")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"SQLite chunk count failed: {e}")
        return 0

def get_query_count() -> int:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM assistant_queries")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"SQLite query count failed: {e}")
        return 0

def get_storage_bytes() -> int:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(size_bytes) FROM assistant_files")
        val = cursor.fetchone()[0]
        conn.close()
        return val if val else 0
    except Exception as e:
        logger.error(f"SQLite storage bytes failed: {e}")
        return 0

def get_all_files() -> List[Dict[str, Any]]:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, file_type, language, size_bytes, created_at FROM assistant_files ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"SQLite get all files failed: {e}")
        return []

def delete_file(file_id: int):
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM assistant_file_chunks WHERE file_id = ?", (file_id,))
        cursor.execute("DELETE FROM assistant_files WHERE id = ?", (file_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"SQLite delete file failed: {e}")

def wipe_all():
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM assistant_file_chunks")
        cursor.execute("DELETE FROM assistant_files")
        cursor.execute("DELETE FROM assistant_queries")
        cursor.execute("DELETE FROM assistant_audits")
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"SQLite wipe all failed: {e}")


# ── Security audits ──────────────────────────────────────────────────
def save_audit(repo_name: str, summary: str, findings: str, score: int,
               grade: str, files_scanned: int, files_skipped: str) -> Optional[int]:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO assistant_audits
                (repo_name, summary, findings, score, grade, files_scanned, files_skipped)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (repo_name, summary, findings, score, grade, files_scanned, files_skipped))
        audit_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return audit_id
    except Exception as e:
        logger.error(f"SQLite save audit failed: {e}")
        return None


def _row_to_audit(row) -> Dict[str, Any]:
    rd = dict(row)
    for field in ("summary", "findings", "files_skipped"):
        if rd.get(field):
            try:
                rd[field] = json.loads(rd[field])
            except Exception:
                pass
    return rd


def get_latest_audit() -> Optional[Dict[str, Any]]:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assistant_audits ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return _row_to_audit(row) if row else None
    except Exception as e:
        logger.error(f"SQLite get latest audit failed: {e}")
        return None


def get_audit_history(limit: int = 10) -> List[Dict[str, Any]]:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM assistant_audits ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [_row_to_audit(r) for r in rows]
    except Exception as e:
        logger.error(f"SQLite get audit history failed: {e}")
        return []

def get_query_history(limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assistant_queries ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for r in rows:
            rd = dict(r)
            try:
                if rd.get("retrieved_files"):
                    rd["retrieved_files"] = json.loads(rd["retrieved_files"])
            except Exception:
                pass
            try:
                if rd.get("agent_trace"):
                    rd["agent_trace"] = json.loads(rd["agent_trace"])
            except Exception:
                pass
            result.append(rd)
        return result
    except Exception as e:
        logger.error(f"SQLite query history failed: {e}")
        return []

def get_recent_queries(n: int = 5) -> List[Dict[str, Any]]:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT question, created_at, plan, retrieved_files, answer, agent_trace FROM assistant_queries ORDER BY created_at DESC LIMIT ?", (n,))
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for r in rows:
            rd = dict(r)
            try:
                if rd.get("retrieved_files"):
                    rd["retrieved_files"] = json.loads(rd["retrieved_files"])
            except Exception:
                pass
            try:
                if rd.get("agent_trace"):
                    rd["agent_trace"] = json.loads(rd["agent_trace"])
            except Exception:
                pass
            result.append(rd)
        return result
    except Exception as e:
        logger.error(f"SQLite recent queries failed: {e}")
        return []

def get_queries_today() -> int:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        today = str(date.today())
        cursor.execute("SELECT COUNT(*) FROM assistant_queries WHERE created_at >= ?", (today,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"SQLite queries today failed: {e}")
        return 0

def insert_query_log(payload: Dict[str, Any]):
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO assistant_queries (question, plan, retrieved_files, answer, agent_trace)
            VALUES (?, ?, ?, ?, ?)
        """, (
            payload.get('question'),
            payload.get('plan'),
            payload.get('retrieved_files'),
            payload.get('answer'),
            payload.get('agent_trace')
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"SQLite insert query failed: {e}")

def get_avg_files_per_query() -> float:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT retrieved_files FROM assistant_queries")
        rows = cursor.fetchall()
        conn.close()
        
        lengths = []
        for r in rows:
            if r[0]:
                try:
                    files = json.loads(r[0])
                    lengths.append(len(files))
                except Exception:
                    pass
        return round(sum(lengths) / len(lengths), 1) if lengths else 0.0
    except Exception as e:
        logger.error(f"SQLite avg files query failed: {e}")
        return 0.0

def semantic_search(embedding: List[float], top_k: int = 8, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        if file_type:
            cursor.execute("""
                SELECT c.id, c.file_id, c.content, f.filename, f.file_type, c.embedding
                FROM assistant_file_chunks c
                JOIN assistant_files f ON f.id = c.file_id
                WHERE f.file_type = ?
            """, (file_type,))
        else:
            cursor.execute("""
                SELECT c.id, c.file_id, c.content, f.filename, f.file_type, c.embedding
                FROM assistant_file_chunks c
                JOIN assistant_files f ON f.id = c.file_id
            """)
            
        rows = cursor.fetchall()
        conn.close()
        
        all_chunks = []
        for r in rows:
            if r[5]: # embedding JSON
                try:
                    all_chunks.append({
                        "chunk_id": r[0],
                        "file_id": r[1],
                        "content": r[2],
                        "filename": r[3],
                        "file_type": r[4],
                        "embedding": json.loads(r[5])
                    })
                except Exception:
                    pass
                    
        scored_chunks = []
        for chunk in all_chunks:
            sim = cosine_similarity(embedding, chunk["embedding"])
            scored_chunks.append({
                "chunk_id": chunk["chunk_id"],
                "file_id": chunk["file_id"],
                "content": chunk["content"],
                "filename": chunk["filename"],
                "file_type": chunk["file_type"],
                "similarity": sim
            })
            
        scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_chunks[:top_k]
    except Exception as e:
        logger.error(f"SQLite semantic search failed: {e}")
        return []

def keyword_search_chunks(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Term-overlap fallback used when embeddings are unavailable (no Gemini key).

    Returns the same shape as the vector search: {content, filename, file_type, score}.
    """
    terms = list(dict.fromkeys(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", query.lower())))[:10]
    if not terms:
        return []
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        where = " OR ".join("LOWER(c.content) LIKE ?" for _ in terms)
        params = [f"%{t}%" for t in terms]
        cursor.execute(f"""
            SELECT c.content, f.filename, f.file_type
            FROM assistant_file_chunks c
            JOIN assistant_files f ON f.id = c.file_id
            WHERE {where}
            LIMIT 400
        """, params)
        rows = cursor.fetchall()
        conn.close()

        scored = []
        for content, filename, file_type in rows:
            low = (content or "").lower()
            score = sum(1 for t in terms if t in low)
            scored.append({"content": content, "filename": filename,
                           "file_type": file_type, "score": score})
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:limit]
    except Exception as e:
        logger.error(f"SQLite keyword chunk search failed: {e}")
        return []


def get_file_content(file_id: int) -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assistant_files WHERE id = ?", (file_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else {}
    except Exception as e:
        logger.error(f"SQLite get file content failed: {e}")
        return {}

def save_file(filename: str, file_type: str, content: str, language: str, size_bytes: int) -> Optional[int]:
    """Saves file to SQLite and returns the file ID."""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM assistant_files WHERE filename = ? AND file_type = ?", (filename, file_type))
        row = cursor.fetchone()
        
        if row:
            cursor.execute("""
                UPDATE assistant_files
                SET content = ?, language = ?, size_bytes = ?
                WHERE id = ?
            """, (content, language, size_bytes, row[0]))
            file_id = row[0]
        else:
            cursor.execute("""
                INSERT INTO assistant_files (filename, file_type, content, language, size_bytes)
                VALUES (?, ?, ?, ?, ?)
            """, (filename, file_type, content, language, size_bytes))
            file_id = cursor.lastrowid
            
        conn.commit()
        conn.close()
        return file_id
    except Exception as e:
        logger.error(f"SQLite save file failed: {e}")
        return None

def clear_chunks(file_id: int):
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM assistant_file_chunks WHERE file_id = ?", (file_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"SQLite clear chunks failed: {e}")

def insert_chunk(file_id: int, chunk_index: int, content: str, embedding_json: Optional[str]):
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO assistant_file_chunks (file_id, chunk_index, content, embedding)
            VALUES (?, ?, ?, ?)
        """, (file_id, chunk_index, content, embedding_json))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"SQLite insert chunk failed: {e}")
