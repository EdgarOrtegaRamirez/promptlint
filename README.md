# PromptLint

Static analysis for AI prompts — score, validate, and improve your prompts before sending them to an LLM.

## Why?

Prompts are the interface between you and AI models, yet most people write them without any quality control. A vague or incomplete prompt leads to poor results, wasted tokens, and frustration.

PromptLint treats prompts like code — it analyzes them against quality rules and gives you actionable feedback before you spend tokens on a bad prompt.

## Features

- **Quality scoring** — 0-100 score with letter grades (A-F)
- **Anti-pattern detection** — catches vague language, contradictions, and ineffective patterns
- **Completeness checks** — verifies role, format, constraints, and context are specified
- **Clarity analysis** — checks for clear objectives and specific tasks
- **Context verification** — confirms language, libraries, and error details are present
- **Multiple output formats** — text (terminal), JSON (CI), and Markdown reports
- **Strict mode** — exit code 1 for scores below 70 (CI/CD integration)
- **Improvement suggestions** — actionable tips for each issue found
- **Zero dependencies for analysis** — core engine has no external deps

## Installation

```bash
pip install -e .
```

Or from source:

```bash
git clone https://github.com/EdgarOrtegaRamirez/promptlint.git
cd promptlint
pip install -e .
```

## Quick Start

```bash
# Analyze a prompt inline
promptlint analyze --text "Write a function to sort a list"

# Analyze from a file
promptlint analyze --file my-prompt.txt

# Pipe a prompt
cat my-prompt.txt | promptlint analyze --stdin

# Quick score
promptlint score --text "Build me something cool with React"

# Get improvement suggestions
promptlint improve --file prompt.txt

# JSON output for CI/CD
promptlint analyze --text "your prompt" --format json

# Strict mode (exit 1 if score < 70)
promptlint analyze --text "your prompt" --strict --format json
```

## CLI Commands

### `promptlint analyze`
Full analysis with detailed report.

```bash
# Text output (default)
promptlint analyze --text "Write a Python function to parse CSV files and return a list of dicts"

# JSON output
promptlint analyze --text "..." --format json

# Filter by category
promptlint analyze --text "..." --category completeness

# Save report to file
promptlint analyze --text "..." --format markdown --json-file report.md
```

### `promptlint score`
Quick one-line score.

```bash
promptlint score --text "Write a function to sort a list"
# Score: 35/100  Grade: F
```

### `promptlint improve`
Get actionable improvement tips.

```bash
promptlint improve --file prompt.txt
```

### `promptlint rules`
List all analysis rules.

```bash
promptlint rules
# Shows all 20+ rules with descriptions
```

## Rules

PromptLint evaluates prompts against these categories:

| Category | What it checks |
|----------|---------------|
| **Anti-patterns** | Vague actions, missing context, overly broad requests, contradictions |
| **Completeness** | Role specification, output format, examples, constraints |
| **Clarity** | Clear objectives, specific task descriptions, sentence structure |
| **Context** | Language mentions, library/framework references, error context |

Each rule has a severity (CRITICAL, HIGH, MEDIUM, LOW, INFO) and point value. The final score is a weighted average.

## Grade Scale

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 90-100 | Excellent prompt |
| B | 80-89 | Good prompt |
| C | 70-79 | Adequate, needs minor improvements |
| D | 60-69 | Below average, significant improvements needed |
| F | 0-59 | Poor prompt quality |

## CI/CD Integration

```yaml
# Example GitHub Actions workflow
- name: Check prompt quality
  run: |
    pip install promptlint
    echo "Build a fastapi app with sqlalchemy and pydantic" > prompt.txt
    promptlint analyze --file prompt.txt --strict --format json > report.json
```

## Project Structure

```
promptlint/
├── src/promptlint/
│   ├── __init__.py       # Package init
│   ├── models.py         # Data models (Issue, PromptScore, etc.)
│   ├── analyzer.py       # Core analysis engine
│   └── cli.py            # Click CLI interface
├── tests/
│   ├── test_analyzer.py  # Analyzer unit tests
│   └── test_cli.py       # CLI integration tests
├── pyproject.toml        # Build config
├── .gitignore
├── README.md
├── LICENSE
└── AGENTS.md
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=promptlint --cov-report=html
```

## License

MIT
