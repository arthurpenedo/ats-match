"""API HTTP: `uvicorn ats_match.api:app --reload`."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import llm
from .matcher import MatchReport, analyze

app = FastAPI(title="ats-match", version="0.1.0")


class MatchRequest(BaseModel):
    resume: str = Field(min_length=20)
    job: str = Field(min_length=20)


class SuggestResponse(BaseModel):
    report: MatchReport
    suggestions: list[llm.Suggestion]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/match", response_model=MatchReport)
def match(req: MatchRequest) -> MatchReport:
    return analyze(req.resume, req.job)


@app.post("/suggest", response_model=SuggestResponse)
def suggest(req: MatchRequest) -> SuggestResponse:
    report = analyze(req.resume, req.job)
    try:
        suggestions = llm.suggest_rewrites(req.resume, req.job, report)
    except llm.RefusalError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return SuggestResponse(report=report, suggestions=suggestions)
