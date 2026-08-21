"""Shared pytest configuration.

Tests import from `solution/` by default. To run them against your own
work instead:

    TEST_TARGET=starter pytest tests/ -v

That is the point of the switch -- the same test suite grades the
reference implementation and the student's, so "the tests pass" means the
same thing in both cases.
"""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.environ.get("TEST_TARGET", "solution")

sys.path.insert(0, os.path.join(ROOT, TARGET))


def pytest_configure(config):
    config.addinivalue_line("markers", "requires_db: needs live Oracle and PostgreSQL")
    print(f"\n[conftest] testing against: {TARGET}/")


@pytest.fixture
def artifact_dir(tmp_path, monkeypatch):
    """Point config.ARTIFACT_DIR at a temp dir so tests never write into
    the real artifacts/ folder."""
    import config

    monkeypatch.setattr(config, "ARTIFACT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def audit_log(tmp_path, monkeypatch):
    import config

    path = tmp_path / "migration_audit.jsonl"
    monkeypatch.setattr(config, "AUDIT_LOG", str(path))
    return path


@pytest.fixture
def no_cutover_approval(monkeypatch):
    import config

    monkeypatch.setattr(config, "CUTOVER_APPROVED", False)
    return config
