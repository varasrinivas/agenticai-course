/**
 * M25 Lab Validator — Checks your Claude Code configuration is complete.
 *
 * Usage:
 *     node validate_config.js [--dir PATH]  # defaults to current directory
 *
 * Checks:
 *   1. .claude/CLAUDE.md exists and has required sections
 *   2. src/api/CLAUDE.md exists and has API-specific content
 *   3. .claude/commands/check-filing.md exists and references $ARGUMENTS
 *   4. .claude/settings.json is valid JSON with hooks and permissions
 *   5. .github/workflows/claude-review.yml exists with required content
 */

import fs from "node:fs";
import path from "node:path";

// --- Colors (ANSI) ---
const green = (t) => `\x1b[92m${t}\x1b[0m`;
const red = (t) => `\x1b[91m${t}\x1b[0m`;
const bold = (t) => `\x1b[1m${t}\x1b[0m`;

class Validator {
  constructor(baseDir) {
    this.baseDir = baseDir;
    this.results = [];
    this.passed = 0;
    this.failed = 0;
  }

  check(name, condition, detail = "") {
    if (condition) {
      this.results.push({ ok: true, name, detail });
      this.passed++;
    } else {
      this.results.push({ ok: false, name, detail });
      this.failed++;
    }
  }

  readFile(relPath) {
    const fullPath = path.join(this.baseDir, relPath);
    try {
      return fs.readFileSync(fullPath, "utf-8");
    } catch {
      return null;
    }
  }

  validateProjectClaudeMd() {
    const relPath = path.join(".claude", "CLAUDE.md");
    const content = this.readFile(relPath);

    this.check(
      "Project CLAUDE.md exists",
      content !== null,
      `Expected file at ${relPath}`
    );

    if (content === null) {
      const sections = [
        "Project Identity",
        "Coding Standards",
        "Domain Rules",
        "API Conventions",
        "Testing",
      ];
      for (const s of sections) {
        this.check(`Project CLAUDE.md has '${s}' section`, false, "File not found");
      }
      return;
    }

    const requiredSections = [
      "Project Identity",
      "Coding Standards",
      "Domain Rules",
      "API Conventions",
      "Testing",
    ];

    for (const section of requiredSections) {
      const regex = new RegExp(`##\\s+${section.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`, "i");
      this.check(
        `Project CLAUDE.md has '${section}' section`,
        regex.test(content),
        `Missing ## ${section} heading`
      );
    }

    // Check for substantive content (not just TODOs)
    const lines = content.split("\n");
    let hasRealContent = false;
    for (const line of lines) {
      const trimmed = line.trim();
      if (
        trimmed &&
        !trimmed.startsWith("#") &&
        !trimmed.startsWith("<!--") &&
        !trimmed.startsWith("-->") &&
        !trimmed.includes("TODO")
      ) {
        hasRealContent = true;
        break;
      }
    }
    this.check(
      "Project CLAUDE.md has substantive content (not just TODOs)",
      hasRealContent,
      "All non-heading lines appear to be TODO comments"
    );
  }

  validateApiClaudeMd() {
    const relPath = path.join("src", "api", "CLAUDE.md");
    const content = this.readFile(relPath);

    this.check(
      "API CLAUDE.md exists",
      content !== null,
      `Expected file at ${relPath}`
    );

    if (content === null) {
      this.check("API CLAUDE.md has endpoint/API content", false, "File not found");
      return;
    }

    const apiKeywords = ["endpoint", "status code", "json", "http", "rate limit", "auth"];
    const lowerContent = content.toLowerCase();
    const found = apiKeywords.filter((kw) => lowerContent.includes(kw));

    this.check(
      "API CLAUDE.md has API-specific content",
      found.length >= 3,
      `Found ${found.length}/6 expected keywords: ${found.join(", ")}`
    );
  }

  validateSlashCommand() {
    const relPath = path.join(".claude", "commands", "check-filing.md");
    const content = this.readFile(relPath);

    this.check(
      "Slash command check-filing.md exists",
      content !== null,
      `Expected file at ${relPath}`
    );

    if (content === null) {
      this.check("Slash command references $ARGUMENTS", false, "File not found");
      this.check("Slash command has validation steps", false, "File not found");
      return;
    }

    this.check(
      "Slash command references $ARGUMENTS",
      content.includes("$ARGUMENTS"),
      "Must include $ARGUMENTS to receive user input"
    );

    const hasFormatCheck =
      /UCC-\w*Y+\w*-\w*S+\w*T?\w*-\w*N+\w*/.test(content) ||
      content.toLowerCase().includes("format") ||
      content.toLowerCase().includes("validate");
    this.check(
      "Slash command has validation steps",
      hasFormatCheck,
      "Should mention format validation for filing numbers"
    );
  }

  validateSettings() {
    const relPath = path.join(".claude", "settings.json");
    const content = this.readFile(relPath);

    this.check(
      "settings.json exists",
      content !== null,
      `Expected file at ${relPath}`
    );

    if (content === null) {
      const checks = [
        "settings.json is valid JSON",
        "settings.json has PreToolUse hook",
        "settings.json has PostToolUse hook",
        "settings.json has permissions.allow",
        "settings.json has permissions.deny",
      ];
      for (const c of checks) {
        this.check(c, false, "File not found");
      }
      return;
    }

    let data;
    try {
      data = JSON.parse(content);
      this.check("settings.json is valid JSON", true, "");
    } catch (e) {
      this.check("settings.json is valid JSON", false, e.message);
      data = {};
    }

    const hooks = data.hooks || {};
    const preHooks = hooks.PreToolUse || [];
    this.check(
      "settings.json has PreToolUse hook",
      Array.isArray(preHooks) && preHooks.length > 0,
      "hooks.PreToolUse should be a non-empty array"
    );

    const postHooks = hooks.PostToolUse || [];
    this.check(
      "settings.json has PostToolUse hook",
      Array.isArray(postHooks) && postHooks.length > 0,
      "hooks.PostToolUse should be a non-empty array"
    );

    const permissions = data.permissions || {};
    const allow = permissions.allow || [];
    this.check(
      "settings.json has permissions.allow",
      Array.isArray(allow) && allow.length > 0,
      "permissions.allow should be a non-empty array"
    );

    const deny = permissions.deny || [];
    this.check(
      "settings.json has permissions.deny",
      Array.isArray(deny) && deny.length > 0,
      "permissions.deny should be a non-empty array"
    );
  }

  validateGithubWorkflow() {
    const relPath = path.join(".github", "workflows", "claude-review.yml");
    const content = this.readFile(relPath);

    this.check(
      "GitHub Actions workflow exists",
      content !== null,
      `Expected file at ${relPath}`
    );

    if (content === null) {
      const checks = [
        "Workflow has pull_request trigger",
        "Workflow uses claude -p",
        "Workflow uses --output-format json",
        "Workflow uses --session for isolation",
        "Workflow posts PR comment with gh pr comment",
      ];
      for (const c of checks) {
        this.check(c, false, "File not found");
      }
      return;
    }

    this.check(
      "Workflow has pull_request trigger",
      content.includes("pull_request"),
      "Should trigger on pull_request events"
    );

    this.check(
      "Workflow uses claude -p",
      content.includes("claude -p"),
      "Should use 'claude -p' for non-interactive review"
    );

    this.check(
      "Workflow uses --output-format json",
      content.includes("--output-format json"),
      "Should output structured JSON results"
    );

    this.check(
      "Workflow uses --session for isolation",
      content.includes("--session"),
      "Should use --session to isolate PR review sessions"
    );

    this.check(
      "Workflow posts PR comment with gh pr comment",
      content.includes("gh pr comment"),
      "Should post review results as a PR comment"
    );
  }

  printReport() {
    console.log();
    console.log(bold("=".repeat(60)));
    console.log(bold("  M25 Lab — Claude Code Configuration Validator"));
    console.log(bold("=".repeat(60)));
    console.log();

    const groupNames = {
      "Project CLAUDE.md": "Step 1: Project-Level CLAUDE.md",
      "API CLAUDE.md": "Step 2: Directory-Level CLAUDE.md",
      "Slash command": "Step 3: Custom Slash Command",
      "settings.json": "Step 4: Settings with Hooks",
      "GitHub Actions": "Step 5: GitHub Actions CI",
      Workflow: "Step 5: GitHub Actions CI",
    };

    let currentGroup = null;

    for (const { ok, name, detail } of this.results) {
      // Determine group
      let group = null;
      for (const [prefix, gname] of Object.entries(groupNames)) {
        if (name.startsWith(prefix)) {
          group = gname;
          break;
        }
      }

      if (group && group !== currentGroup) {
        currentGroup = group;
        console.log(`\n  ${bold(group)}`);
      }

      const icon = ok ? green("  [PASS]") : red("  [FAIL]");
      console.log(`  ${icon} ${name}`);
      if (!ok && detail) {
        console.log(`         ${detail}`);
      }
    }

    console.log();
    console.log(bold("-".repeat(60)));
    const total = this.passed + this.failed;
    const failStr = this.failed
      ? red(`${this.failed} failed`)
      : green("0 failed");
    console.log(
      `  Results: ${green(`${this.passed} passed`)}, ${failStr}, ${total} total`
    );

    if (this.failed === 0) {
      console.log(
        `\n  ${green("All checks passed! Your configuration is complete.")}`
      );
    } else {
      console.log(
        `\n  ${red(`${this.failed} check(s) need attention. Review the TODOs above.`)}`
      );
    }
    console.log(bold("=".repeat(60)));
    console.log();
  }

  run() {
    this.validateProjectClaudeMd();
    this.validateApiClaudeMd();
    this.validateSlashCommand();
    this.validateSettings();
    this.validateGithubWorkflow();
    this.printReport();
    return this.failed === 0 ? 0 : 1;
  }
}

// --- Main ---
function main() {
  let baseDir = ".";
  const args = process.argv.slice(2);
  const dirIdx = args.indexOf("--dir");
  if (dirIdx !== -1 && dirIdx + 1 < args.length) {
    baseDir = args[dirIdx + 1];
  }

  if (!fs.existsSync(baseDir) || !fs.statSync(baseDir).isDirectory()) {
    console.error(`Error: directory '${baseDir}' does not exist.`);
    process.exit(1);
  }

  const validator = new Validator(baseDir);
  const exitCode = validator.run();
  process.exit(exitCode);
}

main();
