"""
tests/test_analyzer.py — Unit tests for the skill extraction and analysis module.
"""

import pytest
from app.analyzer import extract_skills_from_text, analyse_skill_match, build_reason


class TestExtractSkills:
    def test_extracts_python(self):
        skills = extract_skills_from_text("We need a Python developer")
        assert "python" in skills

    def test_extracts_multiple_skills(self):
        text = "Looking for someone with Python, Docker, Kubernetes and AWS experience"
        skills = extract_skills_from_text(text)
        assert "python" in skills
        assert "docker" in skills
        assert "kubernetes" in skills
        assert "aws" in skills

    def test_empty_string_returns_empty(self):
        assert extract_skills_from_text("") == []

    def test_recognises_aliases(self):
        skills = extract_skills_from_text("Must know k8s and JS")
        assert "kubernetes" in skills
        assert "javascript" in skills


class TestAnalyseSkillMatch:
    def test_full_overlap(self):
        jd_skills = ["python", "docker"]
        candidate_raw = ["Python", "Docker"]
        matched, missing, score = analyse_skill_match(jd_skills, candidate_raw)
        assert set(matched) == {"python", "docker"}
        assert missing == []
        assert score == 1.0

    def test_partial_overlap(self):
        jd_skills = ["python", "docker", "kubernetes"]
        candidate_raw = ["Python"]
        matched, missing, score = analyse_skill_match(jd_skills, candidate_raw)
        assert "python" in matched
        assert "docker" in missing
        assert "kubernetes" in missing

    def test_empty_jd_skills(self):
        matched, missing, score = analyse_skill_match([], ["Python"])
        assert matched == []
        assert missing == []
        assert score == 0.0


class TestBuildReason:
    def test_excellent_fit(self):
        candidate = {"name": "Test User", "experience": 5, "role": "Engineer"}
        reason = build_reason(candidate, ["python", "docker"], [], 85, 0.9)
        assert "excellent fit" in reason.lower()

    def test_includes_gaps(self):
        candidate = {"name": "Test User", "experience": 2, "role": "Junior Dev"}
        reason = build_reason(candidate, ["python"], ["docker", "kubernetes"], 50, 0.5)
        assert "docker" in reason.lower()
