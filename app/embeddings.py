"""
embeddings.py — Embedding generation and caching layer.

Wraps sentence-transformers to:
  • Load the model once at startup (singleton pattern).
  • Encode arbitrary text into dense vectors.
  • Cache candidate embeddings so we never recompute them on every request.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model singleton
# ---------------------------------------------------------------------------

_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Return (or lazily initialise) the shared sentence-transformer model."""
    global _model
    if _model is None:
        logger.info("Loading sentence-transformer model: %s", _MODEL_NAME)
        _model = SentenceTransformer(_MODEL_NAME)
        logger.info("Model loaded successfully.")
    return _model


# ---------------------------------------------------------------------------
# Core encoding helpers
# ---------------------------------------------------------------------------

def encode_text(text: str) -> np.ndarray:
    """
    Encode a single string into a normalised float32 embedding vector.

    Normalisation (unit length) is important because FAISS inner-product
    search on normalised vectors is equivalent to cosine similarity.
    """
    model = get_model()
    embedding: np.ndarray = model.encode(
        text,
        convert_to_numpy=True,
        normalize_embeddings=True,   # L2-normalise → cosine via dot product
        show_progress_bar=False,
    )
    return embedding.astype(np.float32)


def encode_batch(texts: List[str]) -> np.ndarray:
    """
    Encode a list of strings in one batched forward pass.

    Returns shape (N, D) float32 array, each row normalised.
    """
    model = get_model()
    embeddings: np.ndarray = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=False,
    )
    return embeddings.astype(np.float32)


# ---------------------------------------------------------------------------
# Candidate embedding cache
# ---------------------------------------------------------------------------

# In-memory cache:  candidate_id  →  np.ndarray
_embedding_cache: Dict[int, np.ndarray] = {}


def _candidate_text(candidate: dict) -> str:
    """
    Build a single rich text representation of a candidate so the
    embedding captures all semantically relevant signals.
    """
    skills_str = ", ".join(candidate["skills"])
    return (
        f"Role: {candidate['role']}. "
        f"Skills: {skills_str}. "
        f"Experience: {candidate['experience']} years. "
        f"Profile: {candidate['description']}"
    )


def build_candidate_embeddings(candidates: List[dict]) -> np.ndarray:
    """
    Generate (and cache) embeddings for every candidate.

    Already-cached candidates are skipped; only new/unknown ones are encoded.

    Returns an (N, D) float32 matrix ordered the same as `candidates`.
    """
    # Identify which candidates are not yet cached
    missing_indices = [
        i for i, c in enumerate(candidates) if c["id"] not in _embedding_cache
    ]

    if missing_indices:
        texts = [_candidate_text(candidates[i]) for i in missing_indices]
        logger.info(
            "Computing embeddings for %d candidate(s)…", len(missing_indices)
        )
        new_embeddings = encode_batch(texts)
        for idx, emb in zip(missing_indices, new_embeddings):
            _embedding_cache[candidates[idx]["id"]] = emb

    # Assemble full matrix (all candidates, in order)
    matrix = np.stack(
        [_embedding_cache[c["id"]] for c in candidates], axis=0
    )
    return matrix


def cache_stats() -> dict:
    """Return a simple dict describing the current embedding cache state."""
    return {"cached_candidates": len(_embedding_cache)}
