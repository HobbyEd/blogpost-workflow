"""Unit test suite voor de FastAPI Web Server REST API (server.py)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from fastapi.testclient import TestClient

from server import app, service


class TestServerAPI(unittest.TestCase):

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.tmp_dir = tempfile.mkdtemp()
        os.environ["BLOGPOST_POSTS_DIR"] = self.tmp_dir

    def tearDown(self) -> None:
        os.environ.pop("BLOGPOST_POSTS_DIR", None)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_read_root(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("html", response.headers.get("content-type", "").lower())
        self.assertIn("Blogpost Command Center", response.text)

    def test_list_posts_empty(self) -> None:
        response = self.client.get("/api/posts")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["posts"], [])

    def test_init_and_get_post_lifecycle(self) -> None:
        slug = "api-test-post"
        titel = "API Test Post"

        # 1. Init post via API met intake gate
        response = self.client.post(
            "/api/posts/init",
            json={"slug": slug, "titel": titel, "yolo": False, "wait_intake_gate": True},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["state"]["slug"], slug)

        # 2. List posts verifieert dat de post aanwezig is
        list_res = self.client.get("/api/posts")
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(list_res.json()["count"], 1)

        # 3. Get post detail opvragen
        detail_res = self.client.get(f"/api/posts/{slug}")
        self.assertEqual(detail_res.status_code, 200)
        detail_data = detail_res.json()
        self.assertEqual(detail_data["slug"], slug)
        self.assertIn("markdown_table", detail_data)

        # 4. Gate goedkeuren (intake -> outline ready)
        app_res = self.client.post(
            f"/api/posts/{slug}/approve",
            json={"note": "API Goedgekeurd"},
        )
        self.assertEqual(app_res.status_code, 200)
        self.assertTrue(app_res.json()["ok"])
        self.assertEqual(app_res.json()["phase"], "outline")
        self.assertEqual(app_res.json()["status"], "ready")

        # 5. Vlag instellen
        flag_res = self.client.post(
            f"/api/posts/{slug}/flags",
            json={"name": "skip_synthesis", "value": True},
        )
        self.assertEqual(flag_res.status_code, 200)
        self.assertTrue(flag_res.json()["flags"]["skip_synthesis"])

        # 6. Doctor inspectie
        doc_res = self.client.get(f"/api/posts/{slug}/doctor")
        self.assertEqual(doc_res.status_code, 200)
        self.assertEqual(doc_res.json()["slug"], slug)

    def test_init_invalid_slug_returns_400(self) -> None:
        response = self.client.post(
            "/api/posts/init",
            json={"slug": "ongeldige_slug_met_HOOFDLETTERS!", "titel": "Fout"},
        )
        self.assertEqual(response.status_code, 400)

    def test_chat_brainstorm_lifecycle(self) -> None:
        session_id = "test-chat-123"
        topic = "Socratische AI Architectuur"
        slug = "socratische-ai-architectuur"

        # 1. Start chat
        res1 = self.client.post("/api/chat/start", json={"session_id": session_id, "topic": topic})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(len(res1.json()["messages"]), 1)

        # 2. Stuur user bericht
        res2 = self.client.post("/api/chat/message", json={"session_id": session_id, "message": "De kernboodschap is dat AI socratisch moet meedenken."})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(len(res2.json()["messages"]), 3)

        # 3. Finalize chat en genereer briefing.md
        res3 = self.client.post("/api/chat/finalize", json={"session_id": session_id, "slug": slug, "titel": topic, "yolo": True})
        self.assertEqual(res3.status_code, 200)
        self.assertTrue(res3.json()["ok"])

        # 4. RAG Reindex en Search testen
        reindex_res = self.client.post("/api/rag/reindex")
        self.assertEqual(reindex_res.status_code, 200)

        search_res = self.client.get("/api/rag/search?q=socratische")
        self.assertEqual(search_res.status_code, 200)

        # 5. Archief-consistentie: het endpoint leest het verdict uit het rapport dat de
        # subagent schrijft (ADR-007). Zonder rapport is dat een 404, geen lege analyse.
        leeg_res = self.client.post(f"/api/posts/{slug}/validate-alignment")
        self.assertEqual(leeg_res.status_code, 404)

        report = (
            "# Archief-consistentie (ADR-007)\n\n"
            '```json\n{"status": "ALIGNMENT_OK", "discrepancies": []}\n```\n\n'
            "Geen tegenspraak gevonden.\n"
        )
        with open(os.path.join(self.tmp_dir, slug, "archief-consistentie.md"), "w", encoding="utf-8") as f:
            f.write(report)

        val_res = self.client.post(f"/api/posts/{slug}/validate-alignment")
        self.assertEqual(val_res.status_code, 200)
        val_data = val_res.json()
        self.assertTrue(val_data["ok"])
        self.assertEqual(val_data["alignment_status"], "ALIGNMENT_OK")
        self.assertFalse(val_data["is_discrepant"])
        self.assertTrue(os.path.isfile(val_data["report_path"]))

        # 6. RAG Status en Background Indexing (ADR-008)
        status_res = self.client.get("/api/rag/status")
        self.assertEqual(status_res.status_code, 200)
        self.assertIn("total_chunks", status_res.json())

        async_reindex_res = self.client.post("/api/rag/reindex-async", json={"purge_and_rebuild": False, "incremental": True})
        self.assertEqual(async_reindex_res.status_code, 202)
        self.assertTrue(async_reindex_res.json()["ok"])

    def test_return_outline_gate(self) -> None:
        slug = "api-return-post"
        self.client.post(
            "/api/posts/init",
            json={"slug": slug, "titel": "Return Test", "yolo": False},
        )
        self.client.post(f"/api/posts/{slug}/run/outline")
        with open(os.path.join(self.tmp_dir, slug, "outline.md"), "w", encoding="utf-8") as f:
            f.write("Eerste outline\n")
        self.client.post(f"/api/posts/{slug}/complete/outline")

        leeg = self.client.post(f"/api/posts/{slug}/return", json={"note": ""})
        self.assertEqual(leeg.status_code, 422)

        ok = self.client.post(
            f"/api/posts/{slug}/return",
            json={"note": "Geen Sinek-sectie."},
        )
        self.assertEqual(ok.status_code, 200, ok.text)
        data = ok.json()
        self.assertTrue(data["ok"])
        self.assertTrue(data["returned"])
        self.assertEqual(data["status"], "running")
        self.assertEqual(data["phase"], "outline")
        self.assertEqual(data["agent_brief"]["author_note"], "Geen Sinek-sectie.")

        te_vroeg = self.client.post(
            f"/api/posts/{slug}/return",
            json={"note": "Nog een keer."},
        )
        self.assertEqual(te_vroeg.status_code, 400)

    def test_return_vanuit_draft_ready(self) -> None:
        slug = "api-return-vanuit-draft"
        self.client.post(
            "/api/posts/init",
            json={"slug": slug, "titel": "Terug vanuit draft", "yolo": False},
        )
        self.client.post(f"/api/posts/{slug}/run/outline")
        with open(os.path.join(self.tmp_dir, slug, "outline.md"), "w", encoding="utf-8") as f:
            f.write("Eerste outline\n")
        self.client.post(f"/api/posts/{slug}/complete/outline")
        self.client.post(f"/api/posts/{slug}/approve", json={"note": "ok"})

        detail = self.client.get(f"/api/posts/{slug}")
        self.assertEqual(detail.status_code, 200)
        self.assertIn("outline", detail.json()["returnable_phases"])

        ok = self.client.post(
            f"/api/posts/{slug}/return",
            json={"note": "Geen Sinek-sectie.", "phase": "outline"},
        )
        self.assertEqual(ok.status_code, 200, ok.text)
        data = ok.json()
        self.assertTrue(data["returned"])
        self.assertEqual(data["returned_to"], "outline")
        self.assertEqual(data["status"], "running")
        self.assertEqual(data["agent_brief"]["author_note"], "Geen Sinek-sectie.")


if __name__ == "__main__":
    unittest.main()
