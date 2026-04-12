from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.document import ProjectDocument
from app.schemas.analysis import AnalysisRead

router = APIRouter()


@router.get("/{analysis_id}", response_model=AnalysisRead)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.get("/latest/by-document/{document_id}", response_model=AnalysisRead)
def get_latest_analysis_by_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not doc or not doc.latest_analysis_id:
        raise HTTPException(status_code=404, detail="Latest analysis not found")

    analysis = db.query(Analysis).filter(Analysis.id == doc.latest_analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return analysis
