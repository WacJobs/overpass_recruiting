import json
from typing import Any

import requests
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.company import Company

settings = get_settings()


def build_overpass_query(
    south: float,
    west: float,
    north: float,
    east: float,
    name_filter: str,
    office_filter: str,
) -> str:
    bbox = f"{south},{west},{north},{east}"
    return f'''
    [out:json][timeout:60];
    (
      node["office"~"{office_filter}",i]["name"~"{name_filter}",i]({bbox});
      way["office"~"{office_filter}",i]["name"~"{name_filter}",i]({bbox});
      relation["office"~"{office_filter}",i]["name"~"{name_filter}",i]({bbox});
    );
    out center tags;
    '''


def fetch_overpass_json(query: str) -> dict[str, Any]:
    response = requests.post(
        settings.overpass_api_url,
        data=query,
        timeout=90,
        headers={"User-Agent": settings.user_agent},
    )
    response.raise_for_status()
    return response.json()


def normalize_elements(payload: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    for element in payload.get("elements", []):
        tags = element.get("tags", {}) or {}
        lat = element.get("lat")
        lon = element.get("lon")

        center = element.get("center") or {}
        if lat is None:
            lat = center.get("lat")
        if lon is None:
            lon = center.get("lon")

        output.append(
            {
                "osm_id": str(element.get("id")),
                "osm_type": element.get("type"),
                "name": tags.get("name"),
                "city": tags.get("addr:city"),
                "website": tags.get("website"),
                "email": tags.get("email"),
                "phone": tags.get("phone"),
                "lat": lat,
                "lon": lon,
                "raw_tags_json": json.dumps(tags),
            }
        )

    return output


def upsert_companies(db: Session, companies: list[dict[str, Any]]) -> int:
    upserted = 0

    for row in companies:
        existing = db.get(Company, row["osm_id"])
        if existing:
            for key, value in row.items():
                setattr(existing, key, value)
        else:
            db.add(Company(**row))
        upserted += 1

    db.commit()
    return upserted


def ingest_from_overpass(
    db: Session,
    south: float,
    west: float,
    north: float,
    east: float,
    name_filter: str,
    office_filter: str,
) -> dict[str, int]:
    query = build_overpass_query(
        south=south,
        west=west,
        north=north,
        east=east,
        name_filter=name_filter,
        office_filter=office_filter,
    )
    payload = fetch_overpass_json(query)
    companies = normalize_elements(payload)
    upserted = upsert_companies(db, companies)
    return {"fetched": len(companies), "upserted": upserted}
