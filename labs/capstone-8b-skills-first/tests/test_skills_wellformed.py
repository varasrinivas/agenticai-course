"""The skills are well-formed and actually loadable.

This is the test the subagent build does not need and this one cannot do
without. A skill that Claude Code declines to load fails silently: the agent
does not error, it just improvises the type mapping from memory and produces
a migration that looks fine. There is no runtime signal.

So the contract gets asserted here, at build time:

  * frontmatter parses, and `name` matches the directory
  * `description` carries trigger phrases, because that is what decides
    whether the skill is ever loaded
  * `allowed-tools` names only tools that exist in this project
  * no invented frontmatter keys -- notably `context:`, which is not a
    Claude Code field
  * every bundled script imports, and its own --self-test passes
  * every `references/` file a SKILL.md points at is really there

Frontmatter keys are checked against what Claude Code actually reads. The
authority is the shipped skill-development guidance: `name` and
`description` are required, and `version`, `allowed-tools`, `tools`,
`user-invocable`, `license`, `argument-hint` and `disable-model-invocation`
are the optional ones. Anything else is a typo that does nothing.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

import pytest

from conftest import EXPECTED_SKILLS, SKILLS_DIR, load_skill_script

REQUIRED_KEYS = {"name", "description"}

# The rest of the frontmatter contract, taken from Claude Code's own schema
# (v2.1.241) rather than from a survey of published skills -- a key being
# absent from every example is not evidence it is unsupported.
OPTIONAL_KEYS = {
    # shared with slash commands
    "model", "allowed-tools", "disallowed-tools", "argument-hint",
    "disable-model-invocation", "user-invocable", "effort", "shell",
    # skill-only
    "when_to_use",   # extra guidance folded into the Skill tool description
    "paths",         # globs; the skill loads only when matching files are touched
    "hooks",         # hooks registered while the skill is active
    "context",       # "inline" (default) or "fork" -- see CONTEXT_VALUES
    "agent",         # agent type to spawn when context: fork
    "background",    # fork reports back as a task notification instead of blocking
    # internal / bookkeeping, tolerated rather than encouraged
    "version", "arguments", "disallowedTools", "fallback",
    "created_by", "improved_by",
}
KNOWN_KEYS = REQUIRED_KEYS | OPTIONAL_KEYS

# `context` is an enum, and the two values mean very different things:
# inline expands the skill into the current conversation; fork spawns a
# subagent, so the skill gets its own context window and only its result
# comes back.
CONTEXT_VALUES = {"inline", "fork"}

# Tools this project actually provides. An allowed-tools entry outside this
# set is a silent no-op at runtime.
PROJECT_TOOLS = {
    "Read", "Write", "Edit", "Bash", "Grep", "Glob",
    "mcp__oracle_src__oracle_describe_schema",
    "mcp__oracle_src__oracle_get_ddl",
    "mcp__oracle_src__oracle_get_plsql_source",
    "mcp__oracle_src__oracle_sample_rows",
    "mcp__oracle_src__oracle_row_count",
    "mcp__oracle_src__oracle_checksum",
    "mcp__pg_target__pg_apply_ddl",
    "mcp__pg_target__pg_copy_load",
    "mcp__pg_target__pg_query",
    "mcp__pg_target__pg_row_count",
    "mcp__pg_target__pg_checksum",
    "mcp__pg_target__pg_cutover",
    "mcp__migration_local__write_artifact",
}

SKILL_NAMES = sorted(EXPECTED_SKILLS)


def read_frontmatter(path: str) -> tuple[dict, str]:
    """Parse the YAML frontmatter without a YAML dependency.

    Deliberately minimal: it handles the `key: value` and `key: [a, b]`
    shapes these skills use. If a skill ever needs richer YAML, that is a
    signal the frontmatter is doing too much.
    """
    text = open(path, encoding="utf-8").read()
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    assert match, f"{path}: no YAML frontmatter delimited by --- lines"
    raw, body = match.group(1), match.group(2)

    data: dict[str, object] = {}
    key = None
    for line in raw.split("\n"):
        field = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if field:
            key, value = field.group(1), field.group(2).strip()
            if value.startswith("[") and value.endswith("]"):
                data[key] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            else:
                data[key] = value
        elif key and line.strip():
            data[key] = f"{data.get(key, '')} {line.strip()}".strip()
    return data, body


@pytest.fixture(scope="module")
def parsed() -> dict[str, tuple[dict, str]]:
    out = {}
    for skill in SKILL_NAMES:
        path = os.path.join(SKILLS_DIR, skill, "SKILL.md")
        out[skill] = read_frontmatter(path)
    return out


# ------------------------------------------------------------ structure

def test_every_expected_skill_exists():
    found = sorted(
        d for d in os.listdir(SKILLS_DIR)
        if os.path.isfile(os.path.join(SKILLS_DIR, d, "SKILL.md"))
    )
    assert found == SKILL_NAMES, (
        f"skills on disk {found} do not match the expected set {SKILL_NAMES}. "
        f"A skill added without updating conftest.EXPECTED_SKILLS is untested."
    )


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_name_matches_directory(skill, parsed):
    data, _ = parsed[skill]
    assert data.get("name") == skill, (
        f"{skill}: frontmatter name is {data.get('name')!r}. Claude Code "
        f"resolves a skill by directory; a mismatch makes it unreferenceable."
    )


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_required_keys_present(skill, parsed):
    data, _ = parsed[skill]
    assert REQUIRED_KEYS <= set(data), f"{skill}: missing {REQUIRED_KEYS - set(data)}"


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_no_invented_frontmatter_keys(skill, parsed):
    """An unrecognised key is ignored silently rather than rejected.

    That is the whole reason this test exists: a typo'd or invented key does
    not fail, so the skill just quietly behaves nothing like its author
    intended. Validate against the real schema at build time instead.
    """
    data, _ = parsed[skill]
    unknown = set(data) - KNOWN_KEYS
    assert not unknown, (
        f"{skill}: unrecognised frontmatter key(s) {sorted(unknown)}. "
        f"Claude Code ignores unknown keys silently. Known keys: {sorted(KNOWN_KEYS)}"
    )


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_context_value_is_valid_if_present(skill, parsed):
    """`context` is an enum, and the wrong value is silently ignored.

    `inline` expands the skill into the current conversation; `fork` spawns a
    subagent so the skill runs in its own context window. Anything else -- a
    typo, or a value someone assumed existed -- leaves the skill running
    inline while its author believes it is isolated.
    """
    data, _ = parsed[skill]
    if "context" not in data:
        pytest.skip(f"{skill} does not set context (defaults to inline)")
    assert data["context"] in CONTEXT_VALUES, (
        f"{skill}: context is {data['context']!r}; must be one of "
        f"{sorted(CONTEXT_VALUES)}"
    )


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_description_is_a_trigger_not_a_label(skill, parsed):
    """The description is the only thing deciding whether the skill loads."""
    data, _ = parsed[skill]
    description = str(data.get("description", ""))
    assert len(description) >= 120, (
        f"{skill}: description is {len(description)} chars. Too short to carry "
        f"trigger phrases, so the skill will not be matched reliably."
    )
    assert "should be used when" in description.lower(), (
        f"{skill}: description should say when to use the skill, in the third "
        f"person, with the phrases a caller would actually say."
    )


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_allowed_tools_exist(skill, parsed):
    data, _ = parsed[skill]
    declared = data.get("allowed-tools")
    if declared is None:
        pytest.skip(f"{skill} declares no allowed-tools")
    assert isinstance(declared, list) and declared, f"{skill}: empty allowed-tools"
    unknown = sorted(set(declared) - PROJECT_TOOLS)
    assert not unknown, (
        f"{skill}: allowed-tools names {unknown}, which this project does not "
        f"provide. The skill would be silently unable to act."
    )


@pytest.mark.parametrize("skill", SKILL_NAMES)
def test_referenced_files_exist(skill, parsed):
    """A SKILL.md that points at a missing reference sends the agent nowhere."""
    _, body = parsed[skill]
    root = os.path.join(SKILLS_DIR, skill)
    missing = []
    for ref in re.findall(r"`((?:\.\./)?[\w./-]+/(?:references|scripts)/[\w.-]+)`", body):
        candidate = os.path.normpath(os.path.join(root, ref))
        if not os.path.exists(candidate):
            # also allow paths written from the project root
            from_root = os.path.normpath(
                os.path.join(SKILLS_DIR, "..", "..", ref))
            if not os.path.exists(from_root):
                missing.append(ref)
    assert not missing, f"{skill}: SKILL.md references missing files {missing}"


# -------------------------------------------------------------- scripts

SCRIPT_CASES = [
    (skill, script)
    for skill, scripts in sorted(EXPECTED_SKILLS.items())
    for script in scripts
]


@pytest.mark.parametrize("skill,script", SCRIPT_CASES)
def test_bundled_script_imports(skill, script):
    module = load_skill_script(skill, script)
    assert module.__doc__, f"{skill}/{script}: no module docstring"
    assert hasattr(module, "main"), f"{skill}/{script}: no main() -- not runnable"


@pytest.mark.parametrize("skill,script", SCRIPT_CASES)
def test_bundled_script_self_test_passes(skill, script):
    """Each script carries its own cases. Run them as the agent would."""
    path = os.path.join(SKILLS_DIR, skill, "scripts", script)
    result = subprocess.run(
        [sys.executable, path, "--self-test"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, (
        f"{skill}/{script} --self-test failed:\n{result.stdout}\n{result.stderr}"
    )


@pytest.mark.parametrize("skill,script", SCRIPT_CASES)
def test_bundled_script_runs_standalone(skill, script):
    """A skill script must not depend on the project's import layout.

    An agent that loads the skill gets the file. If it only works when the
    solution directory happens to be on sys.path, it does not work.
    """
    path = os.path.join(SKILLS_DIR, skill, "scripts", script)
    result = subprocess.run(
        [sys.executable, path, "--help"],
        capture_output=True, text=True, timeout=60,
        cwd=os.path.dirname(path),
        env={**os.environ, "PYTHONPATH": ""},
    )
    assert result.returncode == 0, (
        f"{skill}/{script} cannot run standalone:\n{result.stderr}"
    )


# ------------------------------------------------------- the phase map

def _phase_skills() -> dict[str, list[str]]:
    """Read PHASE_SKILLS out of coordinator.py without importing it.

    Importing pulls in oracledb and psycopg, which are container-only
    dependencies -- the map should still be checkable on a laptop.
    """
    import ast

    solution = SKILLS_DIR.rsplit(os.sep + ".claude", 1)[0]
    source = open(os.path.join(solution, "coordinator.py"), encoding="utf-8").read()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "PHASE_SKILLS":
            return ast.literal_eval(node.value)
    return {}


def test_phase_skill_map_references_real_skills():
    """coordinator.PHASE_SKILLS must not name a skill that does not exist.

    Parsed from source rather than imported, because importing coordinator
    pulls in oracledb and psycopg, which are container-only dependencies.
    """
    mapping = _phase_skills()
    assert mapping, "PHASE_SKILLS not found in coordinator.py"

    named = {s for skills in mapping.values() for s in skills}
    unknown = sorted(named - set(SKILL_NAMES))
    assert not unknown, f"PHASE_SKILLS names skills that do not exist: {unknown}"

    unused = sorted(set(SKILL_NAMES) - named)
    assert not unused, f"skills that no phase ever loads: {unused}"


def test_nullability_skill_is_shared_by_two_phases():
    """The reuse argument, asserted rather than claimed.

    If this ever becomes one phase, the architecture's headline benefit over
    copy-pasted subagent prompts has quietly gone away.
    """
    mapping = _phase_skills()
    phases = [p for p, skills in mapping.items() if "nullability-preservation" in skills]
    assert sorted(phases) == ["data", "validate"], (
        f"nullability-preservation should be loaded by both the load phase and "
        f"the validation phase; found {phases}"
    )
