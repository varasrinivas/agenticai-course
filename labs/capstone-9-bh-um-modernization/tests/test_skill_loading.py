"""Skills carry knowledge and recipes; agents carry control flow and safety.

`.claude/skills/` is new to this lab corpus, so these tests pin the contract:
frontmatter that matches the directory, bundled references and scripts that
exist and run, and -- the part that actually matters -- ONE source of truth for
the domain rather than the same ontology pasted into eight subagent prompts.
"""

import os
import re
import subprocess
import sys

import pytest

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE = os.path.join(LAB, "solution", ".claude")
SKILLS = os.path.join(CLAUDE, "skills")
AGENTS = os.path.join(CLAUDE, "agents")

EXPECTED_SKILLS = {"behavioral-health-um", "umlite-architecture",
                   "rules-to-dmn", "decompose-transaction"}
EXPECTED_AGENTS = {"architecture-cartographer", "monolith-archaeologist",
                   "jsp-archaeologist", "rules-extractor", "gap-analyst",
                   "repo-synthesizer", "frontend-synthesizer", "parity-validator"}


def frontmatter(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no frontmatter"
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def body(path: str) -> str:
    text = open(path, encoding="utf-8").read()
    return re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)


# ------------------------------------------------------------- structure


def test_every_expected_skill_exists():
    found = {d for d in os.listdir(SKILLS)
             if os.path.isfile(os.path.join(SKILLS, d, "SKILL.md"))}
    assert found == EXPECTED_SKILLS


def test_every_expected_agent_exists():
    found = {f[:-3] for f in os.listdir(AGENTS) if f.endswith(".md")}
    assert found == EXPECTED_AGENTS


@pytest.mark.parametrize("skill", sorted(EXPECTED_SKILLS))
def test_skill_frontmatter_matches_its_directory(skill):
    fm = frontmatter(os.path.join(SKILLS, skill, "SKILL.md"))
    assert fm["name"] == skill
    assert len(fm.get("description", "")) > 40, \
        "the description is what decides whether the skill gets loaded"


@pytest.mark.parametrize("agent", sorted(EXPECTED_AGENTS))
def test_agent_frontmatter_matches_its_filename(agent):
    fm = frontmatter(os.path.join(AGENTS, f"{agent}.md"))
    assert fm["name"] == agent
    assert fm.get("description")
    assert fm.get("model")


@pytest.mark.parametrize("agent", sorted(EXPECTED_AGENTS))
def test_every_agent_declares_narrow_tools(agent):
    """A subagent with every tool is a coordinator with a different name."""
    fm = frontmatter(os.path.join(AGENTS, f"{agent}.md"))
    tools = [t.strip() for t in fm["tools"].split(",")]
    assert tools, f"{agent} declares no tools"
    assert len(tools) <= 8, f"{agent} declares {len(tools)} tools"
    for t in tools:
        assert t.startswith("mcp__"), f"{agent}: {t} is not an MCP tool"


# ---------------------------------------------------- bundled references


def test_the_domain_skill_bundles_its_references():
    refs = os.path.join(SKILLS, "behavioral-health-um", "references")
    found = {f for f in os.listdir(refs) if f.endswith(".md")}
    assert found == {"asam-levels.md", "part2-redisclosure.md",
                     "bh-code-sets.md", "parity-nqtl.md"}


def test_every_referenced_file_exists():
    """A skill pointing at a file that is not there teaches nothing twice."""
    missing = []
    for skill in EXPECTED_SKILLS:
        d = os.path.join(SKILLS, skill)
        text = open(os.path.join(d, "SKILL.md"), encoding="utf-8").read()
        for rel in re.findall(r"`(references/[\w./-]+|scripts/[\w./-]+)`", text):
            if not os.path.exists(os.path.join(d, rel)):
                missing.append(f"{skill}/{rel}")
    assert missing == []


def test_the_main_skill_stays_short_and_routes_to_its_references():
    """The whole argument for a skill over a pasted prompt is that the bulk
    stays out of context until it is needed."""
    d = os.path.join(SKILLS, "behavioral-health-um")
    main = len(open(os.path.join(d, "SKILL.md"), encoding="utf-8").read())
    refs = sum(len(open(os.path.join(d, "references", f), encoding="utf-8").read())
               for f in os.listdir(os.path.join(d, "references")))
    assert refs > main, "the references should carry more than the entry point"
    text = open(os.path.join(d, "SKILL.md"), encoding="utf-8").read()
    assert "Load it when" in text, "the entry point must say when to load each reference"


# ------------------------------------------------------- bundled scripts


def test_the_code_validator_runs():
    script = os.path.join(SKILLS, "behavioral-health-um", "scripts",
                          "validate_bh_codes.py")
    r = subprocess.run([sys.executable, script, "--service", "H0018",
                        "--diagnosis", "F10.20"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "clean" in r.stdout


def test_the_code_validator_catches_a_bad_code():
    script = os.path.join(SKILLS, "behavioral-health-um", "scripts",
                          "validate_bh_codes.py")
    r = subprocess.run([sys.executable, script, "--diagnosis", "M54.5"],
                       capture_output=True, text=True)
    assert r.returncode == 1
    assert "not a structurally valid ICD-10".lower() in r.stdout.lower()


def test_the_overlap_checker_finds_the_branch_seven_overlap(tmp_path):
    """The bundled script and the solution's own engine must agree about the
    one case the whole lab turns on."""
    import json
    script = os.path.join(SKILLS, "rules-to-dmn", "scripts", "dmn_overlap.py")
    ir = tmp_path / "ir.json"
    ir.write_text(json.dumps({
        "hit_policy": "FIRST",
        "branches": [
            {"id": "B7a", "kind": "committing",
             "condition": "score >= 10 and dim1 >= 3",
             "outputs": {"loc": "3.7"}},
            {"id": "B7b", "kind": "committing", "condition": "score >= 8",
             "outputs": {"loc": "3.5"}},
        ],
        "overlaps": [],
    }), encoding="utf-8")

    r = subprocess.run([sys.executable, script, "--ir", str(ir)],
                       capture_output=True, text=True)
    assert r.returncode == 1, "unresolved overlaps must be a non-zero exit"
    assert "B7a" in r.stdout and "B7b" in r.stdout
    assert "dim1=3" in r.stdout and "score=10" in r.stdout


def test_the_overlap_checker_never_reports_a_false_clean(tmp_path):
    """A condition it cannot model must be reported as unanalysed, not passed.

    A false 'no overlap' is the one answer this script must never give.
    """
    import json
    script = os.path.join(SKILLS, "rules-to-dmn", "scripts", "dmn_overlap.py")
    ir = tmp_path / "ir.json"
    ir.write_text(json.dumps({
        "hit_policy": "UNIQUE",
        "branches": [{"id": "R1", "kind": "committing",
                      "condition": "someFunction(x) and y in [1,2,3]",
                      "outputs": {"loc": "3.5"}}],
        "overlaps": [],
    }), encoding="utf-8")
    r = subprocess.run([sys.executable, script, "--ir", str(ir)],
                       capture_output=True, text=True)
    assert r.returncode == 1
    assert "could not be analysed" in r.stdout
    assert "cleared" in r.stdout, "an unanalysable row must not read as cleared"


# ----------------------------------------------- one source of truth


def test_the_domain_ontology_is_not_pasted_into_agent_prompts():
    """The anti-pattern the skill exists to prevent.

    If the ASAM ladder were copied into eight subagent prompts it would drift
    the moment one was edited, and cost tokens on every turn.
    """
    offenders = []
    for f in os.listdir(AGENTS):
        text = open(os.path.join(AGENTS, f), encoding="utf-8").read()
        # A full level table pasted into a prompt would carry several of these.
        levels = len(re.findall(r"\b[234]\.\d\b", text))
        if levels > 4:
            offenders.append(f"{f} ({levels} ASAM levels inline)")
    assert offenders == [], (
        f"domain knowledge is duplicated into agent prompts: {offenders}. "
        f"It belongs in the behavioral-health-um skill.")


def test_agents_that_need_the_domain_load_the_skill():
    needs = {"architecture-cartographer", "monolith-archaeologist",
             "jsp-archaeologist", "rules-extractor", "repo-synthesizer",
             "frontend-synthesizer"}
    for agent in needs:
        text = open(os.path.join(AGENTS, f"{agent}.md"), encoding="utf-8").read()
        assert "behavioral-health-um" in text, \
            f"{agent} reads or writes domain material but never loads the skill"


def test_the_recipe_skills_are_loaded_by_the_agents_that_run_them():
    pairs = {
        "rules-extractor": "rules-to-dmn",
        "monolith-archaeologist": "decompose-transaction",
        "repo-synthesizer": "decompose-transaction",
    }
    for agent, skill in pairs.items():
        text = open(os.path.join(AGENTS, f"{agent}.md"), encoding="utf-8").read()
        assert skill in text, f"{agent} should load {skill}"
