from pydantic import BaseModel, Field

from app.schemas.company import CompanyMatchOut


class ResumeTextRequest(BaseModel):
    resume_text: str = Field(min_length=1)
    top_k: int = Field(default=10, ge=1, le=100)


class MatchResponse(BaseModel):
    total_candidates_scored: int
    top_k: int
    matches: list[CompanyMatchOut]
