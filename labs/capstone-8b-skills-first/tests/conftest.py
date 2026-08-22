"""Shared pytest configuration.

Tests import from `solution/` by default. To run them against your own
work instead:

    TEST_TARGET=starter pytest tests/ -v

That is the point of the switch -- the same test suite grades the
reference implementation and the student's, so "the tests pass" means the
same thing in both cases.

Skills-first note: the bundled skill scripts are loaded by path rather than
by package import, because `.claude/skills/<name>/scripts/` is deliberately
not on `sys.path`. A skill script has to be runnable by an agent holding
nothing but the file, so it must not depend on the project's import layout.
`load_skill_script` below is how the tests reach them without breaking that.
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.environ.get("TEST_TARGET", "solution")

sys.path.insert(0, os.path.join(ROOT, TARGET))

SKILLS_DIR = os.path.join(ROOT, TARGET, ".claude", "skills")

# The five skills this architecture is built from, and the scripts each
# bundles. Kept here rather than globbed so that a skill silently
# disappearing is a test failure rather than a smaller test run.
EXPECTED_SKILLS = {
    "oracle-pg-typing": ["check_mapping.py"],
    "plsql-conversion": [],
    "appsql-rewriting": ["find_oracleisms.py"],
    "nullability-preservation": ["compare_nulls.py"],
    "migration-validation": ["compare_checksums.py"],
}


def load_skill_script(skill: str, script: str):
    """Import a script bundled with a skill, by path.

    Returns the loaded module. Raises if the file is missing, which is the
    correct behaviour: a skill whose script has gone is broken, not skippable.
    """
    path = os.path.join(SKILLS_DIR, skill, "scripts", script)
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    name = f"skill_{skill.replace('-', '_')}_{script[:-3]}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def pytest_configure(config):
    config.addinivalue_line("markers", "requires_db: needs live Oracle and PostgreSQL")
    print(f"\n[conftest] testing against: {TARGET}/")
    print(f"[conftest] skills dir: {os.path.relpath(SKILLS_DIR, ROOT)}")


@pytest.fixture(scope="session")
def skills_dir():
    return SKILLS_DIR


@pytest.fixture(scope="session")
def type_mapping():
    return load_skill_script("oracle-pg-typing", "check_mapping.py")


@pytest.fixture(scope="session")
def oracleisms():
    return load_skill_script("appsql-rewriting", "find_oracleisms.py")


@pytest.fixture(scope="session")
def nulls():
    return load_skill_script("nullability-preservation", "compare_nulls.py")


@pytest.fixture(scope="session")
def checksums():
    return load_skill_script("migration-validation", "compare_checksums.py")


@pytest.fixture
def artifact_dir(tmp_path, monkeypatch):
    """Point config.ARTIFACT_DIR at a temp dir so tests never write into
    the real artifacts/ folder."""
    import config

    monkeypatch.setattr(config, "ARTIFACT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def audit_log_path(tmp_path, monkeypatch):
    import config

    # Named ..._path, not `audit_log`: `hooks.audit_log` is a function the
    # tests import and call, and a fixture of the same name shadows it at
    # collection time -- the test then awaits a PathLib object.
    path = tmp_path / "migration_audit.jsonl"
    monkeypatch.setattr(config, "AUDIT_LOG", str(path))
    return path


@pytest.fixture
def no_cutover_approval(monkeypatch):
    import config

    monkeypatch.setattr(config, "CUTOVER_APPROVED", False)
    return config
