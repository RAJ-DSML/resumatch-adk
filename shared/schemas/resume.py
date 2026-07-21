"""
Resume schemas — shared contracts used across all ResuMatch services.

ParsedResume:    raw text extracted by the Parser service
ExtractedResume: structured fields extracted by the Extraction service
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EducationLevel(str, Enum):
    HIGH_SCHOOL = "high_school"
    DIPLOMA = "diploma"
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    OTHER = "other"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class Education(BaseModel):
    degree: str = Field(default="", description="Degree title, e.g. B.Tech Computer Science")
    institution: str = Field(default="", description="Name of university or institution")
    year: Optional[int] = Field(default=None, description="Graduation year")
    level: EducationLevel = Field(default=EducationLevel.UNKNOWN)


class WorkExperience(BaseModel):
    company: str = Field(default="", description="Company or organisation name")
    title: str = Field(default="", description="Job title / role")
    start_year: Optional[int] = Field(default=None)
    end_year: Optional[int] = Field(default=None, description="None means current role")
    duration_months: Optional[int] = Field(default=None, description="Calculated duration in months")
    description: str = Field(default="", description="Role description / responsibilities")
    technologies: list[str] = Field(default_factory=list, description="Tech stack mentioned in this role")


class Project(BaseModel):
    name: str = Field(default="")
    description: str = Field(default="")
    technologies: list[str] = Field(default_factory=list)
    url: Optional[str] = Field(default=None, description="GitHub / live link if present")


# ---------------------------------------------------------------------------
# Top-level schemas
# ---------------------------------------------------------------------------

class ParsedResume(BaseModel):
    """
    Output of the Parser service.
    Raw text extracted from PDF/DOCX — no LLM involved at this stage.
    """
    candidate_id: str = Field(description="UUID assigned by the Parser service")
    filename: str = Field(description="Original uploaded filename")
    raw_text: str = Field(description="Full extracted text content")
    page_count: Optional[int] = Field(default=None)
    extraction_method: str = Field(
        default="pdfminer",
        description="Tool used for extraction: pdfminer | docx2txt | ocr"
    )
    parse_error: Optional[str] = Field(
        default=None,
        description="Non-null if parsing failed or was partial"
    )


class ExtractedResume(BaseModel):
    """
    Output of the Extraction service.
    Structured fields produced by the Extraction Agent (Gemini via ADK).
    """
    candidate_id: str = Field(description="Same UUID as ParsedResume — links the two")
    filename: str

    # Contact
    name: str = Field(default="")
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    linkedin: Optional[str] = Field(default=None)
    github: Optional[str] = Field(default=None)

    # Core profile
    total_experience_years: float = Field(
        default=0.0,
        description="Total years of professional experience (calculated)"
    )
    current_title: str = Field(default="", description="Most recent job title")
    summary: str = Field(default="", description="Professional summary / objective if present")

    # Structured sections
    skills: list[str] = Field(default_factory=list, description="All technical and soft skills")
    education: list[Education] = Field(default_factory=list)
    experience: list[WorkExperience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)

    # Extraction metadata
    extraction_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Model's self-reported confidence in extraction quality"
    )
    extraction_warnings: list[str] = Field(
        default_factory=list,
        description="Low-confidence fields or ambiguous sections flagged by the agent"
    )