from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.industry import NaicsSector

settings = get_settings()

NAICS_2022_2DIGIT = [
    ("11", "Agriculture, Forestry, Fishing and Hunting"),
    ("21", "Mining, Quarrying, and Oil and Gas Extraction"),
    ("22", "Utilities"),
    ("23", "Construction"),
    ("31-33", "Manufacturing"),
    ("42", "Wholesale Trade"),
    ("44-45", "Retail Trade"),
    ("48-49", "Transportation and Warehousing"),
    ("51", "Information"),
    ("52", "Finance and Insurance"),
    ("53", "Real Estate and Rental and Leasing"),
    ("54", "Professional, Scientific, and Technical Services"),
    ("55", "Management of Companies and Enterprises"),
    ("56", "Administrative and Support and Waste Management and Remediation Services"),
    ("61", "Educational Services"),
    ("62", "Health Care and Social Assistance"),
    ("71", "Arts, Entertainment, and Recreation"),
    ("72", "Accommodation and Food Services"),
    ("81", "Other Services (except Public Administration)"),
    ("92", "Public Administration"),
]


def bootstrap_naics_sectors(db: Session) -> dict[str, int]:
    created = 0
    updated = 0

    for code, title in NAICS_2022_2DIGIT:
        existing = db.get(NaicsSector, code)
        if existing:
            existing.title = title
            existing.naics_version = settings.naics_version
            existing.is_active = True
            updated += 1
        else:
            db.add(
                NaicsSector(
                    code=code,
                    title=title,
                    naics_version=settings.naics_version,
                    is_active=True,
                )
            )
            created += 1

    db.commit()
    return {"created": created, "updated": updated, "total": len(NAICS_2022_2DIGIT)}


def naics_sector_map() -> dict[str, str]:
    return dict(NAICS_2022_2DIGIT)
