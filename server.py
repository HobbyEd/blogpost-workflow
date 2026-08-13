"""FastAPI Web Server voor het Blogpost Workflow Command Center."""

from __future__ import annotations

import os
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scripts.orchestrator import WorkflowService

app = FastAPI(
    title="Blogpost Workflow Command Center API",
    description="REST API voor de orkestratie van blogposts, agent-fasen, kwaliteits-gates en vlaggen.",
    version="1.0.0",
)

# CORS inschakelen voor lokale browser-interfaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = WorkflowService()


# --- Pydantic Schema's ---

class InitPostRequest(BaseModel):
    slug: str = Field(..., description="Kebab-case unieke identificatie (bijv. intentie-3-architectuur)")
    titel: str = Field(..., description="Werktitel van de blogpost")
    yolo: bool = Field(False, description="Direct in YOLO-modus starten")
    wait_intake_gate: bool = Field(False, description="Wachten op menselijk akkoord bij intake")


class ActionRequest(BaseModel):
    note: Optional[str] = Field(None, description="Optionele toelichting of beslissingsnotitie")
    post_id: Optional[int] = Field(None, description="WordPress post ID (nodig bij complete deploy)")
    edit_url: Optional[str] = Field(None, description="WordPress bewerk-URL (nodig bij complete deploy)")
    deploy: bool = Field(False, description="Deploy-specifieke goedkeuring (approve --deploy)")


class SetFlagRequest(BaseModel):
    name: str = Field(..., description="Vlagnaam: yolo_mode, skip_synthesis, defer_critique, skip_factcheck, deploy_approved")
    value: bool = Field(..., description="Waarde van de vlag (True / False)")


class ImportMdRequest(BaseModel):
    force: bool = Field(False, description="Overschrijf bestaande state.json indien aanwezig")


class RepairRequest(BaseModel):
    apply: bool = Field(False, description="Pas voorgestelde fase-reparatie direct toe op state.json")


# --- Endpoints ---

@app.get("/")
def read_root() -> dict[str, str]:
    """Health check & API status."""
    return {
        "status": "online",
        "service": "Blogpost Workflow Command Center API",
        "posts_root": service.posts_root(),
    }


@app.get("/api/posts")
def list_posts() -> dict[str, Any]:
    """Haal de lijst op van alle actieve blogposts in de posts/ map."""
    posts_dir = service.posts_root()
    if not os.path.exists(posts_dir):
        return {"posts": []}

    results: list[dict[str, Any]] = []
    for entry in sorted(os.listdir(posts_dir)):
        pdir = os.path.join(posts_dir, entry)
        state_file = os.path.join(pdir, "state.json")
        if os.path.isdir(pdir) and os.path.isfile(state_file):
            try:
                doc = service.doctor(post_dir=pdir)
                results.append({
                    "slug": doc.get("slug", entry),
                    "phase": doc.get("phase"),
                    "status": doc.get("status"),
                    "flags": doc.get("flags"),
                    "ok": doc.get("ok"),
                    "issues_count": len(doc.get("issues", [])),
                    "next": doc.get("next"),
                })
            except Exception as e:
                results.append({"slug": entry, "error": str(e)})

    return {"count": len(results), "posts": results}


@app.post("/api/posts/init", status_code=status.HTTP_201_CREATED)
def init_post(req: InitPostRequest) -> dict[str, Any]:
    """Maak een nieuwe blogpost map aan en initialiseer state.json."""
    try:
        return service.init_post(
            slug=req.slug,
            titel=req.titel,
            yolo=req.yolo,
            wait_intake_gate=req.wait_intake_gate,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/api/posts/{slug}")
def get_post_detail(slug: str) -> dict[str, Any]:
    """Haal gedetailleerde informatie op van een specifieke post (status, statustabel, next)."""
    try:
        status_info = service.get_status(post=slug)
        doctor_info = service.doctor(post=slug)
        return {
            "slug": slug,
            "status_info": status_info,
            "doctor_info": doctor_info,
            "markdown_table": status_info.get("markdown"),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/posts/{slug}/run/{phase}")
def run_phase(slug: str, phase: str) -> dict[str, Any]:
    """Start een specifieke fase voor een blogpost."""
    try:
        return service.run_phase(phase=phase, post=slug)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/posts/{slug}/complete/{phase}")
def complete_phase(slug: str, phase: str, req: ActionRequest = ActionRequest()) -> dict[str, Any]:
    """Rond een actieve fase af (met optionele post_id en edit_url voor deploy)."""
    try:
        return service.complete_phase(
            phase=phase,
            post=slug,
            post_id=req.post_id,
            edit_url=req.edit_url,
        )
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/posts/{slug}/approve")
def approve_gate(slug: str, req: ActionRequest = ActionRequest()) -> dict[str, Any]:
    """Keur de huidige kwaliteits-gate goed en schuif door naar de volgende fase."""
    try:
        return service.approve_gate(post=slug, note=req.note, deploy=req.deploy)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/posts/{slug}/reject")
def reject_gate(slug: str, req: ActionRequest = ActionRequest()) -> dict[str, Any]:
    """Wijs de huidige kwaliteits-gate af en zet de status terug naar ready."""
    try:
        return service.reject_gate(post=slug, note=req.note)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/posts/{slug}/flags")
def set_flag(slug: str, req: SetFlagRequest) -> dict[str, Any]:
    """Schakel een vlag of YOLO-modus in of uit."""
    try:
        return service.set_flag(name=req.name, value=req.value, post=slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/posts/{slug}/doctor")
def doctor_check(slug: str) -> dict[str, Any]:
    """Inspecteer de integriteit en eventuele drift van state.json vs. schijf."""
    try:
        return service.doctor(post=slug)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/posts/{slug}/repair")
def repair_state(slug: str, req: RepairRequest = RepairRequest()) -> dict[str, Any]:
    """Herleid de juiste fase vanaf schijf-artefacten en pas eventueel toe."""
    try:
        return service.repair(post=slug, apply=req.apply)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/posts/{slug}/import-md")
def import_md(slug: str, req: ImportMdRequest = ImportMdRequest()) -> dict[str, Any]:
    """Importeer een legacy state.md bestand naar state.json."""
    try:
        return service.import_md(post=slug, force=req.force)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
