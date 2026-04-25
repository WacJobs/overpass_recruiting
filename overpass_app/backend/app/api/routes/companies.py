from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyOut

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyOut])
def read_companies(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rows = db.execute(select(Company).limit(limit)).scalars().all()
    return rows


@router.get("/{osm_id}", response_model=CompanyOut)
def read_company(osm_id: str, db: Session = Depends(get_db)):
    company = db.get(Company, osm_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company
