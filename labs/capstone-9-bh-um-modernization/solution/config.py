"""Configuration for the behavioral-health UM modernization agent.

Everything that could differ between a laptop, CI and a cloud run lives here.
Nothing in this file is a secret.

Two settings deserve a second look before you change them:

`PHI_ALLOWLIST` is what the protected-content gate will let through. It names
the synthetic fixtures and nothing else. Widening it defeats the "no PHI in
prompts, ever" constraint, which is the reason an agent can be pointed at this
codebase at all.

`FINALIZATION_APPROVED` is read from the environment and never written by this
process. That asymmetry is the human-in-the-loop gate: the agent can see
whether a human approved, and has no way to become approved.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


# `.env` is read here rather than through python-dotenv, so the lab keeps its
# two dependencies. Real environment variables always win: a key exported in
# the shell should not be silently overridden by a stale file.
def _load_env_file(path: str) -> None:
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return  # no .env is the normal case in CI and in Docker
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip().strip(chr(34)).strip(chr(39))
        if name and name not in os.environ:
            os.environ[name] = value


_load_env_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


def _env(name: str, default: str | None = None, *, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(
            f"{name} is not set. Copy .env.example to .env and fill it in, "
            f"or export {name} before running."
        )
    return value or ""


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


# ---------------------------------------------------------------- models
# Routing is by difficulty, not by importance. The reading and reasoning
# phases get Sonnet; validation is mechanical checking against artifacts that
# already exist, so it gets Haiku.
COORDINATOR_MODEL = _env("COORDINATOR_MODEL", "claude-sonnet-4-6")
REASONING_MODEL = _env("REASONING_MODEL", "claude-sonnet-4-6")
MECHANICAL_MODEL = _env("MECHANICAL_MODEL", "claude-haiku-4-5-20251001")

MAX_TURNS = int(_env("MAX_TURNS", "24"))

# Abort rather than discover a runaway loop on the invoice.
TOKEN_BUDGET = int(_env("COST_CEILING_OUTPUT_TOKENS", "400000"))
CIRCUIT_BREAKER_THRESHOLD = int(_env("CIRCUIT_BREAKER_CONSECUTIVE_FAILURES", "3"))


# ----------------------------------------------------------------- paths
def _here(*parts: str) -> str:
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), *parts))


# The two source trees. Read-only, enforced by hook rather than by convention:
# they are evidence, and a parity validator that diffs against a tree the agent
# can edit is diffing against a moving target.
REFERENCE_ROOT = _env("BH_REFERENCE_ROOT", _here("..", "reference-umlite"))
LEGACY_ROOT = _env("BH_LEGACY_ROOT", _here("..", "bhauthtrack"))

# The only writable path. `confine_writes` denies everything else.
EMIT_ROOT = _env("BH_EMIT_ROOT", _here("..", "bh-um-lite"))

ARTIFACT_DIR = _env("ARTIFACT_DIR", _here("..", "artifacts"))
AUDIT_LOG = _env("AUDIT_LOG", _here("..", "modernization_audit.jsonl"))
SESSION_STATE = os.path.join(ARTIFACT_DIR, "session_state.json")

# The reference platform's own enhancement backlog. The gap analyst
# cross-checks against it -- agreement is signal, disagreement is something to
# investigate. It lives outside the vendored copy because it is a governance
# document, not source.
BACKLOG_PATH = _env("BH_BACKLOG_PATH", _here("..", "reference-umlite", "BACKLOG.md"))


# ------------------------------------------------------- protected content
# Paths whose narrative-shaped content may reach the model. Everything here is
# synthetic, generated from a documented seed. Nothing else is allowlisted.
PHI_ALLOWLIST = tuple(
    os.path.normpath(p.strip())
    for p in _env("PHI_ALLOWLIST", os.path.join(LEGACY_ROOT, "db", "02_seed.sql")).split(os.pathsep)
    if p.strip()
)

# Characters of narrative permitted through in one tool result, even from an
# allowlisted fixture. Enough to reason about shape; not enough to accumulate a
# clinical record in the transcript.
NARRATIVE_EXCERPT_BUDGET = int(_env("NARRATIVE_EXCERPT_BUDGET", "400"))


# ------------------------------------------------------------------ gate
# Set by --approve on the CLI, which sets the environment variable this process
# reads. The agent cannot set it: that is the entire point.
FINALIZATION_APPROVED = _flag("BH_FINALIZATION_APPROVED")


# ----------------------------------------------------------------- phases
PHASES_9A = ["map", "excavate", "extract_rules", "gap_analyse", "synthesize", "validate"]
PHASES_9B = ["synthesize_frontend", "validate_frontend"]

# The seven legacy screens, in the order a reviewer meets them. The frontend
# phase asserts every one has a reachable route.
LEGACY_SCREENS = [
    "worklist.jsp",
    "authSubmit.jsp",
    "authDetail.jsp",
    "decision.jsp",
    "locReview.jsp",
    "consentAdmin.jsp",
    "search.jsp",
]

# The transactional method the seam map must account for. Named here so the
# test suite can assert it was analysed rather than skipped.
CRITICAL_TRANSACTION = "AuthCaseService.submitAndDecide"

# Golden cases from db/02_seed.sql. 500001 is the branch-7 overlap and is the
# one case that distinguishes a hit-policy decision from a lucky guess.
GOLDEN_CASES = [500001, 500002, 500003, 500004, 500005, 500006,
                500007, 500008, 500009, 500010, 500011, 500012]
OVERLAP_CASE = 500001
