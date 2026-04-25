import json

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.company import Company, CompanyVector
from app.services.industry_inference_service import get_company_prediction_map, predict_industry_for_text
from app.services.vector_service import vectorize_resume_text

settings = get_settings()


def _industry_alignment(resume_probs: dict[str, float], company_probs: dict[str, float]) -> float:
    keys = set(resume_probs.keys()) | set(company_probs.keys())
    if not keys:
        return 0.0
    return float(sum(resume_probs.get(k, 0.0) * company_probs.get(k, 0.0) for k in keys))


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
    resume_vector = np.asarray(vectorize_resume_text(resume_text), dtype=float).reshape(1, -1)

    if company_matrix.shape[1] != resume_vector.shape[1]:
        raise ValueError(
            "The stored company vectors do not match the fitted TF-IDF vectorizer. "
            "Re-run /api/admin/vectorize-companies."
        )

    semantic_scores = cosine_similarity(resume_vector, company_matrix)[0]

    try:
        resume_industry = predict_industry_for_text(db, resume_text)
        _, company_prediction_map = get_company_prediction_map(db)
    except Exception:
        resume_industry = None
        company_prediction_map = {}

    scored = []
    for idx, base in enumerate(metadata):
        semantic = float(semantic_scores[idx])
        company_prediction = company_prediction_map.get(base["osm_id"])
        industry_alignment = 0.0
        sector_code = None
        if resume_industry and company_prediction:
            industry_alignment = _industry_alignment(
                resume_industry["probabilities"],
                company_prediction["probabilities"],
            )
            sector_code = company_prediction["predicted_sector_code"]

        final_score = semantic
        if resume_industry and company_prediction:
            final_score = (
                settings.industry_semantic_weight * semantic
                + settings.industry_alignment_weight * industry_alignment
            )

        row = base.copy()
        row["score"] = final_score
        row["semantic_score"] = semantic
        row["industry_alignment_score"] = industry_alignment if resume_industry and company_prediction else None
        row["industry_sector_code"] = sector_code
        scored.append(row)

    scored.sort(key=lambda item: item["score"], reverse=True)

    return {
        "total_candidates_scored": len(scored),
        "top_k": top_k,
        "matches": scored[:top_k],
    }
