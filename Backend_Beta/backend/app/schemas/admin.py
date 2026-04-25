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


class IndustryLabelGenerateRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=1000)
    relabel: bool = False
    min_cleaned_chars: int = Field(default=250, ge=50, le=5000)
    auto_approve_confidence: float = Field(default=0.90, ge=0.0, le=1.0)


class IndustryLabelReviewRequest(BaseModel):
    company_osm_ids: list[str] = Field(default_factory=list)
    approve: bool = True


class IndustryFitRequest(BaseModel):
    train_ratio: float = Field(default=0.60, gt=0, lt=1)
    val_ratio: float = Field(default=0.20, gt=0, lt=1)
    test_ratio: float = Field(default=0.20, gt=0, lt=1)
    random_seed: int = 42
    tfidf_max_features: int = Field(default=5000, ge=100, le=50000)
    min_df: int = Field(default=1, ge=1, le=20)
    max_df: float = Field(default=0.95, gt=0.0, le=1.0)
    alpha: float = Field(default=1.0, gt=0.0, le=10.0)
    approved_only: bool = False
    min_label_confidence: float = Field(default=0.70, ge=0.0, le=1.0)


class IndustryPredictCompaniesRequest(BaseModel):
    limit: int = Field(default=500, ge=1, le=5000)
