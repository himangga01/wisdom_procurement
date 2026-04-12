from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.corporation import Corporation
from app.schemas.corporation import CorporationCreate, CorporationRead, CorporationUpdate

router = APIRouter()


@router.get("", response_model=list[CorporationRead])
def list_corporations(db: Session = Depends(get_db)):
    return db.query(Corporation).order_by(Corporation.id.desc()).all()


@router.post("", response_model=CorporationRead)
def create_corporation(payload: CorporationCreate, db: Session = Depends(get_db)):
    corp = Corporation(**payload.model_dump())
    db.add(corp)
    db.commit()
    db.refresh(corp)
    return corp


@router.get("/{corporation_id}", response_model=CorporationRead)
def get_corporation(corporation_id: int, db: Session = Depends(get_db)):
    corp = db.query(Corporation).filter(Corporation.id == corporation_id).first()
    if not corp:
        raise HTTPException(status_code=404, detail="Corporation not found")
    return corp


@router.patch("/{corporation_id}", response_model=CorporationRead)
def update_corporation(corporation_id: int, payload: CorporationUpdate, db: Session = Depends(get_db)):
    corp = db.query(Corporation).filter(Corporation.id == corporation_id).first()
    if not corp:
        raise HTTPException(status_code=404, detail="Corporation not found")

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(corp, key, value)

    db.commit()
    db.refresh(corp)
    return corp


@router.delete("/{corporation_id}")
def delete_corporation(corporation_id: int, db: Session = Depends(get_db)):
    corp = db.query(Corporation).filter(Corporation.id == corporation_id).first()
    if not corp:
        raise HTTPException(status_code=404, detail="Corporation not found")

    db.delete(corp)
    db.commit()
    return {"status": "deleted"}
