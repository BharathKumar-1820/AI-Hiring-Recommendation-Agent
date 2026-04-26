"""
analyzer.py — Skill extraction and gap analysis.

Responsibilities
----------------
1. Extract a canonical skill list from a raw job-description string using a
   curated keyword vocabulary (no paid NLP API required).
2. Compare those JD skills against a candidate's skill list.
3. Return matched skills, missing skills, and a 0-1 overlap score.
4. Generate a concise human-readable explanation of the match.
"""

from __future__ import annotations

import re
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Skill vocabulary
# Comprehensive list of technology / domain keywords we recognise.
# Keys are canonical names; values are alternative spellings / acronyms.
# ---------------------------------------------------------------------------

SKILL_VOCABULARY: dict[str, list[str]] = {
    # Languages
    "python": ["python3", "py"],
    "javascript": ["js", "javascript"],
    "typescript": ["ts", "typescript"],
    "java": ["java"],
    "c++": ["cpp", "c plus plus"],
    "c#": ["csharp", "c sharp", ".net"],
    "go": ["golang"],
    "rust": ["rust"],
    "scala": ["scala"],
    "kotlin": ["kotlin"],
    "swift": ["swift"],
    "ruby": ["ruby", "rails"],
    "php": ["php"],
    "r": [" r ", "r language", "rlang"],
    "sql": ["sql", "mysql", "postgresql", "postgres", "sqlite", "t-sql", "pl/sql"],
    # ML / AI
    "machine learning": ["ml", "machine learning", "supervised learning", "unsupervised learning"],
    "deep learning": ["deep learning", "dl", "neural network", "neural networks"],
    "nlp": ["nlp", "natural language processing", "text mining"],
    "computer vision": ["computer vision", "cv", "image recognition", "object detection"],
    "pytorch": ["pytorch", "torch"],
    "tensorflow": ["tensorflow", "tf", "keras"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "hugging face": ["hugging face", "huggingface", "transformers library"],
    "llm": ["llm", "large language model", "gpt", "llama", "mistral", "claude"],
    "rag": ["rag", "retrieval augmented generation", "retrieval-augmented"],
    "faiss": ["faiss", "vector search", "vector database", "vector db"],
    "langchain": ["langchain", "lang chain"],
    "mlflow": ["mlflow", "ml flow"],
    "feature engineering": ["feature engineering", "feature extraction"],
    # Data Engineering
    "spark": ["apache spark", "pyspark", "spark"],
    "kafka": ["apache kafka", "kafka"],
    "airflow": ["apache airflow", "airflow"],
    "dbt": ["dbt", "data build tool"],
    "etl": ["etl", "data pipeline", "data pipelines"],
    "data warehousing": ["data warehouse", "data warehousing", "snowflake", "bigquery", "redshift"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    # Backend / APIs
    "fastapi": ["fastapi", "fast api"],
    "django": ["django"],
    "flask": ["flask"],
    "node.js": ["node.js", "nodejs", "node js", "express"],
    "rest api": ["rest api", "restful", "rest", "api design"],
    "graphql": ["graphql"],
    "microservices": ["microservices", "micro-services", "microservice architecture"],
    "grpc": ["grpc", "protobuf"],
    # Frontend
    "react": ["react", "reactjs", "react.js"],
    "vue": ["vue", "vuejs", "vue.js"],
    "angular": ["angular", "angularjs"],
    "next.js": ["next.js", "nextjs"],
    "html/css": ["html", "css", "html5", "css3", "sass", "scss"],
    "webpack": ["webpack", "vite", "bundler"],
    "tailwind": ["tailwind", "tailwindcss"],
    # Cloud / DevOps
    "aws": ["aws", "amazon web services", "ec2", "s3", "lambda", "sagemaker"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "azure": ["azure", "microsoft azure"],
    "docker": ["docker", "containerisation", "containerization"],
    "kubernetes": ["kubernetes", "k8s", "kubectl"],
    "terraform": ["terraform", "infrastructure as code", "iac"],
    "ci/cd": ["ci/cd", "github actions", "jenkins", "gitlab ci", "circleci", "devops"],
    "linux": ["linux", "unix", "bash", "shell scripting"],
    # Databases / Storage
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "elasticsearch": ["elasticsearch", "elastic search", "opensearch"],
    "cassandra": ["cassandra"],
    # Security
    "cybersecurity": ["cybersecurity", "cyber security", "infosec", "penetration testing", "pentesting"],
    "oauth": ["oauth", "oauth2", "jwt", "authentication", "authorisation", "authorization"],
    # Soft / Process
    "agile": ["agile", "scrum", "kanban", "sprint"],
    "system design": ["system design", "distributed systems", "high availability"],
    "algorithms": ["algorithms", "data structures", "leetcode"],
    "testing": ["unit testing", "integration testing", "pytest", "jest", "tdd"],
    "git": ["git", "github", "gitlab", "version control"],
}

# Pre-compile lower-cased patterns once
_COMPILED_PATTERNS: list[Tuple[str, re.Pattern]] = []


def _build_patterns() -> None:
    """Build regex patterns from the vocabulary (called once on import)."""
    for canonical, aliases in SKILL_VOCABULARY.items():
        # Escape special regex chars in each alias
        escaped = [re.escape(a) for a in aliases]
        pattern = re.compile(
            r"(?<!\w)(" + "|".join(escaped) + r")(?!\w)",
            re.IGNORECASE,
        )
        _COMPILED_PATTERNS.append((canonical, pattern))


_build_patterns()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_skills_from_text(text: str) -> List[str]:
    """
    Scan `text` and return a deduplicated list of canonical skill names
    found in our vocabulary.
    """
    found: list[str] = []
    text_lower = text.lower()
    for canonical, pattern in _COMPILED_PATTERNS:
        if pattern.search(text_lower):
            found.append(canonical)
    return found


def analyse_skill_match(
    jd_skills: List[str],
    candidate_skills_raw: List[str],
) -> Tuple[List[str], List[str], float]:
    """
    Compare JD skills against a candidate's raw skill list.

    Parameters
    ----------
    jd_skills : list of canonical skill names extracted from the JD.
    candidate_skills_raw : the skills list from candidates.json (may use
        any alias, e.g. "PyTorch", "k8s").

    Returns
    -------
    matched_skills : skills in both JD and candidate profile.
    missing_skills : JD skills absent from the candidate profile.
    overlap_score  : len(matched) / len(jd_skills) ∈ [0, 1].
    """
    if not jd_skills:
        return [], [], 0.0

    # Canonicalise the candidate's own skills so we compare apples-to-apples
    candidate_canonical: set[str] = set()
    for raw_skill in candidate_skills_raw:
        for canonical, pattern in _COMPILED_PATTERNS:
            if pattern.search(raw_skill.lower()):
                candidate_canonical.add(canonical)
                break
        else:
            # If no pattern matched, include the skill as-is (lower-cased)
            candidate_canonical.add(raw_skill.lower())

    jd_set = set(jd_skills)
    matched = sorted(jd_set & candidate_canonical)
    missing = sorted(jd_set - candidate_canonical)
    overlap_score = len(matched) / len(jd_set) if jd_set else 0.0

    return matched, missing, overlap_score


def build_reason(
    candidate: dict,
    matched_skills: List[str],
    missing_skills: List[str],
    score: int,
    similarity: float,
) -> str:
    """
    Generate a short, human-readable explanation for why a candidate
    does (or does not) fit the role.
    """
    name = candidate["name"]
    exp = candidate["experience"]
    role = candidate["role"]
    n_match = len(matched_skills)
    n_miss = len(missing_skills)

    # Lead sentence – quality descriptor based on composite score
    if score >= 80:
        lead = f"{name} is an excellent fit for this role."
    elif score >= 65:
        lead = f"{name} is a strong candidate worth interviewing."
    elif score >= 50:
        lead = f"{name} is a reasonable match with some skill gaps."
    else:
        lead = f"{name} partially matches the role but has notable gaps."

    # Skill mention
    if n_match:
        skill_str = ", ".join(matched_skills[:5])
        skill_sentence = (
            f"They bring {exp} years of experience as a {role} "
            f"and directly match on: {skill_str}."
        )
    else:
        skill_sentence = (
            f"They have {exp} years of experience as a {role}, "
            "though few skills directly overlap with the JD."
        )

    # Gap note
    if n_miss == 0:
        gap_sentence = "No significant skill gaps detected."
    elif n_miss <= 2:
        gap_sentence = f"Minor gaps: {', '.join(missing_skills)}."
    else:
        gap_sentence = (
            f"Key gaps to address: {', '.join(missing_skills[:3])}"
            + (" and others." if n_miss > 3 else ".")
        )

    return f"{lead} {skill_sentence} {gap_sentence}"
