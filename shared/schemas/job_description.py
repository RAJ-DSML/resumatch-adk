"""
Job Description schemas — shared contracts used across all ResuMatch services.

JobDescription:          raw input from the user
StructuredJobDescription: parsed/structured version used by the Matching agent
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ExperienceLevel(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"           # 0-2 years
    MID = "mid"                 # 2-5 years
    SENIOR = "senior"           # 5-10 years
    LEAD = "lead"               # 8+ years
    PRINCIPAL = "principal"     # 12+ years
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class ScoringWeights(BaseModel):
    """
    Controls how the Matching agent weights each criterion.
    All weights should sum to 1.0 — the Matching service will normalise
    if they don't, but it's good practice to set them explicitly.
    """
    skills_match: float = Field(default=0.40, ge=0.0, le=1.0)
    experience_years: float = Field(default=0.25, ge=0.0, le=1.0)
    education: float = Field(default=0.15, ge=0.0, le=1.0)
    domain_relevance: float = Field(default=0.20, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Top-level schemas
# ---------------------------------------------------------------------------

class JobDescription(BaseModel):
    """
    Raw job description as submitted by the user via the UI or API.
    """
    job_id: str = Field(description="UUID assigned at submission time")
    title: str = Field(description="Job title e.g. Senior Data Scientist")
    company: Optional[str] = Field(default=None)
    raw_text: str = Field(description="Full JD text pasted or uploaded by the user")
    scoring_weights: ScoringWeights = Field(
        default_factory=ScoringWeights,
        description="Optional custom weights — defaults work for most cases"
    )


class StructuredJobDescription(BaseModel):
    """
    Structured version of the JD, parsed by the Extraction service
    (same agent, different prompt path) or by a lightweight rule-based parser.
    Used as the comparison target by the Matching agent.
    """
    job_id: str
    title: str
    company: Optional[str] = None

    # Requirements
    required_skills: list[str] = Field(
        default_factory=list,
        description="Must-have skills — absence should penalise score heavily"
    )
    preferred_skills: list[str] = Field(
        default_factory=list,
        description="Nice-to-have skills — presence boosts score but absence doesn't penalise"
    )
    min_experience_years: float = Field(default=0.0)
    max_experience_years: Optional[float] = Field(default=None)
    experience_level: ExperienceLevel = Field(default=ExperienceLevel.UNKNOWN)
    required_education: list[str] = Field(
        default_factory=list,
        description="e.g. ['B.Tech', 'M.Tech', 'PhD'] — any of these satisfies the requirement"
    )
    domain: str = Field(
        default="",
        description="Primary domain e.g. 'GenAI', 'Computer Vision', 'Data Engineering'"
    )
    responsibilities: list[str] = Field(default_factory=list)

    # Scoring config (passed through from JobDescription)
    scoring_weights: ScoringWeights = Field(default_factory=ScoringWeights)