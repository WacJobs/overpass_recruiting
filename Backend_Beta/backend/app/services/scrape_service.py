import re

import requests
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.company import Company, CompanyPage

settings = get_settings()


def fetch_html(url: str, timeout: int = 15) -> str | None:
    if not url:
        return None

    headers = {"User-Agent": settings.user_agent}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def html_to_text(html: str | None) -> str:
    if not html:
        return ""

    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def scrape_company_websites(db: Session, limit: int = 100) -> dict[str, int]:
    stmt = (
        select(Company)
        .where(Company.website.is_not(None))
        .limit(limit)
    )
    companies = db.execute(stmt).scalars().all()

    attempted = 0
    saved = 0

    for company in companies:
        attempted += 1
        try:
            html = fetch_html(company.website)
            cleaned = html_to_text(html)

            page = CompanyPage(
                company_osm_id=company.osm_id,
                source_url=company.website,
                raw_html=html,
                cleaned_text=cleaned,
            )
            db.add(page)
            saved += 1
        except Exception:
            continue

    db.commit()
    return {"attempted": attempted, "saved": saved}
