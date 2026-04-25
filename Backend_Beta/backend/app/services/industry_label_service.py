import json
from typing import Iterable

from openai import OpenAI
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.company import Company, CompanyPage
from app.models.industry import CompanyIndustryLabel
from app.services.naics_service import naics_sector_map

settings = get_settings()


def _latest_page_subquery():
    return (
        select(CompanyPage.company_osm_id, CompanyPage.cleaned_text, CompanyPage.fetched_at)
        .order_by(CompanyPage.company_osm_id, desc(CompanyPage.fetched_at))
    )


def list_label_candidates(db: Session, limit: int, relabel: bool, min_cleaned_chars: int) -> list[tuple[Company, CompanyPage]]:
    companies = db.execute(select(Company).where(Company.website.is_not(None)).limit(limit * 5)).scalars().all()
    candidates: list[tuple[Company, CompanyPage]] = []

    for company in companies:
        latest_page = db.execute(
            select(CompanyPage)
            .where(CompanyPage.company_osm_id == company.osm_id)
            .order_by(desc(CompanyPage.fetched_at))
            .limit(1)
        ).scalar_one_or_none()

        if not latest_page or not latest_page.cleaned_text or len(latest_page.cleaned_text.strip()) < min_cleaned_chars:
            continue

        if not relabel:
            existing = db.execute(
                select(CompanyIndustryLabel)
                .where(CompanyIndustryLabel.company_osm_id == company.osm_id)
                .order_by(desc(CompanyIndustryLabel.created_at))
                .limit(1)
            ).scalar_one_or_none()
            if existing:
                continue

        candidates.append((company, latest_page))
        if len(candidates) >= limit:
            break

    return candidates


def _company_prompt(company_name: str | None, website: str | None, cleaned_text: str) -> str:
    sectors = "\n".join(f"- {code}: {title}" for code, title in naics_sector_map().items())
    truncated_text = cleaned_text[:12000]
    return f"""
Classify the company website into exactly one NAICS 2022 2-digit sector from this allowed list:
{sectors}

Return strictly valid JSON with these keys only:
- naics_sector_code (string, one of the allowed sector codes)
- confidence (number from 0 to 1)
- alternate_sector_code (string or null)
- evidence (array of short strings)
- needs_human_review (boolean)

Company name: {company_name or ''}
Website: {website or ''}
Website text:
{truncated_text}
""".strip()


def _call_openai_for_label(prompt: str) -> tuple[dict, dict]:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_label_model,
        input=prompt,
    )
    output_text = getattr(response, "output_text", None)
    if not output_text:
        raise ValueError("OpenAI did not return output_text for the industry label request.")
    parsed = json.loads(output_text)
    return parsed, response.model_dump() if hasattr(response, "model_dump") else {"output_text": output_text}


def generate_company_labels(
    db: Session,
    limit: int,
    relabel: bool,
    min_cleaned_chars: int,
    auto_approve_confidence: float,
) -> dict[str, int]:
    candidates = list_label_candidates(
        db=db,
        limit=limit,
        relabel=relabel,
        min_cleaned_chars=min_cleaned_chars,
    )

    created = 0
    auto_approved = 0

    for company, latest_page in candidates:
        prompt = _company_prompt(company.name, company.website, latest_page.cleaned_text or "")
        parsed, raw_response = _call_openai_for_label(prompt)

        sector_code = parsed.get("naics_sector_code")
        if sector_code not in naics_sector_map():
            raise ValueError(f"OpenAI returned invalid NAICS sector code: {sector_code}")

        confidence = float(parsed.get("confidence", 0.0))
        is_approved = confidence >= auto_approve_confidence and not parsed.get("needs_human_review", False)

        label = CompanyIndustryLabel(
            company_osm_id=company.osm_id,
            label_source="gpt",
            naics_sector_code=sector_code,
            confidence=confidence,
            alternate_sector_code=parsed.get("alternate_sector_code"),
            evidence_json=json.dumps(parsed.get("evidence", [])),
            raw_response_json=json.dumps(raw_response),
            model_name=settings.openai_label_model,
            prompt_version=settings.industry_prompt_version,
            is_approved=is_approved,
        )
        db.add(label)
        created += 1
        if is_approved:
            auto_approved += 1

    db.commit()
    return {"processed": len(candidates), "created": created, "auto_approved": auto_approved}


def review_company_labels(db: Session, company_osm_ids: Iterable[str], approve: bool) -> dict[str, int]:
    updated = 0

    for osm_id in company_osm_ids:
        label = db.execute(
            select(CompanyIndustryLabel)
            .where(CompanyIndustryLabel.company_osm_id == osm_id)
            .order_by(desc(CompanyIndustryLabel.created_at))
            .limit(1)
        ).scalar_one_or_none()
        if not label:
            continue
        label.is_approved = approve
        updated += 1

    db.commit()
    return {"updated": updated}
