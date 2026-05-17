"""
RAG (Retrieval Augmented Generation) Engine for material recommendations.

Uses BM25 keyword retrieval — no API key or embedding model required.
Drop your material datasheet PDFs into the `rag_docs/` folder.
The index is built automatically on first use and rebuilt whenever the PDFs change.
"""

import os
import pickle
import hashlib
import re
from pathlib import Path
from typing import List, Tuple, Optional

from dotenv import load_dotenv
load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────────
RAG_DOCS_DIR  = Path(__file__).parent / "rag_docs"
CACHE_DIR     = Path(__file__).parent / "rag_cache"
CHUNKS_PATH   = CACHE_DIR / "rag_chunks.pkl"
MANIFEST_PATH = CACHE_DIR / "rag_manifest.txt"

# ── Chunking config ───────────────────────────────────────────────────────────
CHUNK_SIZE    = 800   # characters per chunk
CHUNK_OVERLAP = 150   # overlap between consecutive chunks

# ── Module-level in-memory cache ─────────────────────────────────────────────
_cache: dict = {"bm25": None, "chunks": None, "manifest": None}


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_docs_manifest() -> str:
    """Return an MD5 fingerprint of all PDFs (name + size) in rag_docs/."""
    if not RAG_DOCS_DIR.exists():
        return ""
    files = sorted(RAG_DOCS_DIR.glob("*.pdf"))
    if not files:
        return ""
    manifest = "|".join(f"{f.name}:{f.stat().st_size}" for f in files)
    return hashlib.md5(manifest.encode()).hexdigest()


def _extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF using pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())
        return "\n\n".join(pages)
    except Exception as e:
        print(f"[RAG] Warning: could not read '{pdf_path.name}': {e}")
        return ""


def _chunk_text(text: str, source: str) -> List[dict]:
    """Split text into overlapping chunks."""
    chunks = []
    text = text.strip()
    start = 0
    while start < len(text):
        chunk_text = text[start : start + CHUNK_SIZE].strip()
        if len(chunk_text) > 60:
            chunks.append({"text": chunk_text, "source": source})
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _tokenize(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer, lowercased."""
    return re.findall(r"[a-z0-9°%µ/]+", text.lower())


# ─────────────────────────────────────────────────────────────────────────────
# Index management
# ─────────────────────────────────────────────────────────────────────────────

def build_index():
    """
    Build a fresh BM25 index from all PDFs in rag_docs/.
    Saves chunks + manifest to rag_cache/ for fast subsequent loads.
    Returns (bm25_instance, chunks_list).
    """
    from rank_bm25 import BM25Okapi

    CACHE_DIR.mkdir(exist_ok=True)
    RAG_DOCS_DIR.mkdir(exist_ok=True)

    pdf_files = list(RAG_DOCS_DIR.glob("*.pdf"))
    if not pdf_files:
        print("[RAG] No PDFs found in rag_docs/ — index not built.")
        return None, []

    print(f"[RAG] Building BM25 index from {len(pdf_files)} PDF(s)…")
    all_chunks: List[dict] = []
    for pdf_path in pdf_files:
        text = _extract_text_from_pdf(pdf_path)
        if text:
            chunks = _chunk_text(text, pdf_path.name)
            all_chunks.extend(chunks)
            print(f"[RAG]   {pdf_path.name} → {len(chunks)} chunks")

    if not all_chunks:
        print("[RAG] No text extracted from PDFs.")
        return None, []

    tokenized = [_tokenize(c["text"]) for c in all_chunks]
    bm25 = BM25Okapi(tokenized)

    # Persist to disk
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump({"chunks": all_chunks, "tokenized": tokenized}, f)
    MANIFEST_PATH.write_text(_get_docs_manifest())

    print(f"[RAG] Index built: {len(all_chunks)} chunks")

    _cache["bm25"]     = bm25
    _cache["chunks"]   = all_chunks
    _cache["manifest"] = _get_docs_manifest()

    return bm25, all_chunks


def load_or_build_index():
    """
    Return (bm25, chunks). Loads from disk cache or rebuilds if PDFs changed.
    """
    from rank_bm25 import BM25Okapi

    current_manifest = _get_docs_manifest()
    if not current_manifest:
        return None, []

    # 1. In-memory hit
    if _cache["bm25"] is not None and _cache["manifest"] == current_manifest:
        return _cache["bm25"], _cache["chunks"]

    # 2. Disk hit
    if CHUNKS_PATH.exists() and MANIFEST_PATH.exists():
        if MANIFEST_PATH.read_text().strip() == current_manifest:
            with open(CHUNKS_PATH, "rb") as f:
                data = pickle.load(f)
            bm25 = BM25Okapi(data["tokenized"])
            _cache["bm25"]     = bm25
            _cache["chunks"]   = data["chunks"]
            _cache["manifest"] = current_manifest
            return bm25, data["chunks"]

    # 3. Rebuild
    return build_index()


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

# Generic fallback used when the user's query is too vague to match any
# chunk (e.g. "nothing special"). Surfaces a broad materials overview so
# the LLM still receives database-grounded context.
_FALLBACK_QUERY = "material properties strength temperature pla petg abs tpu print settings infill"


def query_materials(query: str, top_k: int = 5) -> str:
    """
    Retrieve the most relevant material-database chunks for `query` using BM25.
    Returns a formatted context string ready to inject into an LLM prompt.
    Returns an empty string only when the index itself is empty/unavailable —
    a vague query falls back to a generic materials overview.
    """
    try:
        bm25, chunks = load_or_build_index()
        if bm25 is None or not chunks:
            return ""

        import numpy as np
        tokens = _tokenize(query)
        scores = bm25.get_scores(tokens) if tokens else np.zeros(len(chunks))
        top_indices = np.argsort(scores)[::-1][:top_k]

        # If the query didn't match any chunk, re-score with the fallback
        # query so we still surface something useful.
        if not any(scores[idx] > 0 for idx in top_indices):
            fallback_tokens = _tokenize(_FALLBACK_QUERY)
            scores = bm25.get_scores(fallback_tokens)
            top_indices = np.argsort(scores)[::-1][:top_k]

        seen: set = set()
        parts: List[str] = []
        for idx in top_indices:
            if scores[idx] > 0 and 0 <= idx < len(chunks):
                chunk = chunks[idx]
                if chunk["text"] not in seen:
                    parts.append(f"[Source: {chunk['source']}]\n{chunk['text']}")
                    seen.add(chunk["text"])

        # Last-resort fallback: if even the generic query found nothing
        # (extremely sparse index), return the first few chunks verbatim so
        # the LLM still gets *some* grounding.
        if not parts:
            for chunk in chunks[:top_k]:
                if chunk["text"] not in seen:
                    parts.append(f"[Source: {chunk['source']}]\n{chunk['text']}")
                    seen.add(chunk["text"])

        return "\n\n---\n\n".join(parts)

    except Exception as e:
        print(f"[RAG] Query error: {e}")
        return ""


def get_index_stats() -> dict:
    """Return metadata about the current index."""
    try:
        _, chunks = load_or_build_index()
        pdfs = sorted(RAG_DOCS_DIR.glob("*.pdf")) if RAG_DOCS_DIR.exists() else []
        return {
            "num_pdfs":   len(pdfs),
            "num_chunks": len(chunks),
            "pdf_names":  [f.name for f in pdfs],
        }
    except Exception:
        return {"num_pdfs": 0, "num_chunks": 0, "pdf_names": []}


def force_rebuild():
    """Force a full index rebuild regardless of the cache state."""
    _cache["bm25"]     = None
    _cache["chunks"]   = None
    _cache["manifest"] = None
    return build_index()
