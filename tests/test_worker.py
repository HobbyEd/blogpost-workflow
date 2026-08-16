"""Tests voor de execution-plane worker.

Roept Claude Code niet aan. De runner is een testdubbel. Posts staan in een
tempdir via BLOGPOST_POSTS_DIR, nooit in de echte posts/.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from typing import Any
from unittest.mock import MagicMock

from scripts.orchestrator.service import WorkflowService
from scripts.worker import (
    WorkerError,
    extract_deploy_ids,
    find_running_jobs,
    format_prompt,
    run_once,
)


class WorkerTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self._prev_posts = os.environ.get("BLOGPOST_POSTS_DIR")
        os.environ["BLOGPOST_POSTS_DIR"] = self.tmp_dir
        self.service = WorkflowService()

    def tearDown(self) -> None:
        if self._prev_posts is None:
            os.environ.pop("BLOGPOST_POSTS_DIR", None)
        else:
            os.environ["BLOGPOST_POSTS_DIR"] = self._prev_posts
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def init_running(self, slug: str, phase: str = "outline") -> str:
        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel=slug, post_dir=pdir)
        if phase != "outline":
            raise AssertionError("deze testhulp start alleen outline")
        res = self.service.run_phase(phase=phase, post_dir=pdir)
        self.assertTrue(res["ok"], res)
        return pdir

    def write(self, slug: str, filename: str, content: str = "inhoud\n") -> None:
        path = os.path.join(self.tmp_dir, slug, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)


class TestFindRunningJobs(WorkerTestBase):
    def test_negeert_ready_en_waiting_gate(self) -> None:
        ready = os.path.join(self.tmp_dir, "klaar")
        self.service.init_post(slug="klaar", titel="Klaar", post_dir=ready)
        waiting = os.path.join(self.tmp_dir, "wacht")
        self.service.init_post(
            slug="wacht", titel="Wacht", post_dir=waiting, wait_intake_gate=True
        )

        self.assertEqual(find_running_jobs(self.service), [])

    def test_vindt_alleen_running(self) -> None:
        self.init_running("bezig")
        ready = os.path.join(self.tmp_dir, "klaar")
        self.service.init_post(slug="klaar", titel="Klaar", post_dir=ready)

        jobs = find_running_jobs(self.service)
        self.assertEqual([j["slug"] for j in jobs], ["bezig"])
        self.assertEqual(jobs[0]["phase"], "outline")
        self.assertEqual(jobs[0]["brief"]["agent"], "blogpost-onderzoeker")


class TestFormatPrompt(unittest.TestCase):
    def test_verbiedt_approve_en_de_skill(self) -> None:
        prompt = format_prompt(
            {
                "phase": "draft",
                "agent": "blogpost-schrijver",
                "post_dir": "posts/x",
                "inputs": ["posts/x/outline.md"],
                "outputs": ["posts/x/draft.md"],
                "instruction": "Roep blogpost-schrijver aan.",
            }
        )
        self.assertIn("blogpost-schrijver", prompt)
        self.assertIn("posts/x/draft.md", prompt)
        self.assertIn("Geen run, complete, approve of reject", prompt)
        self.assertIn("Roep de skill blogpost-workflow niet aan", prompt)

    def test_zet_author_note_apart_in_de_prompt(self) -> None:
        prompt = format_prompt(
            {
                "phase": "outline",
                "agent": "blogpost-onderzoeker",
                "post_dir": "posts/x",
                "outputs": ["posts/x/outline.md"],
                "instruction": "Schrijf een outline.",
                "author_note": "Geen Sinek-sectie.",
            }
        )
        self.assertIn("Opmerking van de auteur", prompt)
        self.assertIn("Geen Sinek-sectie.", prompt)
        self.assertIn("Plak de opmerking niet als extra alinea", prompt)


class TestExtractDeployIds(unittest.TestCase):
    def test_leest_json_velden(self) -> None:
        text = '{"post_id": 512, "status": "draft", "edit_url": "https://edwinvandillen.nl/wp-admin/post.php?post=512&action=edit"}'
        pid, url = extract_deploy_ids(text)
        self.assertEqual(pid, 512)
        self.assertTrue(url.endswith("post=512&action=edit"))

    def test_leeg_zonder_velden(self) -> None:
        self.assertEqual(extract_deploy_ids("geen json hier"), (None, None))


class TestRunOnce(WorkerTestBase):
    def test_idle_zonder_running(self) -> None:
        res = run_once(self.service)
        self.assertTrue(res["ok"])
        self.assertEqual(res["action"], "idle")

    def test_dry_run_roept_runner_niet(self) -> None:
        self.init_running("droog")
        runner = MagicMock()
        res = run_once(self.service, dry_run=True, runner=runner)
        self.assertEqual(res["action"], "dry_run")
        self.assertEqual(res["slug"], "droog")
        self.assertIn("outline.md", res["prompt"])
        runner.assert_not_called()

    def test_succes_schrijft_artefact_en_complete(self) -> None:
        self.init_running("werk")

        def runner(prompt: str, job: dict[str, Any]) -> dict[str, Any]:
            self.assertIn("blogpost-onderzoeker", prompt)
            self.write(job["slug"], "outline.md", "# Outline\n")
            return {"ok": True, "result": "klaar"}

        res = run_once(self.service, runner=runner)
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["action"], "completed")
        self.assertEqual(res["status"], "waiting_gate")
        self.assertFalse(res.get("yolo_advanced"))

        status = self.service.get_status(post="werk")
        self.assertEqual(status["phase"], "outline")
        self.assertEqual(status["status"], "waiting_gate")

    def test_runner_fout_zet_blocked(self) -> None:
        self.init_running("stuk")

        def runner(_prompt: str, _job: dict[str, Any]) -> dict[str, Any]:
            raise WorkerError("claude -p faalde: boom")

        res = run_once(self.service, runner=runner)
        self.assertFalse(res["ok"])
        self.assertEqual(res["action"], "blocked")
        self.assertIn("boom", res["errors"][0])

        status = self.service.get_status(post="stuk")
        self.assertEqual(status["status"], "blocked")
        self.assertIn("boom", status["blocked_reason"])

    def test_leeg_artefact_wordt_blocked_via_complete(self) -> None:
        self.init_running("leeg")

        def runner(_prompt: str, _job: dict[str, Any]) -> dict[str, Any]:
            return {"ok": True, "result": "ik heb niets geschreven"}

        res = run_once(self.service, runner=runner)
        self.assertFalse(res["ok"])
        self.assertEqual(res["action"], "blocked")
        status = self.service.get_status(post="leeg")
        self.assertEqual(status["status"], "blocked")

    def test_roept_nooit_approve_aan(self) -> None:
        self.init_running("geen-stempel")
        self.service.approve_gate = MagicMock(side_effect=AssertionError("approve verboden"))

        def runner(_prompt: str, job: dict[str, Any]) -> dict[str, Any]:
            self.write(job["slug"], "outline.md", "# Outline\n")
            return {"ok": True, "result": "ok"}

        res = run_once(self.service, runner=runner)
        self.assertTrue(res["ok"], res)
        self.service.approve_gate.assert_not_called()

    def test_specifieke_slug_die_niet_running_is_blijft_idle(self) -> None:
        pdir = os.path.join(self.tmp_dir, "wacht")
        self.service.init_post(slug="wacht", titel="Wacht", post_dir=pdir)
        res = run_once(self.service, slug="wacht")
        self.assertTrue(res["ok"])
        self.assertEqual(res["action"], "idle")
        self.assertEqual(res["status"], "ready")

    def test_on_claim_alleen_bij_echte_uitvoering(self) -> None:
        self.init_running("claim")
        gezien: list[str] = []

        def claim(job: dict[str, Any]) -> None:
            gezien.append(job["slug"])

        dry = run_once(self.service, dry_run=True, on_claim=claim)
        self.assertEqual(dry["action"], "dry_run")
        self.assertEqual(gezien, [])

        def runner(_prompt: str, job: dict[str, Any]) -> dict[str, Any]:
            self.write(job["slug"], "outline.md", "# Outline\n")
            return {"ok": True, "result": "ok"}

        res = run_once(self.service, runner=runner, on_claim=claim)
        self.assertTrue(res["ok"], res)
        self.assertEqual(gezien, ["claim"])


if __name__ == "__main__":
    unittest.main()
