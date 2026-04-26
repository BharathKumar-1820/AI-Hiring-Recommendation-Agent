"""
models.py — Pydantic data models for the AI Hiring Agent API.

Defines the shape of API inputs (job description) and outputs
(ranked candidate matches with scores and skill analysis).
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Candidate — mirrors one record in candidates.json
# ---------------------------------------------------------------------------

class Candidate(BaseModel):
    id: int
    name: str
    skills: List[str]
    experience: int                     # years of experience
    role: str
    description: str                    # free-text profile summary


# ---------------------------------------------------------------------------
# API request body
# ---------------------------------------------------------------------------

class JobDescriptionRequest(BaseModel):
    job_description: str = Field(
        ...,
        min_length=20,
        description="Full text of the job description to match candidates against.",
        example=(
            "We are looking for a Senior ML Engineer with experience in "
            "Python, PyTorch, and deploying models to production using Docker "
            "and Kubernetes. Experience with NLP and transformers is a plus."
        ),
    )


# ---------------------------------------------------------------------------
# Per-candidate result returned in the response (match only)
# ---------------------------------------------------------------------------

class CandidateResult(BaseModel):
    id: int
    name: str
    role: str
    experience: int
    score: int                          # 0-100 composite match score
    similarity_score: float             # raw cosine similarity (0-1)
    skill_overlap_score: float          # fraction of JD skills matched (0-1)
    matched_skills: List[str]
    missing_skills: List[str]
    reason: str                         # 1-2 sentence explanation


# ---------------------------------------------------------------------------
# Top-level API response (match only — backward compatible)
# ---------------------------------------------------------------------------

class MatchResponse(BaseModel):
    job_description: str
    total_candidates_evaluated: int
    results: List[CandidateResult]


# ---------------------------------------------------------------------------
# Conversational outreach models
# ---------------------------------------------------------------------------

class ConversationMessage(BaseModel):
    """A single message in the simulated recruiter–candidate conversation."""
    role: str = Field(
        ...,
        description="'agent' for the AI recruiter, 'candidate' for the simulated candidate.",
    )
    content: str
    timestamp: str                      # ISO-8601 formatted timestamp


class InterestBreakdown(BaseModel):
    """Four-dimensional breakdown of the Interest Score."""
    enthusiasm: int = Field(..., ge=0, le=100, description="Excitement about the role and tech stack")
    availability: int = Field(..., ge=0, le=100, description="Readiness to start within a reasonable timeframe")
    role_alignment: int = Field(..., ge=0, le=100, description="Career trajectory match with the role")
    engagement: int = Field(..., ge=0, le=100, description="Depth and quality of conversational responses")


class EngagementResult(BaseModel):
    """Output of the conversational outreach simulation for one candidate."""
    conversation: List[ConversationMessage]
    interest_score: int = Field(..., ge=0, le=100, description="Overall interest score (0-100)")
    interest_breakdown: InterestBreakdown
    outreach_summary: str               # 1-2 sentence summary of the engagement outcome


# ---------------------------------------------------------------------------
# Pipeline candidate result (match + engagement + final score)
# ---------------------------------------------------------------------------

class PipelineCandidateResult(BaseModel):
    """Full result combining match analysis and engagement assessment."""
    # Identity
    id: int
    name: str
    role: str
    experience: int

    # Match dimension
    match_score: int                    # 0-100 composite match score
    similarity_score: float
    skill_overlap_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    match_reason: str

    # Engagement dimension
    interest_score: int                 # 0-100 overall interest score
    interest_breakdown: InterestBreakdown
    conversation: List[ConversationMessage]
    outreach_summary: str

    # Combined
    final_score: int = Field(..., ge=0, le=100, description="Weighted combination of match + interest")


# ---------------------------------------------------------------------------
# Full pipeline response
# ---------------------------------------------------------------------------

class PipelineResponse(BaseModel):
    """Top-level response for the full talent scouting pipeline."""
    job_description: str
    total_candidates_evaluated: int
    pipeline_stages: List[str] = Field(
        default=[
            "JD Parsing & Skill Extraction",
            "Semantic Search & Matching",
            "Conversational Outreach Simulation",
            "Combined Scoring & Ranking",
        ],
    )
    match_weight: float = 0.6
    interest_weight: float = 0.4
    results: List[PipelineCandidateResult]
