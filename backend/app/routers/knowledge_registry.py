"""External threat-knowledge ingestion and review endpoints."""
import io
import json
from datetime import date, datetime, timezone

import httpx
from docx import Document
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PyPDF2 import PdfReader
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.knowledge_registry import KnowledgeRegistry
from app.models.user import User

router = APIRouter(prefix="/api/knowledge-registry", tags=["Knowledge Registry"])
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".html", ".htm"}


def _text_from_file(filename: str, payload: bytes) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == ".pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(payload)).pages)
    if ext == ".docx":
        return "\n".join(p.text for p in Document(io.BytesIO(payload)).paragraphs)
    return payload.decode("utf-8", errors="replace")


async def _extract_with_qwen(text: str) -> dict:
    """Use an OpenAI-compatible Qwen endpoint when configured; retain a useful local fallback."""
    fallback = {
        "title": next((line.strip() for line in text.splitlines() if line.strip()), "Untitled external knowledge"),
        "summary": text[:1000].strip(), "keywords": [], "language": "en",
        "threat_type": None, "threat_name": None, "threat_actor": None, "campaign_name": None,
        "attack_vector": None, "attack_stage": None, "exploitation_status": None,
        "vendor": None, "product": None, "product_version": None, "operating_system": None,
        "affected_assets": [], "industry_targets": [], "cve_ids": [], "cwe_ids": [],
        "cvss_score": None, "severity": None, "exploit_available": None, "exploit_type": None,
        "mitre_tactics": [], "mitre_techniques": [], "malware_family": None,
        "indicators_of_compromise": {"ip_addresses": [], "domains": [], "urls": [], "file_hashes": [], "registry_keys": []},
        "yara_rules": [], "sigma_rules": [], "business_impact": None, "likelihood": None,
        "risk_level": None, "exploit_maturity": None, "patch_available": None, "patch_reference": None,
        "workaround": None, "recommended_actions": [], "nist_controls": [], "iso27001_controls": [],
        "cis_controls": [], "certin_guidelines": [], "benchmark_category": None,
        "audit_questions": [], "expected_controls": [], "required_evidence": [], "expected_artifacts": [],
        "audit_priority": None, "confidence_score": 0.25, "tags": [],
    }
    if not settings.QWEN_API_URL:
        return fallback
    prompt = "Extract cyber threat intelligence into valid JSON. Use these exact keys: " + ", ".join(fallback) + ". Return JSON only.\n\nSOURCE:\n" + text[:30000]
    try:
        headers = {"Authorization": f"Bearer {settings.QWEN_API_KEY}"} if settings.QWEN_API_KEY else {}
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(settings.QWEN_API_URL, headers=headers, json={"model": settings.QWEN_MODEL, "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}})
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        extracted = json.loads(content)
        return {**fallback, **{key: value for key, value in extracted.items() if key in fallback}}
    except Exception:
        return fallback


@router.post("/extract", status_code=status.HTTP_201_CREATED)
async def extract_knowledge(
    file: UploadFile = File(...), source_name: str = Form(...), source_type: str = Form(...),
    source_url: str | None = Form(None), publication_date: date | None = Form(None),
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    filename = file.filename or "source.txt"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Only PDF, DOCX, TXT, and HTML files are supported.")
    text = _text_from_file(filename, await file.read())
    if not text.strip():
        raise HTTPException(400, "No readable text could be extracted from this file.")
    extracted = await _extract_with_qwen(text)
    record = KnowledgeRegistry(source_name=source_name, source_type=source_type, source_url=source_url,
        publication_date=publication_date, ingestion_date=datetime.now(timezone.utc), original_text=text,
        extraction_model=settings.QWEN_MODEL if settings.QWEN_API_URL else "local-fallback", reviewed_by_analyst=False,
        status="Active", **extracted)
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return _serialize(record)


@router.get("")
async def list_knowledge(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(KnowledgeRegistry).order_by(desc(KnowledgeRegistry.updated_at)).limit(100))).scalars().all()
    return {"records": [_serialize(row) for row in rows]}


@router.put("/{knowledge_id}")
async def update_knowledge(knowledge_id: int, payload: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    record = await db.get(KnowledgeRegistry, knowledge_id)
    if not record:
        raise HTTPException(404, "Knowledge record not found.")
    allowed = {column.name for column in KnowledgeRegistry.__table__.columns} - {"knowledge_id", "knowledge_uuid", "created_at"}
    for key, value in payload.items():
        if key in allowed:
            setattr(record, key, value)
    record.updated_at = datetime.now(timezone.utc)
    await db.flush(); await db.refresh(record)
    return _serialize(record)


def _serialize(record: KnowledgeRegistry) -> dict:
    return {column.name: getattr(record, column.name) for column in record.__table__.columns}
