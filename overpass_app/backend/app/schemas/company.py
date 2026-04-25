from pydantic import BaseModel


class CompanyOut(BaseModel):
    osm_id: str
    osm_type: str | None = None
    name: str | None = None
    city: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    lat: float | None = None
    lon: float | None = None

    model_config = {"from_attributes": True}


class CompanyMatchOut(CompanyOut):
    score: float
