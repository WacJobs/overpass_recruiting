from pydantic import BaseModel, Field


class OverpassIngestRequest(BaseModel):
    south: float
    west: float
    north: float
    east: float
    name_filter: str = ".*"
    office_filter: str = ".*"


class VectorizeRequest(BaseModel):
    limit: int = Field(default=500, ge=1, le=5000)


class ScrapeRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=1000)
