"""
M25 Lab Validator — Checks your Claude Code configuration is complete.

Usage:
    python validate_config.py [--dir PATH]  # defaults to current directory

Checks:
  1. .claude/CLAUDE.md exists and has required sections
  2. src/api/CLAUDE.md exists and has API-specific content
  3. .claude/commands/check-filing.md exists and references $ARGUMENTS
  4. .claude/settings.json is valid JSON with hooks and permissions
  5. .github/workflows/claude-review.yml exists with required content
"""

import json
import os
import re
import sys


def green(text):
    return f"\033[92m{text}\033[0m"


def red(text):
    return f"\033[91m{text}\033[0m"


def bold(text):
    return f"\033[1m{text}\033[0m"


class Validator:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.results = []
        self.passed = 0
        self.failed = 0

    def check(self, name, condition, detail=""):
        if condition:
            self.results.append((True, name, detail))
            self.passed += 1
        else:
            self.results.append((False, name, detail))
            self.failed += 1

    def file_exists(self, rel_path):
        return os.path.isfile(os.path.join(self.base_dir, rel_path))

    def read_file(self, rel_path):
        full_path = os.path.join(self.base_dir, rel_path)
        if not os.path.isfile(full_path):
            return None
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    def validate_project_claude_md(self):
        """Check 1: .claude/CLAUDE.md"""
        path = os.path.join(".claude", "CLAUDE.md")
        content = self.read_file(path)

        self.check(
            "Project CLAUDE.md exists",
            content is not None,
            f"Expected file at {path}",
        )
        if content is None:
            # Skip remaining checks for this file
            for section in [
                "Project Identity",
                "Coding Standards",
                "Domain Rules",
                "API Conventions",
                "Testing",
            ]:
                self.check(
                    f"Project CLAUDE.md has '{section}' section",
                    False,
                    "File not found",
                )
            return

        required_sections = [
            "Project Identity",
            "Coding Standards",
            "Domain Rules",
            "API Conventions",
            "Testing",
        ]
        for section in required_sections:
            has_section = re.search(
                rf"##\s+{re.escape(section)}", content, re.IGNORECASE
            )
            self.check(
                f"Project CLAUDE.md has '{section}' section",
                bool(has_section),
                f"Missing ## {section} heading",
            )

        # Check that sections have actual content (not just TODO comments)
        has_real_content = False
        for line in content.split("\n"):
            line = line.strip()
            if (
                line
                and not line.startswith("#")
                and not line.startswith("<!--")
                and not line.startswith("-->")
                and "TODO" not in line
            ):
                has_real_content = True
                break
        self.check(
            "Project CLAUDE.md has substantive content (not just TODOs)",
            has_real_content,
            "All non-heading lines appear to be TODO comments",
        )

    def validate_api_claude_md(self):
        """Check 2: src/api/CLAUDE.md"""
        path = os.path.join("src", "api", "CLAUDE.md")
        content = self.read_file(path)

        self.check(
            "API CLAUDE.md exists",
            content is not None,
            f"Expected file at {path}",
        )
        if content is None:
            self.check(
                "API CLAUDE.md has endpoint/API content",
                False,
                "File not found",
            )
            return

        # Check for API-specific keywords
        api_keywords = ["endpoint", "status code", "json", "http", "rate limit", "auth"]
        found_keywords = [kw for kw in api_keywords if kw.lower() in content.lower()]
        self.check(
            "API CLAUDE.md has API-specific content",
            len(found_keywords) >= 3,
            f"Found {len(found_keywords)}/6 expected keywords: {found_keywords}",
        )

    def validate_slash_command(self):
        """Check 3: .claude/commands/check-filing.md"""
        path = os.path.join(".claude", "commands", "check-filing.md")
        content = self.read_file(path)

        self.check(
            "Slash command check-filing.md exists",
            content is not None,
            f"Expected file at {path}",
        )
        if content is None:
            self.check("Slash command references $ARGUMENTS", False, "File not found")
            self.check("Slash command has validation steps", False, "File not found")
            return

        self.check(
            "Slash command references $ARGUMENTS",
            "$ARGUMENTS" in content,
            "Must include $ARGUMENTS to receive user input",
        )

        has_format_check = bool(
            re.search(r"UCC-\w*Y+\w*-\w*S+\w*T?\w*-\w*N+\w*", content)
            or "format" in content.lower()
            or "validate" in content.lower()
        )
        self.check(
            "Slash command has validation steps",
            has_format_check,
            "Should mention format validation for filing numbers",
        )

    def validate_settings(self):
        """Check 4: .claude/settings.json"""
        path = os.path.join(".claude", "settings.json")
        content = self.read_file(path)

        self.check(
            "settings.json exists",
            content is not None,
            f"Expected file at {path}",
        )
        if content is None:
            for name in [
                "settings.json is valid JSON",
                "settings.json has PreToolUse hook",
                "settings.json has PostToolUse hook",
                "settings.json has permissions.allow",
                "settings.json has permissions.deny",
            ]:
                self.check(name, False, "File not found")
            return

        # Try to parse JSON
        try:
            data = json.loads(content)
            is_valid = True
        except json.JSONDecodeError as e:
            is_valid = False
            data = {}
            self.check("settings.json is valid JSON", False, str(e))

        if is_valid:
            self.check("settings.json is valid JSON", True, "")

        # Check hooks
        hooks = data.get("hooks", {})
        pre_hooks = hooks.get("PreToolUse", [])
        self.check(
            "settings.json has PreToolUse hook",
            isinstance(pre_hooks, list) and len(pre_hooks) > 0,
            "hooks.PreToolUse should be a non-empty array",
        )

        post_hooks = hooks.get("PostToolUse", [])
        self.check(
            "settings.json has PostToolUse hook",
            isinstance(post_hooks, list) and len(post_hooks) > 0,
            "hooks.PostToolUse should be a non-empty array",
        )

        # Check permissions
        permissions = data.get("permissions", {})
        allow = permissions.get("allow", [])
        self.check(
            "settings.json has permissions.allow",
            isinstance(allow, list) and len(allow) > 0,
            "permissions.allow should be a non-empty array",
        )

        deny = permissions.get("deny", [])
        self.check(
            "settings.json has permissions.deny",
            isinstance(deny, list) and len(deny) > 0,
            "permissions.deny should be a non-empty array",
        )

    def validate_github_workflow(self):
        """Check 5: .github/workflows/claude-review.yml"""
        path = os.path.join(".github", "workflows", "claude-review.yml")
        content = self.read_file(path)

        self.check(
            "GitHub Actions workflow exists",
            content is not None,
            f"Expected file at {path}",
        )
        if content is None:
            for name in [
                "Workflow has pull_request trigger",
                "Workflow uses claude -p",
                "Workflow uses --output-format json",
                "Workflow uses --session for isolation",
                "Workflow posts PR comment with gh pr comment",
            ]:
                self.check(name, False, "File not found")
            return

        self.check(
            "Workflow has pull_request trigger",
            "pull_request" in content,
            "Should trigger on pull_request events",
        )

        self.check(
            "Workflow uses claude -p",
            "claude -p" in content or "claude  -p" in content,
            "Should use 'claude -p' for non-interactive review",
        )

        self.check(
            "Workflow uses --output-format json",
            "--output-format json" in content,
            "Should output structured JSON results",
        )

        self.check(
            "Workflow uses --session for isolation",
            "--session" in content,
            "Should use --session to isolate PR review sessions",
        )

        self.check(
            "Workflow posts PR comment with gh pr comment",
            "gh pr comment" in content,
            "Should post review results as a PR comment",
        )

    def print_report(self):
        print()
        print(bold("=" * 60))
        print(bold("  M25 Lab — Claude Code Configuration Validator"))
        print(bold("=" * 60))
        print()

        current_group = None
        group_names = {
            "Project CLAUDE.md": "Step 1: Project-Level CLAUDE.md",
            "API CLAUDE.md": "Step 2: Directory-Level CLAUDE.md",
            "Slash command": "Step 3: Custom Slash Command",
            "settings.json": "Step 4: Settings with Hooks",
            "GitHub Actions": "Step 5: GitHub Actions CI",
            "Workflow": "Step 5: GitHub Actions CI",
        }

        for ok, name, detail in self.results:
            # Determine group
            group = None
            for prefix, gname in group_names.items():
                if name.startswith(prefix):
                    group = gname
                    break

            if group and group != current_group:
                current_group = group
                print(f"\n  {bold(group)}")

            icon = green("  [PASS]") if ok else red("  [FAIL]")
            print(f"  {icon} {name}")
            if not ok and detail:
                print(f"         {detail}")

        print()
        print(bold("-" * 60))
        total = self.passed + self.failed
        print(f"  Results: {green(str(self.passed) + ' passed')}, ", end="")
        if self.failed:
            print(f"{red(str(self.failed) + ' failed')}, ", end="")
        else:
            print(f"{green('0 failed')}, ", end="")
        print(f"{total} total")

        if self.failed == 0:
            print(f"\n  {green('All checks passed! Your configuration is complete.')}")
        else:
            print(
                f"\n  {red(f'{self.failed} check(s) need attention. Review the TODOs above.')}"
            )
        print(bold("=" * 60))
        print()

    def run(self):
        self.validate_project_claude_md()
        self.validate_api_claude_md()
        self.validate_slash_command()
        self.validate_settings()
        self.validate_github_workflow()
        self.print_report()
        return 0 if self.failed == 0 else 1


def main():
    # Parse --dir argument
    base_dir = "."
    args = sys.argv[1:]
    if "--dir" in args:
        idx = args.index("--dir")
        if idx + 1 < len(args):
            base_dir = args[idx + 1]

    if not os.path.isdir(base_dir):
        print(f"Error: directory '{base_dir}' does not exist.")
        sys.exit(1)

    validator = Validator(base_dir)
    exit_code = validator.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
