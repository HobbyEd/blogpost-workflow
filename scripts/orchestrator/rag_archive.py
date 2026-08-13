"""Lokale RAG Archief Vectorstore voor Blogpost Archief Consistentie (ADR-006 & ADR-008).

Ondersteunt asynchrone non-blocking achtergrond-indexering, incrementele updates
en statusbewaking voor de Beheer-interface.
"""

from __future__ import annotations

import json
import math
import os
import re
import time
from collections import Counter
from datetime import datetime
from typing import Any

from .repository import now_iso, posts_root, repo_root

INDEX_FILE_NAME = ".archive_rag_index.json"


def _tokenize(text: str) -> list[str]:
    """Zet tekst om naar opgeschoonde lowercase unigrammen en bigrammen."""
    text_clean = re.sub(r"[^\w\s]", " ", text.lower())
    words = [w for w in text_clean.split() if len(w) > 2]
    bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words) - 1)]
    return words + bigrams


class LocalRAGArchive:
    """Lokale BM25/TF-IDF Vectorstore voor het blogpost archief."""

    def __init__(self, index_path: str | None = None):
        self.index_path = index_path or os.path.join(posts_root(), INDEX_FILE_NAME)
        self.documents: list[dict[str, Any]] = []
        self.last_indexed_at: str | None = None
        self.is_indexing: bool = False
        self.progress_current: int = 0
        self.progress_total: int = 0
        self.current_item: str = ""
        self.status_message: str = ""
        self.load_index()

    def load_index(self) -> None:
        """Laad bestaande index vanaf schijf indien aanwezig."""
        if os.path.isfile(self.index_path):
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.documents = data.get("documents", [])
                        self.last_indexed_at = data.get("last_indexed_at")
                    elif isinstance(data, list):
                        self.documents = data
            except Exception as e:
                print(f"Waarschuwing: Kon RAG index niet laden: {e}")
                self.documents = []

    def save_index(self) -> None:
        """Sla index op naar schijf (atomisch via temp file)."""
        self.last_indexed_at = now_iso()
        payload = {
            "last_indexed_at": self.last_indexed_at,
            "documents_count": len(self.documents),
            "documents": self.documents,
        }
        temp_path = f"{self.index_path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.index_path)
        except Exception as e:
            print(f"Fout bij opslaan RAG index: {e}")

    def get_status(self) -> dict[str, Any]:
        """Haal actuele RAG beheer- en indexeringsstatus op."""
        articles_map: dict[str, dict[str, Any]] = {}
        for doc in self.documents:
            slug = doc["slug"]
            if slug not in articles_map:
                articles_map[slug] = {
                    "slug": slug,
                    "chunks_count": 0,
                    "last_modified": doc.get("mtime", "onbekend"),
                }
            articles_map[slug]["chunks_count"] += 1

        pct = int((self.progress_current / self.progress_total) * 100) if self.progress_total > 0 else (0 if self.is_indexing else 100)

        return {
            "running": self.is_indexing,
            "last_indexed_at": self.last_indexed_at,
            "total_chunks": len(self.documents),
            "total_posts": len(articles_map),
            "progress_current": self.progress_current,
            "progress_total": self.progress_total,
            "percentage": pct,
            "current_item": self.current_item,
            "status_message": self.status_message or ("Aan het indexeren..." if self.is_indexing else "Gereed"),
            "articles": list(articles_map.values()),
        }

    def index_all_posts(
        self, root_dir: str | None = None, incremental: bool = False, purge: bool = False
    ) -> int:
        """Scant en indexeert Markdown bestanden in posts/ (ADR-008)."""
        self.is_indexing = True
        try:
            pdir = root_dir or posts_root()
            if not os.path.exists(pdir):
                return 0

            if purge:
                self.documents = []

            indexed_slugs = {d["slug"] for d in self.documents} if incremental else set()
            new_docs: list[dict[str, Any]] = list(self.documents) if incremental else []

            entries = [e for e in sorted(os.listdir(pdir)) if os.path.isdir(os.path.join(pdir, e)) and not e.startswith(".")]
            self.progress_total = len(entries)
            self.progress_current = 0

            for idx, entry in enumerate(entries, 1):
                self.progress_current = idx
                self.current_item = entry
                self.status_message = f"Indexeren van '{entry}' ({idx}/{len(entries)})..."
                post_path = os.path.join(pdir, entry)

                if incremental and entry in indexed_slugs:
                    continue

                for fname in ["draft.md", "synthese.md", "outline.md", "briefing.md"]:
                    fpath = os.path.join(post_path, fname)
                    if os.path.isfile(fpath):
                        try:
                            mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat()
                            with open(fpath, "r", encoding="utf-8") as f:
                                content = f.read()

                            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 40]
                            for p_idx, para in enumerate(paragraphs):
                                tokens = _tokenize(para)
                                if tokens:
                                    new_docs.append({
                                        "slug": entry,
                                        "filename": fname,
                                        "chunk_id": f"{entry}:{fname}:{p_idx}",
                                        "mtime": mtime,
                                        "text": para,
                                        "tokens": tokens,
                                    })
                        except Exception as e:
                            print(f"Fout bij indexeren {fpath}: {e}")

            self.documents = new_docs
            self.save_index()
            self.status_message = f"Indexatie afgerond: {len(self.documents)} chunks in index."
            self.current_item = ""
            return len(self.documents)
        finally:
            self.is_indexing = False

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Zoek relevante eerdere blogpost passages op basis van TF-IDF cosine gelijkenis."""
        query_tokens = _tokenize(query)
        if not query_tokens or not self.documents:
            return []

        query_counts = Counter(query_tokens)
        results: list[tuple[float, dict[str, Any]]] = []

        for doc in self.documents:
            doc_tokens = doc.get("tokens", [])
            if not doc_tokens:
                continue

            doc_counts = Counter(doc_tokens)
            common = set(query_counts.keys()) & set(doc_counts.keys())
            if not common:
                continue

            dot_product = sum(query_counts[t] * doc_counts[t] for t in common)
            norm_q = math.sqrt(sum(v * v for v in query_counts.values()))
            norm_d = math.sqrt(sum(v * v for v in doc_counts.values()))

            score = dot_product / (norm_q * norm_d) if (norm_q * norm_d) > 0 else 0.0

            if score > 0.05:
                results.append((score, {
                    "slug": doc["slug"],
                    "filename": doc["filename"],
                    "chunk_id": doc["chunk_id"],
                    "score": round(score, 4),
                    "text": doc["text"],
                }))

        results.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in results[:top_k]]


# Singleton instantie
archive_vectorstore = LocalRAGArchive()
