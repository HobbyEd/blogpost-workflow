"""Regressietests voor scripts/orchestrate.py (de strikte control plane).

Roept de CLI aan als subprocess, altijd met --post-dir naar een tempdir —
raakt nooit posts/ in de echte repo. Stdlib-only (unittest), zelfde
constraint als orchestrate.py zelf.

Draaien:
    python3 -m unittest discover -s tests -v
    # of losstaand:
    python3 tests/test_orchestrate.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ORCHESTRATE = os.path.join(REPO_ROOT, "scripts", "orchestrate.py")


def run_cli(*args: str) -> tuple[int, dict | None, str]:
    """Roep orchestrate.py aan; parse stdout als JSON indien mogelijk."""
    proc = subprocess.run(
        [sys.executable, ORCHESTRATE, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    out = proc.stdout.strip()
    payload = None
    if out:
        try:
            payload = json.loads(out)
        except json.JSONDecodeError:
            payload = None
    if payload is None and proc.stderr.strip():
        try:
            payload = json.loads(proc.stderr.strip())
        except json.JSONDecodeError:
            payload = None
    return proc.returncode, payload, proc.stderr


class OrchestrateTestCase(unittest.TestCase):
    """Basisklasse: elke test krijgt een eigen lege postmap via --post-dir."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.post_dir = os.path.join(self.tmpdir.name, "post")
        os.makedirs(self.post_dir, exist_ok=True)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    # -- helpers --------------------------------------------------------

    def cli(self, *args: str) -> tuple[int, dict | None, str]:
        return run_cli(*args, "--post-dir", self.post_dir)

    def init_state(self, yolo: bool = False, wait_intake_gate: bool = False) -> dict:
        # init kent geen --post-dir (het bepaalt de dir zelf uit --slug), dus
        # schrijf de state direct met de library-functies via een los process
        # dat een expliciet pad accepteert: we simuleren init door de state
        # rechtstreeks te schrijven met dezelfde vorm als cmd_init.
        args = ["init", "--slug", "regressie-post", "--titel", "Regressietest"]
        if yolo:
            args.append("--yolo")
        if wait_intake_gate:
            args.append("--wait-intake-gate")
        # init schrijft altijd naar posts/<slug> in de repo; om de echte
        # posts/-map niet te raken, retten we hem meteen naar --post-dir
        # door de state te kopiëren en de repo-init-map op te ruimen.
        real_dir = os.path.join(REPO_ROOT, "posts", "regressie-post")
        self.addCleanup(_rmtree_if_exists, real_dir)
        code, payload, err = run_cli(*args)
        self.assertEqual(code, 0, err)
        state = payload["state"]
        _write_state(self.post_dir, state)
        return state

    #: Controlerapporten openen met een bevindingenblok (ADR-010 §6, stap 2); zonder dat
    #: blok weigert `complete`. Leeg betekent: niets gevonden.
    CHECK_REPORTS = (
        "stijlcheck.md", "leesbaarheid.md", "reeks-check.md",
        "feitencheck.md", "feitencheck-draft.md",
    )
    LEEG_RAPPORT = '# Rapport\n\n```json\n{"findings": []}\n```\n'
    LEGE_SYNTHESE = '# Synthese\n\n```json\n{"points": []}\n```\n'

    def write(self, name: str, content: str | None = None) -> None:
        if content is None:
            if name in self.CHECK_REPORTS:
                content = self.LEEG_RAPPORT
            elif name == "synthese.md":
                content = self.LEGE_SYNTHESE
            else:
                content = "inhoud\n"
        path = os.path.join(self.post_dir, name)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def state(self) -> dict:
        with open(os.path.join(self.post_dir, "state.json"), encoding="utf-8") as f:
            return json.load(f)


def _write_state(post_dir: str, state: dict) -> None:
    with open(os.path.join(post_dir, "state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _rmtree_if_exists(path: str) -> None:
    import shutil

    if os.path.isdir(path):
        shutil.rmtree(path)


# --------------------------- init / slug ---------------------------


class TestInitAndSlug(unittest.TestCase):
    def test_invalid_slug_rejected(self) -> None:
        code, payload, err = run_cli("init", "--slug", "Niet_Geldig!", "--titel", "x")
        self.assertEqual(code, 1)
        self.assertIn("kebab-case", err)

    def test_valid_slug_creates_expected_defaults(self) -> None:
        real_dir = os.path.join(REPO_ROOT, "posts", "regressie-init-check")
        try:
            code, payload, err = run_cli(
                "init", "--slug", "regressie-init-check", "--titel", "Titel"
            )
            self.assertEqual(code, 0, err)
            state = payload["state"]
            self.assertEqual(state["phase"], "outline")
            self.assertEqual(state["status"], "ready")
            self.assertFalse(state["yolo_mode"])
            self.assertFalse(state["flags"]["deploy_approved"])
        finally:
            _rmtree_if_exists(real_dir)


# --------------------------- linear pipeline ---------------------------


class TestLinearPipelineNoYolo(OrchestrateTestCase):
    """Zonder yolo moet elke content-fase stoppen bij de gate."""

    def test_outline_to_draft_requires_explicit_approve(self) -> None:
        self.init_state(yolo=False)

        code, _, err = self.cli("run", "outline")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.state()["status"], "running")

        self.write("outline.md")
        code, payload, err = self.cli("complete", "outline")
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["status"], "waiting_gate")
        self.assertFalse(payload["yolo_advanced"])

        # Zonder approve mag draft niet starten.
        code, payload, err = self.cli("run", "draft")
        self.assertEqual(code, 2)

        code, payload, err = self.cli("approve", "--note", "outline ok")
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["phase"], "draft")
        self.assertEqual(payload["status"], "ready")

        code, payload, err = self.cli("run", "draft")
        self.assertEqual(code, 0, err)

    def test_complete_without_artefact_blocks(self) -> None:
        self.init_state(yolo=False)
        self.cli("run", "outline")
        # Geen outline.md geschreven.
        code, payload, err = self.cli("complete", "outline")
        self.assertEqual(code, 2)
        self.assertEqual(self.state()["status"], "blocked")
        self.assertIn("outline.md", self.state()["blocked_reason"])

    def test_reject_returns_to_ready_same_phase(self) -> None:
        self.init_state(yolo=False)
        self.cli("run", "outline")
        self.write("outline.md")
        self.cli("complete", "outline")
        code, payload, err = self.cli("reject", "--note", "niet goed")
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["phase"], "outline")
        self.assertEqual(payload["status"], "ready")

    def test_terug_outline_start_zelfde_fase(self) -> None:
        self.init_state(yolo=False)
        self.cli("run", "outline")
        self.write("outline.md")
        self.cli("complete", "outline")

        code, payload, err = self.cli("terug", "--note", "Andere invalshoek.")
        self.assertEqual(code, 0, err)
        self.assertTrue(payload["returned"])
        self.assertEqual(payload["phase"], "outline")
        self.assertEqual(payload["status"], "running")
        self.assertEqual(payload["agent_brief"]["author_note"], "Andere invalshoek.")

    def test_terug_zonder_note_faalt(self) -> None:
        self.init_state(yolo=False)
        self.cli("run", "outline")
        self.write("outline.md")
        self.cli("complete", "outline")
        code, payload, err = self.cli("terug")
        self.assertEqual(code, 2)
        self.assertIsNone(payload)
        self.assertIn("--note", err)

    def test_terug_vanuit_draft_naar_outline(self) -> None:
        self.init_state(yolo=False)
        self.cli("run", "outline")
        self.write("outline.md")
        self.cli("complete", "outline")
        self.cli("approve", "--note", "outline ok")
        self.assertEqual(self.state()["phase"], "draft")

        code, payload, err = self.cli(
            "terug", "--phase", "outline", "--note", "Andere invalshoek."
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["returned_to"], "outline")
        self.assertEqual(payload["status"], "running")
        self.assertEqual(self.state()["phase"], "outline")

    def test_illegal_phase_jump_rejected(self) -> None:
        self.init_state(yolo=False)
        # Fase is 'outline'; direct 'draft' runnen mag niet.
        code, payload, err = self.cli("run", "draft")
        self.assertEqual(code, 2)
        self.assertIn("outline", " ".join(payload["errors"]))


class TestYoloMode(OrchestrateTestCase):
    """Yolo keurt zachte gates goed en start de volgende run zelf."""

    def test_soft_gates_starten_de_volgende_run(self) -> None:
        self.init_state(yolo=True)
        self.cli("run", "outline")
        self.write("outline.md")
        code, payload, err = self.cli("complete", "outline")
        self.assertEqual(code, 0, err)
        self.assertTrue(payload["yolo_advanced"])
        self.assertEqual(payload["auto_started"], "draft")
        self.assertEqual(payload["phase"], "draft")
        self.assertEqual(payload["status"], "running")

        self.write("draft.md")
        code, payload, err = self.cli("complete", "draft")
        self.assertEqual(code, 0, err)
        self.assertTrue(payload["yolo_advanced"])
        self.assertEqual(payload["auto_started"], "factcheck_draft")
        self.assertEqual(payload["phase"], "factcheck_draft")
        self.assertEqual(payload["status"], "running")

    def test_hard_gate_synthesis_stops_even_in_yolo(self) -> None:
        self.init_state(yolo=True)
        for phase, artefact in (
            ("outline", "outline.md"),
            ("draft", "draft.md"),
            ("factcheck_draft", "feitencheck-draft.md"),
            ("style", ("stijlcheck.md", "leesbaarheid.md")),
            ("series", ("reeks-check.md",)),
            ("critique", "grok-feedback.md"),
        ):
            self.cli("run", phase)
            for f in ((artefact,) if isinstance(artefact, str) else artefact or ()):
                self.write(f)
            self.cli("complete", phase)

        self.assertEqual(self.state()["phase"], "synthesis")
        self.assertEqual(self.state()["status"], "running")

        self.write("synthese.md")
        code, payload, err = self.cli("complete", "synthesis")
        self.assertEqual(code, 0, err)
        self.assertFalse(payload["yolo_advanced"], "synthesis is een harde gate, ook in yolo")
        self.assertEqual(payload["status"], "waiting_gate")

    def test_deploy_hard_gate_blocks_run_even_in_yolo(self) -> None:
        self.init_state(yolo=True)
        state = self.state()
        state["phase"] = "deploy"
        state["status"] = "ready"
        _write_state(self.post_dir, state)
        self.write("draft.md")

        code, payload, err = self.cli("run", "deploy")
        self.assertEqual(code, 2)
        self.assertIn("deploy_approved", " ".join(payload["errors"]))


# --------------------------- next / status guidance ---------------------------


class TestNextGuidance(OrchestrateTestCase):
    """Regressietest voor de deploy_approved-gap: `next` mag geen 'run deploy'
    adviseren zolang deploy niet is goedgekeurd (zie analyse d.d. 2026-07-29)."""

    def test_next_does_not_suggest_run_deploy_without_approval(self) -> None:
        self.init_state(yolo=False)
        state = self.state()
        state["phase"] = "deploy"
        state["status"] = "ready"
        _write_state(self.post_dir, state)
        self.write("draft.md")

        code, payload, err = self.cli("next")
        self.assertEqual(code, 0, err)
        self.assertNotEqual(
            payload["action"], "run", "next mag 'run deploy' niet adviseren zonder deploy_approved"
        )
        self.assertEqual(payload["action"], "approve_deploy_first")

    def _approve_deploy_for_current_draft(self, state: dict) -> None:
        """Zet deploy_approved mét de vingerafdruk van de draft die er nu ligt."""
        from scripts.orchestrator.repository import draft_fingerprint

        state["flags"]["deploy_approved"] = True
        state["deploy_approval"] = {"draft_sha": draft_fingerprint(self.post_dir), "at": "2026-01-01T00:00:00+00:00"}

    def test_next_suggests_run_after_deploy_approved(self) -> None:
        self.init_state(yolo=False)
        self.write("draft.md")
        state = self.state()
        state["phase"] = "deploy"
        state["status"] = "ready"
        self._approve_deploy_for_current_draft(state)
        _write_state(self.post_dir, state)

        code, payload, err = self.cli("next")
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["action"], "run")
        self.assertEqual(payload["phase"], "deploy")

    def test_next_vraagt_opnieuw_goedkeuring_na_wijziging_van_de_draft(self) -> None:
        """De goedkeuring hangt aan de tekst, niet aan de post."""
        self.init_state(yolo=False)
        self.write("draft.md")
        state = self.state()
        state["phase"] = "deploy"
        state["status"] = "ready"
        self._approve_deploy_for_current_draft(state)
        _write_state(self.post_dir, state)

        # Correctieronde: de draft wordt herschreven ná de goedkeuring.
        with open(os.path.join(self.post_dir, "draft.md"), "w", encoding="utf-8") as f:
            f.write("# Draft\n\nHerschreven na de goedkeuring.\n")

        code, payload, err = self.cli("next")
        self.assertEqual(code, 0, err)
        self.assertEqual(payload["action"], "approve_deploy_again")

        code, payload, err = self.cli("run", "deploy")
        self.assertNotEqual(code, 0, "run deploy moet weigeren op een vervallen goedkeuring")

    def test_run_deploy_succeeds_after_approve_deploy(self) -> None:
        self.init_state(yolo=False)
        state = self.state()
        state["phase"] = "deploy"
        state["status"] = "ready"
        _write_state(self.post_dir, state)
        self.write("draft.md")
        self.write("feitencheck.md")

        code, payload, err = self.cli("approve", "--deploy")
        self.assertEqual(code, 0, err)
        self.assertTrue(self.state()["flags"]["deploy_approved"])

        code, payload, err = self.cli("run", "deploy")
        self.assertEqual(code, 0, err)

    def test_deploy_blokkeert_zonder_feitencheck(self) -> None:
        """Publiceren zonder broncontrole is hoe een verzonnen citaat live kwam te staan."""
        self.init_state(yolo=False)
        state = self.state()
        state["phase"] = "deploy"
        state["status"] = "ready"
        state["flags"]["deploy_approved"] = True
        _write_state(self.post_dir, state)
        self.write("draft.md")

        code, payload, err = self.cli("run", "deploy")
        self.assertEqual(code, 2)
        self.assertIn("feitencheck", " ".join(payload["errors"]).lower())

    def test_deploy_mag_wel_met_skip_factcheck(self) -> None:
        """De uitzondering bestaat, maar nooit stilzwijgend."""
        from scripts.orchestrator.repository import draft_fingerprint

        self.init_state(yolo=False)
        self.write("draft.md")
        state = self.state()
        state["phase"] = "deploy"
        state["status"] = "ready"
        state["flags"]["deploy_approved"] = True
        state["flags"]["skip_factcheck"] = True
        state["deploy_approval"] = {"draft_sha": draft_fingerprint(self.post_dir), "at": "2026-01-01T00:00:00+00:00"}
        _write_state(self.post_dir, state)

        code, payload, err = self.cli("run", "deploy")
        self.assertEqual(code, 0, err)


# --------------------------- named exceptions ---------------------------


class TestNamedExceptions(OrchestrateTestCase):
    def test_skip_synthesis_jumps_critique_to_visuals(self) -> None:
        self.init_state(yolo=True)
        for phase, artefact in (
            ("outline", "outline.md"),
            ("draft", "draft.md"),
            ("factcheck_draft", "feitencheck-draft.md"),
            ("style", ("stijlcheck.md", "leesbaarheid.md")),
            ("series", ("reeks-check.md",)),
        ):
            self.cli("run", phase)
            for f in ((artefact,) if isinstance(artefact, str) else artefact or ()):
                self.write(f)
            self.cli("complete", phase)

        code, payload, err = self.cli("set-flag", "skip_synthesis", "true")
        self.assertEqual(code, 0, err)

        self.cli("run", "critique")
        self.write("grok-feedback.md")
        code, payload, err = self.cli("complete", "critique")
        self.assertEqual(code, 0, err)
        # Yolo + soft gate critique + skip_synthesis -> direct naar visuals.
        self.assertEqual(payload["phase"], "visuals")

    def test_synthesis_run_blocked_when_skip_synthesis_true(self) -> None:
        self.init_state(yolo=False)
        state = self.state()
        state["phase"] = "synthesis"
        state["status"] = "ready"
        state["flags"]["skip_synthesis"] = True
        _write_state(self.post_dir, state)
        self.write("draft.md")
        self.write("grok-feedback.md")

        code, payload, err = self.cli("run", "synthesis")
        self.assertEqual(code, 2)
        self.assertIn("skip_synthesis", " ".join(payload["errors"]))

    def test_defer_critique_allows_visuals_before_critique(self) -> None:
        self.init_state(yolo=False)
        state = self.state()
        state["phase"] = "critique"
        state["status"] = "ready"
        _write_state(self.post_dir, state)
        self.write("draft.md")

        # Zonder defer_critique mag visuals niet vóór critique.
        code, payload, err = self.cli("run", "visuals")
        self.assertEqual(code, 2)

        code, payload, err = self.cli("set-flag", "defer_critique", "true")
        self.assertEqual(code, 0, err)

        code, payload, err = self.cli("run", "visuals")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.state()["phase"], "visuals")


# --------------------------- doctor / drift ---------------------------


class TestDoctor(OrchestrateTestCase):
    def test_doctor_flags_drift_between_state_and_disk(self) -> None:
        self.init_state(yolo=False)
        state = self.state()
        state["phase"] = "draft"
        state["status"] = "ready"
        state["artefacts"]["outline"] = "present"  # state zegt present, schijf niet
        _write_state(self.post_dir, state)

        code, payload, err = self.cli("doctor")
        self.assertEqual(code, 3)
        msgs = " ".join(i["msg"] for i in payload["issues"])
        self.assertIn("outline", msgs)

    def test_doctor_clean_pipeline_no_hard_issues(self) -> None:
        self.init_state(yolo=True)
        for phase, artefact in (
            ("outline", "outline.md"),
            ("draft", "draft.md"),
            ("factcheck_draft", "feitencheck-draft.md"),
            ("style", ("stijlcheck.md", "leesbaarheid.md")),
            ("series", ("reeks-check.md",)),
            ("critique", "grok-feedback.md"),
        ):
            self.cli("run", phase)
            for f in ((artefact,) if isinstance(artefact, str) else artefact or ()):
                self.write(f)
            self.cli("complete", phase)

        code, payload, err = self.cli("doctor")
        self.assertEqual(code, 0, err)
        self.assertTrue(payload["ok"])


# --------------------------- statustabel ---------------------------


def _row(payload: dict, phase: str) -> dict:
    return next(r for r in payload["rows"] if r["phase"] == phase)


class TestStatusTable(OrchestrateTestCase):
    """Regressietest voor `table`: de tabel is een view, geen aparte state —
    fases vóór de huidige phase-index zijn 'gereed', erna 'open', de huidige
    fase toont de live status. Named exceptions krijgen een eigen label."""

    def test_fresh_post_only_outline_open_rest_untouched(self) -> None:
        self.init_state(yolo=False)
        code, payload, err = self.cli("table", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(_row(payload, "outline")["status"], "klaar om te starten")
        self.assertEqual(_row(payload, "draft")["status"], "open")
        self.assertEqual(_row(payload, "deploy")["status"], "open")

    def test_completed_phase_before_current_shows_gereed_with_artefact(self) -> None:
        self.init_state(yolo=False)
        self.cli("run", "outline")
        self.write("outline.md")
        self.cli("complete", "outline")
        self.cli("approve", "--note", "outline ok")

        code, payload, err = self.cli("table", "--json")
        self.assertEqual(code, 0, err)
        outline_row = _row(payload, "outline")
        self.assertEqual(outline_row["status"], "gereed")
        self.assertEqual(outline_row["artefact"], "outline.md")
        self.assertEqual(_row(payload, "draft")["status"], "klaar om te starten")

    def test_waiting_gate_and_running_reflected_on_current_phase(self) -> None:
        self.init_state(yolo=False)
        self.cli("run", "outline")
        code, payload, err = self.cli("table", "--json")
        self.assertEqual(_row(payload, "outline")["status"], "bezig")

        self.write("outline.md")
        self.cli("complete", "outline")
        code, payload, err = self.cli("table", "--json")
        self.assertEqual(_row(payload, "outline")["status"], "wacht op gate")

    def test_blocked_phase_shows_reason_in_note(self) -> None:
        self.init_state(yolo=False)
        self.cli("run", "outline")
        # outline.md ontbreekt -> complete faalt -> blocked
        self.cli("complete", "outline")
        code, payload, err = self.cli("table", "--json")
        self.assertEqual(code, 0, err)
        row = _row(payload, "outline")
        self.assertEqual(row["status"], "geblokkeerd")
        self.assertIn("outline.md", row["note"])

    def test_skip_synthesis_labeled_overgeslagen_not_gereed(self) -> None:
        self.init_state(yolo=False)
        state = self.state()
        state["phase"] = "visuals"
        state["status"] = "ready"
        state["flags"]["skip_synthesis"] = True
        _write_state(self.post_dir, state)
        self.write("draft.md")
        self.write("grok-feedback.md")

        code, payload, err = self.cli("table", "--json")
        self.assertEqual(code, 0, err)
        row = _row(payload, "synthesis")
        self.assertEqual(row["status"], "overgeslagen")
        self.assertNotEqual(row["status"], "gereed")
        self.assertIn("skip_synthesis", row["note"])

    def test_defer_critique_labeled_uitgesteld_not_gereed(self) -> None:
        self.init_state(yolo=False)
        state = self.state()
        state["phase"] = "visuals"
        state["status"] = "ready"
        state["flags"]["defer_critique"] = True
        _write_state(self.post_dir, state)
        self.write("draft.md")

        code, payload, err = self.cli("table", "--json")
        self.assertEqual(code, 0, err)
        row = _row(payload, "critique")
        self.assertEqual(row["status"], "uitgesteld")
        self.assertNotEqual(row["status"], "gereed")

    def test_done_pipeline_all_gereed_and_markdown_mentions_klaar(self) -> None:
        self.init_state(yolo=False)
        state = self.state()
        state["phase"] = "done"
        state["status"] = "done"
        state["artefacts"]["wp_post_id"] = 999
        state["artefacts"]["edit_url"] = "https://example.invalid/edit"
        _write_state(self.post_dir, state)
        for f in ("outline.md", "draft.md", "grok-feedback.md", "synthese.md"):
            self.write(f)
        os.makedirs(os.path.join(self.post_dir, "visuals"), exist_ok=True)
        self.write("visuals/a.svg")

        code, payload, err = self.cli("table", "--json")
        self.assertEqual(code, 0, err)
        for phase in ("outline", "draft", "style", "series", "critique", "synthesis", "visuals", "deploy"):
            self.assertEqual(_row(payload, phase)["status"], "gereed", phase)
        self.assertEqual(_row(payload, "deploy")["artefact"], "post 999")

        proc = subprocess.run(
            [sys.executable, ORCHESTRATE, "table", "--post-dir", self.post_dir],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("klaar", proc.stdout)

    def test_table_md_output_contains_expected_rows_and_no_done_row(self) -> None:
        self.init_state(yolo=False)
        proc = subprocess.run(
            [sys.executable, ORCHESTRATE, "table", "--post-dir", self.post_dir],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("| 1 Outline en verrijking |", proc.stdout)
        self.assertIn("| 6 Deploy (concept) |", proc.stdout)
        self.assertNotIn("| Klaar |", proc.stdout)


class TestVisualsDetectie(OrchestrateTestCase):
    """Regressietest: een post die al gepubliceerde media hergebruikt heeft geen
    bestanden in visuals/, maar heeft wel visuals. De postcheck moet daarop
    slagen (gevonden bij deel 10, de recap, 2026-08-03)."""

    def _zet_op_visuals_fase(self) -> None:
        self.init_state(yolo=False)
        state = self.state()
        state["phase"] = "visuals"
        state["status"] = "running"
        _write_state(self.post_dir, state)
        self.write("outline.md")
        self.write("grok-feedback.md")
        self.write("synthese.md")

    def test_twee_lokale_visualbestanden_tellen(self) -> None:
        self._zet_op_visuals_fase()
        self.write("draft.md", "# Titel\n\nGeen beeldverwijzing.\n")
        os.makedirs(os.path.join(self.post_dir, "visuals"), exist_ok=True)
        self.write("visuals/diagram.png", "x")
        self.write("visuals/kwadranten.png", "x")

        code, payload, err = self.cli("complete", "visuals")
        self.assertEqual(code, 0, err)

    def test_een_enkele_visual_blokkeert(self) -> None:
        """De huisstijl eist er minimaal twee; die eis hoort in de poort te zitten."""
        self._zet_op_visuals_fase()
        self.write("draft.md", "# Titel\n\nGeen beeldverwijzing.\n")
        os.makedirs(os.path.join(self.post_dir, "visuals"), exist_ok=True)
        self.write("visuals/diagram.png", "x")

        code, payload, err = self.cli("complete", "visuals")
        self.assertEqual(code, 2)
        self.assertIn("minimaal", " ".join(payload["errors"]).lower())

    def test_factcheck_vereist_feitencheck_md(self) -> None:
        self.init_state(yolo=True)
        state = self.state()
        state["phase"] = "factcheck"
        state["status"] = "running"
        _write_state(self.post_dir, state)
        self.write("draft.md")

        code, payload, err = self.cli("complete", "factcheck")
        self.assertEqual(code, 2)
        self.assertIn("feitencheck", " ".join(payload["errors"]).lower())

    BLOKKEREND_RAPPORT = (
        '# Rapport\n\n```json\n{"findings": [\n'
        '  {"severity": "blocking", "categorie": "misquote", "waar": "r.92",\n'
        '   "wat": "Het citaat mist de openingszinsnede uit de bron."}\n]}\n```\n'
    )

    def _factcheck_met(self, rapport: str) -> None:
        self.init_state(yolo=True)
        state = self.state()
        state["phase"] = "factcheck"
        state["status"] = "running"
        _write_state(self.post_dir, state)
        self.write("draft.md")
        self.write("feitencheck.md", rapport)

    def test_factcheck_met_bevinding_stopt_ook_in_yolo(self) -> None:
        """De laatste controle voor publicatie mag yolo niet stilzwijgend passeren."""
        self._factcheck_met(self.BLOKKEREND_RAPPORT)

        code, payload, err = self.cli("complete", "factcheck")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.state()["status"], "waiting_gate")
        self.assertEqual(self.state()["phase"], "factcheck")

    def test_factcheck_zonder_bevinding_schuift_door(self) -> None:
        """Een controle die niets vond, heeft niets voor te leggen (ADR-010 §3.1)."""
        self._factcheck_met(self.LEEG_RAPPORT)

        code, payload, err = self.cli("complete", "factcheck")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.state()["phase"], "alignment")
        self.assertEqual(self.state()["status"], "running")
        self.assertEqual(payload["auto_started"], "alignment")

    def test_svg_en_png_van_dezelfde_visual_tellen_als_een(self) -> None:
        """De PNG is de render van de SVG, geen tweede visual."""
        self._zet_op_visuals_fase()
        self.write("draft.md", "# Titel\n\nGeen beeldverwijzing.\n")
        os.makedirs(os.path.join(self.post_dir, "visuals"), exist_ok=True)
        self.write("visuals/diagram.svg", "x")
        self.write("visuals/diagram.png", "x")

        code, payload, err = self.cli("complete", "visuals")
        self.assertEqual(code, 2)

    def test_beeldverwijzing_naar_externe_media_telt_ook(self) -> None:
        self._zet_op_visuals_fase()
        # Geen visuals/-map: de draft verwijst naar al geuploade media.
        self.write(
            "draft.md",
            "# Titel\n\n![alt een](https://example.invalid/wp-content/uploads/x.png)\n"
            "\n![alt twee](https://example.invalid/wp-content/uploads/y.png)\n",
        )
        self.assertFalse(os.path.isdir(os.path.join(self.post_dir, "visuals")))

        code, payload, err = self.cli("complete", "visuals")
        self.assertEqual(code, 0, err)

    def test_zonder_visuals_en_zonder_beeldverwijzing_blokkeert(self) -> None:
        self._zet_op_visuals_fase()
        self.write("draft.md", "# Titel\n\nAlleen tekst, geen beeld.\n")

        code, payload, err = self.cli("complete", "visuals")
        self.assertEqual(code, 2)
        self.assertIn("visuals", " ".join(payload["errors"]).lower())


if __name__ == "__main__":
    unittest.main()
