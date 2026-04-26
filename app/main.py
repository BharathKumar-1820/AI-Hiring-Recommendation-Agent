"""
main.py — FastAPI application entry point for the AI Hiring Agent.

Endpoints
---------
POST /match      — Match candidates to a job description (match score only).
POST /pipeline   — Full pipeline: match → engage → combined rank.
GET  /health     — Liveness check.
GET  /stats      — Embedding cache statistics.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import matcher
from app.embeddings import cache_stats
from app.models import (
    JobDescriptionRequest,
    MatchResponse,
    PipelineCandidateResult,
    PipelineResponse,
)
from app.outreach import simulate_engagement

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan  (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: pre-load model + build FAISS index. Shutdown: nothing to do."""
    logger.info("=== AI Hiring Agent starting up ===")
    matcher.initialise()          # load candidates → embed → build FAISS index
    logger.info("=== Startup complete — API ready ===")
    yield
    logger.info("=== Shutting down AI Hiring Agent ===")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI-Powered Talent Scouting & Engagement Agent",
    description=(
        "Submit a job description and the agent will discover matching candidates, "
        "engage them conversationally to assess genuine interest, and output a ranked "
        "shortlist scored on two dimensions: Match Score and Interest Score."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# Allow all origins for local development; tighten for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Middleware — request timing
# ---------------------------------------------------------------------------

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = round((time.perf_counter() - start) * 1000, 1)
    response.headers["X-Process-Time-Ms"] = str(elapsed)
    return response


# ---------------------------------------------------------------------------
# Exception handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", summary="Liveness check")
async def health() -> dict:
    """Returns 200 OK when the service is running."""
    return {"status": "ok", "service": "AI Talent Scouting Agent"}


@app.get("/stats", summary="Embedding cache statistics")
async def stats() -> dict:
    """Returns how many candidate embeddings are currently cached."""
    return cache_stats()


@app.post(
    "/match",
    response_model=MatchResponse,
    summary="Match candidates to a job description",
    response_description="Top-5 candidates ranked by composite match score.",
)
async def match_candidates(body: JobDescriptionRequest) -> MatchResponse:
    """
    Analyse a job description and return the top-5 best-matching candidates.

    ### How it works
    1. Encode the JD with a sentence-transformer model.
    2. Run FAISS cosine-similarity search over all candidate embeddings.
    3. Extract required skills from the JD (keyword NLP).
    4. Compare JD skills against each candidate's skill list.
    5. Compute a composite score (60 % semantic + 35 % skill overlap + 5 % exp).
    6. Return ranked results with matched skills, gaps, and an explanation.
    """
    jd = body.job_description.strip()
    if not jd:
        raise HTTPException(status_code=422, detail="job_description must not be empty.")

    logger.info("Received /match request (%d chars)", len(jd))

    try:
        results = matcher.find_top_matches(jd, top_k=5)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return MatchResponse(
        job_description=jd,
        total_candidates_evaluated=len(matcher._candidates),
        results=results,
    )


# ---------------------------------------------------------------------------
# Full pipeline: match → engage → combined rank
# ---------------------------------------------------------------------------

MATCH_WEIGHT = 0.6
INTEREST_WEIGHT = 0.4


@app.post(
    "/pipeline",
    response_model=PipelineResponse,
    summary="Full talent scouting pipeline: match + engage + rank",
    response_description=(
        "Top candidates ranked by combined Match Score and Interest Score."
    ),
)
async def run_pipeline(body: JobDescriptionRequest) -> PipelineResponse:
    """
    End-to-end talent scouting pipeline.

    ### Pipeline stages
    1. **JD Parsing** — Extract skills and requirements from the job description.
    2. **Semantic Search & Matching** — FAISS cosine-similarity + skill gap
       analysis → Match Score (0-100).
    3. **Conversational Outreach** — Simulate personalised recruiter–candidate
       conversations and assess genuine interest → Interest Score (0-100).
    4. **Combined Ranking** — Blend Match Score (60 %) and Interest Score (40 %)
       into a Final Score and re-rank.
    """
    jd = body.job_description.strip()
    if not jd:
        raise HTTPException(status_code=422, detail="job_description must not be empty.")

    logger.info("Received /pipeline request (%d chars)", len(jd))

    # ── Stage 1 & 2: Match ──────────────────────────────────────────────────
    try:
        match_results = matcher.find_top_matches(jd, top_k=5)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # ── Stage 3: Engage each matched candidate ──────────────────────────────
    pipeline_results: list[PipelineCandidateResult] = []

    for mr in match_results:
        # Look up the raw candidate dict for the outreach simulation
        candidate_dict = next(
            c for c in matcher._candidates if c["id"] == mr.id
        )

        engagement = simulate_engagement(
            candidate=candidate_dict,
            job_description=jd,
            match_score=mr.score,
            skill_overlap=mr.skill_overlap_score,
            matched_skills=mr.matched_skills,
            missing_skills=mr.missing_skills,
        )

        # ── Stage 4: Combined score ─────────────────────────────────────────
        final_score = round(
            mr.score * MATCH_WEIGHT + engagement.interest_score * INTEREST_WEIGHT
        )
        final_score = max(0, min(100, final_score))

        pipeline_results.append(
            PipelineCandidateResult(
                id=mr.id,
                name=mr.name,
                role=mr.role,
                experience=mr.experience,
                match_score=mr.score,
                similarity_score=mr.similarity_score,
                skill_overlap_score=mr.skill_overlap_score,
                matched_skills=mr.matched_skills,
                missing_skills=mr.missing_skills,
                match_reason=mr.reason,
                interest_score=engagement.interest_score,
                interest_breakdown=engagement.interest_breakdown,
                conversation=engagement.conversation,
                outreach_summary=engagement.outreach_summary,
                final_score=final_score,
            )
        )

    # Re-rank by final combined score
    pipeline_results.sort(key=lambda r: r.final_score, reverse=True)

    logger.info(
        "Pipeline complete: %d candidates scored and ranked", len(pipeline_results)
    )

    return PipelineResponse(
        job_description=jd,
        total_candidates_evaluated=len(matcher._candidates),
        match_weight=MATCH_WEIGHT,
        interest_weight=INTEREST_WEIGHT,
        results=pipeline_results,
    )
