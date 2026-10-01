from __future__ import annotations

import json
import logging
import re
import shutil
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import uuid
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .config import REPO_DIR, settings
from .repository import create_repository
from .schemas import AuthResponse, ChatRequest, ContractMetadataUpdate, LoginRequest, RegisterRequest, UserView
from .security import hash_password, issue_token, read_token, verify_password
from .services.analysis import analyze_contract
from .services.classifier import ClauseClassifier
from .services.documents import extract_document, page_text_ranges
from .services.llm import LLMService
from .services.reports import generate_pdf_report
from .services.retrieval import ContractRetriever
from .services.rules import RuleEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("contractsense.api")
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.upload_dir.mkdir(parents=True, exist_ok=True)
repo = create_repository(settings)
classifier = ClauseClassifier(settings.legalbert_model_path)
rule_engine = RuleEngine(Path(__file__).resolve().parents[1] / "legal_rules" / "central_rules.json")
retriever = ContractRetriever(repo, settings)
llm = LLMService(settings)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        try:
            repo.close()
        except Exception:
            pass


app = FastAPI(title=settings.app_name, version="0.1.0",
              description="India-aware contract review prototype. Issue-spotting only; not legal advice.",
              lifespan=lifespan)
origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                   allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])
WEB_DIR = REPO_DIR / "frontend" / "web"
FLUTTER_WEB_DIR = REPO_DIR / "frontend" / "build" / "web"
if WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(WEB_DIR)), name="assets")
if (FLUTTER_WEB_DIR / "index.html").is_file():
    app.mount("/flutter", StaticFiles(directory=str(FLUTTER_WEB_DIR), html=True), name="flutter-web")

CONTRACT_TYPES = {"nda", "employment", "vendor", "consultancy", "saas_it", "procurement", "lease", "data_processing", "other"}
ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {"id": user["id"], "email": user["email"], "full_name": user["full_name"], "created_at": user["created_at"]}


def current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    token_data = read_token(authorization.split(" ", 1)[1].strip(), settings.secret_key)
    if not token_data:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please sign in again.")
    user = repo.get_user(token_data["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="Account not found. Please sign in again.")
    return user


def _owned_contract(contract_id: str, user: dict[str, Any]) -> dict[str, Any]:
    contract = repo.get_contract(contract_id, user["id"])
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")
    return contract


def _analysis_is_current(contract: dict[str, Any], latest: dict[str, Any] | None) -> bool:
    if not latest or contract.get("status") != "analyzed":
        return False
    result = latest.get("result", {})
    if result.get("contract_type") != contract.get("contract_type"):
        return False
    if result.get("jurisdiction_state") != (contract.get("jurisdiction_state") or None):
        return False
    if result.get("governing_law") != (contract.get("governing_law") or None):
        return False
    if "msme_supplier" not in result or bool(result["msme_supplier"]) != bool(contract.get("msme_supplier", False)):
        return False
    analysis_engine = result.get("engine", {})
    if analysis_engine.get("classifier_engine") != classifier.engine:
        return False
    if analysis_engine.get("classifier") != classifier.description:
        return False
    if analysis_engine.get("classifier_config_fingerprint") != classifier.configuration_fingerprint:
        return False
    analyzed_rules = analysis_engine.get("rules", {})
    current_rules = rule_engine.info
    for key in ("ruleset_id", "version", "state_ruleset_id", "state_ruleset_version", "last_reviewed"):
        if analyzed_rules.get(key) != current_rules.get(key):
            return False
    return True


def _contract_view(contract: dict[str, Any], latest: dict[str, Any] | None = None) -> dict[str, Any]:
    analysis_current = _analysis_is_current(contract, latest)
    stale = bool(latest and not analysis_current)
    result = latest.get("result", {}) if latest and analysis_current else {}
    return {"id": contract["id"], "filename": contract["filename"], "contract_type": contract["contract_type"],
            "jurisdiction_state": contract.get("jurisdiction_state", ""), "governing_law": contract.get("governing_law", ""),
            "msme_supplier": bool(contract.get("msme_supplier", False)),
            "status": "needs_reanalysis" if stale else contract.get("status", "uploaded"),
            "analysis_stale": stale, "page_count": contract.get("page_count", 0),
            "created_at": contract.get("created_at"), "updated_at": contract.get("updated_at"),
            "analysis_id": latest.get("id") if latest and analysis_current else None,
            "overall_risk_score": result.get("overall_risk_score"), "overall_risk_level": result.get("overall_risk_level"),
            "clause_count": result.get("clause_count", 0)}


@app.get("/", include_in_schema=False)
def home():
    index = WEB_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"name": settings.app_name, "api": "/docs", "message": "Frontend assets are not installed."}


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "app": settings.app_name, "environment": settings.app_env,
            "database": settings.database_backend, "classifier": {"engine": classifier.engine, "description": classifier.description},
            "retrieval": retriever.mode, "llm": llm.status(), "ocr": {"tesseract_binary": bool(shutil.which("tesseract")), "language": settings.pdf_ocr_language},
            "ruleset": rule_engine.info}


@app.get("/api/v1/rules")
def get_rules():
    return {"ruleset": rule_engine.info, "notice": "Review prompts only; not legal advice or a complete pan-India rule set.", "rules": rule_engine.list_rules()}


@app.post("/api/v1/auth/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest):
    if repo.get_user_by_email(payload.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    try:
        password_hash = hash_password(payload.password)
        user = repo.create_user(payload.email, payload.full_name, password_hash)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.warning("Account registration failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=409, detail="Could not create account. Check whether the email is already registered.") from exc
    token = issue_token(user["id"], settings.secret_key, settings.token_ttl_hours)
    return {"access_token": token, "user": _public_user(user)}


@app.post("/api/v1/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    user = repo.get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    token = issue_token(user["id"], settings.secret_key, settings.token_ttl_hours)
    return {"access_token": token, "user": _public_user(user)}


@app.get("/api/v1/auth/me", response_model=UserView)
def me(user: dict[str, Any] = Depends(current_user)):
    return _public_user(user)


@app.get("/api/v1/dashboard/stats")
def dashboard_stats(user: dict[str, Any] = Depends(current_user)):
    contracts = repo.list_contracts(user["id"])
    current_results = []
    for contract in contracts:
        latest = repo.get_latest_analysis(contract["id"], user["id"])
        if _analysis_is_current(contract, latest):
            current_results.append(latest["result"])
    scores = [int(result.get("overall_risk_score", 0)) for result in current_results]
    return {"contracts_total": len(contracts), "analyzed_total": len(current_results),
            "high_priority_total": sum(result.get("overall_risk_level") == "high" for result in current_results),
            "average_risk_score": round(sum(scores) / len(scores)) if scores else 0}


@app.get("/api/v1/contracts/types")
def contract_types():
    return {"types": [
        {"id": "nda", "label": "Non-disclosure agreement"},
        {"id": "employment", "label": "Employment agreement"},
        {"id": "vendor", "label": "Vendor / service agreement"},
        {"id": "consultancy", "label": "Consultancy agreement"},
        {"id": "saas_it", "label": "SaaS / IT agreement"},
        {"id": "procurement", "label": "Procurement agreement"},
        {"id": "lease", "label": "Lease / rental agreement"},
        {"id": "data_processing", "label": "Data processing agreement"},
        {"id": "other", "label": "Other"},
    ]}


@app.post("/api/v1/contracts/upload", status_code=201)
async def upload_contract(file: UploadFile = File(...), contract_type: str = Form("other"),
                         jurisdiction_state: str = Form(""), governing_law: str = Form(""),
                         msme_supplier: bool = Form(False), user: dict[str, Any] = Depends(current_user)):
    filename = Path(file.filename or "contract").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Supported formats: PDF, DOCX, TXT, PNG, JPG, TIFF.")
    if contract_type not in CONTRACT_TYPES:
        raise HTTPException(status_code=422, detail="Select a supported contract type.")
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.max_upload_mb} MB upload limit.")
    if suffix == ".pdf" and not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File extension is PDF but the content is not a valid PDF.")
    contract_id = uuid.uuid4().hex
    stored_path = settings.upload_dir / f"{contract_id}{suffix}"
    stored_path.write_bytes(content)
    try:
        extracted = extract_document(filename, content, settings.pdf_ocr_language)
        contract = repo.create_contract(user["id"], filename, str(stored_path), contract_type,
                                        jurisdiction_state.strip(), governing_law.strip(), msme_supplier)
        # The ID is generated by the repository; use its path for storage cleanup/indexing.
        repo.update_contract(contract["id"], user["id"], extracted_text=extracted.text,
                             page_count=len(extracted.pages), page_ranges=page_text_ranges(extracted.pages),
                             status="ready")
        response_contract = repo.get_contract(contract["id"], user["id"])
        return {"contract": _contract_view(response_contract), "extraction": {"method": extracted.extraction_method,
                "page_count": len(extracted.pages), "character_count": len(extracted.text), "warnings": extracted.warnings},
                "next_step": f"POST /api/v1/contracts/{contract['id']}/analyze"}
    except Exception as exc:
        try:
            stored_path.unlink(missing_ok=True)
        except OSError:
            pass
        if isinstance(exc, HTTPException):
            raise
        if isinstance(exc, (ValueError, RuntimeError)):
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        logger.exception("Document ingestion failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Document ingestion failed. Check the file and server configuration.") from exc


@app.get("/api/v1/contracts")
def list_contracts(user: dict[str, Any] = Depends(current_user)):
    items = repo.list_contracts(user["id"])
    return {"items": [_contract_view(c, repo.get_latest_analysis(c["id"], user["id"])) for c in items]}


@app.get("/api/v1/contracts/{contract_id}")
def get_contract(contract_id: str, user: dict[str, Any] = Depends(current_user)):
    contract = _owned_contract(contract_id, user)
    latest = repo.get_latest_analysis(contract_id, user["id"])
    view = _contract_view(contract, latest)
    view["text_preview"] = contract.get("extracted_text", "")[:2500]
    analysis = latest.get("result") if latest and _analysis_is_current(contract, latest) else None
    return {"contract": view, "analysis": analysis}


@app.patch("/api/v1/contracts/{contract_id}")
def update_contract_metadata(contract_id: str, payload: ContractMetadataUpdate, user: dict[str, Any] = Depends(current_user)):
    existing = _owned_contract(contract_id, user)
    updates = payload.model_dump(exclude_none=True)
    changed = any(existing.get(key) != value for key, value in updates.items())
    if changed:
        repo.update_contract(contract_id, user["id"], status="metadata_changed", **updates)
    contract = _owned_contract(contract_id, user)
    return {"contract": _contract_view(contract, repo.get_latest_analysis(contract_id, user["id"]))}


@app.delete("/api/v1/contracts/{contract_id}")
def delete_contract(contract_id: str, user: dict[str, Any] = Depends(current_user)):
    contract = _owned_contract(contract_id, user)
    path = Path(contract.get("stored_path", ""))
    deleted = repo.delete_contract(contract_id, user["id"])
    if deleted:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Unable to remove stored file for contract %s", contract_id)
        try:
            retriever.delete(contract_id, user["id"])
        except Exception as exc:
            logger.warning("Unable to remove optional vector copies for contract %s (%s)", contract_id, type(exc).__name__)
    return {"deleted": deleted}


@app.post("/api/v1/contracts/{contract_id}/analyze")
def analyze(contract_id: str, user: dict[str, Any] = Depends(current_user)):
    contract = _owned_contract(contract_id, user)
    path = Path(contract.get("stored_path", ""))
    if not path.is_file():
        raise HTTPException(status_code=410, detail="The original upload is missing. Upload the contract again.")
    try:
        extracted = extract_document(contract.get("filename", path.name), path.read_bytes(), settings.pdf_ocr_language)
        page_ranges = page_text_ranges(extracted.pages)
        repo.update_contract(contract_id, user["id"], extracted_text=extracted.text,
                             page_count=len(extracted.pages), page_ranges=page_ranges, status="analyzed")
        contract.update({"extracted_text": extracted.text, "page_count": len(extracted.pages),
                         "page_ranges": page_ranges, "status": "analyzed"})
        result = analyze_contract(contract, classifier, rule_engine)
        retriever.index(contract_id, user["id"], result["clauses"])
        saved = repo.save_analysis(contract_id, user["id"], result)
        return {"analysis_id": saved["id"], "contract_id": contract_id, "result": result, "created_at": saved["created_at"]}
    except (ValueError, RuntimeError) as exc:
        repo.update_contract(contract_id, user["id"], status="error")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Analysis failed for contract %s", contract_id)
        repo.update_contract(contract_id, user["id"], status="error")
        raise HTTPException(status_code=500, detail="Analysis failed. Check server logs for a request ID; contract contents are not logged.") from exc


@app.get("/api/v1/contracts/{contract_id}/analysis")
def get_analysis(contract_id: str, user: dict[str, Any] = Depends(current_user)):
    contract = _owned_contract(contract_id, user)
    latest = repo.get_latest_analysis(contract_id, user["id"])
    if not latest:
        raise HTTPException(status_code=404, detail="No analysis exists yet. Run analysis first.")
    if not _analysis_is_current(contract, latest):
        raise HTTPException(status_code=409, detail="Contract metadata or analysis configuration changed. Re-run analysis before using this result.")
    return latest


@app.get("/api/v1/contracts/{contract_id}/clauses")
def get_clauses(contract_id: str, user: dict[str, Any] = Depends(current_user)):
    contract = _owned_contract(contract_id, user)
    latest = repo.get_latest_analysis(contract_id, user["id"])
    if not latest:
        raise HTTPException(status_code=404, detail="Run analysis before viewing clauses.")
    if not _analysis_is_current(contract, latest):
        raise HTTPException(status_code=409, detail="Contract metadata or analysis configuration changed. Re-run analysis before viewing clauses.")
    return {"items": latest["result"].get("clauses", [])}


@app.post("/api/v1/contracts/{contract_id}/chat")
def chat(contract_id: str, payload: ChatRequest, user: dict[str, Any] = Depends(current_user)):
    contract = _owned_contract(contract_id, user)
    latest = repo.get_latest_analysis(contract_id, user["id"])
    if not latest:
        raise HTTPException(status_code=409, detail="Analyze this contract before starting a contract-grounded chat.")
    if not _analysis_is_current(contract, latest):
        raise HTTPException(status_code=409, detail="Contract metadata or analysis configuration changed. Re-run analysis before chatting.")
    evidence = retriever.search(contract_id, user["id"], payload.message, limit=5)
    legal_notes = rule_engine.evaluate(contract.get("extracted_text", ""), contract)
    history = repo.get_messages(contract_id, user["id"], limit=8)
    response = llm.answer(payload.message, evidence, legal_notes, history=history)
    repo.save_message(contract_id, user["id"], "user", payload.message, [])
    repo.save_message(contract_id, user["id"], "assistant", response["answer"], evidence,
                      response.get("legal_sources", []), response.get("provider", ""),
                      response.get("limitations", ""))
    return response


@app.get("/api/v1/contracts/{contract_id}/chat")
def chat_history(contract_id: str, user: dict[str, Any] = Depends(current_user)):
    contract = _owned_contract(contract_id, user)
    latest = repo.get_latest_analysis(contract_id, user["id"])
    if latest and not _analysis_is_current(contract, latest):
        raise HTTPException(status_code=409, detail="Contract metadata or analysis configuration changed. Re-run analysis before viewing this chat history.")
    return {"items": repo.get_messages(contract_id, user["id"])}


@app.post("/api/v1/contracts/{contract_id}/suggestions")
def suggestions(contract_id: str, payload: ChatRequest, user: dict[str, Any] = Depends(current_user)):
    contract = _owned_contract(contract_id, user)
    latest = repo.get_latest_analysis(contract_id, user["id"])
    if not latest:
        raise HTTPException(status_code=409, detail="Analyze this contract before requesting a suggestion.")
    if not _analysis_is_current(contract, latest):
        raise HTTPException(status_code=409, detail="Contract metadata or analysis configuration changed. Re-run analysis before requesting a suggestion.")
    result = latest["result"]
    query = payload.message.strip()
    clause = next((c for c in result.get("clauses", []) if c.get("id") == query), None)
    if not clause:
        clause = next((c for c in result.get("clauses", []) if c.get("category", "").lower() in query.lower()), None)
    if not clause:
        raise HTTPException(status_code=404, detail="Mention a clause ID (such as clause-0001) or a clause category found in the analysis.")
    evidence = [{"text": clause["text"], "clause_id": clause["id"], "page": clause.get("page", 1)}]
    return {"clause_id": clause["id"], "category": clause["category"], **llm.suggest(clause["text"], clause["category"], evidence)}


@app.get("/api/v1/contracts/{contract_id}/report")
def report(contract_id: str, user: dict[str, Any] = Depends(current_user)):
    contract = _owned_contract(contract_id, user)
    latest = repo.get_latest_analysis(contract_id, user["id"])
    if not latest:
        raise HTTPException(status_code=404, detail="Run analysis before downloading a report.")
    if not _analysis_is_current(contract, latest):
        raise HTTPException(status_code=409, detail="Contract metadata or analysis configuration changed. Re-run analysis before downloading a report.")
    try:
        body = generate_pdf_report(latest["result"])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(contract["filename"]).stem)[:60] or "contract"
    return Response(content=body, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="ContractSense_{safe_name}_report.pdf"'})
