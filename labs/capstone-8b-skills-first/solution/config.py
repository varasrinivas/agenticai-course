"""Configuration for the Oracle -> PostgreSQL migration agent.

Everything that could differ between a laptop, CI, and a cloud run lives
here. Nothing in this file is a secret: credentials are read from the
environment, never hardcoded, and the audit hook redacts them before
anything is written to disk.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(name: str, default: str | None = None, *, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(
            f"{name} is not set. Copy .env.example to .env and fill it in, "
            f"or export {name} before running."
        )
    return value or ""


# --------------------------------------------------------------- models
# Hard reasoning (reading DDL, converting PL/SQL) gets Sonnet.
# High-volume mechanical work gets Haiku. Routing by difficulty rather
# than by "important vs unimportant" is what keeps the bill sane on a
# migration with hundreds of objects.
COORDINATOR_MODEL = _env("COORDINATOR_MODEL", "claude-sonnet-4-6")
REASONING_MODEL = _env("REASONING_MODEL", "claude-sonnet-4-6")
MECHANICAL_MODEL = _env("MECHANICAL_MODEL", "claude-haiku-4-5-20251001")

MAX_TURNS = int(_env("MAX_TURNS", "20"))
MAX_OUTPUT_TOKENS = int(_env("MAX_OUTPUT_TOKENS", "8192"))

# Abort the whole run rather than discover a runaway loop on the invoice.
TOKEN_BUDGET = int(_env("TOKEN_BUDGET", "400000"))
CIRCUIT_BREAKER_THRESHOLD = int(_env("CIRCUIT_BREAKER_THRESHOLD", "3"))


# ------------------------------------------------------------ databases
@dataclass(frozen=True)
class OracleConfig:
    """Source. Read-only by grant AND by hook -- see hooks.py."""

    user: str = field(default_factory=lambda: _env("ORACLE_USER", "migration_reader"))
    password: str = field(default_factory=lambda: _env("ORACLE_PASSWORD", "ReadOnly#2026"))
    dsn: str = field(default_factory=lambda: _env("ORACLE_DSN", "oracle:1521/FREEPDB1"))
    schema: str = field(default_factory=lambda: _env("ORACLE_SCHEMA", "MERIDIAN"))


@dataclass(frozen=True)
class PostgresConfig:
    """Target."""

    host: str = field(default_factory=lambda: _env("PG_HOST", "postgres"))
    port: int = field(default_factory=lambda: int(_env("PG_PORT", "5432")))
    database: str = field(default_factory=lambda: _env("PG_DATABASE", "meridian"))
    user: str = field(default_factory=lambda: _env("PG_USER", "migration"))
    password: str = field(default_factory=lambda: _env("PG_PASSWORD", "migration"))
    # Every generated object lands here first. The cutover renames this
    # schema to `public` -- which is why nothing may be created outside
    # it, and why the PreToolUse guard enforces that.
    target_schema: str = field(default_factory=lambda: _env("PG_TARGET_SCHEMA", "ucc_migrated"))

    def dsn(self) -> str:
        return (
            f"host={self.host} port={self.port} dbname={self.database} "
            f"user={self.user} password={self.password}"
        )


ORACLE = OracleConfig()
POSTGRES = PostgresConfig()


# ------------------------------------------------------------- paths
ARTIFACT_DIR = _env("ARTIFACT_DIR", "artifacts")
AUDIT_LOG = _env("AUDIT_LOG", "migration_audit.jsonl")
SESSION_STATE = os.path.join(ARTIFACT_DIR, "session_state.json")
APP_SOURCE_DIR = _env("APP_SOURCE_DIR", "../app")

# Set by --approve-cutover on the CLI. The agent cannot set this itself:
# that is the entire point of the human-in-the-loop gate.
CUTOVER_APPROVED = os.environ.get("CUTOVER_APPROVED", "").lower() in {"1", "true", "yes"}

# When true, the oracle_* tools replay canned responses from
# legacy-oracle/fixtures/ instead of connecting. For students whose
# hardware cannot run the Oracle container.
FIXTURE_MODE = os.environ.get("FIXTURE_MODE", "").lower() in {"1", "true", "yes"}
FIXTURE_DIR = _env("FIXTURE_DIR", "../legacy-oracle/fixtures")

BATCH_SIZE = int(_env("BATCH_SIZE", "10000"))

# The six tables, largest first. Migrating the big one first means a
# capacity or encoding problem surfaces in minute two, not minute forty.
MIGRATION_ORDER = [
    "UCC_DEBTOR",
    "UCC_FILING",
    "UCC_SECURED_PARTY",
    "UCC_AMENDMENT",
    "FILING_AUDIT",
    "STATE_SOS_SOURCE",
]

PLSQL_OBJECTS = [
    "PKG_RISK_CALC",
    "PKG_FILING_MAINT",
    "TRG_FILING_BI",
    "TRG_FILING_NORMALIZE_BI",
]
