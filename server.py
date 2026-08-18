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


@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


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


class ReturnRequest(BaseModel):
    note: str = Field("", description="Opmerking voor de agent (verplicht bij outline)")
    phase: str = Field("outline", description="Fase om naar terug te gaan")


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
        return FileResponse(index_file, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return {
        "status": "online",
        "service": "Blogpost Workflow Command Center API",
        "posts_root": service.posts_root(),
    }


@app.get("/api/worker")
def get_worker() -> dict[str, Any]:
    """Lees of de execution-plane worker leeft, en welke fase hij draait.

    De worker is een apart proces. Dit endpoint leest alleen het heartbeat-bestand.
    """
    return service.get_worker_status()


@app.get("/api/posts")
def list_posts() -> dict[str, Any]:
    """Haal de lijst op van alle actieve blogposts in de posts/ map, gesorteerd op meest recent gewijzigd (aflopend)."""
    posts_dir = service.posts_root()
    if not os.path.exists(posts_dir):
        return {"count": 0, "posts": []}

    results: list[dict[str, Any]] = []
    entries = [e for e in os.listdir(posts_dir) if not e.startswith(".")]

    for entry in entries:
        pdir = os.path.join(posts_dir, entry)
        state_file = os.path.join(pdir, "state.json")
        if os.path.isdir(pdir) and os.path.isfile(state_file):
            try:
                mtime = os.path.getmtime(state_file)
                doc = service.doctor(post_dir=pdir)
                results.append({
                    "slug": doc.get("slug", entry),
                    "phase": doc.get("phase"),
                    "status": doc.get("status"),
                    "flags": doc.get("flags"),
                    "ok": doc.get("ok"),
                    "issues_count": len(doc.get("issues", [])),
                    "next": doc.get("next"),
                    "mtime": mtime,
                })
            except Exception as e:
                results.append({"slug": entry, "error": str(e), "mtime": 0})

    # Sorteer aflopend op mtime (meest recente blogpost bovenaan)
    results.sort(key=lambda x: x.get("mtime", 0), reverse=True)

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
    """Haal gedetailleerde informatie op van een specifieke post (status, statustabel, next, artefact_contents)."""
    try:
        status_info = service.get_status(post=slug)
        doctor_info = service.doctor(post=slug)

        # Platslaan van status_info naar top-level velden voor de Web UI
        res = dict(status_info)
        res["slug"] = slug
        res["status_info"] = status_info
        res["doctor_info"] = doctor_info
        # De statustabel komt uit de orkestrator, niet uit een tweede implementatie in
        # de frontend. status_info bevat geen markdown; dit veld was daardoor altijd leeg
        # en de UI viel terug op een eigen renderer die inmiddels was afgedreven.
        tabel = service.get_table(post=slug)
        res["markdown_table"] = tabel["markdown"]
        res["blocks"] = tabel["blocks"]

        # Inlezen van artefact bestandsinhoud (draft.md, outline.md, etc.)
        pdir = os.path.join(service.posts_root(), slug)
        artefact_contents = {}
        for fname in [
            "draft.md", "synthese.md", "outline.md", "briefing.md", "grok-feedback.md",
            "stijlcheck.md", "leesbaarheid.md", "reeks-check.md",
            "feitencheck.md", "feitencheck-draft.md", "archief-consistentie.md",
        ]:
            fpath = os.path.join(pdir, fname)
            if os.path.isfile(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                        key = fname.replace(".md", "").replace("-", "_")
                        artefact_contents[key] = content
                        artefact_contents[fname] = content
                except Exception:
                    pass
        res["artefact_contents"] = artefact_contents
        return res
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


_MEDIA_EXT = {".png", ".svg", ".jpg", ".jpeg", ".webp"}


@app.get("/api/posts/{slug}/media/{rel_path:path}")
def get_post_media(slug: str, rel_path: str) -> FileResponse:
    """Geef een visual uit de postmap. Alleen visuals/ met een beeldextensie."""
    delen = [p for p in rel_path.split("/") if p]
    if not delen or delen[0] != "visuals" or ".." in delen:
        raise HTTPException(status_code=404, detail="Alleen visuals/ is opvraagbaar.")
    ext = os.path.splitext(delen[-1])[1].lower()
    if ext not in _MEDIA_EXT:
        raise HTTPException(status_code=404, detail="Dit bestandstype is geen visual.")
    try:
        pdir = service.resolve_dir(post=slug)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    pad = os.path.abspath(os.path.join(pdir, *delen))
    wortel = os.path.abspath(pdir) + os.sep
    if not pad.startswith(wortel) or not os.path.isfile(pad):
        raise HTTPException(status_code=404, detail="Bestand niet gevonden.")
    return FileResponse(pad)


class RevisionRequest(BaseModel):
    opmerking: str = Field(..., description="Opmerking van de auteur na het lezen")
    waar: str = Field("", description="Waar in de post, bv. 'sectie 6'")


class CloseRevisionRequest(BaseModel):
    punt: str = Field(..., description="Punt-id uit revisie.md")
    hoe: str = Field(..., description="Hoe de opmerking is verwerkt")


@app.get("/api/posts/{slug}/revisions")
def get_revisions(slug: str) -> dict[str, Any]:
    """Opmerkingen van de auteur na het lezen in WordPress (ADR-010 §3.4)."""
    try:
        return service.get_revisions(post=slug)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/posts/{slug}/revisions")
def add_revision(slug: str, req: RevisionRequest) -> dict[str, Any]:
    """Leg een opmerking vast; ze houdt de volgende deploy tegen tot ze is verwerkt."""
    try:
        return service.add_revision(opmerking=req.opmerking, waar=req.waar, post=slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/posts/{slug}/revisions/close")
def close_revision(slug: str, req: CloseRevisionRequest) -> dict[str, Any]:
    """Markeer een opmerking als verwerkt, met hoe."""
    try:
        return service.close_revision(punt_id=req.punt, hoe=req.hoe, post=slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/posts/{slug}/revisions/start-round")
def start_revision_round(slug: str) -> dict[str, Any]:
    """Open een herzieningsronde: terug naar de draft met de opmerkingen als opdracht."""
    try:
        return service.start_revision_round(post=slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


class DecidePointRequest(BaseModel):
    punt: str = Field(..., description="Punt-id uit synthese.md")
    keuze: str = Field(..., description="Gekozen variant, bv. 'aannemen' of 'verwerpen'")
    motivering: str = Field("", description="Optionele toelichting bij de keuze")


@app.get("/api/posts/{slug}/synthesis")
def get_synthesis(slug: str) -> dict[str, Any]:
    """Kritiekpunten met hun varianten en de genomen beslissingen (ADR-010 §3.3)."""
    try:
        return service.get_synthesis(post=slug)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/posts/{slug}/synthesis/decide")
def decide_point(slug: str, req: DecidePointRequest) -> dict[str, Any]:
    """Leg de beslissing van de auteur bij één kritiekpunt vast."""
    try:
        return service.decide_point(
            punt_id=req.punt, keuze=req.keuze, motivering=req.motivering, post=slug
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/posts/{slug}/findings")
def get_findings(slug: str) -> dict[str, Any]:
    """Bundel de bevindingen van alle controlefases (ADR-010 §6, stap 3).

    Afgeleid uit de rapporten op schijf, zodat het overzicht niet kan verouderen.
    """
    try:
        return service.get_findings(post=slug)
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


@app.post("/api/posts/{slug}/return")
def return_with_note(slug: str, req: ReturnRequest) -> dict[str, Any]:
    """Stuur de outline-gate terug naar de agent met een verplichte opmerking."""
    try:
        res = service.return_with_note(post=slug, note=req.note, phase=req.phase)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not res.get("ok"):
        raise HTTPException(
            status_code=400,
            detail="; ".join(res.get("errors") or ["terugsturen geweigerd"]),
        )
    return res


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
    """Zoek lexicaal (TF-IDF) in eerdere blogposts (ADR-006 RAG Vectorstore)."""
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
    expected_token = os.environ.get("ADMIN_TOKEN")
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
    """Lees het verdict uit archief-consistentie.md in state.json (ADR-007).

    Voert de check niet uit: die doet de subagent archief-consistentie-check in fase 5c.
    Ontbreekt het rapport, dan volgt een 404.
    """
    try:
        return service.validate_alignment(post=slug)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/posts/{slug}/resolve-alignment")
def resolve_alignment(slug: str, req: ResolveAlignmentRequest) -> dict[str, Any]:
    """Verwerk beslissing van de auteur bij een inhoudelijke afwijking (ADR-007)."""
    try:
        return service.resolve_alignment(post=slug, action=req.action, note=req.note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
