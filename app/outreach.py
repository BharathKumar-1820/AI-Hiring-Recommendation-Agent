"""
outreach.py — Simulated conversational outreach and interest assessment.

Responsibilities
----------------
1. Generate personalised recruiter outreach messages for matched candidates.
2. Simulate realistic candidate responses based on profile signals.
3. Assess interest across four dimensions: enthusiasm, availability,
   role alignment, and engagement.
4. Return a structured EngagementResult with conversation transcript
   and interest scores.

Design notes
------------
• Fully deterministic — no external LLM or paid API required.
• Response quality is driven by real candidate attributes (match score,
  skill overlap, experience, role alignment) so each candidate produces
  a unique, coherent conversation.
• Seeded randomness (based on candidate ID + JD hash) ensures
  reproducibility while adding natural-feeling variation.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Tuple

from app.models import (
    ConversationMessage,
    EngagementResult,
    InterestBreakdown,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deterministic_seed(candidate_id: int, jd_hash: str) -> int:
    """Create a stable seed from candidate ID + JD for reproducible variation."""
    raw = f"{candidate_id}:{jd_hash}"
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


def _jd_hash(job_description: str) -> str:
    return hashlib.sha256(job_description.encode()).hexdigest()[:12]


def _pick(options: list, seed: int, offset: int = 0) -> str:
    """Deterministically pick from a list of options."""
    return options[(seed + offset) % len(options)]


def _clamp(value: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, value))


def _timestamp(base: datetime, minutes_offset: int) -> str:
    return (base + timedelta(minutes=minutes_offset)).isoformat()


# ---------------------------------------------------------------------------
# Response templates
# ---------------------------------------------------------------------------

_GREETINGS = [
    "Thanks for reaching out! I appreciate you thinking of me for this.",
    "Hi there! Thanks for the message — this sounds interesting.",
    "Hello! Great to hear from you. I've been looking for opportunities like this.",
    "Thank you for contacting me! I'm happy to chat about this role.",
    "Hi! This caught my eye — thanks for getting in touch.",
]

_HIGH_ENTHUSIASM = [
    "I'm genuinely excited about this opportunity. The tech stack aligns perfectly with what I love working on.",
    "This role is exactly what I've been looking for — the combination of {skills} is right in my wheelhouse.",
    "I've been wanting to work on something like this. The challenges described in the JD really resonate with me.",
    "I'm very interested! The work described here is exactly the kind of impact I want to make.",
]

_MEDIUM_ENTHUSIASM = [
    "This looks like a solid opportunity. I'd like to learn more about the team and the specific projects.",
    "I'm interested, though I'd want to understand the day-to-day responsibilities better before committing.",
    "The role sounds promising. I have most of the skills mentioned, and I'm open to learning {missing}.",
    "I think this could be a good fit. Can you tell me more about the team culture and growth opportunities?",
]

_LOW_ENTHUSIASM = [
    "I appreciate the outreach. I'm not actively looking right now, but I'm open to hearing more.",
    "Thanks for reaching out. The role is a bit different from my current focus, but I'm curious to learn more.",
    "I'm somewhat interested, though I'd need to understand how this aligns with my career goals.",
    "Interesting opportunity. I have some concerns about the skill gaps, but I'm open to discussing further.",
]

_AVAILABILITY_RESPONSES = {
    "immediate": [
        "I'm currently between roles, so I could start within 1-2 weeks.",
        "I'm available immediately — I recently completed my last engagement.",
        "I can start right away. I've been looking for the right opportunity.",
    ],
    "short": [
        "I have a 2-week notice period, so I could start in about 3 weeks.",
        "I'd need about 2-3 weeks to wrap up my current project and transition.",
        "I could realistically start within a month after giving notice.",
    ],
    "medium": [
        "I have a standard 30-day notice period at my current company.",
        "I'd need about 4-6 weeks — I want to leave my current team in good shape.",
        "My notice period is one month, but I could potentially negotiate that down.",
    ],
    "long": [
        "I'm mid-project right now, so I'd need about 2-3 months to transition.",
        "I have a 90-day notice period at my current role. I know it's long, but the role interests me.",
        "I'd need at least 2 months — I have commitments I need to honor first.",
    ],
}

_SALARY_RESPONSES = [
    "I'm flexible on compensation — the role and growth matter more to me at this stage.",
    "I have a range in mind, but I'd rather understand the full package before discussing numbers.",
    "I'm looking for competitive market-rate compensation. Happy to discuss specifics later.",
    "Comp is important, but it's not my primary driver. I'm more interested in the technical challenges.",
]

_ALIGNMENT_HIGH = [
    "This role is a natural next step in my career. I've been building exactly these skills for the past {exp} years.",
    "My background as a {role} maps directly to what you're describing. I can hit the ground running.",
    "I've been intentionally moving my career in this direction — this role feels like a great fit.",
]

_ALIGNMENT_MEDIUM = [
    "While my background is in {role}, I see a lot of overlap with this position. I'm keen to make the transition.",
    "I've been expanding my skills in this area and feel ready to take on a more focused role.",
    "Some of my experience is adjacent, but I've been actively upskilling in the areas mentioned.",
]

_ALIGNMENT_LOW = [
    "I'll be honest — this would be a bit of a pivot for me. But I'm a fast learner and very motivated.",
    "My current role as {role} is quite different, but I've been exploring this space on my own time.",
    "I'd be coming at this from a different angle, but I believe my transferable skills are relevant.",
]

_CLOSING_POSITIVE = [
    "I'd love to move forward with a formal interview. When would work for you?",
    "This has been a great conversation. I'm definitely interested in next steps.",
    "Thanks for the detailed overview. Count me in for the next round — I'm excited to learn more.",
]

_CLOSING_NEUTRAL = [
    "I appreciate the information. Let me think it over and get back to you soon.",
    "Thanks for the chat. I'd like to discuss this with my partner before committing to next steps.",
    "Good conversation. I'm cautiously interested — could you send me more details about the team?",
]

_CLOSING_HESITANT = [
    "Thanks for the overview. I have some reservations, but I'm not ruling it out entirely.",
    "I appreciate your time. I'll need to weigh this against other options I'm considering.",
    "Thank you. I'm not sure this is the right fit, but I'd like to keep the door open.",
]


# ---------------------------------------------------------------------------
# Scoring logic
# ---------------------------------------------------------------------------

def _compute_interest_signals(
    candidate: dict,
    match_score: int,
    skill_overlap: float,
    matched_skills: list[str],
    missing_skills: list[str],
    seed: int,
) -> InterestBreakdown:
    """
    Compute the four interest dimensions from candidate profile signals.

    Scoring rationale:
    - enthusiasm: driven by match_score + role alignment + seed variation
    - availability: driven by experience level (seniors have longer notice)
    - role_alignment: driven by skill overlap + how close their current role is
    - engagement: driven by match quality + experience (experienced = more detailed)
    """
    exp = candidate["experience"]
    n_matched = len(matched_skills)
    n_missing = len(missing_skills)
    variation = (seed % 15) - 7  # -7 to +7 range for natural variation

    # ── Enthusiasm ──────────────────────────────────────────────────────────
    # Base: match score scaled to 0-100, plus variation
    enthusiasm_base = int(match_score * 1.1)  # slightly amplify
    if n_missing == 0:
        enthusiasm_base += 10  # perfect skill match → extra excited
    elif n_missing > 3:
        enthusiasm_base -= 10  # too many gaps → hesitant
    enthusiasm = _clamp(enthusiasm_base + variation)

    # ── Availability ────────────────────────────────────────────────────────
    # Junior/mid = more available, senior = longer notice periods
    if exp <= 3:
        avail_base = 85 + variation
    elif exp <= 5:
        avail_base = 72 + variation
    elif exp <= 8:
        avail_base = 60 + variation
    else:
        avail_base = 50 + variation
    # High enthusiasm bumps availability slightly
    if enthusiasm >= 75:
        avail_base += 8
    availability = _clamp(avail_base)

    # ── Role alignment ──────────────────────────────────────────────────────
    # Based on skill overlap and how many critical skills match
    alignment_base = int(skill_overlap * 90)
    if exp >= 5 and n_matched >= 4:
        alignment_base += 10  # experienced + many matches = strong alignment
    elif n_missing > n_matched:
        alignment_base -= 10  # more gaps than matches = weak alignment
    role_alignment = _clamp(alignment_base + (variation // 2))

    # ── Engagement ──────────────────────────────────────────────────────────
    # How detailed and responsive (senior + interested = more engaged)
    engagement_base = 50 + (exp * 3) + (enthusiasm // 4)
    if match_score >= 70:
        engagement_base += 10  # good match = more willing to engage
    engagement = _clamp(engagement_base + variation)

    return InterestBreakdown(
        enthusiasm=enthusiasm,
        availability=availability,
        role_alignment=role_alignment,
        engagement=engagement,
    )


def _interest_score_from_breakdown(breakdown: InterestBreakdown) -> int:
    """Weighted average of the four interest dimensions."""
    raw = (
        breakdown.enthusiasm * 0.25
        + breakdown.availability * 0.25
        + breakdown.role_alignment * 0.25
        + breakdown.engagement * 0.25
    )
    return _clamp(round(raw))


# ---------------------------------------------------------------------------
# Conversation generation
# ---------------------------------------------------------------------------

def _generate_conversation(
    candidate: dict,
    job_description: str,
    matched_skills: list[str],
    missing_skills: list[str],
    match_score: int,
    interest: InterestBreakdown,
    seed: int,
) -> List[ConversationMessage]:
    """
    Generate a 4-5 turn simulated conversation between the AI recruiter
    agent and the candidate.
    """
    messages: List[ConversationMessage] = []
    base_time = datetime(2025, 6, 15, 10, 0, 0)
    name = candidate["name"].split()[0]  # first name
    role = candidate["role"]
    exp = candidate["experience"]
    skills_str = ", ".join(matched_skills[:4]) if matched_skills else "your background"
    missing_str = ", ".join(missing_skills[:3]) if missing_skills else ""

    # ── Turn 1: Agent outreach ──────────────────────────────────────────────
    agent_intro = (
        f"Hi {name}! I'm an AI recruiting assistant, and I came across your profile. "
        f"We have an exciting opportunity that aligns well with your experience in {skills_str}. "
        f"Based on our analysis, your profile is a strong match for this role. "
        f"Would you be open to hearing more about it?"
    )
    messages.append(ConversationMessage(
        role="agent", content=agent_intro, timestamp=_timestamp(base_time, 0),
    ))

    # ── Turn 2: Candidate greeting + initial interest ───────────────────────
    greeting = _pick(_GREETINGS, seed, offset=0)

    if interest.enthusiasm >= 75:
        interest_line = _pick(_HIGH_ENTHUSIASM, seed, 1).format(
            skills=skills_str, missing=missing_str,
        )
    elif interest.enthusiasm >= 50:
        interest_line = _pick(_MEDIUM_ENTHUSIASM, seed, 1).format(
            skills=skills_str, missing=missing_str,
        )
    else:
        interest_line = _pick(_LOW_ENTHUSIASM, seed, 1).format(
            skills=skills_str, missing=missing_str,
        )

    messages.append(ConversationMessage(
        role="candidate",
        content=f"{greeting} {interest_line}",
        timestamp=_timestamp(base_time, 12),
    ))

    # ── Turn 3: Agent asks about availability + alignment ───────────────────
    agent_followup = (
        f"Great to hear your interest! To give you a better picture — this role involves "
        f"working with {skills_str} in a fast-paced environment. "
        f"A couple of quick questions: What does your availability look like, "
        f"and how do you see this fitting into your career trajectory?"
    )
    messages.append(ConversationMessage(
        role="agent", content=agent_followup, timestamp=_timestamp(base_time, 15),
    ))

    # ── Turn 4: Candidate on availability + alignment ───────────────────────
    # Availability response
    if interest.availability >= 80:
        avail_category = "immediate"
    elif interest.availability >= 60:
        avail_category = "short"
    elif interest.availability >= 40:
        avail_category = "medium"
    else:
        avail_category = "long"

    avail_resp = _pick(_AVAILABILITY_RESPONSES[avail_category], seed, 2)

    # Alignment response
    if interest.role_alignment >= 70:
        align_resp = _pick(_ALIGNMENT_HIGH, seed, 3).format(role=role, exp=exp)
    elif interest.role_alignment >= 45:
        align_resp = _pick(_ALIGNMENT_MEDIUM, seed, 3).format(role=role, exp=exp)
    else:
        align_resp = _pick(_ALIGNMENT_LOW, seed, 3).format(role=role, exp=exp)

    messages.append(ConversationMessage(
        role="candidate",
        content=f"{avail_resp} {align_resp}",
        timestamp=_timestamp(base_time, 35),
    ))

    # ── Turn 5: Agent wraps up with comp question ───────────────────────────
    agent_closing = (
        f"Thanks for sharing that, {name}. One last question — do you have any "
        f"expectations around compensation, or is there anything else you'd like "
        f"to know about the role before we potentially move to a formal interview?"
    )
    messages.append(ConversationMessage(
        role="agent", content=agent_closing, timestamp=_timestamp(base_time, 38),
    ))

    # ── Turn 6: Candidate closing ───────────────────────────────────────────
    salary_resp = _pick(_SALARY_RESPONSES, seed, 4)

    overall_interest = _interest_score_from_breakdown(interest)
    if overall_interest >= 70:
        closing = _pick(_CLOSING_POSITIVE, seed, 5)
    elif overall_interest >= 45:
        closing = _pick(_CLOSING_NEUTRAL, seed, 5)
    else:
        closing = _pick(_CLOSING_HESITANT, seed, 5)

    messages.append(ConversationMessage(
        role="candidate",
        content=f"{salary_resp} {closing}",
        timestamp=_timestamp(base_time, 55),
    ))

    return messages


# ---------------------------------------------------------------------------
# Outreach summary generation
# ---------------------------------------------------------------------------

def _build_outreach_summary(
    candidate: dict,
    interest_score: int,
    breakdown: InterestBreakdown,
) -> str:
    """Generate a recruiter-friendly summary of the engagement outcome."""
    name = candidate["name"]

    if interest_score >= 75:
        lead = f"{name} showed strong enthusiasm and is highly interested in the role."
    elif interest_score >= 55:
        lead = f"{name} expressed moderate interest and is open to exploring the opportunity."
    elif interest_score >= 35:
        lead = f"{name} was cautiously interested but has some reservations."
    else:
        lead = f"{name} showed limited interest in the role at this time."

    # Highlight the strongest and weakest dimensions
    dims = {
        "enthusiasm": breakdown.enthusiasm,
        "availability": breakdown.availability,
        "role alignment": breakdown.role_alignment,
        "engagement": breakdown.engagement,
    }
    strongest = max(dims, key=dims.get)
    weakest = min(dims, key=dims.get)

    detail = (
        f"Strongest signal: {strongest} ({dims[strongest]}/100). "
        f"Area to probe further: {weakest} ({dims[weakest]}/100)."
    )

    return f"{lead} {detail}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def simulate_engagement(
    candidate: dict,
    job_description: str,
    match_score: int,
    skill_overlap: float,
    matched_skills: list[str],
    missing_skills: list[str],
) -> EngagementResult:
    """
    Run the full conversational outreach simulation for one candidate.

    Parameters
    ----------
    candidate         : raw dict from candidates.json
    job_description   : the original JD text
    match_score       : the composite match score (0-100)
    skill_overlap     : skill overlap ratio (0-1)
    matched_skills    : canonical skill names that matched
    missing_skills    : canonical skill names missing from candidate

    Returns
    -------
    EngagementResult with conversation transcript, interest score,
    breakdown, and recruiter summary.
    """
    jd_h = _jd_hash(job_description)
    seed = _deterministic_seed(candidate["id"], jd_h)

    logger.info(
        "Simulating outreach for candidate %d (%s)",
        candidate["id"], candidate["name"],
    )

    # Step 1: Compute interest signals
    breakdown = _compute_interest_signals(
        candidate=candidate,
        match_score=match_score,
        skill_overlap=skill_overlap,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        seed=seed,
    )

    # Step 2: Compute overall interest score
    interest_score = _interest_score_from_breakdown(breakdown)

    # Step 3: Generate conversation
    conversation = _generate_conversation(
        candidate=candidate,
        job_description=job_description,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        match_score=match_score,
        interest=breakdown,
        seed=seed,
    )

    # Step 4: Build recruiter summary
    summary = _build_outreach_summary(candidate, interest_score, breakdown)

    return EngagementResult(
        conversation=conversation,
        interest_score=interest_score,
        interest_breakdown=breakdown,
        outreach_summary=summary,
    )
