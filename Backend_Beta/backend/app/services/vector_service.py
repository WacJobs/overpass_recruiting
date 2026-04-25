import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.company import Company, CompanyPage, CompanyVector

settings = get_settings()

MODEL_NAME = "tfidf_v1"


def build_company_text(company: Company, latest_page: CompanyPage | None) -> str:
    pieces = [
        company.name or "",
        company.city or "",
        company.website or "",
        latest_page.cleaned_text if latest_page and latest_page.cleaned_text else "",
    ]
    return " ".join(piece for piece in pieces if piece).strip()


def make_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        max_features=settings.tfidf_max_features,
        stop_words="english",
        lowercase=True,
    )


def _artifact_path() -> Path:
    path = Path(settings.vectorizer_artifact_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_vectorizer(vectorizer: TfidfVectorizer) -> None:
    joblib.dump(vectorizer, _artifact_path())


def load_vectorizer() -> TfidfVectorizer:
    path = _artifact_path()
    if not path.exists():
        raise ValueError(
            "No fitted TF-IDF vectorizer artifact was found. "
            "Run /api/admin/vectorize-companies first."
        )
    return joblib.load(path)


def vectorize_resume_text(text: str) -> list[float]:
    vectorizer = load_vectorizer()
    arr = vectorizer.transform([text]).toarray()[0]
    return arr.astype(float).tolist()


def vectorize_companies(db: Session, limit: int = 500) -> dict[str, int]:
    companies = db.execute(select(Company).limit(limit)).scalars().all()

    rows: list[tuple[Company, str]] = []

    for company in companies:
        latest_page = db.execute(
            select(CompanyPage)
            .where(CompanyPage.company_osm_id == company.osm_id)
            .order_by(desc(CompanyPage.fetched_at))
            .limit(1)
        ).scalar_one_or_none()

        company_text = build_company_text(company, latest_page)
        if company_text:
            rows.append((company, company_text))

    if not rows:
        return {"processed": 0, "updated": 0, "feature_dim": 0}

    texts = [text for _, text in rows]
    vectorizer = make_vectorizer()
    matrix = vectorizer.fit_transform(texts).toarray()
    save_vectorizer(vectorizer)

    updated = 0

    for (company, _), vec in zip(rows, matrix):
        vector_json = json.dumps(np.asarray(vec, dtype=float).tolist())
        feature_dim = int(len(vec))

        existing = db.get(CompanyVector, company.osm_id)
        if existing:
            existing.model_name = MODEL_NAME
            existing.vector_dim = feature_dim
            existing.vector_json = vector_json
        else:
            db.add(
                CompanyVector(
                    company_osm_id=company.osm_id,
                    model_name=MODEL_NAME,
                    vector_dim=feature_dim,
                    vector_json=vector_json,
                )
            )
        updated += 1

    db.commit()
    return {
        "processed": len(rows),
        "updated": updated,
        "feature_dim": int(matrix.shape[1]),
    }
