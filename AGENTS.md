# AGENTS.md — PromptLint

## Project Overview

PromptLint is a Python CLI tool that analyzes AI prompts for quality, clarity, completeness, and anti-patterns. It returns a weighted score (0-100) with letter grades and actionable suggestions.

## Architecture

```
promptlint/
├── src/promptlint/
│   ├── __init__.py       # Version info
│   ├── models.py         # Pydantic data models (Issue, PromptScore, RuleScore)
│   ├── analyzer.py       # Core analysis engine (PromptAnalyzer class)
│   └── cli.py            # Click CLI with 4 commands (analyze, rules, score, improve)
├── tests/
│   ├── test_analyzer.py  # Analyzer unit tests
│   └── test_cli.py       # CLI integration tests
├── pyproject.toml        # hatchling build config
├── .github/workflows/ci.yml
└── README.md
```

## Key Design Decisions

1. **Regex-first analysis** — All rules use regex patterns for speed and broad applicability. No LLM dependency.
2. **Weighted scoring** — Each rule has a point value; final score is weighted average (0-100).
3. **Zero external deps for analysis** — Core analyzer uses only stdlib + pydantic (for models).
4. **Click CLI** — Standard CLI framework with subcommands.
5. **Extensible rule system** — New rules added to analyzer.py dictionaries (ANTI_PATTERNS, COMPLETENESS_PATTERNS, etc.).

## Building & Testing

```bash
# Install
pip install -e .

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=promptlint

# Run a specific test
pytest tests/test_analyzer.py -v
```

## Adding a New Rule

1. Find the appropriate dictionary in `analyzer.py` (ANTI_PATTERNS, COMPLETENESS_PATTERNS, etc.)
2. Add a new entry:
   ```python
   "my_rule_key": {
       "id": "KEY001",
       "regex": r"your_regex_pattern",
       "message": "Descriptive issue message",
       "suggestion": "Actionable improvement tip",
       "severity": Severity.MEDIUM,
       "category": IssueCategory.CLARITY,
       "max_points": 5,
   },
   ```
3. If it's a structural rule, add a case in `_check_structural()` in analyzer.py
4. Add corresponding tests in `tests/test_analyzer.py`

## Rule Types

- **anti_pattern**: Match patterns that reduce quality (inverse — presence = bad)
- **completeness**: Match patterns that indicate quality (positive — presence = good)
- **clarity**: Similar to completeness — want to find clarity indicators
- **context**: Similar to completeness — want to find context indicators
- **structural**: Special checks (length, sentences, special chars, etc.)

## Security Notes

- No network calls
- No hardcoded secrets
- All input validated through Click args
- File paths validated for traversal
- No subprocess execution
- Safe regex (no catastrophic backtracking risk — all patterns are simple)
