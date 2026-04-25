from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import Base, engine, get_db
from app.schemas.admin import OverpassIngestRequest, ScrapeRequest, VectorizeRequest
from app.services.overpass_service import ingest_from_overpass
from app.services.scrape_service import scrape_company_websites
from app.services.vector_service import vectorize_companies

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/init-db")
def init_db() -> dict:
    Base.metadata.create_all(bind=engine)
    return {"status": "initialized"}


@router.post("/ingest-overpass")
def ingest_overpass(payload: OverpassIngestRequest, db: Session = Depends(get_db)):
    return ingest_from_overpass(
        db=db,
        south=payload.south,
        west=payload.west,
        north=payload.north,
        east=payload.east,
        name_filter=payload.name_filter,
        office_filter=payload.office_filter,
    )


@router.post("/scrape-websites")
def scrape_websites(payload: ScrapeRequest, db: Session = Depends(get_db)):
    return scrape_company_websites(db=db, limit=payload.limit)


@router.post("/vectorize-companies")
def vectorize_company_texts(payload: VectorizeRequest, db: Session = Depends(get_db)):
    return vectorize_companies(db=db, limit=payload.limit)
