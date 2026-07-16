"""CLI entry point for PromptLint."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click

from .analyzer import PromptAnalyzer
from .models import PromptScore


def _read_prompt(text: Optional[str], file: Optional[str], stdin: bool) -> str:
    """Read prompt text from various sources."""
    if file and text:
        raise click.UsageError("Cannot specify both --text and --file")

    if file:
        path = Path(file)
        if not path.exists():
            raise click.NoSuchOption(f"File not found: {file}")
        return path.read_text(encoding="utf-8").strip()

    if stdin:
        return sys.stdin.read().strip()

    if text:
        return text

    # If no source given, try to read from stdin interactively
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    raise click.UsageError(
        "No prompt provided. Use --text 'your prompt', --file path.txt, "
        "or pipe from stdin."
    )


@click.group()
@click.version_option(version="0.1.0", prog_name="promptlint")
def main() -> None:
    """PromptLint — AI prompt quality analyzer.

    Score, validate, and improve AI prompts with static analysis.
    """


@main.command()
@click.argument("prompt_file", required=False)
@click.option(
    "--text",
    "-t",
    help="Prompt text to analyze",
)
@click.option(
    "--file",
    "-f",
    help="Path to a file containing the prompt",
)
@click.option(
    "--stdin",
    "-s",
    is_flag=True,
    help="Read prompt from stdin",
)
@click.option(
    "--language",
    "-l",
    help="Known programming language (e.g., python, typescript)",
)
@click.option(
    "--format",
    "-o",
    "output_format",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format",
)
@click.option(
    "--json-file",
    help="Save JSON output to a file instead of printing",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Exit with code 1 if score is below 70",
)
@click.option(
    "--category",
    type=click.Choice(["clarity", "completeness", "constraints", "context", "anti_pattern", "format"]),
    help="Only show issues in this category",
)
def analyze(
    prompt_file: Optional[str],
    text: Optional[str],
    file: Optional[str],
    stdin: bool,
    language: Optional[str],
    output_format: str,
    json_file: Optional[str],
    strict: bool,
    category: Optional[str],
) -> None:
    """Analyze a prompt for quality issues.

    Reads a prompt from a file, text argument, or stdin, then evaluates it
    against quality rules and returns a score with actionable suggestions.
    """
    try:
        prompt_text = _read_prompt(text, file, stdin)
    except (click.UsageError, click.NoSuchOption) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

    if not prompt_text:
        click.echo("Error: Empty prompt provided.", err=True)
        raise SystemExit(1)

    analyzer = PromptAnalyzer()
    result: PromptScore = analyzer.analyze(
        prompt_text,
        language=language,
        format=output_format,
    )

    # Filter by category if specified
    if category:
        from .models import IssueCategory
        result.issues = [
            i for i in result.issues
            if i.category.value == category
        ]

    # Output results
    if output_format == "json":
        data = {
            "score": result.raw_score,
            "grade": result.grade,
            "rules_total": result.total_rules,
            "rules_passed": result.passed_rules,
            "rules_failed": result.failed_rules,
            "warnings": result.warnings,
            "issues": [
                {
                    "rule_id": i.rule_id,
                    "severity": i.severity.value,
                    "category": i.category.value,
                    "message": i.message,
                    "suggestion": i.suggestion,
                }
                for i in result.issues
            ],
            "summary": result.summary,
        }
        output = json.dumps(data, indent=2, ensure_ascii=False)
        if json_file:
            Path(json_file).write_text(output + "\n", encoding="utf-8")
            click.echo(f"JSON report saved to {json_file}")
        else:
            click.echo(output)
    elif output_format == "markdown":
        output = _format_markdown(result, category)
        if json_file:
            Path(json_file).write_text(output + "\n", encoding="utf-8")
            click.echo(f"Report saved to {json_file}")
        else:
            click.echo(output)
    else:
        output = _format_text(result, category)
        click.echo(output)

    # Strict mode exit code
    if strict and result.raw_score < 70:
        raise SystemExit(1)


@main.command()
@click.option(
    "--json",
    "to_json",
    is_flag=True,
    help="Output rules as JSON",
)
def rules(to_json: bool) -> None:
    """List all analysis rules with descriptions."""
    analyzer = PromptAnalyzer()
    rules_info = []

    for rule_info in analyzer.rules:
        rule = rule_info["rule"]
        rules_info.append({
            "rule_id": rule["id"],
            "type": rule_info["type"],
            "category": rule["category"].value,
            "severity": rule["severity"].value,
            "description": rule["message"],
            "suggestion": rule["suggestion"],
            "max_points": rule_info["weight"],
        })

    if to_json:
        click.echo(json.dumps(rules_info, indent=2))
    else:
        click.echo(f"{'Rule ID':<10} {'Category':<16} {'Severity':<10} {'Description'}")
        click.echo("-" * 80)
        for r in rules_info:
            click.echo(
                f"{r['rule_id']:<10} {r['category']:<16} {r['severity']:<10} {r['description']}"
            )


@main.command()
@click.argument("prompt_file", required=False)
@click.option(
    "--text",
    "-t",
    help="Prompt text to score",
)
@click.option(
    "--file",
    "-f",
    help="Path to file containing prompt",
)
def score(prompt_file: Optional[str], text: Optional[str], file: Optional[str]) -> None:
    """Quick score a prompt (short output)."""
    try:
        prompt_text = _read_prompt(text, file, False)
    except (click.UsageError, click.NoSuchOption) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

    if not prompt_text:
        click.echo("Error: Empty prompt.", err=True)
        raise SystemExit(1)

    analyzer = PromptAnalyzer()
    result: PromptScore = analyzer.analyze(prompt_text)

    click.echo(f"Score: {result.raw_score:.0f}/100  Grade: {result.grade}")
    if result.grade in ("A", "B"):
        click.echo("✓ Prompt quality is good")
    elif result.grade in ("C",):
        click.echo("~ Prompt could be improved")
    else:
        click.echo("⚠ Prompt needs significant improvement")

    if result.failed_rules > 0:
        click.echo(f"\n{result.failed_rules} rule(s) flagged:")
        for issue in result.issues[:3]:
            click.echo(f"  [{issue.severity.value.upper()}] {issue.message}")
            if len(result.issues) > 3:
                click.echo(f"  ... and {len(result.issues) - 3} more")
                break


@main.command()
@click.argument("prompt_file", required=False)
@click.option(
    "--text",
    "-t",
    help="Prompt text to improve",
)
@click.option(
    "--file",
    "-f",
    help="Path to file containing prompt",
)
@click.option(
    "--language",
    "-l",
    help="Target programming language",
)
def improve(prompt_file: Optional[str], text: Optional[str], file: Optional[str], language: Optional[str]) -> None:
    """Get suggestions to improve a prompt.

    Shows the original prompt, issues found, and actionable improvement suggestions.
    """
    try:
        prompt_text = _read_prompt(text, file, False)
    except (click.UsageError, click.NoSuchOption) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

    if not prompt_text:
        click.echo("Error: Empty prompt.", err=True)
        raise SystemExit(1)

    click.echo("=" * 60)
    click.echo("ORIGINAL PROMPT")
    click.echo("=" * 60)
    # Display first 300 chars with ellipsis
    display = prompt_text[:300]
    if len(prompt_text) > 300:
        display += "..."
    click.echo(display)
    click.echo()

    analyzer = PromptAnalyzer()
    result: PromptScore = analyzer.analyze(prompt_text, language=language)

    click.echo("=" * 60)
    click.echo(f"SCORE: {result.raw_score:.0f}/100  Grade: {result.grade}")
    click.echo(f"Rules passed: {result.passed_rules}/{result.total_rules}")
    click.echo()

    if not result.issues:
        click.echo("✨ No issues found! Great prompt!")
        return

    # Group by severity
    severity_order = ["critical", "high", "medium", "low", "info"]
    for sev in severity_order:
        sev_issues = [i for i in result.issues if i.severity.value == sev]
        if not sev_issues:
            continue
        emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "ℹ️"}[sev]
        click.echo(f"{emoji} {sev.upper()} ISSUES:")
        for issue in sev_issues:
            click.echo(f"  • {issue.message}")
            click.echo(f"    → {issue.suggestion}")
        click.echo()

    click.echo("=" * 60)
    click.echo("IMPROVEMENT TIPS")
    click.echo("=" * 60)
    # Show actionable tips
    tips = set()
    for issue in result.issues:
        tips.add(issue.suggestion)

    for i, tip in enumerate(tips, 1):
        click.echo(f"{i}. {tip}")


def _format_text(result: PromptScore, category: Optional[str]) -> str:
    """Format results as plain text."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"PromptLint Analysis — Score: {result.raw_score:.0f}/100  Grade: {result.grade}")
    lines.append("=" * 60)
    lines.append(f"Rules passed: {result.passed_rules}/{result.total_rules}")

    if result.issues:
        lines.append(f"\nIssues ({len(result.issues)}):")
        for issue in result.issues:
            lines.append(
                f"  [{issue.severity.value.upper():>8}] {issue.category.value}: {issue.message}"
            )
            lines.append(f"           Suggestion: {issue.suggestion}")
    else:
        lines.append("\nNo issues found!")

    lines.append("")
    return "\n".join(lines)


def _format_markdown(result: PromptScore, category: Optional[str]) -> str:
    """Format results as markdown."""
    lines = []
    lines.append("# PromptLint Analysis Report")
    lines.append("")
    lines.append(f"**Score:** {result.raw_score:.0f}/100  |  **Grade:** {result.grade}")
    lines.append(f"**Rules passed:** {result.passed_rules}/{result.total_rules}")
    lines.append("")

    if result.issues:
        lines.append("## Issues")
        lines.append("")
        lines.append("| Severity | Category | Rule | Message | Suggestion |")
        lines.append("|----------|----------|------|---------|------------|")
        for issue in result.issues:
            lines.append(
                f"| {issue.severity.value.upper()} | {issue.category.value} | {issue.rule_id} | {issue.message} | {issue.suggestion} |"
            )
        lines.append("")
    else:
        lines.append("No issues found! ✨")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by PromptLint*")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
