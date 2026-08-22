"""Guardrails.

Five, in order of how much damage they prevent:

  1. `protected_content_gate`      -- clinical narrative never reaches the model.
  2. `enforce_source_readonly`     -- neither source tree can be written.
  3. `confine_writes`              -- output lands only under bh-um-lite/.
  4. `hitl_finalization_gate`      -- the agent cannot approve its own work.
  5. `audit_log`                   -- everything that happened, redacted.

The first four are `can_use_tool` denials, and that is the important detail:
they run BEFORE the tool executes and return `PermissionResultDeny`, so the
call never happens. A hook that logged the disclosure after the fact would be a
good post-mortem and a bad guardrail.

Hook 1 is the one worth reading twice. It inspects tool RESULTS, not just
inputs, because the risk here is not the agent doing something dangerous -- it
is the agent being *told* something it must not be told. Once protected content
is in the context window it is in the transcript, in the provider's logs, and
in any summary that follows. There is no taking it back.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

import config

# ---------------------------------------------------------------------
# 1. Protected content never reaches the model.
# ---------------------------------------------------------------------
# Detection is by SHAPE, not by keyword. A clinical narrative does not announce
# itself; it is a run of prose sentences using clinical register. Keyword
# matching on "alcohol" or "opioid" catches the obvious cases and misses
# everything written by a clinician in a hurry.
#
# Deliberately over-eager. A gate that blocks a config comment is annoying; one
# that passes a treatment record is an unlawful disclosure.

# A clinical subject followed, nearby, by a clinical verb or noun.
#
# THE LIMIT OF THIS APPROACH, STATED PLAINLY: shape detection is defence in
# depth, not a proof. A narrative written without any of these words will pass,
# and no regex closes that gap. The control that actually holds is that every
# fixture in this lab is SYNTHETIC -- this gate is the second line, for the day
# someone points the agent at a tree that is not.
#
# The subject list is broader than it first looks for a reason: clinicians write
# "the individual", "the patient", "he reports", and a pattern that only knew
# "member" missed prose that was obviously clinical to any human reader.
_CLINICAL_REGISTER = re.compile(
    r"\b(member|patient|client|individual|resident|he|she|they)\b.{0,100}\b("
    r"present(s|ed|ing)?|report(s|ed|ing)?|denie[sd]|admit(s|ted)|"
    r"disclos(e|ed|ure)|assess(ed|ment)|ideation|withdrawal|relapse|"
    r"intoxicat|detox|sober|abstinen|craving|discharge[sd]?|"
    r"treatment|therapy|counsel(ling|ing)?|episode|referral|admission|"
    r"engagement|symptom|dose|medication|prescrib|diagnos|"
    r"seen (twice|once|weekly|daily)|follow.?up"
    r")\b",
    re.I | re.S,
)

# Column and field names whose *values* are protected wherever they appear.
_NARRATIVE_FIELDS = re.compile(
    r"\b(clinical_?narrative|clinicalNarrative|narrative|chief_?complaint|"
    r"clinical_?notes?|hpi|progress_?note)\b",
    re.I,
)

# Prose-shaped: several sentences of words, not code and not a column list.
#
# The trailing \s* rather than \s+ matters. With \s+ the LAST sentence of a
# narrative goes unmatched -- there is no whitespace after its full stop -- so
# redaction leaves one clinical sentence standing. That was a real leak, found
# by running the gate over the seed fixture rather than over a mock.
_PROSE = re.compile(r"(?:[A-Z][^.!?\n]{25,}[.!?]\s*){2,}")


def _norm(path: str) -> str:
    return os.path.normpath(os.path.abspath(path))


_ALLOWLIST = tuple(_norm(p) for p in config.PHI_ALLOWLIST)


def is_allowlisted(path: str | None) -> bool:
    """Only the synthetic fixtures may carry narrative-shaped content."""
    if not path:
        return False
    target = _norm(path)
    return any(target == a or target.startswith(a + os.sep) for a in _ALLOWLIST)


def looks_like_protected_content(text: str) -> bool:
    """Does this look like clinical narrative rather than code or config?"""
    # --------------------------------------------------------------------
    # TODO 13 -- Detect clinical narrative by SHAPE, not by keyword.
    #
    # A narrative does not announce itself. Matching on "alcohol" or "opioid"
    # catches the obvious cases and misses everything a clinician wrote in a
    # hurry.
    #
    # Prose in clinical register, or a narrative field name next to prose. Be
    # deliberately over-eager: a gate that blocks a config comment is annoying;
    # one that passes a treatment record is an unlawful disclosure.
    #
    # AND STATE THE LIMIT. This is defence in depth, not a proof. The control
    # that actually holds is that every fixture here is synthetic.
    #
    # Verify: tests/test_no_phi_in_prompt.py
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


def _source_path_of(tool_input: dict) -> str | None:
    for key in ("path", "file", "relative_path", "fqcn", "view", "object_name", "source"):
        v = tool_input.get(key)
        if isinstance(v, str) and v:
            return v
    return None


def redact_narrative(text: str) -> str:
    """Replace narrative-shaped runs with a tagged marker.

    Tagged rather than removed: the model needs to know that something was
    withheld and why, or it will conclude the field is empty and report the
    clinical narrative as absent -- which is exactly the wrong finding.
    """
    # --------------------------------------------------------------------
    # TODO 14 -- Replace narrative-shaped runs with a TAGGED marker.
    #
    # Tagged, not removed. Silently removing it leads the model to conclude the
    # field is empty and report the clinical narrative as absent, which is the
    # opposite of the finding.
    #
    # Watch the last sentence of a paragraph. A pattern requiring whitespace
    # after the final full stop leaves one clinical sentence standing, and one
    # sentence is a disclosure.
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


def excerpt(text: str, budget: int | None = None) -> str:
    limit = budget if budget is not None else config.NARRATIVE_EXCERPT_BUDGET
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n[... {len(text) - limit} chars withheld: excerpt budget]"


async def protected_content_gate(tool_name: str, tool_input: dict, context: Any):
    """PreToolUse on every tool.

    Matches `.*` deliberately. Scoping this to the legacy server would miss
    content arriving by any other path -- a Read of a file, a Bash cat, a tool
    added next month.
    """
    path = _source_path_of(tool_input)

    # An input that itself carries narrative is the agent about to write
    # protected content somewhere. Deny regardless of destination.
    for key in ("content", "text", "payload", "case_json", "evidence"):
        value = tool_input.get(key)
        if isinstance(value, str) and looks_like_protected_content(value):
            if not is_allowlisted(path):
                return PermissionResultDeny(
                    message=(
                        f"Protected clinical content blocked in {key!r}.\n"
                        f"This run operates under 'no PHI in prompts, ever'. Clinical "
                        f"narrative may not be copied into artifacts, prompts, logs or "
                        f"events.\n"
                        f"Work from the SHAPE of the field -- its name, type, nullability "
                        f"and which sinks it reaches -- not from its contents. You do not "
                        f"need to read a narrative to determine that it is discarded."
                    )
                )

    return PermissionResultAllow()


def filter_tool_result(tool_name: str, tool_input: dict, result_text: str) -> tuple[str, bool]:
    """Inspect a tool RESULT before it reaches the model.

    Returns (text, was_modified).

    Called by the tool servers themselves rather than by a PreToolUse hook,
    because a PreToolUse hook runs before the tool and therefore cannot see
    what it returns. That is a real limitation and this is the honest way
    around it: the guarantee lives at the boundary where the data actually
    appears.
    """
    # --------------------------------------------------------------------
    # TODO 15 -- Inspect a tool RESULT before it reaches the model.
    #
    # A PreToolUse hook runs before the tool and cannot see what it returns, so
    # this guarantee lives at the boundary where the data actually appears.
    #
    # Allowlisted synthetic fixture -> allowed through, but BUDGETED. An agent
    # reading the whole seed file accumulates a clinical record in its
    # transcript one tool call at a time.
    # Anything else -> redacted, and say which path was refused.
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


# ---------------------------------------------------------------------
# 2. Both source trees are read-only.
# ---------------------------------------------------------------------
# These servers expose no write tools at all, so this hook is defence in depth.
# What it actually catches is path traversal: a `path` of "../../etc/passwd" or
# "../bhauthtrack/db/01_schema.sql" reaching a read tool that then hands back
# something outside the tree it is supposed to serve.

_READONLY_PREFIXES = {
    "mcp__reference_src__": config.REFERENCE_ROOT,
    "mcp__legacy_src__": config.LEGACY_ROOT,
}


def _escapes(root: str, candidate: str) -> bool:
    resolved = _norm(os.path.join(root, candidate))
    return not (resolved == _norm(root) or resolved.startswith(_norm(root) + os.sep))


async def enforce_source_readonly(tool_name: str, tool_input: dict, context: Any):
    """PreToolUse on mcp__reference_src__* and mcp__legacy_src__*."""
    # --------------------------------------------------------------------
    # TODO 16 -- Deny path traversal out of either source tree.
    #
    # These servers expose no write tools, so this is defence in depth. What it
    # actually catches is `../`.
    #
    # Both trees are EVIDENCE. A parity validator that diffs the port against a
    # tree the agent can reach outside of is diffing against a moving target.
    #
    # Verify: tests/test_hooks_readonly.py
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


# ---------------------------------------------------------------------
# 3. Writes are confined to bh-um-lite/.
# ---------------------------------------------------------------------


async def confine_writes(tool_name: str, tool_input: dict, context: Any):
    """PreToolUse on mcp__local__write_artifact."""
    if not tool_name.endswith("write_artifact"):
        return PermissionResultAllow()

    relative = str(tool_input.get("relative_path") or "").strip()
    if not relative:
        return PermissionResultDeny(message="write_artifact needs a relative_path.")

    if os.path.isabs(relative) or _escapes(config.EMIT_ROOT, relative):
        return PermissionResultDeny(
            message=(
                f"Writes are confined to bh-um-lite/. {relative!r} resolves outside it.\n"
                f"The agent's own configuration is not part of its output: emitting "
                f"subagents or skills into the workspace being modernized confuses "
                f"the tool with the product."
            )
        )
    return PermissionResultAllow()


# ---------------------------------------------------------------------
# 4. The agent cannot approve its own modernization.
# ---------------------------------------------------------------------


def _read_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def finalization_briefing() -> str:
    """What a human needs in front of them to decide.

    Assembled from artifacts rather than from the agent's summary of them, on
    purpose. The agent's account of its own run is the thing under review.
    """
    lines: list[str] = []

    register = _read_json(os.path.join(config.ARTIFACT_DIR, "gap-register.json"))
    if register:
        dist = register.get("distribution", {})
        lines.append("GAP REGISTER: " + ", ".join(f"{k} {v}" for k, v in dist.items()))
        for e in register.get("entries", []):
            if e.get("verdict") == "must-not-port":
                lines.append(f"  MUST-NOT-PORT  {e.get('capability')}")
                lines.append(f"                 harm: {e.get('harm')}")
            elif e.get("verdict") == "must-build-new":
                lines.append(f"  must-build-new {e.get('capability')}")
        for p in register.get("acceptance_problems", []):
            lines.append(f"  ! {p}")
    else:
        lines.append("GAP REGISTER: MISSING -- phase 4 did not complete.")

    parity = _read_json(os.path.join(config.ARTIFACT_DIR, "parity-report.json"))
    if parity:
        lines.append("")
        lines.append(f"PARITY: {parity.get('verdict', 'unknown')}")
        for check in parity.get("checks", []):
            flag = ""
            if check.get("expected_nonzero") and check.get("count") == 0:
                flag = "   <-- clean, and expected non-zero. SUSPECT THE VALIDATOR."
            lines.append(f"  [{check.get('id')}] {check.get('name')}: "
                         f"{check.get('count')}{flag}")
        for b in parity.get("blocking", []):
            lines.append(f"  BLOCKING: {b}")
    else:
        lines.append("")
        lines.append("PARITY: MISSING -- phase 6 did not complete.")

    queue = _read_json(os.path.join(config.ARTIFACT_DIR, "manual-review-queue.json"))
    items = (queue or {}).get("items", [])
    lines.append("")
    lines.append(f"QUEUED FOR HUMAN DECISION: {len(items)}")
    for item in items:
        lines.append(f"  {item.get('artifact')}: {item.get('reason')}")
    if not items:
        lines.append("  NONE -- which for this system means something was guessed at. "
                     "BH_AUTH.LEGACY_OVERRIDE has no surviving documentation and is "
                     "set on roughly 400 live rows.")
    return "\n".join(lines)


async def hitl_finalization_gate(tool_name: str, tool_input: dict, context: Any):
    """PreToolUse on mcp__local__finalize_modernization.

    Denies unless a human set the environment variable by passing --approve.
    The agent reads that variable and cannot write it. That asymmetry is the
    gate; everything else is presentation.
    """
    # --------------------------------------------------------------------
    # TODO 17 -- The agent cannot approve its own modernization.
    #
    # Deny unless a human set the environment variable by passing --approve.
    # The agent reads that variable and has no way to write it; that asymmetry
    # IS the gate.
    #
    # Return the briefing with the denial -- assembled from the artifacts, not
    # from the agent's summary of them. The agent's account of its own run is
    # the thing under review.
    #
    # Verify: tests/test_hitl_gate.py
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


# ---------------------------------------------------------------------
# 5. Audit log.
# ---------------------------------------------------------------------

# The character classes stop at a quote, brace, bracket or comma on purpose.
# A greedy \S+ swallows the JSON that follows the credential -- `password=x"}`
# becomes `password=***` and the surrounding document no longer parses. An
# audit log that crashes on a connection string is worse than no audit log,
# because it fails exactly when something interesting was happening.
_CRED = r"([^\s\"'}\],]+)"

_SECRET_PATTERNS = [
    re.compile(r"(password\s*=\s*)" + _CRED, re.I),
    re.compile(r"(://[^:/\s]+:)([^@/\s]+)(@)"),
    re.compile(r"(sk-ant-[A-Za-z0-9_-]{6})([A-Za-z0-9_-]+)"),
    re.compile(r"(ANTHROPIC_API_KEY\s*=\s*)" + _CRED, re.I),
]

# Credentials of a different kind: a reviewer's licensure is not a secret, but
# it identifies a person against a clinical decision, and an audit log is not
# the place to accumulate that.
_ACTOR_PATTERNS = [
    re.compile(r"(\breviewer_?credential\"?\s*[:=]\s*\"?)([A-Z_]+)", re.I),
    re.compile(r"(\bldap_?dn\"?\s*[:=]\s*\"?)([^\",\s]+)", re.I),
]


def redact(text: str) -> str:
    """Strip credentials, then narrative.

    Deliberately aggressive. An audit log that over-redacts is annoying; one
    that leaks a treatment record into a file someone commits is an incident.
    """
    # --------------------------------------------------------------------
    # TODO 18 -- Strip credentials, then narrative.
    #
    # Careful with greedy patterns: `\S+` after `password=` eats the closing
    # quote and brace, and an audit log that will not parse is worse than none
    # -- it fails exactly when something interesting was happening.
    # --------------------------------------------------------------------
    raise NotImplementedError("see the TODO above")


def redact_values(node: Any) -> Any:
    """Redact string VALUES in place of redacting serialized JSON.

    Redacting the serialized form means a pattern can eat a quote or a brace
    and leave a document that no longer parses. Walking the structure and
    cleaning each string keeps the shape intact whatever the pattern does.
    """
    if isinstance(node, str):
        return redact(node)
    if isinstance(node, dict):
        return {k: redact_values(v) for k, v in node.items()}
    if isinstance(node, (list, tuple)):
        return [redact_values(v) for v in node]
    return node


async def audit_log(tool_name: str, tool_input: dict, tool_response: Any, context: Any):
    """PostToolUse on every tool -- one JSON line per call."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "params": redact_values(tool_input),
        "duration_ms": getattr(context, "duration_ms", None),
    }

    try:
        text = tool_response["content"][0]["text"]
        entry["result_size"] = len(text)
        payload = json.loads(text)
        for key in ("row_count", "returned", "finding_count", "written"):
            if key in payload:
                entry[key] = payload[key]
        if payload.get("error"):
            entry["error"] = redact(str(payload["error"]))[:400]
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        pass

    try:
        os.makedirs(os.path.dirname(config.AUDIT_LOG) or ".", exist_ok=True)
        with open(config.AUDIT_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError as exc:
        print(f"[audit] WARNING: could not append to {config.AUDIT_LOG}: {exc}")


# ---------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------


async def can_use_tool(tool_name: str, tool_input: dict, context: Any):
    """Every PreToolUse guard, in order, first denial wins.

    Order matters: the protected-content gate runs first because a denial for
    any other reason still leaves the question of whether the call would have
    disclosed something.
    """
    for guard in (protected_content_gate, enforce_source_readonly,
                  confine_writes, hitl_finalization_gate):
        result = await guard(tool_name, tool_input, context)
        if isinstance(result, PermissionResultDeny):
            return result
    return PermissionResultAllow()


# ---------------------------------------------------------------------
# Budget and circuit breaker
# ---------------------------------------------------------------------


class TokenBudget:
    """Abort the run rather than discover a runaway loop on the invoice."""

    def __init__(self, ceiling: int | None = None):
        self.ceiling = ceiling if ceiling is not None else config.TOKEN_BUDGET
        self.spent = 0

    def add(self, tokens: int) -> None:
        self.spent += max(0, int(tokens or 0))

    def exceeded(self) -> bool:
        return self.spent >= self.ceiling

    def remaining(self) -> int:
        return max(0, self.ceiling - self.spent)

    def __str__(self) -> str:
        return f"{self.spent:,}/{self.ceiling:,} output tokens"


class CircuitBreaker:
    """Three consecutive failures in one phase halts the run.

    Consecutive, not cumulative: a phase that fails, recovers and fails again
    is having a bad time; one that fails three times running is not going to
    succeed on the fourth, and each attempt costs money and produces another
    plausible-looking partial artifact.
    """

    def __init__(self, threshold: int | None = None):
        self.threshold = threshold if threshold is not None else config.CIRCUIT_BREAKER_THRESHOLD
        self.consecutive = 0
        self.last_error = ""

    def record_success(self) -> None:
        self.consecutive = 0

    def record_failure(self, error: str) -> None:
        self.consecutive += 1
        self.last_error = error

    def tripped(self) -> bool:
        return self.consecutive >= self.threshold
