"""Tests voor het worker-heartbeatbestand en GET /api/worker."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

from fastapi.testclient import TestClient

from scripts.orchestrator import worker_status
from server import app


class HeartbeatTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self._prev = os.environ.get("BLOGPOST_POSTS_DIR")
        os.environ["BLOGPOST_POSTS_DIR"] = self.tmp_dir

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("BLOGPOST_POSTS_DIR", None)
        else:
            os.environ["BLOGPOST_POSTS_DIR"] = self._prev
        shutil.rmtree(self.tmp_dir, ignore_errors=True)


class TestReadWriteHeartbeat(HeartbeatTestBase):
    def test_geen_bestand_is_down(self) -> None:
        status = worker_status.read_status()
        self.assertFalse(status["alive"])
        self.assertEqual(status["state"], "down")
        self.assertIn("worker.py --watch", status["hint"])

    def test_verse_heartbeat_van_dit_proces_is_alive(self) -> None:
        worker_status.write_heartbeat(
            pid=os.getpid(),
            state="busy",
            job={"slug": "test-keten", "phase": "outline"},
            interval_s=30,
        )
        status = worker_status.read_status()
        self.assertTrue(status["alive"])
        self.assertEqual(status["state"], "busy")
        self.assertEqual(status["job"]["slug"], "test-keten")
        self.assertIsNone(status["hint"])

    def test_dode_pid_is_down(self) -> None:
        worker_status.write_heartbeat(pid=99999999, state="idle")
        status = worker_status.read_status()
        self.assertFalse(status["alive"])
        self.assertTrue(status["stale"])

    def test_clear_verwijdert_bestand(self) -> None:
        worker_status.write_heartbeat(pid=os.getpid(), state="idle")
        self.assertTrue(os.path.isfile(worker_status.heartbeat_path()))
        worker_status.clear_heartbeat()
        self.assertFalse(os.path.isfile(worker_status.heartbeat_path()))
        self.assertFalse(worker_status.read_status()["alive"])


class TestWorkerApi(HeartbeatTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.client = TestClient(app)

    def test_get_worker_zonder_bestand(self) -> None:
        res = self.client.get("/api/worker")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["alive"])
        self.assertEqual(data["state"], "down")

    def test_get_worker_met_heartbeat(self) -> None:
        worker_status.write_heartbeat(
            pid=os.getpid(),
            state="busy",
            job={"slug": "api-post", "phase": "draft"},
        )
        res = self.client.get("/api/worker")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["alive"])
        self.assertEqual(data["job"]["phase"], "draft")


if __name__ == "__main__":
    unittest.main()
