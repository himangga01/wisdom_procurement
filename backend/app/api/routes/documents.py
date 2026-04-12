import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.document import ProjectDocument
from app.models.project import Project
from app.schemas.document import DocumentRead, ReanalyzeResponse
from app.services.analysis_service import run_document_analysis

router = APIRouter()

ALLOWED_EXT = {".pdf", ".docx"}


@router.get("", response_model=list[DocumentRead])
def list_documents(project_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(ProjectDocument)
    if project_id is not None:
        query = query.filter(ProjectDocument.project_id == project_id)
    return query.order_by(ProjectDocument.id.desc()).all()


@router.post("", response_model=DocumentRead)
async def upload_document(
    project_id: int = Form(...),
    document_type: str = Form("general"),
    memo: str = Form(""),
    revision_note: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=400, detail="Invalid project_id")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX are supported")

    storage_dir = Path(settings.storage_root) / "uploads" / str(project_id)
    storage_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = storage_dir / safe_name

    content = await file.read()
    stored_path.write_bytes(content)

    doc = ProjectDocument(
        project_id=project_id,
        document_type=document_type,
        original_file_name=file.filename,
        stored_file_path=str(stored_path),
        mime_type=file.content_type or "",
        file_size=len(content),
        memo=memo,
        revision_note=revision_note,
        parsing_status="pending",
        ocr_status="pending",
        analysis_status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return doc


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    path = Path(doc.stored_file_path)
    if path.exists():
        path.unlink()

    db.delete(doc)
    db.commit()
    return {"status": "deleted"}


@router.post("/{document_id}/reanalyze", response_model=ReanalyzeResponse)
def reanalyze_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    analysis = run_document_analysis(db, doc, force=True)
    return ReanalyzeResponse(analysis_id=analysis.id, status="completed", message="Re-analysis completed")


@router.post("/{document_id}/analyze", response_model=ReanalyzeResponse)
def analyze_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    analysis = run_document_analysis(db, doc, force=False)
    return ReanalyzeResponse(analysis_id=analysis.id, status="completed", message="Analysis completed")
