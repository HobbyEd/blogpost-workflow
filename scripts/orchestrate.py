#!/usr/bin/env python3
"""Strikte control plane voor de blogpost-workflow (CLI interface wrapper).

Fasevolgorde, pre/postconditions, gates en named exceptions zitten in het
`orchestrator` package. Dit script vormt de CLI wrapper om die functionaliteit.

Zie adr/ (geldend) en docs/README.md.

Gebruik:
    python3 scripts/orchestrate.py init --slug S --titel T
    python3 scripts/orchestrate.py status --post S
    python3 scripts/orchestrate.py next --post S
    python3 scripts/orchestrate.py run outline --post S
    python3 scripts/orchestrate.py complete outline --post S
    python3 scripts/orchestrate.py approve --post S --note "ok"
    python3 scripts/orchestrate.py terug --post S --note "andere invalshoek"
    python3 scripts/orchestrate.py doctor --post S
    python3 scripts/orchestrate.py import-md --post S

Exitcodes: 0 ok, 1 usage/IO, 2 illegale transitie of pre/post-fout, 3 doctor hard fail.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Zorg ervoor dat het 'orchestrator' package geïmporteerd kan worden
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from orchestrator.constants import FLAG_NAMES, PHASE_LABELS, RUNNABLE
from orchestrator.service import WorkflowService

service = WorkflowService()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Strikte blogpost-orkestrator (control plane)")
    sub = p.add_subparsers(dest="command", required=True)

    def add_post_args(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--post", help="Slug onder posts/")
        sp.add_argument("--post-dir", help="Absoluut of relatief pad naar postmap")

    sp = sub.add_parser("init", help="Nieuwe postmap + state.json")
    sp.add_argument("--slug", required=True)
    sp.add_argument("--titel", required=True)
    sp.add_argument("--yolo", action="store_true")
    sp.add_argument("--force", action="store_true")
    sp.add_argument(
        "--wait-intake-gate",
        action="store_true",
        help="Start op intake/waiting_gate i.p.v. outline/ready",
    )

    sp = sub.add_parser("status", help="Toon fase en next action")
    add_post_args(sp)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("table", help="Statustabel per fase, afgeleid uit state.json + schijf")
    add_post_args(sp)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("revisie", help="Opmerkingen na het lezen: toevoegen, afhandelen of tonen")
    add_post_args(sp)
    sp.add_argument("--opmerking", help="Nieuwe opmerking van de auteur")
    sp.add_argument("--waar", default="", help="Waar in de post, bv. 'sectie 6'")
    sp.add_argument("--afgehandeld", help="Punt-id dat is verwerkt")
    sp.add_argument("--hoe", default="", help="Hoe het punt is verwerkt")

    sp = sub.add_parser("herzien", help="Open een herzieningsronde: terug naar de draft")
    add_post_args(sp)

    sp = sub.add_parser("decide", help="Beslis over één kritiekpunt in de synthese")
    add_post_args(sp)
    sp.add_argument("--punt", required=True, help="Punt-id uit synthese.md")
    sp.add_argument("--keuze", required=True, help="Gekozen variant, bv. aannemen of verwerpen")
    sp.add_argument("--motivering", required=True, help="Eén regel: waarom deze keuze")

    sp = sub.add_parser("synthesis", help="Kritiekpunten met varianten en genomen besluiten")
    add_post_args(sp)

    sp = sub.add_parser("findings", help="Bevindingen van alle controlefases gebundeld")
    add_post_args(sp)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("next", help="Eén toegestane vervolgactie + agent_brief")
    add_post_args(sp)

    sp = sub.add_parser("run", help="Start phase (prechecks → running)")
    add_post_args(sp)
    sp.add_argument("phase", choices=sorted(RUNNABLE))

    sp = sub.add_parser("complete", help="Rond phase af (postchecks → gate of yolo)")
    add_post_args(sp)
    sp.add_argument("phase", choices=sorted(RUNNABLE))
    sp.add_argument("--post-id", type=int, default=None)
    sp.add_argument("--edit-url", default=None)

    sp = sub.add_parser("approve", help="Gate akkoord → volgende phase")
    add_post_args(sp)
    sp.add_argument("--note", default=None)
    sp.add_argument(
        "--deploy",
        action="store_true",
        help="Zet deploy_approved (en approve deploy-gate indien waiting)",
    )

    sp = sub.add_parser("reject", help="Gate afgewezen → opnieuw ready")
    add_post_args(sp)
    sp.add_argument("--note", default=None)

    sp = sub.add_parser(
        "terug",
        help="Outline-gate terug naar de agent met een verplichte opmerking",
    )
    add_post_args(sp)
    sp.add_argument("--note", required=True, help="Wat de agent moet aanpassen")

    sp = sub.add_parser("set-flag", help="Zet yolo_mode of named exception")
    add_post_args(sp)
    sp.add_argument("name", choices=["yolo_mode", *FLAG_NAMES])
    sp.add_argument("value", choices=["true", "false"])

    sp = sub.add_parser("doctor", help="Detecteer drift state vs. schijf")
    add_post_args(sp)

    sp = sub.add_parser("import-md", help="Importeer legacy state.md → state.json")
    add_post_args(sp)
    sp.add_argument("--force", action="store_true")

    sp = sub.add_parser("render-md", help="Projectie state.json → state.generated.md")
    add_post_args(sp)
    sp.add_argument("--in-place", action="store_true", help="Schrijf state.md (let op: overschrijft)")

    sp = sub.add_parser("repair", help="Stel phase/status voor op basis van artefacten")
    add_post_args(sp)
    sp.add_argument("--apply", action="store_true")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            res = service.init_post(
                slug=args.slug,
                titel=args.titel,
                yolo=args.yolo,
                force=args.force,
                wait_intake_gate=args.wait_intake_gate,
            )
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0

        if args.command == "status":
            res = service.get_status(post=args.post, post_dir=args.post_dir)
            if args.json:
                print(json.dumps(res, ensure_ascii=False, indent=2))
            else:
                print(f"Post:     {res['slug']}")
                print(f"Titel:    {res['titel']}")
                print(f"Phase:    {res['phase']} ({PHASE_LABELS.get(res['phase'], '')})")
                print(f"Status:   {res['status']}")
                print(f"Yolo:     {res['yolo_mode']}")
                print(f"Flags:    {json.dumps(res['flags'], ensure_ascii=False)}")
                print(f"Gate:     {json.dumps(res['gate'], ensure_ascii=False)}")
                if res.get("blocked_reason"):
                    print(f"Blocked:  {res['blocked_reason']}")
                print(f"Artefacts:{json.dumps(res['artefacts'], ensure_ascii=False)}")
                action = res["next"]
                print(f"Next:     {action.get('action')} — {action.get('summary')}")
            return 0

        if args.command == "table":
            res = service.get_table(post=args.post, post_dir=args.post_dir)
            if args.json:
                print(
                    json.dumps(
                        {"slug": res["slug"], "titel": res["titel"], "rows": res["rows"]},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            else:
                print(res["markdown"])
            return 0

        if args.command == "revisie":
            if args.opmerking and args.afgehandeld:
                print("Kies één van beide: --opmerking of --afgehandeld.", file=sys.stderr)
                return 1
            if args.opmerking:
                res = service.add_revision(
                    opmerking=args.opmerking, waar=args.waar,
                    post=args.post, post_dir=args.post_dir,
                )
                print(f"{res['punt']['id']} vastgelegd. Open: {res['open']} van {res['totaal']}.")
            elif args.afgehandeld:
                res = service.close_revision(
                    punt_id=args.afgehandeld, hoe=args.hoe,
                    post=args.post, post_dir=args.post_dir,
                )
                print(f"{res['punt']['id']} afgehandeld. Open: {res['open']} van {res['totaal']}.")
            else:
                res = service.get_revisions(post=args.post, post_dir=args.post_dir)
                print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0

        if args.command == "herzien":
            res = service.start_revision_round(post=args.post, post_dir=args.post_dir)
            ids = ", ".join(p["id"] for p in res["punten"])
            print(f"Herzieningsronde gestart: terug naar {res['phase']}. Open punten: {ids}.")
            return 0

        if args.command == "decide":
            res = service.decide_point(
                punt_id=args.punt,
                keuze=args.keuze,
                motivering=args.motivering,
                post=args.post,
                post_dir=args.post_dir,
            )
            print(f"{res['punt']}: {res['keuze']} vastgelegd. Nog open: {res['open']} van {res['totaal']}.")
            return 0

        if args.command == "synthesis":
            res = service.get_synthesis(post=args.post, post_dir=args.post_dir)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0

        if args.command == "findings":
            res = service.get_findings(post=args.post, post_dir=args.post_dir)
            if args.json:
                print(json.dumps(res, ensure_ascii=False, indent=2))
            else:
                print(res["markdown"])
            return 0

        if args.command == "next":
            res = service.get_next(post=args.post, post_dir=args.post_dir)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0

        if args.command == "run":
            res = service.run_phase(phase=args.phase, post=args.post, post_dir=args.post_dir)
            if not res.get("ok"):
                print(json.dumps(res, ensure_ascii=False, indent=2), file=sys.stderr)
                return 2
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0

        if args.command == "complete":
            res = service.complete_phase(
                phase=args.phase,
                post=args.post,
                post_dir=args.post_dir,
                post_id=args.post_id,
                edit_url=args.edit_url,
            )
            if not res.get("ok"):
                print(json.dumps(res, ensure_ascii=False, indent=2), file=sys.stderr)
                return 2
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0

        if args.command == "approve":
            res = service.approve_gate(
                post=args.post,
                post_dir=args.post_dir,
                note=args.note,
                deploy=args.deploy,
            )
            if not res.get("ok"):
                print(json.dumps(res, ensure_ascii=False, indent=2), file=sys.stderr)
                return 2
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0

        if args.command == "reject":
            res = service.reject_gate(
                post=args.post,
                post_dir=args.post_dir,
                note=args.note,
            )
            if not res.get("ok"):
                print(json.dumps(res, ensure_ascii=False, indent=2), file=sys.stderr)
                return 2
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0

        if args.command == "terug":
            res = service.return_with_note(
                note=args.note,
                post=args.post,
                post_dir=args.post_dir,
            )
            if not res.get("ok"):
                print(json.dumps(res, ensure_ascii=False, indent=2), file=sys.stderr)
                return 2
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0

        if args.command == "set-flag":
            val = args.value == "true"
            res = service.set_flag(
                name=args.name,
                value=val,
                post=args.post,
                post_dir=args.post_dir,
            )
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0

        if args.command == "doctor":
            res = service.doctor(post=args.post, post_dir=args.post_dir)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0 if res.get("ok") else 3

        if args.command == "import-md":
            res = service.import_md(
                post=args.post,
                post_dir=args.post_dir,
                force=args.force,
            )
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0

        if args.command == "render-md":
            res = service.render_md(
                post=args.post,
                post_dir=args.post_dir,
                in_place=args.in_place,
            )
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0

        if args.command == "repair":
            res = service.repair(
                post=args.post,
                post_dir=args.post_dir,
                apply=args.apply,
            )
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0

    except (FileNotFoundError, ValueError, FileExistsError) as e:
        print(str(e), file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Ongeldige JSON: {e}", file=sys.stderr)
        return 1

    parser.error(f"Onbekend commando: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
