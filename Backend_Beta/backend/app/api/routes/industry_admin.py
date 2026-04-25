from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.database import get_db
from app.schemas.admin import (
    IndustryFitRequest,
    IndustryLabelGenerateRequest,
    IndustryLabelReviewRequest,
    IndustryPredictCompaniesRequest,
)
from app.schemas.industry import IndustryModelStatusOut, IndustryPredictionOut, IndustryPredictTextRequest, LabelGenerationSummary
from app.services.industry_inference_service import predict_company_industries, predict_industry_for_text
from app.services.industry_label_service import generate_company_labels, review_company_labels
from app.services.industry_training_service import fit_industry_classifier, get_active_industry_model_status
from app.services.naics_service import bootstrap_naics_sectors

router = APIRouter(prefix="/admin/industry", tags=["admin-industry"], dependencies=[Depends(require_admin)])


@router.post("/bootstrap-naics")
def bootstrap_naics(db: Session = Depends(get_db)):
    return bootstrap_naics_sectors(db)


@router.post("/labels/generate", response_model=LabelGenerationSummary)
def generate_labels(payload: IndustryLabelGenerateRequest, db: Session = Depends(get_db)):
    try:
        return generate_company_labels(
            db=db,
            limit=payload.limit,
            relabel=payload.relabel,
            min_cleaned_chars=payload.min_cleaned_chars,
            auto_approve_confidence=payload.auto_approve_confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/labels/review")
def review_labels(payload: IndustryLabelReviewRequest, db: Session = Depends(get_db)):
    return review_company_labels(db=db, company_osm_ids=payload.company_osm_ids, approve=payload.approve)


@router.post("/model/fit")
def fit_model(payload: IndustryFitRequest, db: Session = Depends(get_db)):
    try:
        return fit_industry_classifier(
            db=db,
            train_ratio=payload.train_ratio,
            val_ratio=payload.val_ratio,
            test_ratio=payload.test_ratio,
            random_seed=payload.random_seed,
            tfidf_max_features=payload.tfidf_max_features,
            min_df=payload.min_df,
            max_df=payload.max_df,
            alpha=payload.alpha,
            approved_only=payload.approved_only,
            min_label_confidence=payload.min_label_confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/model/status", response_model=IndustryModelStatusOut)
def model_status(db: Session = Depends(get_db)):
    return get_active_industry_model_status(db)


@router.post("/model/predict-companies")
def predict_companies(payload: IndustryPredictCompaniesRequest, db: Session = Depends(get_db)):
    try:
        return predict_company_industries(db=db, limit=payload.limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/model/predict-text", response_model=IndustryPredictionOut)
def predict_text(payload: IndustryPredictTextRequest, db: Session = Depends(get_db)):
    try:
        result = predict_industry_for_text(db=db, text=payload.text)
        return {
            "predicted_sector_code": result["predicted_sector_code"],
            "predicted_sector_title": result.get("predicted_sector_title"),
            "confidence": result["confidence"],
            "probabilities": result["probabilities"],
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
