"""Core data models for PromptLint."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for prompt issues."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueCategory(str, Enum):
    """Categories of prompt issues."""

    CLARITY = "clarity"
    COMPLETENESS = "completeness"
    CONSTRAINTS = "constraints"
    CONTEXT = "context"
    ANTI_PATTERN = "anti_pattern"
    FORMAT = "format"


class Issue(BaseModel):
    """A single issue found during prompt analysis."""

    rule_id: str
    severity: Severity
    category: IssueCategory
    message: str
    suggestion: str
    line_number: Optional[int] = None


class RuleScore(BaseModel):
    """Score for an individual rule."""

    rule_id: str
    max_points: float
    achieved_points: float
    status: str  # "pass", "warn", "fail"
    description: str


class PromptScore(BaseModel):
    """Overall prompt analysis result."""

    raw_score: float  # 0-100
    total_rules: int
    passed_rules: int
    failed_rules: int
    warnings: int
    grade: str  # A, B, C, D, F
    issues: list[Issue] = Field(default_factory=list)
    rule_scores: list[RuleScore] = Field(default_factory=list)
    summary: str = ""
