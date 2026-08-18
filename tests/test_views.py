"""Tests voor de detailweergave-inventaris (artefact_views en gate_reason)."""

from __future__ import annotations

import os
import tempfile
import unittest

from scripts.orchestrator.repository import empty_state
from scripts.orchestrator.views import build_artefact_views, gate_reason, list_visual_files


class TestArtefactViews(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.pdir = self.tmp.name
        self.state = empty_state("demo", "Demo")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _schrijf(self, naam: str, tekst: str = "inhoud\n") -> None:
        path = os.path.join(self.pdir, naam)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(tekst)

    def test_alleen_aanwezige_bestanden_zijn_present(self) -> None:
        self._schrijf("outline.md")
        self._schrijf("draft.md")
        views = {v["id"]: v for v in build_artefact_views(self.state, self.pdir)}
        self.assertTrue(views["outline"]["present"])
        self.assertTrue(views["draft"]["present"])
        self.assertFalse(views["style"]["present"])
        self.assertEqual([f["name"] for f in views["style"]["files"]], ["stijlcheck.md", "leesbaarheid.md"])

    def test_stijl_heeft_twee_rapporten_en_verdict(self) -> None:
        self._schrijf("stijlcheck.md")
        self._schrijf("leesbaarheid.md")
        self.state["verdicts"] = {
            "style": {"blocking": 2, "advisory": 4, "status": "FINDINGS", "findings": []},
        }
        views = {v["id"]: v for v in build_artefact_views(self.state, self.pdir)}
        self.assertTrue(views["style"]["present"])
        self.assertEqual(views["style"]["verdict"]["blocking"], 2)
        self.assertEqual(sum(1 for f in views["style"]["files"] if f["present"]), 2)

    def test_visuals_een_kaart_per_stam(self) -> None:
        self._schrijf("visuals/kaart.svg", "<svg></svg>")
        self._schrijf("visuals/kaart.png", "png")
        files = list_visual_files(self.pdir)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["stem"], "kaart")
        self.assertEqual(files[0]["name"], "kaart.png")


class TestGateReason(unittest.TestCase):
    def test_geen_reden_buiten_waiting_gate(self) -> None:
        state = empty_state("demo", "Demo")
        state["status"] = "ready"
        self.assertIsNone(gate_reason(state))

    def test_blocking_controlefase(self) -> None:
        state = empty_state("demo", "Demo")
        state["status"] = "waiting_gate"
        state["phase"] = "style"
        state["gate"]["pending"] = "style"
        state["verdicts"] = {
            "style": {
                "blocking": 2,
                "advisory": 24,
                "findings": [
                    {"severity": "blocking", "categorie": "buiten de band", "waar": "hele document", "wat": "te kort"},
                    {"severity": "advisory", "categorie": "em-dash", "waar": "r.1", "wat": "streep"},
                ],
            }
        }
        reden = gate_reason(state)
        self.assertIsNotNone(reden)
        self.assertEqual(reden["kind"], "blocking")
        self.assertEqual(reden["blocking"], 2)
        self.assertEqual(len(reden["findings"]), 1)
        self.assertIn("blokkerende", reden["headline"])
        self.assertIn("YOLO", reden["detail"])

    def test_reeks_zonder_blocking_geen_waiting(self) -> None:
        state = empty_state("demo", "Demo")
        state["status"] = "ready"
        state["phase"] = "critique"
        self.assertIsNone(gate_reason(state))


if __name__ == "__main__":
    unittest.main()
