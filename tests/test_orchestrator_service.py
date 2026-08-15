"""Unit testsuite voor de WorkflowService API (pure Python orkestrator service)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from typing import Any

from scripts.orchestrator.service import WorkflowService

#: Een controlerapport zonder bevindingen (ADR-010 §6, stap 2).
LEEG_RAPPORT = '# Rapport\n\n```json\n{"findings": []}\n```\n'

#: Een controlerapport met één blokkerende bevinding.
BLOKKEREND_RAPPORT = """# Rapport

```json
{"findings": [
  {"severity": "blocking", "categorie": "misquote", "waar": "r.92",
   "wat": "Het citaat mist de openingszinsnede uit de bron."}
]}
```
"""

#: Een controlerapport met alleen punten ter overweging.
ADVISORY_RAPPORT = """# Rapport

```json
{"findings": [
  {"severity": "advisory", "categorie": "komma+en", "waar": "r.11",
   "wat": "Opsomming, geen twee hoofdzinnen; geen overtreding."}
]}
```
"""

#: Rapporten zoals de subagent archief-consistentie-check ze schrijft (ADR-007).
ALIGNMENT_OK_REPORT = """# Archief-consistentie (ADR-007)

```json
{"status": "ALIGNMENT_OK", "discrepancies": []}
```

Geen tegenspraak gevonden met eerder gepubliceerd werk.
"""

ALIGNMENT_DISCREPANCY_REPORT = """# Archief-consistentie (ADR-007)

```json
{"status": "DISCREPANCY_DETECTED", "discrepancies": [
  {"historical_slug": "intentie-1-waarom-intentie-waarde-draagt",
   "historical_ref": "https://edwinvandillen.nl/?p=500",
   "previous_text": "Intentie hoort thuis bij de opdrachtgever.",
   "current_text": "Intentie hoort thuis bij de uitvoerder.",
   "toelichting": "Twee onverenigbare antwoorden op dezelfde vraag."}
]}
```

Eén bevinding.
"""


class ServiceTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.service = WorkflowService()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    #: Controlerapporten openen met een bevindingenblok (ADR-010 §6, stap 2).
    CHECK_REPORTS = ("stijlcheck.md", "leesbaarheid.md", "reeks-check.md", "feitencheck.md")

    def create_post_file(self, slug: str, filename: str, content: str | None = None) -> str:
        if content is None:
            content = LEEG_RAPPORT if filename in self.CHECK_REPORTS else "content\n"
        pdir = os.path.join(self.tmp_dir, slug)
        os.makedirs(pdir, exist_ok=True)
        path = os.path.join(pdir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path


class TestServiceInitAndSlug(ServiceTestBase):
    def test_init_valid_slug(self) -> None:
        slug = "my-test-post"
        res = self.service.init_post(slug=slug, titel="Test Titel", force=True)
        self.assertTrue(res["ok"])
        self.assertTrue(os.path.isdir(res["post_dir"]))
        self.assertTrue(os.path.isfile(os.path.join(res["post_dir"], "state.json")))
        state = res["state"]
        self.assertEqual(state["slug"], slug)
        self.assertEqual(state["titel"], "Test Titel")
        self.assertEqual(state["phase"], "outline")
        self.assertEqual(state["status"], "ready")

    def test_init_invalid_slug_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.service.init_post(slug="Invalid_Slug!", titel="Test")

    def test_init_existing_slug_raises_file_exists_error(self) -> None:
        slug = "duplicate-post"
        pdir = os.path.join(self.tmp_dir, slug)

        # First init succeeds
        res = self.service.init_post(slug=slug, titel="Test 1", post_dir=pdir)
        self.assertTrue(res["ok"])

        # Second init without force raises FileExistsError
        with self.assertRaises(FileExistsError):
            self.service.init_post(slug=slug, titel="Test 2", post_dir=pdir)

    def test_init_wait_intake_gate(self) -> None:
        slug = "intake-gate-post"
        pdir = os.path.join(self.tmp_dir, slug)
        res = self.service.init_post(slug=slug, titel="Intake Test", wait_intake_gate=True, post_dir=pdir)
        self.assertTrue(res["ok"])
        state = res["state"]
        self.assertEqual(state["phase"], "intake")
        self.assertEqual(state["status"], "waiting_gate")
        self.assertEqual(state["gate"]["pending"], "intake")


class TestServiceLinearPipeline(ServiceTestBase):
    def test_full_pipeline_lifecycle(self) -> None:
        slug = "lifecycle-post"
        pdir = os.path.join(self.tmp_dir, slug)

        # 1. Init
        self.service.init_post(slug=slug, titel="Lifecycle Test", post_dir=pdir)
        status = self.service.get_status(post_dir=pdir)
        self.assertEqual(status["phase"], "outline")
        self.assertEqual(status["status"], "ready")

        # 2. Outline phase
        res = self.service.run_phase(phase="outline", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.create_post_file(slug, "outline.md", "# Outline content")
        res = self.service.complete_phase(phase="outline", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.assertEqual(res["status"], "waiting_gate")

        # Approve outline -> draft
        res = self.service.approve_gate(post_dir=pdir, note="Outline akkoord")
        self.assertTrue(res["ok"])
        self.assertEqual(res["phase"], "draft")
        self.assertEqual(res["status"], "ready")

        # 3. Draft phase
        res = self.service.run_phase(phase="draft", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.create_post_file(slug, "draft.md", "# Draft content\n![vis1](visuals/v1.png)\n![vis2](visuals/v2.png)")
        res = self.service.complete_phase(phase="draft", post_dir=pdir)
        self.assertTrue(res["ok"])
        res = self.service.approve_gate(post_dir=pdir, note="Draft akkoord")
        self.assertEqual(res["phase"], "style")

        # 4. Style phase: beide rapporten zijn verplicht, en zonder blokkerende bevinding
        # schuift de gate vanzelf door (ADR-010 §3.1).
        res = self.service.run_phase(phase="style", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.create_post_file(slug, "stijlcheck.md")
        res = self.service.complete_phase(phase="style", post_dir=pdir)
        self.assertFalse(res["ok"], "zonder leesbaarheid.md is de style-fase niet af")
        self.create_post_file(slug, "leesbaarheid.md")
        res = self.service.complete_phase(phase="style", post_dir=pdir)
        self.assertTrue(res["ok"], res.get("errors"))
        self.assertEqual(res["phase"], "series")
        self.assertEqual(res["status"], "ready")

        # 5. Series phase
        res = self.service.run_phase(phase="series", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.create_post_file(slug, "reeks-check.md")
        res = self.service.complete_phase(phase="series", post_dir=pdir)
        self.assertTrue(res["ok"], res.get("errors"))
        self.assertEqual(res["phase"], "critique")

        # 6. Critique phase
        res = self.service.run_phase(phase="critique", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.create_post_file(slug, "grok-feedback.md", "# Grok feedback")
        res = self.service.complete_phase(phase="critique", post_dir=pdir)
        self.assertTrue(res["ok"])
        res = self.service.approve_gate(post_dir=pdir)
        self.assertEqual(res["phase"], "synthesis")

        # 7. Synthesis phase (HARD GATE)
        res = self.service.run_phase(phase="synthesis", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.create_post_file(slug, "synthese.md", "# Synthese document")
        res = self.service.complete_phase(phase="synthesis", post_dir=pdir)
        self.assertTrue(res["ok"])
        res = self.service.approve_gate(post_dir=pdir, note="Synthese akkoord")
        self.assertEqual(res["phase"], "visuals")

        # 8. Visuals phase
        vdir = os.path.join(pdir, "visuals")
        os.makedirs(vdir, exist_ok=True)
        with open(os.path.join(vdir, "v1.png"), "w") as f:
            f.write("img1")
        with open(os.path.join(vdir, "v2.png"), "w") as f:
            f.write("img2")
        res = self.service.run_phase(phase="visuals", post_dir=pdir)
        self.assertTrue(res["ok"])
        res = self.service.complete_phase(phase="visuals", post_dir=pdir)
        self.assertTrue(res["ok"])
        res = self.service.approve_gate(post_dir=pdir)
        self.assertEqual(res["phase"], "factcheck")

        # 9. Factcheck phase (HARD GATE)
        res = self.service.run_phase(phase="factcheck", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.create_post_file(slug, "feitencheck.md")
        res = self.service.complete_phase(phase="factcheck", post_dir=pdir)
        self.assertTrue(res["ok"], res.get("errors"))
        self.assertEqual(res["phase"], "alignment")

        # 9b. Alignment phase (ADR-007): zonder bevinding schuift de gate automatisch
        # door naar deploy, ook zonder yolo. Er is dan niets voor te leggen.
        res = self.service.run_phase(phase="alignment", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.create_post_file(slug, "archief-consistentie.md", ALIGNMENT_OK_REPORT)
        res = self.service.complete_phase(phase="alignment", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.assertTrue(res["yolo_advanced"])
        self.assertEqual(res["phase"], "deploy")

        # 10. Deploy phase (HARD GATE)
        res = self.service.approve_gate(post_dir=pdir, deploy=True)
        self.assertTrue(res["ok"])
        res = self.service.run_phase(phase="deploy", post_dir=pdir)
        self.assertTrue(res["ok"])
        res = self.service.complete_phase(phase="deploy", post_dir=pdir, post_id=123, edit_url="http://example.com/wp-admin")
        self.assertTrue(res["ok"])
        res = self.service.approve_gate(post_dir=pdir, deploy=True)
        self.assertEqual(res["phase"], "done")
        self.assertEqual(res["status"], "done")

    def test_reject_returns_to_ready(self) -> None:
        slug = "reject-test"
        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Reject Test", post_dir=pdir)
        self.service.run_phase(phase="outline", post_dir=pdir)
        self.create_post_file(slug, "outline.md", "Outline text")
        self.service.complete_phase(phase="outline", post_dir=pdir)

        # State is waiting_gate
        res = self.service.reject_gate(post_dir=pdir, note="Herziening nodig")
        self.assertTrue(res["ok"])
        self.assertEqual(res["phase"], "outline")
        self.assertEqual(res["status"], "ready")


class TestServiceYoloAndHardGates(ServiceTestBase):
    def test_yolo_mode_auto_advances_soft_gates(self) -> None:
        slug = "yolo-test"
        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Yolo Test", yolo=True, post_dir=pdir)

        # Run & complete outline -> yolo auto-approves outline to draft/ready
        self.service.run_phase(phase="outline", post_dir=pdir)
        self.create_post_file(slug, "outline.md", "Outline")
        res = self.service.complete_phase(phase="outline", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.assertTrue(res["yolo_advanced"])

        status = self.service.get_status(post_dir=pdir)
        self.assertEqual(status["phase"], "draft")
        self.assertEqual(status["status"], "ready")

    def test_yolo_mode_stops_at_hard_gate(self) -> None:
        slug = "yolo-hard-gate"
        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Yolo Hard Gate", yolo=True, post_dir=pdir)
        self.create_post_file(slug, "outline.md", "Outline")
        self.create_post_file(slug, "draft.md", "Draft\n![v1](v1.png)\n![v2](v2.png)")
        self.create_post_file(slug, "grok-feedback.md", "Feedback")

        # Manually set phase to synthesis (hard gate)
        self.service.set_flag(name="yolo_mode", value=True, post_dir=pdir)
        state = self.service.get_status(post_dir=pdir)

        # Fast forward state to synthesis / running
        from scripts.orchestrator.repository import load_state, save_state
        raw_state = load_state(pdir)
        raw_state["phase"] = "synthesis"
        raw_state["status"] = "running"
        save_state(pdir, raw_state)

        self.create_post_file(slug, "synthese.md", "Synthese")
        res = self.service.complete_phase(phase="synthesis", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.assertFalse(res["yolo_advanced"])  # Hard gate MUST NOT auto-advance
        self.assertEqual(res["status"], "waiting_gate")


class TestServiceFlagsAndExceptions(ServiceTestBase):
    def test_skip_synthesis_flag(self) -> None:
        slug = "skip-synth-test"
        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Skip Synthesis Test", post_dir=pdir)
        self.service.set_flag(name="skip_synthesis", value=True, post_dir=pdir)

        status = self.service.get_status(post_dir=pdir)
        self.assertTrue(status["flags"]["skip_synthesis"])

    def test_defer_critique_flag(self) -> None:
        slug = "defer-critique-test"
        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Defer Critique Test", post_dir=pdir)
        self.create_post_file(slug, "outline.md", "Outline")
        self.create_post_file(slug, "draft.md", "Draft\n![v1](v1.png)\n![v2](v2.png)")
        self.service.set_flag(name="defer_critique", value=True, post_dir=pdir)

        # Fast forward to critique
        from scripts.orchestrator.repository import load_state, save_state
        raw_state = load_state(pdir)
        raw_state["phase"] = "critique"
        raw_state["status"] = "ready"
        save_state(pdir, raw_state)

        # visuals run should be allowed with defer_critique=True even without grok-feedback.md
        res = self.service.run_phase(phase="visuals", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.assertEqual(res["phase"], "visuals")


class TestServiceDoctorAndRepair(ServiceTestBase):
    def test_doctor_detects_clean_pipeline(self) -> None:
        slug = "doctor-clean"
        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Doctor Clean Test", post_dir=pdir)
        doc = self.service.doctor(post_dir=pdir)
        self.assertTrue(doc["ok"])
        self.assertEqual(len(doc["issues"]), 0)

    def test_repair_proposes_phase_from_disk(self) -> None:
        slug = "repair-test"
        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Repair Test", post_dir=pdir)
        self.create_post_file(slug, "outline.md", "Outline")
        self.create_post_file(slug, "draft.md", "Draft")

        rep = self.service.repair(post_dir=pdir, apply=True)
        self.assertTrue(rep["applied"])
        self.assertEqual(rep["proposal"]["phase"], "style")


class TestServiceAlignmentGate(ServiceTestBase):
    """De archief-consistentie-gate uit ADR-007, fase 5c."""

    def _post_op_alignment(self, slug: str, yolo: bool = False) -> str:
        """Zet een post klaar in fase alignment met status ready."""
        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Alignment Test", post_dir=pdir, yolo=yolo)
        self.create_post_file(slug, "draft.md", "# Draft")
        state = self.service.get_status(post_dir=pdir)
        self.service.set_flag(name="skip_factcheck", value=True, post_dir=pdir)
        # Fase direct zetten; de weg ernaartoe is elders al gedekt.
        from scripts.orchestrator.repository import load_state, save_state

        s = load_state(pdir)
        s["phase"] = "alignment"
        s["status"] = "ready"
        save_state(pdir, s)
        self.assertEqual(state["slug"], slug)
        return pdir

    def test_geen_bevinding_schuift_automatisch_door(self) -> None:
        pdir = self._post_op_alignment("align-ok")
        self.service.run_phase(phase="alignment", post_dir=pdir)
        self.create_post_file("align-ok", "archief-consistentie.md", ALIGNMENT_OK_REPORT)

        res = self.service.complete_phase(phase="alignment", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.assertEqual(res["phase"], "deploy")
        self.assertEqual(res["status"], "ready")

    def test_bevinding_stopt_bij_de_gate_ook_zonder_yolo(self) -> None:
        pdir = self._post_op_alignment("align-discrepant")
        self.service.run_phase(phase="alignment", post_dir=pdir)
        self.create_post_file(
            "align-discrepant", "archief-consistentie.md", ALIGNMENT_DISCREPANCY_REPORT
        )

        res = self.service.complete_phase(phase="alignment", post_dir=pdir)
        self.assertTrue(res["ok"])
        self.assertEqual(res["phase"], "alignment")
        self.assertEqual(res["status"], "waiting_gate")

        status = self.service.get_status(post_dir=pdir)
        self.assertEqual(status["archival_alignment"]["status"], "DISCREPANCY_DETECTED")
        self.assertEqual(status["next"]["gate_type"], "hard")

    def test_bevinding_stopt_ook_in_yolo_mode(self) -> None:
        """De hele reden dat de gate bestaat: yolo mag hem niet passeren."""
        pdir = self._post_op_alignment("align-yolo", yolo=True)
        self.service.run_phase(phase="alignment", post_dir=pdir)
        self.create_post_file(
            "align-yolo", "archief-consistentie.md", ALIGNMENT_DISCREPANCY_REPORT
        )

        res = self.service.complete_phase(phase="alignment", post_dir=pdir)
        self.assertEqual(res["status"], "waiting_gate")
        self.assertEqual(res["phase"], "alignment")

    def test_rapport_zonder_verdictblok_wordt_geweigerd(self) -> None:
        pdir = self._post_op_alignment("align-geen-verdict")
        self.service.run_phase(phase="alignment", post_dir=pdir)
        self.create_post_file(
            "align-geen-verdict", "archief-consistentie.md", "# Ziet er prima uit\n"
        )

        res = self.service.complete_phase(phase="alignment", post_dir=pdir)
        self.assertFalse(res["ok"])
        self.assertIn("verdictblok", " ".join(res["errors"]))

    def test_bevinding_zonder_geciteerd_paar_wordt_geweigerd(self) -> None:
        """ADR-007: zonder beide citaten is er geen bevinding."""
        pdir = self._post_op_alignment("align-half-citaat")
        self.service.run_phase(phase="alignment", post_dir=pdir)
        half = """# Archief-consistentie

```json
{"status": "DISCREPANCY_DETECTED", "discrepancies": [
  {"historical_slug": "intentie-1", "previous_text": "Iets uit een eerdere post."}
]}
```
"""
        self.create_post_file("align-half-citaat", "archief-consistentie.md", half)

        res = self.service.complete_phase(phase="alignment", post_dir=pdir)
        self.assertFalse(res["ok"])
        self.assertIn("current_text", " ".join(res["errors"]))

    def test_voortschrijdend_inzicht_vereist_een_toelichting(self) -> None:
        pdir = self._post_op_alignment("align-resolutie")
        self.service.run_phase(phase="alignment", post_dir=pdir)
        self.create_post_file(
            "align-resolutie", "archief-consistentie.md", ALIGNMENT_DISCREPANCY_REPORT
        )
        self.service.complete_phase(phase="alignment", post_dir=pdir)

        with self.assertRaises(ValueError):
            self.service.resolve_alignment(post_dir=pdir, action="progressive_insight", note="  ")

        res = self.service.resolve_alignment(
            post_dir=pdir, action="progressive_insight", note="Bewust herzien in deel 4."
        )
        self.assertTrue(res["ok"])
        state = res["state"]
        self.assertEqual(state["archival_alignment"]["status"], "RESOLVED_PROGRESSIVE_INSIGHT")
        self.assertEqual(state["archival_alignment"]["resolution"]["author_note"], "Bewust herzien in deel 4.")

    def test_afwijzen_als_fout_zet_terug_naar_draft(self) -> None:
        pdir = self._post_op_alignment("align-afwijzen")
        self.service.run_phase(phase="alignment", post_dir=pdir)
        self.create_post_file(
            "align-afwijzen", "archief-consistentie.md", ALIGNMENT_DISCREPANCY_REPORT
        )
        self.service.complete_phase(phase="alignment", post_dir=pdir)

        res = self.service.resolve_alignment(post_dir=pdir, action="error_rejected")
        state = res["state"]
        self.assertEqual(state["phase"], "draft")
        self.assertEqual(state["status"], "ready")
        self.assertIsNone(state["blocked_reason"], "status ready mag geen blocked_reason houden")


class TestVoorwaardelijkeGates(ServiceTestBase):
    """Een controle die niets vond, heeft niets voor te leggen (ADR-010 §3.1)."""

    def _op_style(self, slug: str, stijl: str, leesbaar: str) -> str:
        from scripts.orchestrator.repository import load_state, save_state

        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Gates", post_dir=pdir)
        self.create_post_file(slug, "draft.md", "# Draft\n")
        self.create_post_file(slug, "stijlcheck.md", stijl)
        self.create_post_file(slug, "leesbaarheid.md", leesbaar)
        s = load_state(pdir)
        s["phase"], s["status"] = "style", "ready"
        save_state(pdir, s)
        self.service.run_phase(phase="style", post_dir=pdir)
        return pdir

    def test_zonder_bevinding_schuift_door(self) -> None:
        pdir = self._op_style("gate-leeg", LEEG_RAPPORT, LEEG_RAPPORT)
        res = self.service.complete_phase(phase="style", post_dir=pdir)
        self.assertEqual(res["phase"], "series")
        self.assertEqual(res["status"], "ready")

    def test_alleen_ter_overweging_schuift_ook_door(self) -> None:
        """De stijl-check vindt bijna altijd kandidaten; die mogen niet blokkeren."""
        pdir = self._op_style("gate-advies", ADVISORY_RAPPORT, LEEG_RAPPORT)
        res = self.service.complete_phase(phase="style", post_dir=pdir)
        self.assertEqual(res["phase"], "series")

        verdict = self.service.get_status(post_dir=pdir)["verdicts"]["style"]
        self.assertEqual(verdict["blocking"], 0)
        self.assertEqual(verdict["advisory"], 1)

    def test_blokkerende_bevinding_stopt_de_gate(self) -> None:
        pdir = self._op_style("gate-blok", BLOKKEREND_RAPPORT, LEEG_RAPPORT)
        res = self.service.complete_phase(phase="style", post_dir=pdir)
        self.assertEqual(res["phase"], "style")
        self.assertEqual(res["status"], "waiting_gate")

        volgende = self.service.get_next(post_dir=pdir)
        self.assertEqual(volgende["gate_type"], "hard")

    def test_bevinding_in_het_tweede_rapport_telt_ook(self) -> None:
        pdir = self._op_style("gate-tweede", LEEG_RAPPORT, BLOKKEREND_RAPPORT)
        res = self.service.complete_phase(phase="style", post_dir=pdir)
        self.assertEqual(res["status"], "waiting_gate")

    def test_rapport_zonder_bevindingenblok_wordt_geweigerd(self) -> None:
        pdir = self._op_style("gate-geen-blok", "# Ziet er prima uit\n", LEEG_RAPPORT)
        res = self.service.complete_phase(phase="style", post_dir=pdir)
        self.assertFalse(res["ok"])
        self.assertIn("json-blok", " ".join(res["errors"]))

    def test_onbekende_zwaarte_wordt_geweigerd(self) -> None:
        rapport = '# Rapport\n\n```json\n{"findings": [{"severity": "ernstig", "categorie": "x", "waar": "r.1", "wat": "y"}]}\n```\n'
        pdir = self._op_style("gate-zwaarte", rapport, LEEG_RAPPORT)
        res = self.service.complete_phase(phase="style", post_dir=pdir)
        self.assertFalse(res["ok"])
        self.assertIn("zwaarte", " ".join(res["errors"]))


class TestBevindingenBundel(ServiceTestBase):
    """Eén overzicht in plaats van vijf bestanden (ADR-010 §6, stap 3)."""

    def _post_met_rapporten(self, slug: str) -> str:
        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Bundel", post_dir=pdir)
        self.create_post_file(slug, "draft.md", "# Draft\n")
        self.create_post_file(slug, "stijlcheck.md", ADVISORY_RAPPORT)
        self.create_post_file(slug, "leesbaarheid.md", LEEG_RAPPORT)
        self.create_post_file(slug, "reeks-check.md", BLOKKEREND_RAPPORT)
        self.create_post_file(slug, "feitencheck.md", LEEG_RAPPORT)
        self.create_post_file(slug, "archief-consistentie.md", ALIGNMENT_DISCREPANCY_REPORT)
        return pdir

    def test_bundelt_over_alle_controlefases(self) -> None:
        pdir = self._post_met_rapporten("bundel")
        res = self.service.get_findings(post_dir=pdir)

        self.assertEqual(res["blocking"], 2, "reeks-check en alignment")
        self.assertEqual(res["advisory"], 1, "stijl-check")
        self.assertEqual({f["phase"] for f in res["phases"]}, {"style", "series", "factcheck", "alignment"})

    def test_blokkerend_staat_bovenaan(self) -> None:
        pdir = self._post_met_rapporten("bundel-volgorde")
        res = self.service.get_findings(post_dir=pdir)
        zwaartes = [b["severity"] for b in res["findings"]]
        self.assertEqual(zwaartes, ["blocking", "blocking", "advisory"])

    def test_niet_gedraaide_fase_wordt_als_zodanig_gemeld(self) -> None:
        slug = "bundel-leeg"
        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Bundel leeg", post_dir=pdir)
        self.create_post_file(slug, "draft.md", "# Draft\n")

        res = self.service.get_findings(post_dir=pdir)
        self.assertEqual(res["blocking"], 0)
        self.assertTrue(all(f["staat"] == "niet gedraaid" for f in res["phases"]))
        self.assertIn("Geen bevindingen", res["markdown"])

    def test_onleesbaar_rapport_valt_op_maar_breekt_niets(self) -> None:
        slug = "bundel-kapot"
        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Bundel kapot", post_dir=pdir)
        self.create_post_file(slug, "draft.md", "# Draft\n")
        self.create_post_file(slug, "stijlcheck.md", "# Geen blok\n")
        self.create_post_file(slug, "leesbaarheid.md", LEEG_RAPPORT)

        res = self.service.get_findings(post_dir=pdir)
        style = next(f for f in res["phases"] if f["phase"] == "style")
        self.assertEqual(style["staat"], "onleesbaar")
        self.assertIn("Niet te lezen", res["markdown"])


class TestRapportActualiteit(ServiceTestBase):
    """Een controle op een tekst die niet meer bestaat, is geen controle (ADR-010 §3.5)."""

    def _klaar_voor_deploy(self, slug: str) -> str:
        from scripts.orchestrator.repository import load_state, save_state

        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Actualiteit", post_dir=pdir)
        self.create_post_file(slug, "draft.md", "# Draft\n\nEerste versie.\n")
        self.create_post_file(slug, "feitencheck.md")
        self.create_post_file(slug, "archief-consistentie.md", ALIGNMENT_OK_REPORT)

        # Beide controlefases netjes afronden, zodat hun vingerafdruk wordt vastgelegd.
        for fase in ("factcheck", "alignment"):
            s = load_state(pdir)
            s["phase"], s["status"] = fase, "ready"
            save_state(pdir, s)
            self.service.run_phase(phase=fase, post_dir=pdir)
            res = self.service.complete_phase(phase=fase, post_dir=pdir)
            self.assertTrue(res["ok"], res.get("errors"))

        s = load_state(pdir)
        s["phase"], s["status"] = "deploy", "ready"
        save_state(pdir, s)
        self.service.approve_gate(post_dir=pdir, deploy=True)
        return pdir

    def _herschrijf_draft(self, slug: str) -> None:
        self.create_post_file(slug, "draft.md", "# Draft\n\nHerschreven na de controles.\n")

    def test_vingerafdruk_wordt_vastgelegd_bij_complete(self) -> None:
        pdir = self._klaar_voor_deploy("actueel")
        from scripts.orchestrator.repository import draft_fingerprint, load_state

        afgeleid = load_state(pdir)["derived_from"]
        self.assertEqual(afgeleid["factcheck"], draft_fingerprint(pdir))
        self.assertEqual(afgeleid["alignment"], draft_fingerprint(pdir))

    def test_deploy_mag_met_actuele_rapporten(self) -> None:
        pdir = self._klaar_voor_deploy("actueel-deploy")
        res = self.service.run_phase(phase="deploy", post_dir=pdir)
        self.assertTrue(res["ok"], res.get("errors"))

    def test_deploy_geweigerd_na_herschreven_draft(self) -> None:
        pdir = self._klaar_voor_deploy("verouderd")
        self._herschrijf_draft("verouderd")

        res = self.service.run_phase(phase="deploy", post_dir=pdir)
        self.assertFalse(res["ok"])
        fouten = " ".join(res["errors"])
        self.assertIn("feitencheck.md", fouten)
        self.assertIn("archief-consistentie.md", fouten)

    def test_skip_factcheck_haalt_alleen_de_feitencheck_uit_de_eis(self) -> None:
        pdir = self._klaar_voor_deploy("skip-fc")
        self._herschrijf_draft("skip-fc")
        self.service.set_flag(name="skip_factcheck", value=True, post_dir=pdir)

        res = self.service.run_phase(phase="deploy", post_dir=pdir)
        self.assertFalse(res["ok"], "alignment is nog steeds verouderd")
        fouten = " ".join(res["errors"])
        self.assertNotIn("feitencheck.md", fouten)
        self.assertIn("archief-consistentie.md", fouten)

    def test_zonder_vingerafdruk_blokkeert_niets(self) -> None:
        """Posts van vóór deze registratie mogen niet zonder aanleiding vastlopen."""
        from scripts.orchestrator.repository import load_state, save_state

        slug = "legacy"
        pdir = os.path.join(self.tmp_dir, slug)
        self.service.init_post(slug=slug, titel="Legacy", post_dir=pdir)
        self.create_post_file(slug, "draft.md", "# Draft\n")
        self.create_post_file(slug, "feitencheck.md")
        self.create_post_file(slug, "archief-consistentie.md", ALIGNMENT_OK_REPORT)
        s = load_state(pdir)
        s["phase"], s["status"] = "deploy", "ready"
        s["derived_from"] = {}
        save_state(pdir, s)
        self.service.approve_gate(post_dir=pdir, deploy=True)

        res = self.service.run_phase(phase="deploy", post_dir=pdir)
        self.assertTrue(res["ok"], res.get("errors"))

        doc = self.service.doctor(post_dir=pdir)
        meldingen = " ".join(i["msg"] for i in doc["issues"])
        self.assertIn("geen vingerafdruk", meldingen)

    def test_doctor_meldt_een_verouderd_rapport(self) -> None:
        pdir = self._klaar_voor_deploy("doctor-verouderd")
        self._herschrijf_draft("doctor-verouderd")

        doc = self.service.doctor(post_dir=pdir)
        meldingen = " ".join(i["msg"] for i in doc["issues"])
        self.assertIn("oudere draft", meldingen)


if __name__ == "__main__":
    unittest.main()
