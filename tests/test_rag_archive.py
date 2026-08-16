"""Unit testsuite voor de lokale RAG archiefindex (ADR-006 & ADR-008).

De index bevat alleen live artikelen. Tests injecteren WordPress-chunks of
mocken de fetch; er is geen netwerkverkeer naar edwinvandillen.nl.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest

from scripts.orchestrator.rag_archive import LocalRAGArchive, _local_source_id, _wp_source_id


PARAGRAAF_A = (
    "Intentie is de reden waarom een systeem gebouwd wordt, en die reden verdwijnt "
    "zodra de code geschreven is en niemand haar heeft vastgelegd.\n"
)
PARAGRAAF_B = (
    "Stroomopwaarts betekent dat de controle naar voren wordt gehaald, naar het moment "
    "waarop de bedoeling nog gevormd wordt in plaats van achteraf getoetst.\n"
)


class RAGTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.index_path = os.path.join(self.tmp_dir, "index.json")
        self.posts_dir = os.path.join(self.tmp_dir, "posts")
        os.makedirs(self.posts_dir)
        self.store = LocalRAGArchive(index_path=self.index_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def write_artefact(self, slug: str, filename: str, content: str) -> str:
        pdir = os.path.join(self.posts_dir, slug)
        os.makedirs(pdir, exist_ok=True)
        path = os.path.join(pdir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def add_live(
        self,
        slug: str,
        text: str,
        title: str | None = None,
        mtime: str = "2026-08-01T00:00:00",
    ) -> list[dict]:
        """Zet een live artikel in de index, zoals de WordPress-fetch dat zou doen."""
        chunks = LocalRAGArchive.chunk_live_article(slug, title or slug, text, mtime)
        self.store._replace_source(_wp_source_id(slug), chunks)
        self.store._rebuild_stats()
        self.store.save_index()
        return chunks

    def texts(self) -> list[str]:
        return [d["text"] for d in self.store.documents]


class TestIndexeren(RAGTestBase):
    def test_lokale_artefacten_komen_niet_in_de_index(self) -> None:
        self.write_artefact("intentie-3-waarom-intentie-zich-verstopt", "outline.md", PARAGRAAF_A)
        self.write_artefact("intentie-3-waarom-intentie-zich-verstopt", "draft.md", PARAGRAAF_B)
        self.store.index_all_posts(self.posts_dir, include_wordpress=False)

        self.assertEqual(self.store.documents, [])

    def test_bestaande_local_chunks_worden_gestript(self) -> None:
        self.store.documents.append({
            "slug": "intentie-3",
            "title": "intentie-3",
            "filename": "outline.md",
            "source_id": _local_source_id("intentie-3", "outline.md"),
            "chunk_id": "intentie-3:outline.md:0",
            "mtime": "2026-08-12T00:00:00",
            "text": PARAGRAAF_A,
            "tf": {"intentie": 1},
        })
        self.add_live("live-post", PARAGRAAF_B)
        self.store.index_all_posts(include_wordpress=False)

        self.assertEqual({d["slug"] for d in self.store.documents}, {"live-post"})
        self.assertTrue(all(d["source_id"].startswith("wp:") for d in self.store.documents))

    def test_gewijzigd_live_artikel_wordt_incrementeel_opnieuw_geindexeerd(self) -> None:
        self.add_live("post-een", PARAGRAAF_A, mtime="2026-08-01T00:00:00")

        nieuw = LocalRAGArchive.chunk_live_article(
            "post-een", "post-een", PARAGRAAF_B, "2026-08-16T00:00:00"
        )
        self.store.fetch_wordpress_posts = lambda delay_seconds=0.4: (nieuw, True)
        self.store.index_all_posts(include_wordpress=True, incremental=True)

        self.assertTrue(any("Stroomopwaarts betekent" in t for t in self.texts()))
        self.assertFalse(any("Intentie is de reden" in t for t in self.texts()))

    def test_ongewijzigd_live_artikel_wordt_incrementeel_overgeslagen(self) -> None:
        chunks = self.add_live("post-een", PARAGRAAF_A, mtime="2026-08-01T00:00:00")
        self.store.fetch_wordpress_posts = lambda delay_seconds=0.4: (chunks, True)
        eerste = list(self.store.documents)
        self.store.index_all_posts(include_wordpress=True, incremental=True)
        self.assertEqual(len(self.store.documents), len(eerste))

    def test_verdwenen_live_artikel_wordt_getombstoned(self) -> None:
        self.add_live("post-een", PARAGRAAF_A)
        self.add_live("post-twee", PARAGRAAF_B)
        blijvers = [d for d in self.store.documents if d["slug"] == "post-twee"]
        self.store.fetch_wordpress_posts = lambda delay_seconds=0.4: (blijvers, True)
        self.store.index_all_posts(include_wordpress=True, incremental=True)
        self.assertEqual({d["slug"] for d in self.store.documents}, {"post-twee"})

    def test_onvolledige_fetch_wist_bestaande_artikelen_niet(self) -> None:
        self.add_live("post-een", PARAGRAAF_A)
        self.store.fetch_wordpress_posts = lambda delay_seconds=0.4: ([], False)
        self.store.index_all_posts(include_wordpress=True)
        self.assertIn("post-een", {d["slug"] for d in self.store.documents})

    def test_purge_wist_alles(self) -> None:
        self.add_live("post-een", PARAGRAAF_A)
        self.store.fetch_wordpress_posts = lambda delay_seconds=0.4: ([], True)
        self.store.index_all_posts(include_wordpress=True, purge=True)
        self.assertEqual(self.store.documents, [])


class TestPersistentie(RAGTestBase):
    def test_index_overleeft_herladen(self) -> None:
        self.add_live("post-een", PARAGRAAF_A)
        opnieuw = LocalRAGArchive(index_path=self.index_path)
        self.assertEqual(len(opnieuw.documents), len(self.store.documents))
        self.assertTrue(opnieuw.doc_freq)
        self.assertEqual(len(opnieuw._doc_norms), len(opnieuw.documents))

    def test_oud_indexformaat_wordt_gemigreerd(self) -> None:
        """Een index zonder tf/source_id (formaat 1) moet leesbaar blijven."""
        legacy = {
            "last_indexed_at": "2026-08-01T00:00:00+00:00",
            "documents": [{
                "slug": "oude-post",
                "title": "Oude post",
                "filename": "wordpress_live",
                "chunk_id": "wp:oude-post:0",
                "mtime": "2026-08-01T00:00:00",
                "text": PARAGRAAF_A,
                "tokens": ["intentie", "reden", "intentie"],
            }],
        }
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(legacy, f)

        store = LocalRAGArchive(index_path=self.index_path)
        doc = store.documents[0]
        self.assertEqual(doc["tf"], {"intentie": 2, "reden": 1})
        self.assertEqual(doc["source_id"], "wp:oude-post")
        self.assertTrue(store.search("intentie"))


class TestPostmapWisseling(RAGTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.vorige_env = os.environ.get("BLOGPOST_POSTS_DIR")

    def tearDown(self) -> None:
        if self.vorige_env is None:
            os.environ.pop("BLOGPOST_POSTS_DIR", None)
        else:
            os.environ["BLOGPOST_POSTS_DIR"] = self.vorige_env
        super().tearDown()

    def test_indexpad_volgt_de_actuele_postmap(self) -> None:
        echte_map = os.path.join(self.tmp_dir, "echt")
        andere_map = os.path.join(self.tmp_dir, "ander")
        os.makedirs(echte_map)
        os.makedirs(andere_map)

        store = LocalRAGArchive()
        os.environ["BLOGPOST_POSTS_DIR"] = echte_map
        store.index_all_posts(include_wordpress=False)
        echt_index = os.path.join(echte_map, ".archive_rag_index.json")
        self.assertTrue(os.path.isfile(echt_index))
        inhoud_voor = open(echt_index, encoding="utf-8").read()

        os.environ["BLOGPOST_POSTS_DIR"] = andere_map
        store.index_all_posts(include_wordpress=False)

        self.assertTrue(os.path.isfile(os.path.join(andere_map, ".archive_rag_index.json")))
        self.assertEqual(
            inhoud_voor,
            open(echt_index, encoding="utf-8").read(),
            "de index van de eerste postmap mag niet overschreven zijn",
        )

    def test_zoeken_ziet_de_index_van_de_actuele_postmap(self) -> None:
        os.environ["BLOGPOST_POSTS_DIR"] = self.posts_dir
        store = LocalRAGArchive()
        chunks = LocalRAGArchive.chunk_live_article(
            "post-een", "post-een", PARAGRAAF_A, "2026-08-01T00:00:00"
        )
        store._replace_source(_wp_source_id("post-een"), chunks)
        store._rebuild_stats()
        store.save_index()
        self.assertTrue(store.search("intentie reden"))

        os.environ["BLOGPOST_POSTS_DIR"] = os.path.join(self.tmp_dir, "leeg")
        os.makedirs(os.environ["BLOGPOST_POSTS_DIR"])
        self.assertEqual(store.search("intentie reden"), [])


class TestZoeken(RAGTestBase):
    def test_idf_weegt_zeldzame_termen_zwaarder(self) -> None:
        gedeeld = "software software software engineering engineering engineering"
        for i in range(8):
            self.add_live(f"ruis-{i}", f"{gedeeld} en nog wat vulling erbij.\n")
        self.add_live("de-juiste", f"{gedeeld} en hier staat het woord stroomopwaarts.\n")

        treffers = self.store.search("software engineering stroomopwaarts", top_k=1)
        self.assertEqual(treffers[0]["slug"], "de-juiste")

    def test_per_slug_limit_spreidt_over_posts(self) -> None:
        alineas = "\n\n".join(f"{PARAGRAAF_A.strip()} Variant {i} van dezelfde alinea." for i in range(6))
        self.add_live("veelprater", alineas)
        self.add_live("stille-post", PARAGRAAF_A)

        treffers = self.store.search("intentie reden systeem", top_k=3, per_slug_limit=2)
        self.assertEqual(len(treffers), 3)
        self.assertEqual(sum(1 for t in treffers if t["slug"] == "veelprater"), 2)
        self.assertIn("stille-post", {t["slug"] for t in treffers})

    def test_te_weinig_posts_vult_aan_met_extra_passages(self) -> None:
        alineas = "\n\n".join(f"{PARAGRAAF_A.strip()} Variant {i} van dezelfde alinea." for i in range(6))
        self.add_live("veelprater", alineas)

        treffers = self.store.search("intentie reden systeem", top_k=4, per_slug_limit=2)
        self.assertEqual(len(treffers), 4)

    def test_per_slug_limit_nul_laat_alles_toe(self) -> None:
        alineas = "\n\n".join(f"{PARAGRAAF_A.strip()} Variant {i}." for i in range(4))
        self.add_live("veelprater", alineas)

        treffers = self.store.search("intentie reden systeem", top_k=4, per_slug_limit=0)
        self.assertEqual(len(treffers), 4)

    def test_exclude_slug_filtert_de_eigen_post(self) -> None:
        self.add_live("huidige", PARAGRAAF_A)
        self.add_live("eerdere", PARAGRAAF_A)

        treffers = self.store.search("intentie reden systeem", top_k=10, exclude_slug="huidige")
        self.assertTrue(treffers)
        self.assertNotIn("huidige", {t["slug"] for t in treffers})

    def test_titelwoorden_wegen_mee(self) -> None:
        self.add_live("andere-slug", PARAGRAAF_B, title="volwassenheid en intentie")
        self.assertTrue(self.store.search("intentie volwassenheid"))

    def test_lege_index_en_lege_query(self) -> None:
        self.assertEqual(self.store.search("intentie"), [])
        self.add_live("post-een", PARAGRAAF_A)
        self.assertEqual(self.store.search(""), [])


class TestStatus(RAGTestBase):
    def test_status_telt_posts_en_chunks(self) -> None:
        self.add_live("post-een", PARAGRAAF_A)
        self.add_live("post-twee", PARAGRAAF_B)

        status = self.store.get_status()
        self.assertFalse(status["running"])
        self.assertEqual(status["total_posts"], 2)
        self.assertEqual(status["total_chunks"], len(self.store.documents))
        self.assertEqual({a["origin"] for a in status["articles"]}, {"wordpress"})


if __name__ == "__main__":
    unittest.main()
