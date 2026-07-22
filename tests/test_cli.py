"""Tests for the CLI interface."""

import json
from pathlib import Path

from click.testing import CliRunner

from promptlint.cli import main


class TestCLI:
    """Tests for CLI commands."""

    def setup_method(self):
        self.runner = CliRunner()

    # --- analyze command ---

    def test_analyze_text_option(self):
        result = self.runner.invoke(main, ["analyze", "--text", "test"])
        assert result.exit_code == 0
        assert "Score:" in result.output

    def test_analyze_file_option(self, tmp_path: Path):
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("Write a Python function")
        result = self.runner.invoke(main, ["analyze", "--file", str(prompt_file)])
        assert result.exit_code == 0
        assert "Score:" in result.output

    def test_analyze_stdin(self):
        result = self.runner.invoke(
            main, ["analyze", "--stdin"], input="Write a Python function\n"
        )
        assert result.exit_code == 0
        assert "Score:" in result.output

    def test_analyze_no_input(self):
        result = self.runner.invoke(main, ["analyze"])
        assert result.exit_code != 0
        assert "Empty prompt" in result.output or "No prompt provided" in result.output

    def test_analyze_file_not_found(self):
        result = self.runner.invoke(
            main, ["analyze", "--file", "/nonexistent/path.txt"]
        )
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_analyze_json_output(self):
        result = self.runner.invoke(
            main, ["analyze", "--text", "test", "--format", "json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "score" in data
        assert "grade" in data
        assert "issues" in data

    def test_analyze_json_file_output(self, tmp_path: Path):
        output_file = tmp_path / "report.json"
        result = self.runner.invoke(
            main,
            [
                "analyze",
                "--text",
                "test",
                "--format",
                "json",
                "--json-file",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert "score" in data

    def test_analyze_markdown_output(self):
        result = self.runner.invoke(
            main, ["analyze", "--text", "test", "--format", "markdown"]
        )
        assert result.exit_code == 0
        assert "# PromptLint" in result.output

    def test_analyze_category_filter(self):
        result = self.runner.invoke(
            main, ["analyze", "--text", "do something", "--category", "anti_pattern"]
        )
        assert result.exit_code == 0

    def test_analyze_strict_mode_pass(self):
        prompt = """Act as a senior Python developer. Write a function called 'sort_list' that takes a list of integers and returns them sorted in ascending order. The function should use the built-in sorted() function and handle edge cases like empty lists and None values. Return the result as a list.

Example:
Input: [3, 1, 2]
Output: [1, 2, 3]

Constraints:
- Must handle empty lists
- Must not modify the original list
- Time complexity should be O(n log n)"""
        result = self.runner.invoke(main, ["analyze", "--text", prompt, "--strict"])
        assert result.exit_code == 0

    def test_analyze_strict_mode_fail(self):
        result = self.runner.invoke(
            main, ["analyze", "--text", "do something", "--strict"]
        )
        assert result.exit_code == 1

    def test_analyze_both_text_and_file(self):
        result = self.runner.invoke(main, ["analyze", "--text", "foo", "--file", "bar"])
        assert result.exit_code != 0
        assert "Cannot specify both" in result.output

    # --- score command ---

    def test_score_basic(self):
        result = self.runner.invoke(main, ["score", "--text", "test"])
        assert result.exit_code == 0
        assert "Score:" in result.output
        assert "Grade:" in result.output

    def test_score_file(self, tmp_path: Path):
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("test")
        result = self.runner.invoke(main, ["score", "--file", str(prompt_file)])
        assert result.exit_code == 0

    def test_score_empty(self):
        result = self.runner.invoke(main, ["score", "--text", ""])
        assert result.exit_code != 0

    # --- improve command ---

    def test_improve_basic(self):
        result = self.runner.invoke(main, ["improve", "--text", "test prompt"])
        assert result.exit_code == 0
        assert "IMPROVEMENT TIPS" in result.output

    def test_improve_file(self, tmp_path: Path):
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("do something")
        result = self.runner.invoke(main, ["improve", "--file", str(prompt_file)])
        assert result.exit_code == 0

    # --- rules command ---

    def test_rules_text_output(self):
        result = self.runner.invoke(main, ["rules"])
        assert result.exit_code == 0
        assert "Rule ID" in result.output
        assert "AP001" in result.output

    def test_rules_json_output(self):
        result = self.runner.invoke(main, ["rules", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) > 0
        assert "rule_id" in data[0]

    # --- version ---

    def test_version(self):
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
