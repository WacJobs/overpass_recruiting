import json
from pathlib import Path

import joblib
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.company import Company, CompanyPage
from app.models.industry import CompanyIndustryPrediction, IndustryModelRun, NaicsSector


class IndustryInferenceError(ValueError):
    pass


def get_active_model_run(db: Session) -> IndustryModelRun | None:
    return db.execute(
        select(IndustryModelRun)
        .where(IndustryModelRun.is_active.is_(True))
        .order_by(desc(IndustryModelRun.created_at))
        .limit(1)
    ).scalar_one_or_none()


def _load_pipeline(artifact_path: str):
    path = Path(artifact_path)
    if not path.exists():
        raise IndustryInferenceError(f"Industry model artifact not found at {artifact_path}")
    return joblib.load(path)


def predict_industry_for_text(db: Session, text: str) -> dict:
    model_run = get_active_model_run(db)
    if not model_run:
        raise IndustryInferenceError("No active industry model is available. Fit the model first.")

    pipeline = _load_pipeline(model_run.artifact_path)
    probabilities = pipeline.predict_proba([text])[0]
    classes = list(pipeline.classes_)
    best_idx = int(probabilities.argmax())
    predicted_code = classes[best_idx]
    sector = db.get(NaicsSector, predicted_code)

    return {
        "predicted_sector_code": predicted_code,
        "predicted_sector_title": sector.title if sector else None,
        "confidence": float(probabilities[best_idx]),
        "probabilities": {code: float(prob) for code, prob in zip(classes, probabilities)},
        "model_run_id": model_run.id,
    }


def predict_company_industries(db: Session, limit: int = 500) -> dict[str, int]:
    model_run = get_active_model_run(db)
    if not model_run:
        raise IndustryInferenceError("No active industry model is available. Fit the model first.")

    pipeline = _load_pipeline(model_run.artifact_path)
    companies = db.execute(select(Company).where(Company.website.is_not(None)).limit(limit)).scalars().all()

    updated = 0
    classes = list(pipeline.classes_)

    for company in companies:
        latest_page = db.execute(
            select(CompanyPage)
            .where(CompanyPage.company_osm_id == company.osm_id)
            .order_by(desc(CompanyPage.fetched_at))
            .limit(1)
        ).scalar_one_or_none()
        if not latest_page or not latest_page.cleaned_text:
            continue

        probabilities = pipeline.predict_proba([latest_page.cleaned_text])[0]
        best_idx = int(probabilities.argmax())
        predicted_code = classes[best_idx]
        confidence = float(probabilities[best_idx])

        existing = db.execute(
            select(CompanyIndustryPrediction).where(
                CompanyIndustryPrediction.company_osm_id == company.osm_id,
                CompanyIndustryPrediction.model_run_id == model_run.id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.predicted_sector_code = predicted_code
            existing.confidence = confidence
            existing.probabilities_json = json.dumps({code: float(prob) for code, prob in zip(classes, probabilities)})
        else:
            db.add(
                CompanyIndustryPrediction(
                    company_osm_id=company.osm_id,
                    model_run_id=model_run.id,
                    predicted_sector_code=predicted_code,
                    confidence=confidence,
                    probabilities_json=json.dumps({code: float(prob) for code, prob in zip(classes, probabilities)}),
                )
            )
        updated += 1

    db.commit()
    return {"processed": len(companies), "updated": updated, "model_run_id": model_run.id}


def get_company_prediction_map(db: Session) -> tuple[int | None, dict[str, dict]]:
    model_run = get_active_model_run(db)
    if not model_run:
        return None, {}

    rows = db.execute(
        select(CompanyIndustryPrediction)
        .where(CompanyIndustryPrediction.model_run_id == model_run.id)
    ).scalars().all()

    prediction_map: dict[str, dict] = {}
    for row in rows:
        prediction_map[row.company_osm_id] = {
            "predicted_sector_code": row.predicted_sector_code,
            "confidence": float(row.confidence or 0.0),
            "probabilities": json.loads(row.probabilities_json),
        }
    return model_run.id, prediction_map
