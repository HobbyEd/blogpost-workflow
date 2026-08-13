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
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("service", data)

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


if __name__ == "__main__":
    unittest.main()
