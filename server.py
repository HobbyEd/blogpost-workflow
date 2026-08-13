"""FastAPI Web Server voor het Blogpost Workflow Command Center."""

from __future__ import annotations

import os
from typing import Any, Optional
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, status
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


class ChatStartRequest(BaseModel):
    session_id: str = Field(..., description="Unieke sessie identificatie")
    topic: str = Field(..., description="Onderwerp of voorlopige titel voor de brainstorm")


class ChatMessageRequest(BaseModel):
    session_id: str = Field(..., description="Sessie identificatie")
    message: str = Field(..., description="Bericht van de auteur aan de onderzoeker")


class ChatFinalizeRequest(BaseModel):
    session_id: str = Field(..., description="Sessie identificatie")
    slug: str = Field(..., description="Kebab-case slug voor de nieuwe post")
    titel: str = Field(..., description="Definitieve of voorlopige titel")
    yolo: bool = Field(False, description="Start direct in YOLO-modus")


class ResolveAlignmentRequest(BaseModel):
    action: str = Field(..., description="Actie: 'progressive_insight' of 'error_rejected'")
    note: Optional[str] = Field(None, description="Toelichtingsnotitie van de auteur bij voortschrijdend inzicht of afwijzing")


class ReindexRequest(BaseModel):
    purge_and_rebuild: bool = Field(False, description="Wis bestaande RAG index en bouw vanaf nul op")
    incremental: bool = Field(True, description="Indexeer uitsluitend nieuwe blogposts")


from scripts.orchestrator.brainstorm import (
    get_brainstorm_session,
    start_brainstorm_session,
)


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

web_dir = os.path.join(os.path.dirname(__file__), "web")
if os.path.isdir(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")


# --- Endpoints ---

@app.get("/")
def read_root():
    """HTML Web UI Dashboard voorpagina."""
    index_file = os.path.join(web_dir, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file)
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


# --- Modus 1: Socratische Chat Endpoints ---

@app.post("/api/chat/start")
def start_chat(req: ChatStartRequest) -> dict[str, Any]:
    """Start een nieuwe Socratische brainstorm sessie (Modus 1)."""
    sess = start_brainstorm_session(req.session_id, req.topic)
    return {
        "session_id": sess.session_id,
        "topic": sess.topic,
        "messages": sess.messages,
    }


@app.post("/api/chat/message")
def send_chat_message(req: ChatMessageRequest) -> dict[str, Any]:
    """Stuur een bericht in een actieve brainstorm sessie."""
    sess = get_brainstorm_session(req.session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Sessie {req.session_id} niet gevonden.")
    
    reply = sess.add_user_message(req.message)
    return {
        "session_id": sess.session_id,
        "reply": reply,
        "messages": sess.messages,
    }


@app.post("/api/chat/finalize")
def finalize_chat(req: ChatFinalizeRequest) -> dict[str, Any]:
    """Rond brainstorm af, schrijf briefing.md en initialiseer post voor Modus 2 (Stepper)."""
    sess = get_brainstorm_session(req.session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Sessie {req.session_id} niet gevonden.")

    # Initialiseer post via service
    init_res = service.init_post(
        slug=req.slug,
        titel=req.titel,
        yolo=req.yolo,
    )

    pdir = init_res["post_dir"]
    briefing_content = sess.generate_briefing_md(req.slug)
    briefing_path = os.path.join(pdir, "briefing.md")

    with open(briefing_path, "w", encoding="utf-8") as f:
        f.write(briefing_content)

    return {
        "ok": True,
        "slug": req.slug,
        "post_dir": pdir,
        "briefing_path": briefing_path,
        "briefing_preview": briefing_content,
        "state": init_res["state"],
    }


# --- Modus 4: RAG Archief Vectorstore & Archief-Alignment Endpoints ---

@app.get("/api/rag/status")
def get_rag_status() -> dict[str, Any]:
    """Haal de actuele status, statistieken en geïndexeerde artikelen van de RAG vectorstore op (ADR-008)."""
    return service.get_rag_status()


@app.get("/api/rag/search")
def search_rag_archive(q: str, top_k: int = 5) -> dict[str, Any]:
    """Zoek semantisch in eerdere blogposts (ADR-006 RAG Vectorstore)."""
    results = service.search_archive(query=q, top_k=top_k)
    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


@app.post("/api/rag/reindex")
def reindex_rag_archive() -> dict[str, Any]:
    """Herindexeer alle schijf-artefacten in posts/ naar de RAG Vectorstore (synchroon)."""
    return service.reindex_archive()


@app.post("/api/rag/reindex-async", status_code=status.HTTP_202_ACCEPTED)
def reindex_rag_archive_async(
    req: ReindexRequest,
    background_tasks: BackgroundTasks,
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
) -> dict[str, Any]:
    """Herindexeer het RAG archief op de achtergrond (non-blocking, beveiligd met ADMIN_TOKEN - ADR-008)."""
    expected_token = os.environ.get("ADMIN_TOKEN") or os.environ.get("admin_token")
    if expected_token and x_admin_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Onbevoegd: Ongeldige of ontbrekende ADMIN_TOKEN.",
        )

    background_tasks.add_task(
        service.reindex_archive,
        purge=req.purge_and_rebuild,
        incremental=req.incremental and not req.purge_and_rebuild,
    )

    return {
        "ok": True,
        "status": "indexing_started",
        "message": "RAG-indexering gestart op de achtergrond.",
        "purge": req.purge_and_rebuild,
    }


@app.post("/api/posts/{slug}/validate-alignment")
def validate_alignment(slug: str) -> dict[str, Any]:
    """Voer de Archief Alignment Check uit (Claude 3.5 Sonnet / ADR-009) en genereer archief-consistentie.md."""
    try:
        return service.validate_alignment(post=slug)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/posts/{slug}/resolve-alignment")
def resolve_alignment(slug: str, req: ResolveAlignmentRequest) -> dict[str, Any]:
    """Verwerk beslissing van de auteur bij een inhoudelijke afwijking (ADR-009)."""
    try:
        return service.resolve_alignment(post=slug, action=req.action, note=req.note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
