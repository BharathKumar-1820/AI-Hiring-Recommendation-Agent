"""
matcher.py — FAISS-powered similarity search and candidate ranking engine.

Pipeline
--------
1. Build (or reuse) a FAISS index over all candidate embeddings.
2. Encode the incoming job description.
3. Run inner-product search (≡ cosine similarity on unit vectors).
4. Retrieve the top-K raw candidates.
5. Perform skill analysis via analyzer.py.
6. Compute a composite score that blends semantic similarity and skill overlap.
7. Return sorted CandidateResult objects ready for the API response.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List

import faiss
import numpy as np

from app.analyzer import analyse_skill_match, build_reason, extract_skills_from_text
from app.embeddings import build_candidate_embeddings, encode_text
from app.models import CandidateResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_PATH = Path(__file__).parent.parent / "data" / "candidates.json"

# ---------------------------------------------------------------------------
# Module-level state  (populated once by initialise())
# ---------------------------------------------------------------------------

_candidates: List[dict] = []          # raw dicts from candidates.json
_faiss_index: faiss.IndexFlatIP | None = None   # inner-product FAISS index


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def load_candidates() -> List[dict]:
    """Read candidates.json and return the list of candidate dicts."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Candidate data file not found: {DATA_PATH}")
    with DATA_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    logger.info("Loaded %d candidates from %s", len(data), DATA_PATH)
    return data


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """
    Create a FAISS IndexFlatIP (exact inner-product search).

    Because our embeddings are L2-normalised, inner-product == cosine similarity.
    IndexFlatIP does an exhaustive linear scan — perfectly fine for a dataset
    of hundreds to low-thousands of candidates.
    """
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    logger.info(
        "FAISS index built: %d vectors, dimension %d", index.ntotal, dim
    )
    return index


def initialise() -> None:
    """
    Load candidates and build the FAISS index.

    Called once from FastAPI's startup event so every request can reuse the
    already-built index without repeating I/O or embedding computation.
    """
    global _candidates, _faiss_index

    _candidates = load_candidates()
    embeddings = build_candidate_embeddings(_candidates)
    _faiss_index = build_faiss_index(embeddings)
    logger.info("Matcher initialised — ready to serve requests.")


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _composite_score(
    similarity: float,
    skill_overlap: float,
    experience_years: int,
    min_exp: int = 0,
) -> int:
    """
    Combine multiple signals into a single 0-100 integer score.

    Weights
    -------
    • Semantic similarity  — 60 %  (captures holistic fit from free text)
    • Skill overlap        — 35 %  (direct keyword match on required skills)
    • Experience bonus     —  5 %  (soft bonus; capped at 5 pts)

    The experience bonus is computed as min(experience_years / 10, 1) * 5,
    meaning 10+ years gives the full 5-point bonus.
    """
    sem_score   = similarity * 60          # 0-60
    skill_score = skill_overlap * 35       # 0-35
    exp_bonus   = min(experience_years / 10, 1.0) * 5   # 0-5

    raw = sem_score + skill_score + exp_bonus
    return min(100, max(0, round(raw)))


# ---------------------------------------------------------------------------
# Main search function
# ---------------------------------------------------------------------------

def find_top_matches(
    job_description: str,
    top_k: int = 5,
    fetch_k_multiplier: int = 3,
) -> List[CandidateResult]:
    """
    Given a job description string, return the top_k best-matching candidates.

    Parameters
    ----------
    job_description    : raw JD text from the API request.
    top_k              : number of results to return (default 5).
    fetch_k_multiplier : we fetch top_k * multiplier candidates from FAISS
                         before re-ranking so skill analysis can reorder.

    Returns
    -------
    List of CandidateResult, sorted descending by composite score.
    """
    if _faiss_index is None or not _candidates:
        raise RuntimeError(
            "Matcher not initialised. Call matcher.initialise() first."
        )

    # ── Step 1: Extract skills from the job description ──────────────────────
    jd_skills = extract_skills_from_text(job_description)
    logger.debug("JD skills detected: %s", jd_skills)

    # ── Step 2: Encode the job description ───────────────────────────────────
    jd_embedding = encode_text(job_description)           # shape: (D,)
    jd_embedding_2d = jd_embedding.reshape(1, -1)         # FAISS wants (1, D)

    # ── Step 3: FAISS search — retrieve more than top_k for re-ranking ───────
    fetch_k = min(top_k * fetch_k_multiplier, len(_candidates))
    similarities, indices = _faiss_index.search(jd_embedding_2d, fetch_k)

    # similarities shape: (1, fetch_k); indices shape: (1, fetch_k)
    sim_scores: np.ndarray = similarities[0]
    idx_array:  np.ndarray = indices[0]

    # ── Step 4: Build enriched results for each retrieved candidate ───────────
    results: List[CandidateResult] = []
    for rank, (idx, raw_sim) in enumerate(zip(idx_array, sim_scores)):
        if idx == -1:            # FAISS returns -1 for unfilled slots
            continue

        candidate = _candidates[idx]

        # Clamp cosine similarity to [0, 1] (can be slightly negative due to
        # floating-point arithmetic on near-orthogonal vectors)
        similarity = float(np.clip(raw_sim, 0.0, 1.0))

        # ── Skill analysis ────────────────────────────────────────────────
        matched, missing, overlap = analyse_skill_match(
            jd_skills, candidate["skills"]
        )

        # ── Composite score ───────────────────────────────────────────────
        score = _composite_score(
            similarity=similarity,
            skill_overlap=overlap,
            experience_years=candidate["experience"],
        )

        # ── Human-readable reason ─────────────────────────────────────────
        reason = build_reason(candidate, matched, missing, score, similarity)

        results.append(
            CandidateResult(
                id=candidate["id"],
                name=candidate["name"],
                role=candidate["role"],
                experience=candidate["experience"],
                score=score,
                similarity_score=round(similarity, 4),
                skill_overlap_score=round(overlap, 4),
                matched_skills=matched,
                missing_skills=missing,
                reason=reason,
            )
        )

    # ── Step 5: Re-rank by composite score and return top_k ──────────────────
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]
