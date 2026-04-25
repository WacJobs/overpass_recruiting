import json

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company, CompanyVector
from app.services.vector_service import vectorize_text


def score_resume_text(db: Session, resume_text: str, top_k: int) -> dict:
    rows = db.execute(
        select(Company, CompanyVector)
        .join(CompanyVector, Company.osm_id == CompanyVector.company_osm_id)
    ).all()

    if not rows:
        raise ValueError("No company vectors are available yet. Ingest and vectorize companies first.")

    metadata: list[dict] = []
    vectors: list[np.ndarray] = []

    for company, vector in rows:
        try:
            vec = np.asarray(json.loads(vector.vector_json), dtype=float)
        except Exception:
            continue

        metadata.append(
            {
                "osm_id": company.osm_id,
                "osm_type": company.osm_type,
                "name": company.name,
                "city": company.city,
                "website": company.website,
                "email": company.email,
                "phone": company.phone,
                "lat": company.lat,
                "lon": company.lon,
            }
        )
        vectors.append(vec)

    if not vectors:
        raise ValueError("Company vectors exist in the database, but none could be parsed.")

    company_matrix = np.vstack(vectors)
    resume_vector = np.asarray(vectorize_text(resume_text), dtype=float).reshape(1, -1)

    scores = cosine_similarity(resume_vector, company_matrix)[0]
    top_indices = np.argsort(scores)[::-1][:top_k]

    matches = []
    for idx in top_indices:
        row = metadata[idx].copy()
        row["score"] = float(scores[idx])
        matches.append(row)

    return {
        "total_candidates_scored": len(metadata),
        "top_k": top_k,
        "matches": matches,
    }
