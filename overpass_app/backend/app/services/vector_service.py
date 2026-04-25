import json

from sklearn.feature_extraction.text import HashingVectorizer
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.company import Company, CompanyPage, CompanyVector

settings = get_settings()

vectorizer = HashingVectorizer(
    n_features=settings.vector_dim,
    alternate_sign=False,
    norm="l2",
    stop_words="english",
)

MODEL_NAME = "hashing_vectorizer_v1"


def build_company_text(company: Company, latest_page: CompanyPage | None) -> str:
    pieces = [
        company.name or "",
        company.city or "",
        company.website or "",
        latest_page.cleaned_text if latest_page and latest_page.cleaned_text else "",
    ]
    return " ".join(piece for piece in pieces if piece).strip()


def vectorize_text(text: str) -> list[float]:
    arr = vectorizer.transform([text]).toarray()[0]
    return arr.astype(float).tolist()


def vectorize_companies(db: Session, limit: int = 500) -> dict[str, int]:
    companies = db.execute(select(Company).limit(limit)).scalars().all()

    processed = 0
    updated = 0

    for company in companies:
        latest_page = db.execute(
            select(CompanyPage)
            .where(CompanyPage.company_osm_id == company.osm_id)
            .order_by(desc(CompanyPage.fetched_at))
            .limit(1)
        ).scalar_one_or_none()

        company_text = build_company_text(company, latest_page)
        if not company_text:
            continue

        vector_json = json.dumps(vectorize_text(company_text))
        existing = db.get(CompanyVector, company.osm_id)

        if existing:
            existing.model_name = MODEL_NAME
            existing.vector_dim = settings.vector_dim
            existing.vector_json = vector_json
        else:
            db.add(
                CompanyVector(
                    company_osm_id=company.osm_id,
                    model_name=MODEL_NAME,
                    vector_dim=settings.vector_dim,
                    vector_json=vector_json,
                )
            )
        processed += 1
        updated += 1

    db.commit()
    return {"processed": processed, "updated": updated}
