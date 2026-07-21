"""Analysis engine for prompt quality evaluation."""

from __future__ import annotations

import re
from typing import Optional

from .models import Issue, IssueCategory, PromptScore, RuleScore, Severity


# Well-known anti-patterns that reduce prompt quality
ANTI_PATTERNS = {
    "vague_action": {
        "id": "AP001",
        "regex": r"\b(make|do|handle|process|fix|improve)\b.*\b(the|m|it|this|that)\b.*\b(better|up|differently)\b",
        "message": "Vague action with unclear outcome",
        "suggestion": "Specify exactly what you want changed and what the expected result should be",
        "severity": Severity.MEDIUM,
        "category": IssueCategory.ANTI_PATTERN,
        "max_points": 5,
    },
    "missing_context": {
        "id": "AP002",
        "regex": r"\b(do|create|build|write)\b.*\bsomething\b",
        "message": "Asking to create 'something' without specifying what",
        "suggestion": "Describe specifically what you want built or created",
        "severity": Severity.HIGH,
        "category": IssueCategory.ANTI_PATTERN,
        "max_points": 10,
    },
    "overly_broad": {
        "id": "AP003",
        "regex": r"\b(everything|all|whole|entire|complete)\b.*\b(project|code|app|system)\b",
        "message": "Attempting to handle everything at once",
        "suggestion": "Break down into specific, focused tasks",
        "severity": Severity.MEDIUM,
        "category": IssueCategory.ANTI_PATTERN,
        "max_points": 5,
    },
    "contradictory": {
        "id": "AP004",
        "regex": r"\b(always|never|don't|do not|avoid)\b.*\b(use|include|add|have|keep)\b.*\b(always|never|all|everything)\b",
        "message": "Potentially contradictory constraints",
        "suggestion": "Review constraints for consistency",
        "severity": Severity.MEDIUM,
        "category": IssueCategory.ANTI_PATTERN,
        "max_points": 5,
    },
    "negative_only": {
        "id": "AP006",
        "regex": r"^(?:don't|do not|avoid|no|don't use|don't create|don't include)",
        "message": "Prompt starts with negation only",
        "suggestion": "Include positive instructions alongside negative constraints",
        "severity": Severity.MEDIUM,
        "category": IssueCategory.ANTI_PATTERN,
        "max_points": 5,
    },
}

# Expected patterns for completeness
COMPLETENESS_PATTERNS = {
    "role_specification": {
        "id": "C001",
        "regex": r"\b(?:as a|act as|you are|you should be|imagine you are|pretend you are|角色|专家)\b",
        "message": "No role/persona specified",
        "suggestion": "Consider specifying a role: 'Act as a senior Python developer...' or 'You are a security expert...'",
        "severity": Severity.LOW,
        "category": IssueCategory.COMPLETENESS,
        "max_points": 5,
    },
    "output_format": {
        "id": "C002",
        "regex": r"\b(format|output|return|json|markdown|xml|yaml|table|list|code|text|summary|report)\b",
        "message": "No output format specified",
        "suggestion": "Specify desired output format: 'Return the result as JSON' or 'Format as a table'",
        "severity": Severity.LOW,
        "category": IssueCategory.FORMAT,
        "max_points": 5,
    },
    "examples": {
        "id": "C003",
        "regex": r"\b(example|eg\b|such as|like this|for instance|for example|such like)\b",
        "message": "No examples provided",
        "suggestion": "Include examples to clarify expected behavior",
        "severity": Severity.INFO,
        "category": IssueCategory.COMPLETENESS,
        "max_points": 5,
    },
    "constraints": {
        "id": "C004",
        "regex": r"\b(must|should|must not|mustn't|cannot|can't|cannot|do not|do not use|avoid|only|limited to|no more than|max|minimum|at least)\b",
        "message": "No constraints specified",
        "suggestion": "Add constraints: 'Must handle edge cases', 'Max 3 steps', 'Do not use external libraries'",
        "severity": Severity.LOW,
        "category": IssueCategory.CONSTRAINTS,
        "max_points": 10,
    },
}

# Clarity patterns
CLARITY_PATTERNS = {
    "clear_objective": {
        "id": "CR001",
        "regex": r"\b(to|by|in order to|purpose|goal|objective|aim|intend|want|need)\b",
        "message": "Objective not clearly stated",
        "suggestion": "Start with clear intent: 'I want to build...' or 'The goal is to...'",
        "severity": Severity.LOW,
        "category": IssueCategory.CLARITY,
        "max_points": 10,
    },
    "specific_task": {
        "id": "CR002",
        "regex": r"\b(function|method|class|module|file|endpoint|api|route|handler|component|widget|service|functionality|feature|logic|algorithm|implementation)\b",
        "message": "Task description may be too generic",
        "suggestion": "Be specific: mention 'API endpoint' instead of 'thing', 'function' instead of 'code'",
        "severity": Severity.INFO,
        "category": IssueCategory.CLARITY,
        "max_points": 5,
    },
}

# Context patterns
CONTEXT_PATTERNS = {
    "language_mention": {
        "id": "X001",
        "regex": r"\b(python|javascript|typescript|go|rust|java|c\+\+|ruby|php|swift|kotlin|shell|bash|sql|html|css|markdown|yaml|toml|json|xml|docker|kubernetes|react|vue|angular|django|flask|fastapi|express|next\.js|spring|rails|erlang|elixir|haskell|scala)\b",
        "message": "No programming language specified",
        "suggestion": "Specify the language: 'in Python', 'using TypeScript', 'with Django'",
        "severity": Severity.LOW,
        "category": IssueCategory.CONTEXT,
        "max_points": 5,
    },
    "library_mention": {
        "id": "X002",
        "regex": r"\b(lodash|axios|requests|numpy|pandas|tensorflow|pytorch|fastapi|django|flask|express|react|vue|svelte|angular|tailwind|bootstrap|pytest|jest|webpack|vite|docker|kubernetes|redis|postgres|mysql|mongodb|graphql|prisma|sqlalchemy|click|typer|rich|pydantic)\b",
        "message": "No library/framework specified",
        "suggestion": "Mention preferred libraries: 'using Pydantic for validation', 'with React hooks'",
        "severity": Severity.INFO,
        "category": IssueCategory.CONTEXT,
        "max_points": 5,
    },
    "error_context": {
        "id": "X003",
        "regex": r"\b(error|exception|bug|issue|problem|not working|crash|fail|traceback|stack overflow|segfault|panic|runtime error|compile error|syntax error|permission denied|connection refused|timeout)\b",
        "message": "Error context not provided",
        "suggestion": "Include error messages, stack traces, or reproduction steps",
        "severity": Severity.LOW,
        "category": IssueCategory.CONTEXT,
        "max_points": 5,
    },
}


class PromptAnalyzer:
    """Analyzes a prompt and returns quality scores and issues."""

    def __init__(self) -> None:
        self.rules: list[dict] = []
        self._init_rules()

    def _init_rules(self) -> None:
        """Initialize all analysis rules."""
        # Anti-patterns (checked at beginning)
        for key, rule in ANTI_PATTERNS.items():
            self.rules.append(
                {
                    "type": "anti_pattern",
                    "key": key,
                    "rule": rule,
                    "weight": rule["max_points"],
                }
            )

        # Completeness checks
        for key, rule in COMPLETENESS_PATTERNS.items():
            self.rules.append(
                {
                    "type": "completeness",
                    "key": key,
                    "rule": rule,
                    "weight": rule["max_points"],
                }
            )

        # Clarity checks
        for key, rule in CLARITY_PATTERNS.items():
            self.rules.append(
                {
                    "type": "clarity",
                    "key": key,
                    "rule": rule,
                    "weight": rule["max_points"],
                }
            )

        # Context checks
        for key, rule in CONTEXT_PATTERNS.items():
            self.rules.append(
                {
                    "type": "context",
                    "key": key,
                    "rule": rule,
                    "weight": rule["max_points"],
                }
            )

        # Add structural checks
        self.rules.append(
            {
                "type": "structural",
                "key": "prompt_length",
                "rule": {
                    "id": "S001",
                    "message": "Prompt is very short (less than 20 characters)",
                    "suggestion": "Add more detail and context to improve prompt quality",
                    "severity": Severity.LOW,
                    "category": IssueCategory.CLARITY,
                    "max_points": 5,
                },
                "weight": 5,
            }
        )
        self.rules.append(
            {
                "type": "structural",
                "key": "prompt_length_long",
                "rule": {
                    "id": "S002",
                    "message": "Prompt is very long (over 2000 characters)",
                    "suggestion": "Consider breaking into smaller, focused prompts for better results",
                    "severity": Severity.INFO,
                    "category": IssueCategory.CLARITY,
                    "max_points": 3,
                },
                "weight": 3,
            }
        )
        self.rules.append(
            {
                "type": "structural",
                "key": "special_chars",
                "rule": {
                    "id": "S003",
                    "message": "Prompt contains special characters (e.g., emojis, symbols)",
                    "suggestion": "Use clear text instead of symbols for better model comprehension",
                    "severity": Severity.INFO,
                    "category": IssueCategory.FORMAT,
                    "max_points": 3,
                },
                "weight": 3,
            }
        )
        self.rules.append(
            {
                "type": "structural",
                "key": "sentence_count",
                "rule": {
                    "id": "S004",
                    "message": "Prompt has very few sentences (less than 2)",
                    "suggestion": "Add more sentences to provide better context and clarity",
                    "severity": Severity.LOW,
                    "category": IssueCategory.CLARITY,
                    "max_points": 5,
                },
                "weight": 5,
            }
        )
        self.rules.append(
            {
                "type": "structural",
                "key": "question_only",
                "rule": {
                    "id": "S005",
                    "message": "Prompt is a single question",
                    "suggestion": "Add context: 'Why does X happen? Consider Y and Z factors.'",
                    "severity": Severity.INFO,
                    "category": IssueCategory.CLARITY,
                    "max_points": 3,
                },
                "weight": 3,
            }
        )

    def analyze(
        self,
        text: str,
        *,
        language: Optional[str] = None,
        format: Optional[str] = None,
    ) -> PromptScore:
        """Analyze a prompt and return quality scores and issues.

        Args:
            text: The prompt text to analyze.
            language: Known programming language (override auto-detection).
            format: Expected output format.

        Returns:
            PromptScore with analysis results.
        """
        issues: list[Issue] = []
        rule_scores: list[RuleScore] = []
        total_max = 0.0
        total_achieved = 0.0

        for rule_info in self.rules:
            rule = rule_info["rule"]
            rule_type = rule_info["type"]
            weight = rule_info["weight"]
            total_max += weight

            # Check anti-patterns
            if rule_type == "anti_pattern":
                matched = self._check_anti_pattern(text, rule)
                if matched:
                    issues.append(
                        Issue(
                            rule_id=rule["id"],
                            severity=rule["severity"],
                            category=rule["category"],
                            message=rule["message"],
                            suggestion=rule["suggestion"],
                        )
                    )
                    rule_scores.append(
                        RuleScore(
                            rule_id=rule["id"],
                            max_points=weight,
                            achieved_points=0.0,
                            status="fail",
                            description=rule["message"],
                        )
                    )
                    # Deduct full weight
                    total_achieved += 0.0
                    continue
                else:
                    # No anti-pattern found — full points
                    total_achieved += weight
                    rule_scores.append(
                        RuleScore(
                            rule_id=rule["id"],
                            max_points=weight,
                            achieved_points=weight,
                            status="pass",
                            description=rule["message"],
                        )
                    )
                    continue

            # Check structural rules
            if rule_type == "structural":
                result = self._check_structural(text, rule_info["key"])
                if result is not None:
                    achieved, found = result
                    if found:
                        # Problem found — deduct points and add issue
                        issues.append(
                            Issue(
                                rule_id=rule["id"],
                                severity=rule["severity"],
                                category=rule["category"],
                                message=rule["message"],
                                suggestion=rule["suggestion"],
                            )
                        )
                        rule_scores.append(
                            RuleScore(
                                rule_id=rule["id"],
                                max_points=weight,
                                achieved_points=achieved,
                                status="fail",
                                description=rule["message"],
                            )
                        )
                    else:
                        # No problem — full points
                        rule_scores.append(
                            RuleScore(
                                rule_id=rule["id"],
                                max_points=weight,
                                achieved_points=weight,
                                status="pass",
                                description=f"✓ {rule['message']}",
                            )
                        )
                    total_achieved += achieved
                    continue

            # Check completeness/clarity/context patterns (inverse — want to find them)
            if rule_type in ("completeness", "clarity", "context"):
                matched = self._check_pattern(text, rule)
                if matched:
                    # Good — pattern found
                    total_achieved += weight
                    rule_scores.append(
                        RuleScore(
                            rule_id=rule["id"],
                            max_points=weight,
                            achieved_points=weight,
                            status="pass",
                            description=f"✓ {rule['message']}",
                        )
                    )
                else:
                    # Missing pattern — issue
                    issues.append(
                        Issue(
                            rule_id=rule["id"],
                            severity=rule["severity"],
                            category=rule["category"],
                            message=rule["message"],
                            suggestion=rule["suggestion"],
                        )
                    )
                    rule_scores.append(
                        RuleScore(
                            rule_id=rule["id"],
                            max_points=weight,
                            achieved_points=0.0,
                            status="fail",
                            description=rule["message"],
                        )
                    )
                    total_achieved += 0.0

        # Calculate final score
        if total_max > 0:
            raw_score = min(100.0, (total_achieved / total_max) * 100.0)
        else:
            raw_score = 0.0

        grade = self._score_to_grade(raw_score)

        # Count statuses
        passed = sum(1 for rs in rule_scores if rs.status == "pass")
        failed = sum(1 for rs in rule_scores if rs.status == "fail")
        warnings = sum(1 for rs in rule_scores if rs.status == "warn")

        # Build summary
        summary = self._build_summary(raw_score, issues, passed, failed)

        return PromptScore(
            raw_score=round(raw_score, 1),
            total_rules=len(rule_scores),
            passed_rules=passed,
            failed_rules=failed,
            warnings=warnings,
            grade=grade,
            issues=issues,
            rule_scores=rule_scores,
            summary=summary,
        )

    def _check_anti_pattern(self, text: str, rule: dict) -> bool:
        """Check if an anti-pattern is present."""
        pattern = rule.get("regex", "")
        if not pattern:
            return False
        return bool(re.search(pattern, text, re.IGNORECASE))

    def _check_pattern(self, text: str, rule: dict) -> bool:
        """Check if a desired pattern is present."""
        pattern = rule.get("regex", "")
        if not pattern:
            return False
        return bool(re.search(pattern, text, re.IGNORECASE))

    def _check_structural(
        self, text: str, key: str
    ) -> tuple[float, bool] | None:
        """Check structural properties. Returns (achieved_points, found_issue)."""
        if key == "prompt_length":
            if len(text.strip()) < 20:
                return (0.0, True)
            return (5.0, False)

        if key == "prompt_length_long":
            if len(text) > 2000:
                return (0.0, True)
            return (3.0, False)

        if key == "special_chars":
            # Check for emojis or special Unicode characters beyond basic punctuation
            if re.search(r'[\U0001F600-\U0001F9FF\U00002700-\U000027BF]', text):
                return (0.0, True)
            return (3.0, False)

        if key == "sentence_count":
            sentences = len(re.findall(r'[.!?]+', text))
            if sentences < 2:
                return (0.0, True)
            return (5.0, False)

        if key == "question_only":
            stripped = text.strip()
            if stripped.endswith('?') and stripped.count('?') == 1 and stripped.count('.') == 0:
                return (0.0, True)
            return (3.0, False)

        return None

    def _score_to_grade(self, score: float) -> str:
        """Convert numerical score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _build_summary(
        self,
        score: float,
        issues: list[Issue],
        passed: int,
        failed: int,
    ) -> str:
        """Build a human-readable summary."""
        parts = []
        parts.append(f"Score: {score:.0f}/100 (Grade: {self._score_to_grade(score)})")

        if issues:
            # Group by severity
            critical = [i for i in issues if i.severity == Severity.CRITICAL]
            high = [i for i in issues if i.severity == Severity.HIGH]
            medium = [i for i in issues if i.severity == Severity.MEDIUM]
            low = [i for i in issues if i.severity == Severity.LOW]
            info = [i for i in issues if i.severity == Severity.INFO]

            if critical or high:
                parts.append(
                    f"⚠ {len(critical) + len(high)} critical/high issues need attention"
                )
            if medium:
                parts.append(f"⚡ {len(medium)} medium issues to consider")
            if low or info:
                parts.append(f"ℹ {len(low) + len(info)} informational notes")
        else:
            parts.append("✨ No issues found! Great prompt!")

        parts.append(f"{passed} rules passed, {failed} rules flagged")
        return " | ".join(parts)
