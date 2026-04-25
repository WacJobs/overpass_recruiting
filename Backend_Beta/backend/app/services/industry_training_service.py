import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.company import CompanyPage
from app.models.industry import CompanyIndustryLabel, IndustryModelRun

settings = get_settings()


class IndustryTrainingError(ValueError):
    pass


def _artifact_dir() -> Path:
    path = Path(settings.industry_artifact_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _latest_eligible_labels(db: Session, approved_only: bool, min_label_confidence: float) -> list[tuple[str, str, str]]:
    labels = db.execute(
        select(CompanyIndustryLabel)
        .order_by(CompanyIndustryLabel.company_osm_id, desc(CompanyIndustryLabel.created_at))
    ).scalars().all()

    latest_by_company: dict[str, CompanyIndustryLabel] = {}
    for label in labels:
        if label.company_osm_id not in latest_by_company:
            latest_by_company[label.company_osm_id] = label

    rows: list[tuple[str, str, str]] = []
    for company_osm_id, label in latest_by_company.items():
        if approved_only and not label.is_approved:
            continue
        if not approved_only and (label.confidence or 0.0) < min_label_confidence and not label.is_approved:
            continue

        latest_page = db.execute(
            select(CompanyPage)
            .where(CompanyPage.company_osm_id == company_osm_id)
            .order_by(desc(CompanyPage.fetched_at))
            .limit(1)
        ).scalar_one_or_none()
        if not latest_page or not latest_page.cleaned_text:
            continue

        rows.append((company_osm_id, latest_page.cleaned_text, label.naics_sector_code))
    return rows


def _safe_split(X, y, train_ratio: float, val_ratio: float, test_ratio: float, random_seed: int):
    total = train_ratio + val_ratio + test_ratio
    if abs(total - 1.0) > 1e-6:
        raise IndustryTrainingError("train_ratio + val_ratio + test_ratio must equal 1.0")

    if len(X) < 10:
        raise IndustryTrainingError("Need at least 10 labeled companies before fitting the industry model.")

    try:
        X_train, X_temp, y_train, y_temp = train_test_split(
            X,
            y,
            test_size=(1 - train_ratio),
            random_state=random_seed,
            stratify=y,
        )
        relative_test = test_ratio / (val_ratio + test_ratio)
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp,
            y_temp,
            test_size=relative_test,
            random_state=random_seed,
            stratify=y_temp,
        )
    except ValueError:
        X_train, X_temp, y_train, y_temp = train_test_split(
            X,
            y,
            test_size=(1 - train_ratio),
            random_state=random_seed,
        )
        relative_test = test_ratio / (val_ratio + test_ratio)
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp,
            y_temp,
            test_size=relative_test,
            random_state=random_seed,
        )

    return X_train, X_val, X_test, y_train, y_val, y_test


def fit_industry_classifier(
    db: Session,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    random_seed: int,
    tfidf_max_features: int,
    min_df: int,
    max_df: float,
    alpha: float,
    approved_only: bool,
    min_label_confidence: float,
) -> dict:
    rows = _latest_eligible_labels(
        db=db,
        approved_only=approved_only,
        min_label_confidence=min_label_confidence,
    )
    if len(rows) < 10:
        raise IndustryTrainingError("Not enough eligible labeled companies to fit the industry classifier.")

    _, texts, labels = zip(*rows)
    X_train, X_val, X_test, y_train, y_val, y_test = _safe_split(
        list(texts), list(labels), train_ratio, val_ratio, test_ratio, random_seed
    )

    pipeline = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=tfidf_max_features,
                    min_df=min_df,
                    max_df=max_df,
                    stop_words="english",
                    lowercase=True,
                ),
            ),
            ("nb", MultinomialNB(alpha=alpha)),
        ]
    )
    pipeline.fit(X_train, y_train)

    val_pred = pipeline.predict(X_val)
    test_pred = pipeline.predict(X_test)
    metrics = {
        "val_accuracy": float(accuracy_score(y_val, val_pred)),
        "val_macro_f1": float(f1_score(y_val, val_pred, average="macro", zero_division=0)),
        "test_accuracy": float(accuracy_score(y_test, test_pred)),
        "test_macro_f1": float(f1_score(y_test, test_pred, average="macro", zero_division=0)),
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact_path = _artifact_dir() / f"industry_nb_{ts}.joblib"
    joblib.dump(pipeline, artifact_path)

    db.execute(select(IndustryModelRun).where(IndustryModelRun.is_active.is_(True)))
    for run in db.execute(select(IndustryModelRun).where(IndustryModelRun.is_active.is_(True))).scalars().all():
        run.is_active = False

    model_run = IndustryModelRun(
        model_type="industry_nb",
        model_name="tfidf_multinomial_nb_v1",
        artifact_path=str(artifact_path),
        label_space_version=f"naics_{settings.naics_version}_2digit",
        train_count=len(X_train),
        val_count=len(X_val),
        test_count=len(X_test),
        metrics_json=json.dumps(metrics),
        is_active=True,
    )
    db.add(model_run)
    db.commit()
    db.refresh(model_run)

    return {
        "model_run_id": model_run.id,
        "artifact_path": str(artifact_path),
        "train_count": len(X_train),
        "val_count": len(X_val),
        "test_count": len(X_test),
        "metrics": metrics,
    }


def get_active_industry_model_status(db: Session) -> dict:
    run = db.execute(
        select(IndustryModelRun)
        .where(IndustryModelRun.is_active.is_(True))
        .order_by(desc(IndustryModelRun.created_at))
        .limit(1)
    ).scalar_one_or_none()

    if not run:
        return {
            "active_model_run_id": None,
            "model_name": None,
            "train_count": None,
            "val_count": None,
            "test_count": None,
            "metrics": None,
        }

    return {
        "active_model_run_id": run.id,
        "model_name": run.model_name,
        "train_count": run.train_count,
        "val_count": run.val_count,
        "test_count": run.test_count,
        "metrics": json.loads(run.metrics_json) if run.metrics_json else None,
    }
