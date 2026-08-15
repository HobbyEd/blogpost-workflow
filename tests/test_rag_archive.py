"""Unit testsuite voor de lokale RAG archiefindex (ADR-006 & ADR-008).

Alle tests draaien op een tijdelijke postmap en met `include_wordpress=False`,
zodat er geen netwerkverkeer naar edwinvandillen.nl nodig is.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
import unittest

from scripts.orchestrator.rag_archive import LocalRAGArchive, _wp_source_id


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

    def index(self, **kwargs) -> int:
        kwargs.setdefault("include_wordpress", False)
        return self.store.index_all_posts(self.posts_dir, **kwargs)

    def texts(self) -> list[str]:
        return [d["text"] for d in self.store.documents]


class TestIndexeren(RAGTestBase):
    def test_lokale_artefacten_komen_in_de_index(self) -> None:
        self.write_artefact("post-een", "draft.md", PARAGRAAF_A)
        self.write_artefact("post-een", "outline.md", PARAGRAAF_B)
        self.index()

        filenames = {d["filename"] for d in self.store.documents}
        self.assertEqual(filenames, {"draft.md", "outline.md"})
        self.assertTrue(all(d["source_id"].startswith("local:") for d in self.store.documents))

    def test_gewijzigd_bestand_wordt_incrementeel_opnieuw_geindexeerd(self) -> None:
        """De kern van bevinding A1b: een herschreven draft moet de index bijwerken."""
        path = self.write_artefact("post-een", "draft.md", PARAGRAAF_A)
        self.index()
        self.assertTrue(any("Intentie is de reden" in t for t in self.texts()))

        time.sleep(0.01)
        with open(path, "w", encoding="utf-8") as f:
            f.write(PARAGRAAF_B)
        self.index(incremental=True)

        self.assertTrue(any("Stroomopwaarts betekent" in t for t in self.texts()))
        self.assertFalse(
            any("Intentie is de reden" in t for t in self.texts()),
            "de oude versie van de alinea mag niet naast de nieuwe blijven staan",
        )

    def test_ongewijzigd_bestand_wordt_incrementeel_overgeslagen(self) -> None:
        self.write_artefact("post-een", "draft.md", PARAGRAAF_A)
        self.index()
        eerste = list(self.store.documents)

        self.index(incremental=True)
        self.assertEqual(len(self.store.documents), len(eerste))

    def test_verwijderd_bestand_verdwijnt_uit_de_index(self) -> None:
        """Tombstoning: bevinding A1c."""
        path = self.write_artefact("post-een", "draft.md", PARAGRAAF_A)
        self.write_artefact("post-twee", "draft.md", PARAGRAAF_B)
        self.index()
        self.assertEqual({d["slug"] for d in self.store.documents}, {"post-een", "post-twee"})

        os.remove(path)
        self.index(incremental=True)
        self.assertEqual({d["slug"] for d in self.store.documents}, {"post-twee"})

    def test_verwijderde_postmap_verdwijnt_uit_de_index(self) -> None:
        self.write_artefact("post-een", "draft.md", PARAGRAAF_A)
        self.write_artefact("post-twee", "draft.md", PARAGRAAF_B)
        self.index()

        shutil.rmtree(os.path.join(self.posts_dir, "post-een"))
        self.index(incremental=True)
        self.assertEqual({d["slug"] for d in self.store.documents}, {"post-twee"})

    def test_wordpress_chunks_blijven_staan_bij_lokale_herindexering(self) -> None:
        """Een lokale verversing mag het live archief niet uit de index gooien."""
        self.write_artefact("post-een", "draft.md", PARAGRAAF_A)
        self.index()
        self.store.documents.append({
            "slug": "live-post",
            "title": "Live post",
            "filename": "wordpress_live",
            "source_id": _wp_source_id("live-post"),
            "chunk_id": "wp:live-post:0",
            "mtime": "2026-01-01T00:00:00",
            "text": PARAGRAAF_B,
            "tf": {"stroomopwaarts": 1},
        })

        self.index(incremental=True)
        self.assertIn("live-post", {d["slug"] for d in self.store.documents})

        self.index(purge=False)
        self.assertIn(
            "live-post",
            {d["slug"] for d in self.store.documents},
            "een volledige lokale herbouw mag WordPress-chunks niet wissen",
        )

    def test_purge_wist_alles(self) -> None:
        self.write_artefact("post-een", "draft.md", PARAGRAAF_A)
        self.index()
        os.remove(os.path.join(self.posts_dir, "post-een", "draft.md"))

        self.index(purge=True)
        self.assertEqual(self.store.documents, [])


class TestPersistentie(RAGTestBase):
    def test_index_overleeft_herladen(self) -> None:
        self.write_artefact("post-een", "draft.md", PARAGRAAF_A)
        self.index()

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
                "filename": "draft.md",
                "chunk_id": "oude-post:draft.md:0",
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
        self.assertEqual(doc["source_id"], "local:oude-post:draft.md")
        self.assertTrue(store.search("intentie"))


class TestPostmapWisseling(RAGTestBase):
    """De module-singleton mag geen index van de ene postmap in de andere schrijven.

    Dit was de oorzaak van bevinding 1.3a: de testsuite verzet `BLOGPOST_POSTS_DIR`
    naar een tijdelijke map, terwijl het indexpad bij import was vastgelegd op de
    echte `posts/`. Elke testrun overschreef daardoor de echte index.
    """

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

        store = LocalRAGArchive()  # geen expliciet pad: volgt BLOGPOST_POSTS_DIR

        os.environ["BLOGPOST_POSTS_DIR"] = echte_map
        os.makedirs(os.path.join(echte_map, "post-een"))
        with open(os.path.join(echte_map, "post-een", "draft.md"), "w", encoding="utf-8") as f:
            f.write(PARAGRAAF_A)
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
        self.write_artefact("post-een", "draft.md", PARAGRAAF_A)

        store = LocalRAGArchive()
        store.index_all_posts(include_wordpress=False)
        self.assertTrue(store.search("intentie reden"))

        os.environ["BLOGPOST_POSTS_DIR"] = os.path.join(self.tmp_dir, "leeg")
        os.makedirs(os.environ["BLOGPOST_POSTS_DIR"])
        self.assertEqual(store.search("intentie reden"), [])


class TestZoeken(RAGTestBase):
    def test_idf_weegt_zeldzame_termen_zwaarder(self) -> None:
        """Zonder IDF wint de post die het algemene woord het vaakst herhaalt."""
        gedeeld = "software software software engineering engineering engineering"
        for i in range(8):
            self.write_artefact(f"ruis-{i}", "draft.md", f"{gedeeld} en nog wat vulling erbij.\n")
        self.write_artefact(
            "de-juiste", "draft.md", f"{gedeeld} en hier staat het woord stroomopwaarts.\n"
        )
        self.index()

        treffers = self.store.search("software engineering stroomopwaarts", top_k=1)
        self.assertEqual(treffers[0]["slug"], "de-juiste")

    def test_per_slug_limit_spreidt_over_posts(self) -> None:
        alineas = "\n\n".join(f"{PARAGRAAF_A.strip()} Variant {i} van dezelfde alinea." for i in range(6))
        self.write_artefact("veelprater", "draft.md", alineas)
        self.write_artefact("stille-post", "draft.md", PARAGRAAF_A)
        self.index()

        treffers = self.store.search("intentie reden systeem", top_k=3, per_slug_limit=2)
        self.assertEqual(len(treffers), 3)
        self.assertEqual(sum(1 for t in treffers if t["slug"] == "veelprater"), 2)
        self.assertIn("stille-post", {t["slug"] for t in treffers})

    def test_te_weinig_posts_vult_aan_met_extra_passages(self) -> None:
        """Liever meer passages uit dezelfde post dan een halflege ranglijst."""
        alineas = "\n\n".join(f"{PARAGRAAF_A.strip()} Variant {i} van dezelfde alinea." for i in range(6))
        self.write_artefact("veelprater", "draft.md", alineas)
        self.index()

        treffers = self.store.search("intentie reden systeem", top_k=4, per_slug_limit=2)
        self.assertEqual(len(treffers), 4)

    def test_per_slug_limit_nul_laat_alles_toe(self) -> None:
        alineas = "\n\n".join(f"{PARAGRAAF_A.strip()} Variant {i}." for i in range(4))
        self.write_artefact("veelprater", "draft.md", alineas)
        self.index()

        treffers = self.store.search("intentie reden systeem", top_k=4, per_slug_limit=0)
        self.assertEqual(len(treffers), 4)

    def test_exclude_slug_filtert_de_eigen_post(self) -> None:
        self.write_artefact("huidige", "draft.md", PARAGRAAF_A)
        self.write_artefact("eerdere", "draft.md", PARAGRAAF_A)
        self.index()

        treffers = self.store.search("intentie reden systeem", top_k=10, exclude_slug="huidige")
        self.assertTrue(treffers)
        self.assertNotIn("huidige", {t["slug"] for t in treffers})

    def test_titelwoorden_wegen_mee(self) -> None:
        self.write_artefact("volwassenheid-en-intentie", "draft.md", PARAGRAAF_B)
        self.index()

        self.assertTrue(self.store.search("intentie volwassenheid"))

    def test_lege_index_en_lege_query(self) -> None:
        self.assertEqual(self.store.search("intentie"), [])
        self.write_artefact("post-een", "draft.md", PARAGRAAF_A)
        self.index()
        self.assertEqual(self.store.search(""), [])


class TestStatus(RAGTestBase):
    def test_status_telt_posts_en_chunks(self) -> None:
        self.write_artefact("post-een", "draft.md", PARAGRAAF_A)
        self.write_artefact("post-twee", "draft.md", PARAGRAAF_B)
        self.index()

        status = self.store.get_status()
        self.assertFalse(status["running"])
        self.assertEqual(status["total_posts"], 2)
        self.assertEqual(status["total_chunks"], len(self.store.documents))
        self.assertEqual({a["origin"] for a in status["articles"]}, {"lokaal"})


if __name__ == "__main__":
    unittest.main()
