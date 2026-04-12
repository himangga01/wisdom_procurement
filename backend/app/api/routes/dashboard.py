from fastapi import APIRouter
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.corporation import Corporation
from app.models.document import ProjectDocument
from app.models.project import Project
from fastapi import Depends

router = APIRouter()


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    return {
        "corporation_count": db.query(func.count(Corporation.id)).scalar() or 0,
        "project_count": db.query(func.count(Project.id)).scalar() or 0,
        "document_count": db.query(func.count(ProjectDocument.id)).scalar() or 0,
    }
