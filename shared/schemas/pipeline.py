"""
Pipeline schemas — the state and result contracts that flow through
the entire ResuMatch multi-agent pipeline.

PipelineJob:      created at submission, tracks overall job state
MatchScore:       output of the Matching agent for one candidate
CritiqueResult:   output of the Critique agent for one MatchScore
CandidateReport:  final ranked entry in the Report agent's output
PipelineResult:   the complete final output of the pipeline
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PipelineStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    EXTRACTING = "extracting"
    MATCHING = "matching"
    CRITIQUING = "critiquing"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"


class CritiqueVerdict(str, Enum):
    APPROVED = "approved"           # Score looks accurate, proceed
    ADJUSTED = "adjusted"           # Score adjusted after critique
    FLAGGED = "flagged"             # Significant concern, needs human review
    REJECTED = "rejected"           # Extraction was too poor to score reliably


# ---------------------------------------------------------------------------
# Matching output
# ---------------------------------------------------------------------------

class SkillMatchDetail(BaseModel):
    """Breakdown of skill matching for transparency / explainability."""
    required_skills_matched: list[str] = Field(default_factory=list)
    required_skills_missing: list[str] = Field(default_factory=list)
    preferred_skills_matched: list[str] = Field(default_factory=list)
    skills_match_score: float = Field(default=0.0, ge=0.0, le=1.0)


class MatchScore(BaseModel):
    """
    Output of the Matching agent for a single candidate.
    One MatchScore per resume in the pipeline job.
    """
    candidate_id: str
    job_id: str

    # Weighted overall score (0.0 - 1.0)
    overall_score: float = Field(ge=0.0, le=1.0)

    # Per-criterion scores (0.0 - 1.0 each)
    skills_score: float = Field(ge=0.0, le=1.0)
    experience_score: float = Field(ge=0.0, le=1.0)
    education_score: float = Field(ge=0.0, le=1.0)
    domain_score: float = Field(ge=0.0, le=1.0)

    # Explainability
    skill_detail: SkillMatchDetail = Field(default_factory=SkillMatchDetail)
    strengths: list[str] = Field(
        default_factory=list,
        description="Top 3 reasons this candidate is a good fit"
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Top 3 gaps or concerns"
    )
    matching_reasoning: str = Field(
        default="",
        description="Agent's free-text reasoning for the overall score"
    )


# ---------------------------------------------------------------------------
# Critique output
# ---------------------------------------------------------------------------

class CritiqueResult(BaseModel):
    """
    Output of the Critique agent for a single MatchScore.
    The Critique agent can approve, adjust, flag, or reject a score.
    """
    candidate_id: str
    job_id: str

    verdict: CritiqueVerdict
    original_score: float = Field(ge=0.0, le=1.0)
    adjusted_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Set only when verdict is ADJUSTED"
    )
    critique_notes: str = Field(
        default="",
        description="Critique agent's reasoning — why it approved/adjusted/flagged"
    )
    hallucination_flags: list[str] = Field(
        default_factory=list,
        description="Skills or claims in the match that weren't in the original resume"
    )
    bias_flags: list[str] = Field(
        default_factory=list,
        description="Potential bias signals detected (e.g. institution prestige over-weighting)"
    )

    @property
    def final_score(self) -> float:
        """The score to use in final ranking — adjusted if critique changed it."""
        return self.adjusted_score if self.adjusted_score is not None else self.original_score


# ---------------------------------------------------------------------------
# Report output
# ---------------------------------------------------------------------------

class CandidateReport(BaseModel):
    """
    A single candidate's entry in the final ranked report.
    Combines data from all upstream agents.
    """
    rank: int = Field(description="1-indexed rank in the shortlist")
    candidate_id: str
    filename: str
    candidate_name: str = Field(default="Unknown")

    final_score: float = Field(ge=0.0, le=1.0)
    verdict: CritiqueVerdict

    # Pulled from MatchScore for the report
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    skill_detail: SkillMatchDetail = Field(default_factory=SkillMatchDetail)

    # Report agent's human-readable summary
    summary: str = Field(
        default="",
        description="2-3 sentence narrative summary written by the Report agent"
    )
    recommendation: str = Field(
        default="",
        description="e.g. 'Strong hire', 'Interview recommended', 'Not suitable'"
    )
    critique_notes: str = Field(default="")
    hallucination_flags: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level pipeline job
# ---------------------------------------------------------------------------

class PipelineJob(BaseModel):
    """
    Created by the Orchestrator when a new job is submitted.
    Tracks state across the full pipeline.
    """
    job_id: str
    status: PipelineStatus = Field(default=PipelineStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Input
    resume_filenames: list[str] = Field(default_factory=list)
    resume_count: int = Field(default=0)

    # Progress tracking
    parsed_count: int = Field(default=0)
    extracted_count: int = Field(default=0)
    matched_count: int = Field(default=0)
    critiqued_count: int = Field(default=0)

    error_message: Optional[str] = Field(default=None)


class PipelineResult(BaseModel):
    """
    The complete final output of the ResuMatch pipeline.
    Returned by the Report service and displayed in the UI.
    """
    job_id: str
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    # Job metadata
    job_title: str = Field(default="")
    company: Optional[str] = None
    resumes_processed: int = Field(default=0)
    resumes_failed: int = Field(default=0)

    # Ranked shortlist
    shortlist: list[CandidateReport] = Field(
        default_factory=list,
        description="Ranked candidates — index 0 is rank 1 (best match)"
    )

    # Pipeline-level summary
    pipeline_summary: str = Field(
        default="",
        description="Report agent's overall summary of the candidate pool"
    )
    processing_time_seconds: Optional[float] = Field(default=None)