"""Lokale RAG Archief Vectorstore voor Blogpost Archief Consistentie (ADR-006).

Deze module converteert alle eerder geschreven/gepubliceerde blogposts uit de posts/ map
naar een semantische index. Zowel de onderzoeker als de schrijver en de archief-validatie
agent gebruiken deze index om inhoudelijke lijn en terminologie te waarborgen.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from typing import Any

from .repository import posts_root, repo_root

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
        if index_path:
            self.index_path = index_path
        else:
            self.index_path = os.path.join(posts_root(), INDEX_FILE_NAME)
        self.documents: list[dict[str, Any]] = []
        self.load_index()

    def load_index(self) -> None:
        """Laad bestaande index vanaf schijf indien aanwezig."""
        if os.path.isfile(self.index_path):
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
            except Exception as e:
                print(f"Waarschuwing: Kon RAG index niet laden: {e}")
                self.documents = []

    def save_index(self) -> None:
        """Sla index op naar schijf."""
        try:
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Fout bij opslaan RAG index: {e}")

    def index_all_posts(self, root_dir: str | None = None) -> int:
        """Scant alle posts in posts/ en indexeert Markdown bestanden."""
        pdir = root_dir or posts_root()
        if not os.path.exists(pdir):
            return 0

        new_docs: list[dict[str, Any]] = []

        for entry in os.listdir(pdir):
            post_path = os.path.join(pdir, entry)
            if not os.path.isdir(post_path) or entry.startswith("."):
                continue

            # Zoek relevante Markdown artefacten (draft.md, synthese.md, outline.md)
            for fname in ["draft.md", "synthese.md", "outline.md", "briefing.md"]:
                fpath = os.path.join(post_path, fname)
                if os.path.isfile(fpath):
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Opsplitsen in alinea's (chunks)
                        paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 40]
                        for idx, para in enumerate(paragraphs):
                            tokens = _tokenize(para)
                            if tokens:
                                new_docs.append({
                                    "slug": entry,
                                    "filename": fname,
                                    "chunk_id": f"{entry}:{fname}:{idx}",
                                    "text": para,
                                    "tokens": tokens,
                                })
                    except Exception as e:
                        print(f"Fout bij indexeren {fpath}: {e}")

        self.documents = new_docs
        self.save_index()
        return len(self.documents)

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
            
            # TF-IDF Cosine similarity berekening
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

        # Sorteer op hoogste score
        results.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in results[:top_k]]


# Singleton instantie
archive_vectorstore = LocalRAGArchive()
