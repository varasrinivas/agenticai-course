"""Capstone 9 content, part C: planes, PHI, setup, build guide."""

PART_C = r"""
    <!-- ===== SKILL VS SUBAGENT VS COMMAND ===== -->
    <section class="section" id="planes">
      <h2 id="planes-heading">Skill, Subagent, or Slash Command?</h2>

      <p>This capstone is the first in the course to use <code>.claude/skills/</code>, so the boundary deserves stating plainly. All three are markdown files in <code>.claude/</code>. They are not interchangeable.</p>

      <table class="data-table">
        <tr><th></th><th>Skill</th><th>Subagent</th><th>Slash command</th></tr>
        <tr><td><strong>Lives in</strong></td><td><code>.claude/skills/&lt;name&gt;/SKILL.md</code></td><td><code>.claude/agents/&lt;name&gt;.md</code></td><td><code>.claude/commands/&lt;name&gt;.md</code></td></tr>
        <tr><td><strong>Loaded</strong></td><td>On demand, by description match</td><td>When delegated to</td><td>When a person types it</td></tr>
        <tr><td><strong>Context</strong></td><td>Shares the caller's</td><td><strong>Its own window</strong></td><td>Shares the caller's</td></tr>
        <tr><td><strong>Can bundle files</strong></td><td>Yes &mdash; <code>references/</code>, <code>scripts/</code></td><td>No</td><td>No</td></tr>
        <tr><td><strong>Can restrict tools</strong></td><td>Advisory</td><td><strong>Yes, enforced</strong></td><td>No</td></tr>
        <tr><td><strong>Can block a tool call</strong></td><td>No</td><td>No &mdash; hooks do that</td><td>No</td></tr>
        <tr><td><strong>Use it for</strong></td><td>Knowledge, and runbooks</td><td>Work needing isolation or a narrow tool grant</td><td>An entry point a person invokes</td></tr>
      </table>

      <h3 id="planes-why-skill">Why the domain is a Skill and not eight prompts</h3>

      <p>Six of the eight subagents need the ASAM ladder, the Part 2 rules and the code sets. There are two ways to give it to them.</p>

      <p>Paste it into six system prompts, and: it drifts the moment one is edited; it costs tokens on every turn of every subagent whether or not that turn needs it; and there is no single place to correct it when the clinical policy changes.</p>

      <p>Or write it once as <code>.claude/skills/behavioral-health-um/</code>, with the entry point short and four bundled references that stay out of context until something needs them:</p>

      <div class="code-block-wrapper">
        <div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'skill-md')">SKILL.md</button></div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="skill-md"><pre><code class="language-markdown">---
name: behavioral-health-um
description: Behavioral-health utilization management domain knowledge -- ASAM
  levels and the six dimensions, LOCUS/CALOCUS, concurrent review cadence,
  42 CFR Part 2, MHPAEA parity, BH code sets, and the reviewer-licensure rule.
  Load this before reading, classifying, or generating anything in a
  behavioral-health prior-authorization system.
---

| Reference | Load it when |
|---|---|
| `references/asam-levels.md` | Classifying a level of care, or writing a decision table |
| `references/part2-redisclosure.md` | Anything touching consent, disclosure, logging, eventing, search |
| `references/bh-code-sets.md` | Validating or emitting a service, diagnosis or instrument code |
| `references/parity-nqtl.md` | A rule applies to BH that may have no med/surg analogue |

`scripts/validate_bh_codes.py` checks a code against the sets in the third
reference. Run it rather than reasoning about whether `H0018` is real.</code></pre></div>
      </div>

      <p>That table is the mechanism. The entry point is a router; the bulk arrives only when needed.</p>

      <div class="callout-warning">
        <span class="box-label">Three anti-patterns</span>
        <ul>
          <li><strong>The ontology in every prompt.</strong> Drift plus token cost. This is the one the lab tests for &mdash; <code>test_skill_loading.py</code> fails if more than four ASAM levels appear inline in any agent file.</li>
          <li><strong>A Skill doing orchestration.</strong> A Skill cannot sequence phases, cannot isolate context, and cannot block a tool call. Writing "then delegate to the validator" in a Skill produces a suggestion, not a control.</li>
          <li><strong>A slash command where a Skill belongs.</strong> A command is an entry point a person types. If the agent should reach for it on its own, mid-run, it is a Skill.</li>
        </ul>
      </div>

      <h3 id="planes-recipes">Recipes are Skills too</h3>

      <p>Two of the four Skills in this lab are not knowledge at all &mdash; they are runbooks: <code>rules-to-dmn</code> and <code>decompose-transaction</code>. Same steps every time, run once per rules block and once per transactional method. Each bundles a script, because a bundled script is a thing that gets <em>run</em> rather than a procedure that gets recalled:</p>

      <div class="code-block-wrapper">
        <div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'overlap-sh')">Shell</button></div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="overlap-sh"><pre><code class="language-bash">python .claude/skills/rules-to-dmn/scripts/dmn_overlap.py \
    --ir artifacts/rules_ir.json --report artifacts/overlap.md</code></pre></div>
      </div>

      <p>That checker enumerates every pair of committing rows and reports pairs that can both match, with a concrete witness. Do not reason about overlap by inspection &mdash; the pairs that matter are the ones whose conditions are on <em>different variables</em> and therefore look disjoint. And when it cannot model a condition it <strong>raises</strong> rather than reporting no overlap: a false clean is the one answer that checker must never give.</p>
    </section>

    <!-- ===== NO PHI ===== -->
    <section class="section" id="no-phi">
      <h2 id="no-phi-heading">No PHI in Prompts, Ever</h2>

      <p>Taken verbatim from the platform organisation's own AI ground rules, and elevated here to a first-class constraint rather than a footnote &mdash; because this agent reads a system whose most valuable content is substance-use-disorder clinical narrative.</p>

      <p>The question the lab is really teaching: <strong>how do you point an agent at a regulated codebase without feeding it regulated data?</strong></p>

      <h3 id="no-phi-three">Three layers</h3>

      <div class="step-box">
        <span class="step-num">Layer 1 &mdash; the fixtures</span>
        <p>Every row in <code>bhauthtrack/</code> is <strong>synthetic</strong>, generated from documented seed <code>20260822</code>. Codes are real and correctly formatted &mdash; the rules would not be worth reading otherwise. The people are not.</p>
        <p>This is the control that actually holds. Everything below is defence in depth.</p>
      </div>

      <div class="step-box">
        <span class="step-num">Layer 2 &mdash; the gate</span>
        <p>A <code>PreToolUse</code> hook matching <strong>every</strong> tool, plus a result filter at the tool-server boundary. It detects by <em>shape</em>, not by keyword: a narrative does not announce itself, and matching on "alcohol" or "opioid" catches the obvious cases and misses everything a clinician wrote in a hurry.</p>
        <p>Content from an allowlisted synthetic fixture passes, but <strong>budgeted</strong> &mdash; an agent reading the whole seed file otherwise accumulates a clinical record in its transcript one tool call at a time. Content from anywhere else is redacted and <em>tagged</em>, so the model knows something was withheld rather than concluding the field is empty.</p>
      </div>

      <div class="step-box">
        <span class="step-num">Layer 3 &mdash; the audit</span>
        <p><code>PostToolUse</code> on every call, one JSON line, credentials and narrative redacted before the write.</p>
      </div>

      <div class="callout-security">
        <span class="box-label">Why the gate inspects RESULTS, not just inputs</span>
        <p>The risk here is not the agent doing something dangerous. It is the agent being <em>told</em> something it must not be told.</p>
        <p>Once protected content is in the context window it is in the transcript, in the provider's logs, and in every summary that follows. There is no taking it back. A <code>PreToolUse</code> hook runs before the tool and therefore cannot see what it returns &mdash; so the guarantee lives at the boundary where the data actually appears, in <code>filter_tool_result()</code>.</p>
      </div>

      <h3 id="no-phi-shape">Shape detection, and its limit</h3>

      <div class="code-block-wrapper">
        <div class="code-tabs">
          <button class="code-tab active" onclick="switchTab(this,'phi-py')">Python</button>
          <button class="code-tab" onclick="switchTab(this,'phi-ts')">Node / TypeScript</button>
        </div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="phi-py"><pre><code class="language-python"># solution/hooks.py
#
# THE LIMIT OF THIS APPROACH, STATED PLAINLY: shape detection is defence in
# depth, not a proof. A narrative written without any of these words will
# pass, and no regex closes that gap. The control that actually holds is that
# every fixture in this lab is SYNTHETIC.
_CLINICAL_REGISTER = re.compile(
    r"\b(member|patient|client|individual|resident|he|she|they)\b.{0,100}\b("
    r"present(s|ed|ing)?|report(s|ed|ing)?|ideation|withdrawal|relapse|"
    r"treatment|therapy|counsel(ling|ing)?|episode|referral|admission|"
    r"engagement|symptom|dose|medication|prescrib|diagnos"
    r")\b", re.I | re.S)

# Several sentences of prose, not code and not a column list.
#
# The trailing \s* rather than \s+ matters. With \s+ the LAST sentence of a
# narrative goes unmatched -- there is no whitespace after its full stop --
# so redaction leaves one clinical sentence standing. That was a real leak,
# found by running the gate over the seed fixture rather than over a mock.
_PROSE = re.compile(r"(?:[A-Z][^.!?\n]{25,}[.!?]\s*){2,}")</code></pre></div>
        <div class="code-panel" id="phi-ts"><pre><code class="language-typescript">// solution/hooks.ts
//
// THE LIMIT OF THIS APPROACH, STATED PLAINLY: shape detection is defence in
// depth, not a proof. A narrative written without any of these words will
// pass, and no regex closes that gap. The control that actually holds is that
// every fixture in this lab is SYNTHETIC.
const CLINICAL_REGISTER =
  /\b(member|patient|client|individual|resident|he|she|they)\b[\s\S]{0,100}\b(present(s|ed|ing)?|report(s|ed|ing)?|ideation|withdrawal|relapse|treatment|therapy|counsel(ling|ing)?|episode|referral|admission|engagement|symptom|dose|medication|prescrib|diagnos)\b/i;

// Several sentences of prose, not code and not a column list.
//
// The trailing \s* rather than \s+ matters. With \s+ the LAST sentence of a
// narrative goes unmatched -- there is no whitespace after its full stop --
// so redaction leaves one clinical sentence standing. That was a real leak,
// found by running the gate over the seed fixture rather than over a mock.
const PROSE = /(?:[A-Z][^.!?\n]{25,}[.!?]\s*){2,}/;</code></pre></div>
      </div>

      <p><code>tests/test_no_phi_in_prompt.py</code> plants a realistic narrative and asserts the gate fires; it also walks every non-allowlisted file in the legacy tree and asserts that <strong>none</strong> of them would reach the model carrying narrative-shaped content. That is the one check in this capstone that must report zero.</p>
    </section>

    <!-- ===== ENV SETUP ===== -->
    <section class="section" id="env-setup">
      <h2 id="env-setup-heading">Environment Setup</h2>

      <p>No database, no broker, no cloud account. This agent reads a repository and writes a repository, and everything under <code>tests/</code> runs without an API key.</p>

      <table class="data-table">
        <tr><th>Requirement</th><th>Version</th><th>Why</th></tr>
        <tr><td>Python</td><td><strong>3.10+</strong></td><td>The solution uses <code>X | None</code> union syntax throughout. Developed on 3.11; 3.12 in the container</td></tr>
        <tr><td><code>claude-agent-sdk</code></td><td><strong>&gt;= 0.2.0</strong></td><td>Tier 3. <code>query</code>, <code>tool</code>, <code>create_sdk_mcp_server</code>, <code>HookMatcher</code>, <code>PermissionResultDeny</code></td></tr>
        <tr><td><code>pytest</code></td><td><strong>&gt;= 8.0</strong></td><td>All 242 tests, offline</td></tr>
        <tr><td>Node.js</td><td>18+ <em>(phase 9B only)</em></td><td>Only to <code>npm install</code> the vendored donor so its Angular workspace builds. Not needed for 9A</td></tr>
        <tr><td>Docker</td><td>optional</td><td>Tier-1 deployment. <strong>Rancher Desktop works</strong> &mdash; Docker Desktop is not required</td></tr>
      </table>

      <p>Windows, macOS and Linux all work; there is no WSL requirement. The only platform-specific line is the venv activation path, shown below. <strong>Nothing here needs a paid subscription beyond an Anthropic API key</strong>, and the tests do not need even that.</p>

      <div class="code-block-wrapper">
        <div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'setup-sh')">Shell</button></div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="setup-sh"><pre><code class="language-bash">cd labs/capstone-9-bh-um-modernization

python -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp solution/.env.example solution/.env    # add your ANTHROPIC_API_KEY

# The vendored donor ships without node_modules, and Angular was never
# installed in the upstream checkout either -- no @angular packages, no `ng`
# binary. Required before anything in phase 9B will build.
cd reference-umlite && npm install && cd ..

# Everything here runs offline.
pytest tests/ -v
python solution/evaluation/test_suite.py --self-check</code></pre></div>
      </div>

      <div class="callout-warning">
        <span class="box-label">Expected output on a fresh checkout</span>
        <p><code>242 passed</code>. To run the same suite against your own work instead of the reference, point <code>BH_SOLUTION_DIR</code> at the starter tree:</p>
        <div class="code-block-wrapper"><div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'starter-run-sh')">Shell</button></div><button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="starter-run-sh"><pre><code class="language-bash">BH_SOLUTION_DIR=starter pytest tests/ -q</code></pre></div></div>
        <p>On a fresh <code>starter/</code> that reports <strong>95 passed, 147 failing</strong>, and every one of the failures is a <code>NotImplementedError</code> raised by a TODO you have not filled in yet &mdash; never an import error or a missing fixture. The 95 that already pass are the ones asserting on the two source trees, which you never modify. That number is your progress bar: it should only go up.</p>
      </div>

      <p><code>bhauthtrack/</code> needs no build. It is read, never run &mdash; there is no Oracle instance in this lab and no Tomcat. The SQL is a specification, not a database.</p>
    </section>

    <!-- ===== FILE TREE ===== -->
    <section class="section" id="file-tree">
      <h2 id="file-tree-heading">File Structure</h2>

      <p>Two trees you read, one you write, and the agent that does it.</p>

      <div class="code-block-wrapper">
        <div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'tree-txt')">Layout</button></div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="tree-txt"><pre><code class="language-bash">labs/capstone-9-bh-um-modernization/
├── bhauthtrack/                 # DOMAIN DONOR. Read-only, enforced in code.
│   ├── db/                      #   schema, the golden set, PKG_LOC_RULES, the drift log
│   └── src/main/                #   controller service dao domain batch security ws + 9 JSPs
├── reference-umlite/            # ARCHITECTURE DONOR. Read-only, enforced in code.
│   ├── camunda/                 #   prior-auth.bpmn, pa-decision.dmn
│   ├── BACKLOG.md               #   the platform team's own planned-and-unbuilt list
│   └── VENDORED.md              #   what the donor does and does not have
├── spec/agent-spec.md           # the 12-section contract
├── solution/                    # THE AGENT
│   ├── .claude/
│   │   ├── skills/              #   behavioral-health-um, umlite-architecture,
│   │   │                        #   rules-to-dmn, decompose-transaction
│   │   ├── agents/              #   the eight specialists
│   │   ├── commands/            #   modernize, validate, report
│   │   └── settings.json        #   five hooks, six matcher groups
│   ├── rules_ir.py              #   BOTH engines + the divergence diff
│   ├── gap_register.py          #   the deliverable, with its constraints in code
│   ├── seam_map.py              #   and its refusals
│   ├── hooks.py  hooks_cli.py   #   five guards, one implementation, two entry points
│   ├── tools_reference.py       #   6 read-only tools
│   ├── tools_legacy.py          #   7 read-only tools
│   ├── tools_emit.py            #   5 tools that produce output
│   ├── dmn_writer.py            #   refuses to emit a table that would be wrong
│   ├── bpmn_writer.py           #   refuses a process that cannot express the domain
│   ├── screen_inventory.py      #   phase 9B
│   ├── route_writer.py          #   phase 9B
│   ├── validation.py            #   the nine parity checks, as pure functions
│   ├── coordinator.py           #   sequences; has NO file tools
│   └── evaluation/              #   golden cases, reference IR, 22 scenarios
├── starter/                     # same tree, 31 numbered TODOs. Generated.
├── tests/                       # 219 tests, all offline
├── expected_output/             # the reference run. Generated, not hand-written.
├── appendix/manual-loop.py      # the only messages.create() in the capstone
└── deploy/{local,gcp,aws}/</code></pre></div>
      </div>

      <p>Note what <code>solution/</code> and <code>bh-um-lite/</code> are not: the agent's own subagents and skills are <strong>not</strong> part of its output. An agent that emits its own configuration into the workspace it is modernizing has confused the tool with the product, and <code>confine_writes</code> denies it.</p>
    </section>

    <!-- ===== PHASE 9A ===== -->
    <section class="section" id="phase-9a">
      <h2 id="phase-9a-heading">Phase 9A: Backend and Workflow</h2>

      <p>Ten to twelve hours. Thirty-three numbered TODOs live in <code>starter/</code>; list them with <code>grep -rn "TODO [0-9]" starter/</code>. The order matters &mdash; TODOs 1&ndash;6 are the two rule engines, because <strong>until both engines run you cannot tell a correct conversion from a lucky one</strong>, and everything after depends on being able to tell.</p>

      <div class="step-box">
        <span class="step-num">Step 1 &mdash; TODOs 1&ndash;2 &mdash; transcribe the ladder</span>
        <p><strong>What &amp; why.</strong> <code>evaluate_legacy()</code> is a faithful Python transcription of <code>PKG_LOC_RULES.EVAL_LOC</code> plus <code>LocRulesService</code>. It exists so the divergence diff can run in CI without an Oracle instance &mdash; and, more usefully, so the classification of each branch is <em>visible in code a student reads next to the original</em>.</p>
        <p><strong>File.</strong> <code>solution/rules_ir.py</code></p>
        <p><strong>The classification that matters.</strong> Branch 3's <code>dim1 &gt;= 4</code> arm <em>commits and returns</em>. Its <code>dim1 == 3</code> arm <em>accumulates and falls through</em>. One source branch, two kinds. Getting this wrong is the single most common conversion error, and it produces answers that are wrong and plausible.</p>
        <p><strong>Run.</strong> <code>pytest tests/test_rules_hit_policy.py -v</code></p>
        <p><strong>Expected.</strong> 14 passed, including <code>test_reference_conversion_matches_the_ladder_exactly</code> across all twelve golden cases.</p>
        <div class="callout-why">
          <span class="box-label">What just happened?</span>
          <p>You now have a reference implementation of the legacy rules that runs offline. Every later phase is measurable against it &mdash; and <code>test_plsql_alone_gets_three_cases_wrong</code> proves, concretely, that skipping the Java layer breaks cases 500002, 500008 and 500012.</p>
        </div>
        <p><strong>Anticipated errors.</strong></p>
        <ul>
          <li><em>All twelve cases diverge from the seed's stated outcomes.</em> You applied the Java layer inside the ladder rather than after it. It runs on the committed decision, so it can only downgrade or pend.</li>
          <li><em>Case 500007 comes out at 3.5 instead of 2.5.</em> Dimension 4 inverts. A low readiness score <em>subtracts</em>.</li>
          <li><em>Case 500010 approves instead of pending.</em> The EDI case has all six dimensions at zero &mdash; including dimension 4, which fires the readiness penalty. Every EDI-submitted residential request pends.</li>
        </ul>
      </div>

      <div class="step-box">
        <span class="step-num">Step 2 &mdash; TODOs 3&ndash;6 &mdash; the decision-table engine</span>
        <p><strong>What &amp; why.</strong> <code>evaluate_ir()</code> does what a DMN engine does: match rows, apply a hit policy. It is the second half of the divergence diff.</p>
        <p><strong>File.</strong> <code>solution/rules_ir.py</code></p>
        <p><strong>The one to get right.</strong> <code>UNIQUE</code> must <em>raise</em> when more than one row matches, and an unstated policy must raise too &mdash; DMN defaults to <code>UNIQUE</code>, so silence is a production error waiting for the first case that matches twice.</p>
        <p><strong>Run.</strong> <code>python solution/evaluation/test_suite.py --self-check</code></p>
        <p><strong>Expected.</strong> Scenarios 1&ndash;3 pass: the overlap is declared with a witness, the policy is justified, and the accumulating branches are not rows.</p>
        <div class="callout-why">
          <span class="box-label">What just happened?</span>
          <p>Run <code>diff_engines</code> with a naive <code>FIRST</code> table and you get zero divergences. Sort the rows by id and you get ten. That is the whole lesson about hit policy, and you can now reproduce it on demand.</p>
        </div>
        <p><strong>Anticipated errors.</strong></p>
        <ul>
          <li><em><code>UNIQUE</code> silently returns the first match.</em> It must <strong>raise</strong>. The error is the table telling you the ladder&rsquo;s ordering carried information it does not &mdash; swallowing it converts a loud failure into a wrong determination.</li>
          <li><em>A table with no <code>hit_policy</code> evaluates anyway.</em> DMN defaults to <code>UNIQUE</code>, so silence is a production error waiting for the first case that matches twice. Raise on the missing field.</li>
          <li><em>The score comes out wrong on every case.</em> You applied the accumulating branches in the wrong order, or emitted one as a row. Order is load-bearing, and an accumulating branch is an <em>input</em>, not a decision.</li>
        </ul>
      </div>

      <div class="step-box">
        <span class="step-num">Step 3 &mdash; TODOs 7&ndash;12 &mdash; the register and the seam map</span>
        <p><strong>What &amp; why.</strong> The gap register is the deliverable, and its constraints belong in code. A prompt saying "must-not-port requires a named harm" is a request; a tool that returns an error is a rule.</p>
        <p><strong>Files.</strong> <code>solution/gap_register.py</code>, <code>solution/seam_map.py</code></p>
        <p><strong>Run.</strong> <code>pytest tests/test_flag_classification.py tests/test_consent_atomicity.py tests/test_term_mapping.py -v</code></p>
        <p><strong>Expected.</strong> 44 passed, including the three seam refusals and the term map’s
        <div class="callout-why">
          <span class="box-label">What just happened?</span>
          <p>You moved three rules out of prose and into code. &ldquo;must-not-port requires a named harm&rdquo; is now something the tool returns an error for, not something a reviewer has to remember &mdash; and <code>Seam.validate()</code> will not let you cut a seam that silently loses a guarantee.</p>
        </div>: a seam with no replacement, an incomplete replacement, and a <code>must-be-atomic</code> pair someone tried to cut.</p>
        <p><strong>Anticipated errors.</strong></p>
        <ul>
          <li><em>Your register accepts a <code>must-not-port</code> with no harm.</em> Then the register's most important verdict means nothing. Raise.</li>
          <li><em><code>Seam.validate()</code> passes a <code>must-be-atomic</code> seam.</em> That seam cannot be cut. Either move it or record <code>rejected_because</code> &mdash; recording a rejection <em>is</em> a result.</li>
        </ul>
      </div>

      <div class="step-box">
        <span class="step-num">Step 4 &mdash; TODOs 13&ndash;18 &mdash; the five guards</span>
        <p><strong>What &amp; why.</strong> Four <code>can_use_tool</code> denials plus an audit hook. They run <em>before</em> the tool, so the dangerous call never happens &mdash; a <code>PostToolUse</code> hook would be an excellent post-mortem and a bad guardrail.</p>
        <p><strong>File.</strong> <code>solution/hooks.py</code></p>
        <p><strong>Run.</strong> <code>pytest tests/test_no_phi_in_prompt.py tests/test_hooks_readonly.py tests/test_hitl_gate.py -v</code></p>
        <p><strong>Expected.</strong> 50 passed. The one that matters is <code>test_the_gate_reports_zero_against_the_real_fixtures</code>.</p>
        <div class="callout-why">
          <span class="box-label">What just happened?</span>
          <p>That last test walks every non-allowlisted file in the legacy tree and asserts none of them would reach the model carrying narrative-shaped content. It is the one check in this capstone that must report <strong>zero</strong> &mdash; and it is now proving that on the real fixtures rather than on a mock.</p>
        </div>
        <p><strong>Anticipated errors.</strong></p>
        <ul>
          <li><em>Redaction leaves the last sentence of a narrative standing.</em> Your prose pattern requires whitespace after the final full stop. One clinical sentence is a disclosure.</li>
          <li><em>The audit log will not parse.</em> A greedy <code>\S+</code> after <code>password=</code> ate the closing quote and brace. Redact <em>values</em>, not serialized JSON.</li>
          <li><em>The gate flags a Java file full of code.</em> You are matching keywords rather than shape. Require prose <em>and</em> clinical register.</li>
        </ul>
      </div>

      <div class="step-box">
        <span class="step-num">Step 5 &mdash; TODOs 19&ndash;24 &mdash; tools and writers</span>
        <p><strong>What &amp; why.</strong> Five local tools and the two Camunda writers. Both writers <strong>refuse</strong> rather than emitting with a warning &mdash; a file that looks finished is worse, because the next person reads the file and not the warning.</p>
        <p><strong>Files.</strong> <code>tools_emit.py</code>, <code>dmn_writer.py</code>, <code>bpmn_writer.py</code></p>
        <p><strong>Run.</strong> <code>pytest tests/test_dmn_can_deny.py tests/test_concurrent_review_loop.py -v</code></p>
        <p><strong>Expected.</strong> 28 passed, and <code>D.render(reference_ir)</code> produces well-formed DMN with <code>hitPolicy="UNIQUE"</code>, nine rules and a reachable <code>DENIED</code>.</p>
        <div class="callout-why">
          <span class="box-label">What just happened?</span>
          <p>Both writers now <em>refuse</em>. Feed <code>bpmn_writer</code> a one-shot process and it names the four things missing; feed <code>dmn_writer</code> a table with an unresolved overlap and it will not emit. A refusal that explains itself is worth more than a file with a warning at the top, because the next person reads the file.</p>
        </div>
        <p><strong>Anticipated errors.</strong></p>
        <ul>
          <li><em>The generated XML will not parse.</em> <code>--</code> cannot appear inside an XML comment, and your hit-policy justification is prose written for humans who use double dashes freely. Sanitise before interpolating.</li>
          <li><em><code>to_feel()</code> produces a cell for a two-input condition.</em> It should raise. A guessed cell is a wrong clinical rule that looks finished.</li>
        </ul>
      </div>

      <div class="step-box">
        <span class="step-num">Step 6 &mdash; TODOs 25&ndash;27 &mdash; the parity checks</span>
        <p><strong>What &amp; why.</strong> Ten checks, as pure functions, so they are testable without an agent run. <em>A check nobody has ever seen fire is not a check.</em></p>
        <p><strong>File.</strong> <code>solution/validation.py</code></p>
        <p><strong>Run.</strong> <code>pytest tests/test_part2_leak.py tests/test_narrative_roundtrip.py -v</code></p>
        <p><strong>Expected.</strong> 17 passed, each one planting a specific flaw and asserting the check finds it.</p>
        <div class="callout-why">
          <span class="box-label">What just happened?</span>
          <p>Every check has now been <em>seen to fire</em>. That is the bar: a check nobody has watched catch its own flaw is a check you are trusting on faith, and these are the ten things standing between a plausible port and a correct one.</p>
        </div>
        <div class="callout-warning">
          <span class="box-label">The semantics to get right</span>
          <p>Four checks are the ones a naive port trips. A clean result from one of them is <strong>not</strong> a problem by itself &mdash; a good port comes back clean on all four, and a check that could never pass is a check people learn to ignore.</p>
          <p>Clean is suspicious when the check <em>could not have fired</em>: it scanned nothing, or its inputs cannot exercise what it is for. Both are measured &mdash; <code>scanned</code> and <code>could_have_fired</code> &mdash; rather than assumed.</p>
        </div>
        <p><strong>Anticipated errors.</strong></p>
        <ul>
          <li><em>The leak scan misses an audit table&rsquo;s narrative column.</em> Two reasons, and you probably have both: <code>narrative</code> does not match inside <code>old_narrative</code> because the underscore is a word character, and the table name sits on a different line from the column, so a line-by-line scan cannot see the pair.</li>
          <li><em>Your leak scan flags a comment.</em> Warning the next developer not to log the narrative is exactly what you want them to do. Skip comment lines, or the only way to pass is to stop explaining the mistake.</li>
          <li><em>The consent check passes on a schema with no enforcement.</em> You checked current state. Ask instead whether anything <em>prevents</em> the bad state &mdash; a foreign key, a NOT NULL, a constraint. Clean today and reachable tomorrow is not the same as safe.</li>
        </ul>
      </div>

      <div class="step-box">
        <span class="step-num">Step 7 &mdash; run it</span>
        <p><strong>What &amp; why.</strong> Everything above is a part. This is the first time the coordinator sequences all six phases against both source trees, with the hooks live.</p>
        <p><strong>Run.</strong> <code>cd solution &amp;&amp; python coordinator.py --phase 9a</code></p>
        <p><strong>Expected.</strong> Six phases, then a denial from <code>finalize_modernization</code> carrying the gap register, the parity summary and the manual-review queue.</p>
        <div class="callout-why">
          <span class="box-label">What just happened?</span>
          <p><strong>The denial is the successful outcome.</strong> The agent does not get to decide that its own work is ready &mdash; and it cannot, because the approval flag is read from the environment and there is no code path by which the agent writes it.</p>
        </div>
        <p><strong>Anticipated errors.</strong></p>
        <ul>
          <li><em><code>ANTHROPIC_API_KEY is not set -- no phase can run.</code></em> Every phase calls the model, so the coordinator checks for the key before it starts rather than surfacing a transport traceback five frames deep. Either export it, or put it in <code>solution/.env</code> &mdash; <code>config.py</code> reads that file on import, and an exported variable always wins over a stale one in the file.</li>
          <li><em>The run halts after phase 4 saying the register does not meet acceptance.</em> Working as intended. A register that is mostly <code>port-as-is</code> means the architecture was read and the domain was not, and the coordinator checks that itself rather than believing the phase&rsquo;s own report.</li>
          <li><em>A phase reports success but wrote nothing.</em> Also caught &mdash; <code>check_gates()</code> looks at the artifact rather than the summary. If it did not catch yours, that gate is what needs the fix.</li>
          <li><em>The run is far more expensive than you expected.</em> Check the token budget in <code>config.py</code> and the circuit breaker. Three consecutive failures in one phase should halt; a phase retrying forever is the failure mode the breaker exists for.</li>
        </ul>
      </div>
    </section>

    <!-- ===== PHASE 9B ===== -->
    <section class="section" id="phase-9b">
      <h2 id="phase-9b-heading">Phase 9B: Frontend</h2>

      <p>Four to six hours, TODOs 28&ndash;31, and it is <strong>gated on 9A being green</strong>. The coordinator refuses to start it otherwise:</p>

      <div class="code-block-wrapper">
        <div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'gate9b-py')">Python</button></div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="gate9b-py"><pre><code class="language-python"># solution/coordinator.py
elif args.phase == "9b":
    # 9B is gated on 9A. Run it against a red 9A and the client ends up
    # guarding around enforcement the backend does not have -- which looks
    # like the rule was migrated and is not.
    missing = [p for p in config.PHASES_9A if not session.is_complete(p)]
    if missing:
        print(f"9B is gated on 9A being green. Not complete: {', '.join(missing)}")
        return 1</code></pre></div>
      </div>

      <div class="step-box">
        <span class="step-num">Step 8 &mdash; TODOs 29&ndash;30 &mdash; the screen inventory</span>
        <p><strong>What &amp; why.</strong> Seven screens, twenty rules, eleven with no server-side enforcement. Detection is regex; judgement is the agent's &mdash; finding <code>&lt;c:if test="${sessionScope.roleMask ge 4}"&gt;</code> is a job for a pattern, and deciding it means "only a physician may deny" is not.</p>
        <p><strong>File.</strong> <code>solution/screen_inventory.py</code></p>
        <p><strong>Run.</strong> <code>pytest tests/test_view_rules_relocated.py -v</code></p>
        <p><strong>Expected.</strong> 24 passed, including the seven parametrised cases proving a template is refused as a relocation.</p>
        <div class="callout-why">
          <span class="box-label">What just happened?</span>
          <p>You now have a data structure that cannot represent the mistake. <code>*ngIf</code>, <code>template-conditional</code>, <code>client-side</code> and <code>v-if</code> are all rejected as proposed homes &mdash; so a rule cannot be recorded as relocated when it has only changed template languages.</p>
        </div>
        <p><strong>Anticipated errors.</strong></p>
        <ul>
          <li><em>A screen contributes no rules.</em> Read it again. Every one of the seven has at least one, and <code>consentAdmin.jsp</code> is the easiest to miss because its role check is in the controller rather than the markup &mdash; two conventions coexist in this codebase.</li>
          <li><em>You record a rule with <code>server_side_equivalent</code> left blank.</em> Refused, deliberately. &ldquo;NONE&rdquo; is a finding and has to be said out loud; eleven of the twenty rules are NONE.</li>
        </ul>
      </div>

      <div class="step-box">
        <span class="step-num">Step 9 &mdash; TODO 31 &mdash; the route writer</span>
        <p><strong>What &amp; why.</strong> Routes, a guard, environment config, and two components. The reference platform contributes an equivalent for exactly one of seven screens.</p>
        <p><strong>File.</strong> <code>solution/route_writer.py</code></p>
        <p><strong>Run.</strong> <code>pytest tests/test_screen_coverage.py -v</code> then <code>python coordinator.py --phase 9b</code></p>
        <p><strong>Expected.</strong> 15 passed; check 8 reports zero over seven client files.</p>
        <div class="callout-why">
          <span class="box-label">What just happened?</span>
          <p>Seven screens, seven reachable routes, and every rule that used to live in a template now in a guard, a service check, a computed field, an API omission or a workflow candidate group. Run <code>python coordinator.py --phase all</code> and both phases go end to end &mdash; and still stop at the gate.</p>
        </div>
        <p><strong>Anticipated errors.</strong></p>
        <ul>
          <li><em>Your guard compares a number.</em> <code>roleMask &gt;= 4</code> is the approximation JSTL was forced into because it has no bitwise operator &mdash; and it is the <em>permissive</em> side. Mask 33 passes it and fails <code>hasRole(MD)</code>. Test named roles.</li>
          <li><em>Every screen reports as routed however you break the routes file.</em> You are matching a substring; <code>member</code> appears in <code>memberLastName</code> in half the components. Match a <code>path:</code> declaration.</li>
          <li><em>The check flags your own environment file.</em> It warns about the donor's hardcoded URL by quoting it. Skip comment lines &mdash; otherwise the only way to pass is to stop explaining the mistake.</li>
        </ul>
      </div>
    </section>
"""
