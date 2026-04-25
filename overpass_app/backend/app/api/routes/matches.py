from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.match import MatchResponse, ResumeTextRequest
from app.services.match_service import score_resume_text

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/score-text", response_model=MatchResponse)
def score_text_resume(payload: ResumeTextRequest, db: Session = Depends(get_db)):
    try:
        return score_resume_text(db=db, resume_text=payload.resume_text, top_k=payload.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
