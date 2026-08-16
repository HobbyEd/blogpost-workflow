"""Lokale RAG Archief Vectorstore voor Blogpost Archief Consistentie (ADR-006 & ADR-008).

Ondersteunt asynchrone non-blocking achtergrond-indexering, incrementele updates
en statusbewaking voor de Beheer-interface.

Retrieval is lexicaal: TF-IDF met cosine-gelijkenis over unigrammen en bigrammen.
Er zijn geen embeddings; zie ADR-006 voor de afweging.
"""

from __future__ import annotations

import json
import math
import os
import re
import threading
import time
from collections import Counter
from html import unescape
from typing import Any
import httpx

from .repository import now_iso, posts_root

INDEX_FILE_NAME = ".archive_rag_index.json"
INDEX_FORMAT_VERSION = 2
WP_POSTS_URL = "https://edwinvandillen.nl/?rest_route=/wp/v2/posts"

#: Hoe zwaar titelwoorden meetellen in een chunk. Een post met "intentie" in de titel
#: gaat over intentie, ook in de alinea's die het woord zelf niet herhalen.
TITLE_WEIGHT = 2


def _tokenize(text: str) -> list[str]:
    """Zet tekst om naar opgeschoonde lowercase unigrammen en bigrammen."""
    text_clean = re.sub(r"[^\w\s]", " ", text.lower())
    words = [w for w in text_clean.split() if len(w) > 2]
    bigrammen = [f"{words[i]}_{words[i+1]}" for i in range(len(words) - 1)]
    return words + bigrammen


def _local_source_id(slug: str, filename: str) -> str:
    """Bron-id van een lokaal artefact; alle chunks eruit delen deze id."""
    return f"local:{slug}:{filename}"


def _wp_source_id(slug: str) -> str:
    """Bron-id van een live WordPress-artikel; alle chunks eruit delen deze id."""
    return f"wp:{slug}"


def _chunk_tf(text: str, title: str) -> dict[str, int]:
    """Termfrequenties van een chunk, met de titel als extra zwaar wegend veld."""
    counts = Counter(_tokenize(text))
    for token in _tokenize(title):
        counts[token] += TITLE_WEIGHT
    return dict(counts)


class LocalRAGArchive:
    """Lokale TF-IDF vectorstore over het blogpost-archief.

    De index is een lijst chunks. Elke chunk hoort bij precies één live
    WordPress-artikel (`source_id` = `wp:<slug>`). De site is de enige bron
    van waarheid (ADR-006 §6). Lokale werkmappen worden niet geïndexeerd.
    Een bron wordt altijd in zijn geheel vervangen, nooit chunk voor chunk
    aangevuld, zodat verouderde tekst niet blijft staan.
    """

    def __init__(self, index_path: str | None = None):
        self._explicit_index_path = index_path
        self._loaded_from: str | None = None
        self.documents: list[dict[str, Any]] = []
        self.last_indexed_at: str | None = None
        self.is_indexing: bool = False
        self.progress_current: int = 0
        self.progress_total: int = 0
        self.current_item: str = ""
        self.status_message: str = ""
        self.doc_freq: dict[str, int] = {}
        self._doc_norms: list[float] = []
        self._lock = threading.RLock()
        self.load_index()

    # ------------------------------------------------------------------
    # Persistentie
    # ------------------------------------------------------------------

    @property
    def index_path(self) -> str:
        """Pad naar het indexbestand, afgeleid van de actuele postmap.

        Dit wordt bewust niet bij constructie vastgelegd. De store is een
        module-singleton, terwijl `BLOGPOST_POSTS_DIR` per aanroep kan verschillen
        (de testsuite doet dat). Een vastgelegd pad zorgde ervoor dat een run op een
        tijdelijke postmap de echte index overschreef.
        """
        if self._explicit_index_path:
            return self._explicit_index_path
        return os.path.join(posts_root(), INDEX_FILE_NAME)

    def _ensure_loaded(self) -> None:
        """Herlaad de index wanneer de postmap sinds de vorige aanroep gewisseld is."""
        if self._loaded_from != self.index_path:
            self.load_index()

    def load_index(self) -> None:
        """Laad de vectorindex van schijf (ADR-008)."""
        with self._lock:
            self.documents = []
            self.doc_freq = {}
            self._doc_norms = []
            self.last_indexed_at = None
            self._loaded_from = self.index_path
            if not os.path.exists(self.index_path):
                return
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.last_indexed_at = data.get("last_indexed_at")
                self.documents = data.get("documents", [])
                self.doc_freq = data.get("doc_freq") or {}
            except Exception as e:
                print(f"Waarschuwing: Kan RAG-index niet laden: {e}")
                self.documents = []
                self.doc_freq = {}
                return

            self._migrate_loaded_documents()
            if self.doc_freq:
                self._recompute_norms()
            else:
                self._rebuild_stats()

    def _migrate_loaded_documents(self) -> None:
        """Breng chunks uit een oudere indexversie naar het huidige formaat."""
        for doc in self.documents:
            if "tf" not in doc:
                doc["tf"] = dict(Counter(doc.pop("tokens", [])))
            if "source_id" not in doc:
                if doc.get("filename") == "wordpress_live":
                    doc["source_id"] = _wp_source_id(doc.get("slug", ""))
                else:
                    doc["source_id"] = _local_source_id(
                        doc.get("slug", ""), doc.get("filename", "")
                    )

    def save_index(self) -> None:
        """Sla index op naar schijf (atomisch via temp file)."""
        with self._lock:
            self.last_indexed_at = now_iso()
            self._loaded_from = self.index_path
            payload = {
                "format_version": INDEX_FORMAT_VERSION,
                "last_indexed_at": self.last_indexed_at,
                "documents_count": len(self.documents),
                "doc_freq": self.doc_freq,
                "documents": self.documents,
            }
            temp_path = f"{self.index_path}.tmp"
            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False)
                os.replace(temp_path, self.index_path)
            except Exception as e:
                print(f"Fout bij opslaan RAG index: {e}")

    # ------------------------------------------------------------------
    # Statistiek (IDF)
    # ------------------------------------------------------------------

    def _rebuild_stats(self) -> None:
        """Herbereken document frequencies en de genormaliseerde documentlengtes."""
        df: Counter[str] = Counter()
        for doc in self.documents:
            df.update(doc["tf"].keys())
        self.doc_freq = dict(df)
        self._recompute_norms()

    def _idf(self, token: str) -> float:
        """Gesmoothde inverse document frequency; onbekende termen krijgen het maximum."""
        n = len(self.documents)
        if n == 0:
            return 0.0
        return math.log((n + 1) / (self.doc_freq.get(token, 0) + 1)) + 1.0

    def _recompute_norms(self) -> None:
        """Cache de TF-IDF vectorlengte per document voor de cosine-noemer."""
        self._doc_norms = [
            math.sqrt(sum((count * self._idf(token)) ** 2 for token, count in doc["tf"].items()))
            for doc in self.documents
        ]

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """Haal actuele RAG beheer- en indexeringsstatus op."""
        self._ensure_loaded()
        articles_map: dict[str, dict[str, Any]] = {}
        for doc in self.documents:
            slug = doc["slug"]
            if slug not in articles_map:
                articles_map[slug] = {
                    "slug": slug,
                    "title": doc.get("title", slug),
                    "chunks_count": 0,
                    "last_modified": doc.get("mtime", "onbekend"),
                    "origin": "wordpress",
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

    # ------------------------------------------------------------------
    # Indexeren
    # ------------------------------------------------------------------

    def fetch_wordpress_posts(self, delay_seconds: float = 0.4) -> tuple[list[dict[str, Any]], bool]:
        """Haal gepubliceerde artikelen op via de WordPress REST API van edwinvandillen.nl.

        Geeft de chunks terug plus een vlag of het ophalen volledig geslaagd is.
        Die vlag bepaalt of tombstoning van WordPress-bronnen veilig is: bij een
        halve fetch zou anders het halve archief uit de index verdwijnen.
        """
        # status=publish is verplicht: concepten en privéberichten zijn geen archief.
        page = 1
        all_wp_docs: list[dict[str, Any]] = []
        complete = False

        while True:
            url = f"{WP_POSTS_URL}&status=publish&per_page=10&page={page}"
            try:
                r = httpx.get(url, timeout=15)
                if r.status_code != 200:
                    break
                posts = r.json()
                if not posts:
                    complete = True
                    break

                for p in posts:
                    slug = p.get("slug", "")
                    title = unescape(p.get("title", {}).get("rendered", slug))
                    modified = p.get("modified", now_iso())
                    raw_content = p.get("content", {}).get("rendered", "")
                    clean_text = unescape(re.sub(r"<[^>]+>", " ", raw_content))
                    all_wp_docs.extend(self.chunk_live_article(slug, title, clean_text, modified))

                total_pages = int(r.headers.get("X-WP-TotalPages", 1))
                if page >= total_pages:
                    complete = True
                    break
                page += 1
                time.sleep(delay_seconds)
            except Exception as e:
                print(f"Fout bij ophalen WordPress pagina {page}: {e}")
                break

        return all_wp_docs, complete

    def _source_mtimes(self) -> dict[str, str]:
        """Huidige mtime per bron-id, zoals die in de index staat."""
        return {doc["source_id"]: doc.get("mtime", "") for doc in self.documents}

    def _replace_source(self, source_id: str, chunks: list[dict[str, Any]]) -> None:
        """Vervang alle chunks van één bron; verwijdert de bron als chunks leeg is."""
        self.documents = [d for d in self.documents if d.get("source_id") != source_id]
        self.documents.extend(chunks)

    @staticmethod
    def chunk_live_article(
        slug: str,
        title: str,
        text: str,
        mtime: str,
    ) -> list[dict[str, Any]]:
        """Splits live artikeltekst in alinea-chunks. Alleen voor WordPress-bronnen."""
        chunks: list[dict[str, Any]] = []
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) > 40]
        for p_idx, para in enumerate(paragraphs):
            tokens = _tokenize(para)
            if tokens:
                chunks.append({
                    "slug": slug,
                    "title": title,
                    "filename": "wordpress_live",
                    "source_id": _wp_source_id(slug),
                    "chunk_id": f"wp:{slug}:{p_idx}",
                    "mtime": mtime,
                    "text": para,
                    "tf": _chunk_tf(para, title),
                })
        return chunks

    def index_all_posts(
        self,
        root_dir: str | None = None,
        incremental: bool = False,
        purge: bool = False,
        include_wordpress: bool = True,
    ) -> int:
        """Indexeer uitsluitend live artikelen van edwinvandillen.nl (ADR-006 §6).

        Lokale werkmappen worden niet gelezen. Bestaande `local:`-chunks verdwijnen
        bij elke run. `include_wordpress=False` is alleen voor tests: geen netwerk,
        wel opruimen van lokale resten.
        """
        with self._lock:
            self._ensure_loaded()
            self.is_indexing = True
            try:
                if purge:
                    self.documents = []

                known_mtimes = self._source_mtimes() if incremental else {}

                # Werk in uitvoering hoort niet in het archief, ook niet als het
                # in een oudere index is blijven staan.
                self.documents = [
                    d for d in self.documents
                    if not str(d.get("source_id", "")).startswith("local:")
                ]

                self.progress_total = 6
                self.progress_current = 0

                if include_wordpress:
                    self.status_message = "Ophalen live artikelen van edwinvandillen.nl (WordPress REST API)..."
                    wp_docs, fetch_complete = self.fetch_wordpress_posts(delay_seconds=0.4)

                    by_source: dict[str, list[dict[str, Any]]] = {}
                    for doc in wp_docs:
                        by_source.setdefault(doc["source_id"], []).append(doc)

                    for source_id, chunks in by_source.items():
                        if incremental and known_mtimes.get(source_id) == chunks[0]["mtime"]:
                            continue
                        self._replace_source(source_id, chunks)

                    if fetch_complete:
                        # Tombstoning van artikelen die van de site verdwenen zijn.
                        self.documents = [
                            d for d in self.documents
                            if not str(d.get("source_id", "")).startswith("wp:")
                            or d["source_id"] in by_source
                        ]
                    else:
                        self.status_message = "Waarschuwing: WordPress-fetch onvolledig; bestaande artikelen behouden."

                self._rebuild_stats()
                self.progress_current = self.progress_total
                self.save_index()
                unique_posts = len({d["slug"] for d in self.documents})
                self.status_message = f"Indexatie afgerond: {len(self.documents)} chunks uit {unique_posts} artikelen geïndexeerd."
                self.current_item = ""
                return len(self.documents)
            finally:
                self.is_indexing = False

    # ------------------------------------------------------------------
    # Zoeken
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 5,
        exclude_slug: str | None = None,
        per_slug_limit: int = 2,
    ) -> list[dict[str, Any]]:
        """Zoek passages op TF-IDF cosine-gelijkenis met de zoekopdracht.

        `per_slug_limit` begrenst het aantal passages per post. Zonder die grens vult
        de post met de meeste rake alinea's de hele ranglijst, terwijl de vraag
        "waar heb ik dit eerder gezegd" juist om verschillende posts vraagt. Zet op
        0 om alle passages toe te laten.
        """
        query_tokens = _tokenize(query)
        with self._lock:
            self._ensure_loaded()
            if not query_tokens or not self.documents:
                return []
            if len(self._doc_norms) != len(self.documents):
                self._recompute_norms()

            query_tf = Counter(query_tokens)
            query_weights = {t: c * self._idf(t) for t, c in query_tf.items()}
            norm_q = math.sqrt(sum(w * w for w in query_weights.values()))
            if norm_q == 0:
                return []

            results: list[tuple[float, dict[str, Any]]] = []
            for doc, norm_d in zip(self.documents, self._doc_norms):
                if norm_d == 0:
                    continue
                if exclude_slug and doc["slug"] == exclude_slug:
                    continue
                doc_tf = doc["tf"]
                common = query_weights.keys() & doc_tf.keys()
                if not common:
                    continue

                dot_product = sum(query_weights[t] * doc_tf[t] * self._idf(t) for t in common)
                score = dot_product / (norm_q * norm_d)

                if score > 0.05:
                    results.append((score, {
                        "slug": doc["slug"],
                        "title": doc.get("title", doc["slug"]),
                        "filename": doc["filename"],
                        "chunk_id": doc["chunk_id"],
                        "score": round(score, 4),
                        "text": doc["text"],
                    }))

            results.sort(key=lambda x: x[0], reverse=True)

            selected: list[dict[str, Any]] = []
            per_slug: Counter[str] = Counter()
            overflow: list[dict[str, Any]] = []
            for _, hit in results:
                if per_slug_limit and per_slug[hit["slug"]] >= per_slug_limit:
                    overflow.append(hit)
                    continue
                per_slug[hit["slug"]] += 1
                selected.append(hit)
                if len(selected) >= top_k:
                    return selected

            # Zijn er te weinig verschillende posts, vul dan aan met de rest.
            return (selected + overflow)[:top_k]


# Singleton instantie
archive_vectorstore = LocalRAGArchive()
