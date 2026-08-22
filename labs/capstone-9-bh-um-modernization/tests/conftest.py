"""Shared fixtures.

`solution/` is put on the path so the tests import the real modules rather than
a copy. Nothing here needs an API key: every module the tests exercise is
either SDK-free by design (rules_ir, gap_register, seam_map, condition) or
imports the SDK only for its permission types.
"""

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(ROOT)
# Point BH_SOLUTION_DIR at "starter" to run this suite against your own work
# instead of the reference: BH_SOLUTION_DIR=starter pytest tests/ -q
SOLUTION = os.path.join(LAB, os.environ.get("BH_SOLUTION_DIR", "solution"))
# evaluation/ carries the reference answers the 9B tests build from. Both go on
# the path HERE rather than in each test module, so pointing SOLUTION at
# starter/ is enough to run this whole suite against a student's work.
for _p in (SOLUTION, os.path.join(SOLUTION, "evaluation")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


@pytest.fixture(scope="session")
def lab_root():
    return LAB


@pytest.fixture(scope="session")
def legacy_root():
    return os.path.join(LAB, "bhauthtrack")


@pytest.fixture(scope="session")
def reference_root():
    return os.path.join(LAB, "reference-umlite")


@pytest.fixture(scope="session")
def reference_ir():
    """The reference answer for the rules conversion."""
    path = os.path.join(SOLUTION, "evaluation", "reference_rules_ir.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="session")
def golden():
    """(case, expected, meta) for every golden case."""
    import rules_ir
    return rules_ir.load_golden()


@pytest.fixture(scope="session")
def golden_cases(golden):
    return [c for c, _e, _m in golden]


@pytest.fixture
def artifacts(tmp_path, monkeypatch):
    """An isolated artifact directory, so tests never touch a real run."""
    import config
    d = tmp_path / "artifacts"
    d.mkdir()
    monkeypatch.setattr(config, "ARTIFACT_DIR", str(d))
    return str(d)


@pytest.fixture
def emit_root(tmp_path, monkeypatch):
    import config
    d = tmp_path / "bh-um-lite"
    d.mkdir()
    monkeypatch.setattr(config, "EMIT_ROOT", str(d))
    return str(d)


NARRATIVE = (
    "Member presents following a third emergency department contact this quarter. "
    "Reports escalating passive ideation with a specific plan disclosed at triage. "
    "Outpatient contact has been irregular. Requesting medically monitored "
    "inpatient care for stabilisation."
)


@pytest.fixture
def narrative():
    """Realistic clinical prose. Synthetic -- taken from the seed fixture."""
    return NARRATIVE
