from pydantic import BaseModel, Field


class IndustryPredictionOut(BaseModel):
    predicted_sector_code: str
    predicted_sector_title: str | None = None
    confidence: float
    probabilities: dict[str, float]


class LabelGenerationSummary(BaseModel):
    processed: int
    created: int
    auto_approved: int


class IndustryModelStatusOut(BaseModel):
    active_model_run_id: int | None = None
    model_name: str | None = None
    train_count: int | None = None
    val_count: int | None = None
    test_count: int | None = None
    metrics: dict | None = None


class IndustryPredictTextRequest(BaseModel):
    text: str = Field(min_length=1)
