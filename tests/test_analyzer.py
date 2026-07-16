"""Tests for the PromptAnalyzer engine."""

import pytest
from promptlint.analyzer import PromptAnalyzer
from promptlint.models import PromptScore, Severity, IssueCategory


class TestPromptAnalyzerBasic:
    """Basic functionality tests."""

    def setup_method(self):
        self.analyzer = PromptAnalyzer()

    def test_analyze_returns_prompt_score(self):
        result = self.analyzer.analyze("Write a Python function to sort a list")
        assert isinstance(result, PromptScore)
        assert 0 <= result.raw_score <= 100
        assert result.grade in ("A", "B", "C", "D", "F")

    def test_empty_prompt(self):
        result = self.analyzer.analyze("")
        assert result.raw_score < 50

    def test_good_prompt_high_score(self):
        prompt = """Act as a senior Python developer. Write a function called 'sort_list' that takes a list of integers and returns them sorted in ascending order. The function should use the built-in sorted() function and handle edge cases like empty lists and None values. Return the result as a list.

Example:
Input: [3, 1, 2]
Output: [1, 2, 3]

Constraints:
- Must handle empty lists
- Must not modify the original list
- Time complexity should be O(n log n)"""
        result = self.analyzer.analyze(prompt)
        assert result.raw_score >= 70
        assert result.grade in ("A", "B", "C")

    def test_bad_prompt_low_score(self):
        prompt = "do something with the code"
        result = self.analyzer.analyze(prompt)
        assert result.raw_score < 50
        assert result.grade in ("D", "F")

    def test_very_short_prompt(self):
        result = self.analyzer.analyze("hi")
        assert result.raw_score < 50

    def test_single_question_prompt(self):
        result = self.analyzer.analyze("How do I sort a list?")
        assert result.grade in ("C", "D", "F")


class TestAntiPatterns:
    """Tests for anti-pattern detection."""

    def setup_method(self):
        self.analyzer = PromptAnalyzer()

    def test_vague_action_detected(self):
        prompt = "make this better"
        result = self.analyzer.analyze(prompt)
        anti_patterns = [i for i in result.issues if i.category == IssueCategory.ANTI_PATTERN]
        assert len(anti_patterns) > 0

    def test_missing_context_detected(self):
        prompt = "create something cool"
        result = self.analyzer.analyze(prompt)
        anti_patterns = [i for i in result.issues if i.category == IssueCategory.ANTI_PATTERN]
        assert len(anti_patterns) > 0

    def test_overly_broad_detected(self):
        prompt = "improve the entire project code"
        result = self.analyzer.analyze(prompt)
        anti_patterns = [i for i in result.issues if i.category == IssueCategory.ANTI_PATTERN]
        assert len(anti_patterns) > 0


class TestCompletenessChecks:
    """Tests for completeness pattern detection."""

    def setup_method(self):
        self.analyzer = PromptAnalyzer()

    def test_role_specification_found(self):
        prompt = "Act as a Python developer and write a function"
        result = self.analyzer.analyze(prompt)
        completeness = [i for i in result.issues if i.category == IssueCategory.COMPLETENESS]
        role_issues = [i for i in completeness if i.rule_id == "C001"]
        assert len(role_issues) == 0

    def test_output_format_found(self):
        prompt = "Write a function and return the result as JSON"
        result = self.analyzer.analyze(prompt)
        format_issues = [i for i in result.issues if i.rule_id == "C002"]
        assert len(format_issues) == 0

    def test_constraints_found(self):
        prompt = "Write a function that must handle edge cases and should not use external libraries"
        result = self.analyzer.analyze(prompt)
        constraint_issues = [i for i in result.issues if i.rule_id == "C004"]
        assert len(constraint_issues) == 0


class TestContextChecks:
    """Tests for context pattern detection."""

    def setup_method(self):
        self.analyzer = PromptAnalyzer()

    def test_language_mention_found(self):
        prompt = "Write a Python function to parse CSV files"
        result = self.analyzer.analyze(prompt)
        context_issues = [i for i in result.issues if i.rule_id == "X001"]
        assert len(context_issues) == 0

    def test_no_language_mentioned(self):
        prompt = "Write a function to sort a list"
        result = self.analyzer.analyze(prompt)
        context_issues = [i for i in result.issues if i.rule_id == "X001"]
        assert len(context_issues) > 0

    def test_library_mention_found(self):
        prompt = "Write a FastAPI endpoint that uses Pydantic for validation"
        result = self.analyzer.analyze(prompt)
        library_issues = [i for i in result.issues if i.rule_id == "X002"]
        assert len(library_issues) == 0


class TestStructuralChecks:
    """Tests for structural property checks."""

    def setup_method(self):
        self.analyzer = PromptAnalyzer()

    def test_short_prompt_penalty(self):
        result = self.analyzer.analyze("hi")
        short_issues = [i for i in result.issues if i.rule_id == "S001"]
        assert len(short_issues) > 0

    def test_long_prompt_penalty(self):
        long_prompt = "a" * 2500
        result = self.analyzer.analyze(long_prompt)
        long_issues = [i for i in result.issues if i.rule_id == "S002"]
        assert len(long_issues) > 0

    def test_sentence_count_check(self):
        result = self.analyzer.analyze("hi")
        sentence_issues = [i for i in result.issues if i.rule_id == "S004"]
        assert len(sentence_issues) > 0

    def test_question_only_check(self):
        result = self.analyzer.analyze("How do I sort a list?")
        question_issues = [i for i in result.issues if i.rule_id == "S005"]
        assert len(question_issues) > 0


class TestGrading:
    """Tests for grade assignment."""

    def setup_method(self):
        self.analyzer = PromptAnalyzer()

    def test_grade_a(self):
        prompt = """Act as a senior Python developer. I want to build a fast function to sort a list of integers. Return the sorted result as a Python list.

Example:
Input: [3, 1, 2]
Output: [1, 2, 3]

Constraints:
- Must handle empty lists
- Must not modify the original list
- Use Python built-in sorted() for O(n log n) complexity
- No external libraries needed

Language: Python
Context: This is for a coding interview preparation. The interviewer expects a clean implementation with docstrings."""
        result = self.analyzer.analyze(prompt)
        assert result.grade == "A"

    def test_grade_b(self):
        prompt = "Act as a Python developer. Write a function to sort a list. Use built-in sorted(). Return as a list."
        result = self.analyzer.analyze(prompt)
        assert result.grade in ("B", "C")

    def test_grade_f(self):
        result = self.analyzer.analyze("do something")
        assert result.grade == "F"


class TestSummary:
    """Tests for summary generation."""

    def setup_method(self):
        self.analyzer = PromptAnalyzer()

    def test_summary_contains_score(self):
        result = self.analyzer.analyze("test prompt")
        assert "Score:" in result.summary

    def test_summary_contains_grade(self):
        result = self.analyzer.analyze("test prompt")
        assert "Grade:" in result.summary

    def test_no_issues_summary(self):
        prompt = """Act as a senior Python developer. I want to build a function to sort a list. Return the result as a Python list using the built-in sorted() function.

Example:
Input: [3, 1, 2]
Output: [1, 2, 3]

Constraints:
- Must handle empty lists
- Must not modify the original list
- Use Python built-in sorted() for O(n log n) complexity
- No external libraries needed

Language: Python with Pydantic
Context: This is for a coding interview. The interviewer expects a clean implementation with docstrings. Raise a clear error for invalid input types."""
        result = self.analyzer.analyze(prompt)
        assert "No issues found" in result.summary
