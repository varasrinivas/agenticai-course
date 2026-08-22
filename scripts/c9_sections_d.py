"""Capstone 9 content, part D: spec-driven, guardrails, validation, deploy,
Part 2 callouts, troubleshooting, going further, quiz, references."""

PART_D = r"""
    <!-- ===== SPEC-DRIVEN ===== -->
    <section class="section" id="spec-driven">
      <h2 id="spec-driven-heading">Track 2: Build It Twice, Then Diff</h2>

      <p>The brief asked a question you should now be able to answer for yourself: <em>migrate the repo, or generate a new one?</em> Do both and compare.</p>

      <div class="code-block-wrapper">
        <div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'spec-sh')">Shell</button></div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="spec-sh"><pre><code class="language-bash"># Track 1 -- modernize. Reads both trees.
cd solution && python coordinator.py --phase all

# Track 2 -- generate. Reads the spec only.
/generate-from-spec spec/agent-spec.md          # writes to generated/

diff -r bh-um-lite/ generated/</code></pre></div>
      </div>

      <table class="data-table">
        <tr><th>Track</th><th>Inherits</th><th>Misses</th></tr>
        <tr><td><strong>1 &mdash; Modernize</strong><br>reads the donor and the monolith</td><td>Architecture fidelity, the platform's conventions, the flag idiom</td><td>Silently inherits the donor's <em>holes</em> &mdash; traps 2, 3, 4, 5 and 7</td></tr>
        <tr><td><strong>2 &mdash; Generate</strong><br>reads the spec</td><td>Clean intent, no clinical bias, every requirement stated once</td><td>No institutional knowledge &mdash; the branch-7 overlap rows, the two member identifiers, the 2013 merge comment explaining the transaction</td></tr>
      </table>

      <div class="callout-why">
        <span class="box-label">The lesson</span>
        <p><strong>Porting carries architecture and its blind spots. Generating carries intent but not institutional knowledge.</strong></p>
        <p>The production answer is neither: it is port-then-spec-review. Run track 1, then read the spec against what it produced and ask what the spec knows that the port forgot &mdash; and what the port knows that nobody thought to write down.</p>
        <p>That second question is where the value is. Nobody would have written "the transaction must be atomic because the JTA config drifted between environments in 2013" into a specification. It is only in the code, in a comment, because someone lived it.</p>
      </div>
    </section>

    <!-- ===== GUARDRAILS ===== -->
    <section class="section" id="guardrails">
      <h2 id="guardrails-heading">Guardrails and the Human Gate</h2>

      <p>Five hooks, wired as six matcher groups in <code>.claude/settings.json</code>. Four are <code>can_use_tool</code> denials &mdash; they run <em>before</em> the tool, so the call never happens.</p>

      <table class="data-table">
        <tr><th>Hook</th><th>Matcher</th><th>Does</th></tr>
        <tr><td><code>protected_content_gate</code></td><td><code>.*</code></td><td>Denies narrative-shaped content in any tool input; the result filter redacts on the way back</td></tr>
        <tr><td><code>enforce_reference_readonly</code></td><td><code>mcp__reference_src__.*</code></td><td>Denies path traversal out of the donor tree</td></tr>
        <tr><td><code>enforce_legacy_readonly</code></td><td><code>mcp__legacy_src__.*</code></td><td>Same, for the monolith</td></tr>
        <tr><td><code>confine_writes</code></td><td><code>write_artifact</code></td><td>Denies any path outside <code>bh-um-lite/</code></td></tr>
        <tr><td><code>hitl_finalization_gate</code></td><td><code>finalize_modernization</code></td><td><strong>Always denies</strong> without human approval</td></tr>
        <tr><td><code>audit_log</code></td><td><code>.*</code> (PostToolUse)</td><td>One JSON line per call, redacted</td></tr>
      </table>

      <p>The protected-content gate matches <strong>every</strong> tool deliberately. Scoping it to the legacy server would miss content arriving by any other path &mdash; a file read, a shell command, a tool added next month.</p>

      <h3 id="guardrails-gate">The agent cannot approve its own work</h3>

      <p><code>finalize_modernization</code> denies unless <code>BH_FINALIZATION_APPROVED</code> is set. The agent <em>reads</em> that variable and has no code path by which it writes one. That asymmetry is the entire gate; the briefing it returns is presentation.</p>

      <div class="code-block-wrapper">
        <div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'gate-txt')">The denial</button></div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="gate-txt"><pre><code class="language-bash">FINALIZATION REQUIRES HUMAN APPROVAL.

GAP REGISTER: port-as-is 2, extend 4, must-build-new 6, must-not-port 3
  MUST-NOT-PORT  cleartext PHI in logs, events and search
                 harm: decomposition multiplies one log sink into several...
  MUST-NOT-PORT  consent enforcement as a feature flag
                 harm: a week of CONSENT_ENABLED=false is unlawful disclosure...
  must-build-new concurrent review
  must-build-new 42 CFR Part 2 consent model
  ...

PARITY: READY FOR REVIEW
  [1] rules divergence: 0
  [2] protected-content leak: 0
  ...

QUEUED FOR HUMAN DECISION: 5
  BH_AUTH.LEGACY_OVERRIDE: ticket body reads, in full, "per DM request"
  LocRulesService adjustment B: the 2016 parity note, never actioned
  ...

A person must read artifacts/modernization_report.html and re-run:
    python coordinator.py --phase finalize --approve</code></pre></div>
      </div>

      <p><strong>The denial is the successful end of the run.</strong> The briefing is assembled from the artifacts, not from the agent's summary of them &mdash; the agent's account of its own work is the thing under review.</p>

      <div class="callout-warning">
        <span class="box-label">Approval is not a config value</span>
        <p>In the cloud tiers, <code>BH_FINALIZATION_APPROVED</code> appears in <em>no</em> manifest: not the Cloud Run env vars, not the ECS task definition. The moment it lives in YAML it is on by default, forever, for every future run, and the gate is gone with nothing failing to signal it.</p>
        <p>Approval is a separate job (<code>gcp/approve-job.yaml</code>) or an override someone types (<code>aws/finalize-override.json</code>) &mdash; which CloudTrail records and an environment variable does not. And the agent's own IAM role must not carry permission to invoke it.</p>
      </div>
    </section>

    <!-- ===== VALIDATION ===== -->
    <section class="section" id="validation">
      <h2 id="validation-heading">Validation and Evals</h2>

      <p>Ten checks, written as pure functions so they are testable without an agent run. <em>A check nobody has ever seen fire is not a check</em> &mdash; every one has a test that plants the flaw and asserts the check finds it.</p>

      <table class="data-table">
        <tr><th>#</th><th>Check</th><th>Catches</th></tr>
        <tr><td>1</td><td>Rules divergence</td><td>The hit-policy artefact at the ASAM 3.5/3.7 boundary</td></tr>
        <tr><td>2</td><td>Protected-content leak</td><td>Narrative in a log, event, index, audit column or error path</td></tr>
        <tr><td>3</td><td>Narrative round-trip</td><td>Validated-then-discarded, asserted on the <em>column</em></td></tr>
        <tr><td>4</td><td>Consent atomicity</td><td>State <strong>and</strong> whether anything enforces it</td></tr>
        <tr><td>5</td><td>Workflow</td><td>No loop, no timer, no escalation, an unassigned task</td></tr>
        <tr><td>6</td><td>Decision table</td><td>Unreachable denial, no diagnosis input, unstated policy</td></tr>
        <tr><td>7</td><td>Identity</td><td>One opaque member id where there should be two</td></tr>
        <tr><td>8</td><td>Screen coverage <em>(9B)</em></td><td>A screen with no route; a rule still in a template</td></tr>
        <tr><td>9</td><td>Feature-flag classification</td><td>A regulatory control behind a flag</td></tr>
        <tr><td>10</td><td>Term mapping</td><td>A donor status unaccounted for; a silent name collision</td></tr>
      </table>

      <div class="callout-warning">
        <span class="box-label">The semantics that took two attempts to get right</span>
        <p>Checks 1&ndash;4 are the four a naive port trips. The obvious design is to treat a clean result as blocking &mdash; and it is wrong, because then the <em>reference answer</em> can never pass. A check that could never pass is a check people learn to ignore.</p>
        <p>What matters is whether the check <strong>could have fired</strong>. Every check reports what it <code>scanned</code>, and a clean result is flagged suspicious only when it scanned nothing, or when <code>could_have_fired</code> is false &mdash; a case set with no case at the overlap boundary, an empty emitted tree.</p>
        <p>Both are measured rather than assumed.</p>
      </div>

      <h3 id="validation-evals">Twenty-four scenarios</h3>

      <p>The tests cover mechanics. The evaluation suite scores <strong>judgement</strong>: did the run notice the overlap, did it refuse to guess at the undocumented flag, did it name the harm, did it flag the silent term collisions.</p>

      <div class="code-block-wrapper">
        <div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'eval-sh')">Shell</button></div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="eval-sh"><pre><code class="language-bash">python solution/evaluation/test_suite.py --phase 9a    # >= 20 / 22
python solution/evaluation/test_suite.py              # >= 22 / 24</code></pre></div>
      </div>

      <p>Several scenarios score a <strong>refusal</strong>. Scenario 4 &mdash; <em>REFUSES to interpret <code>LEGACY_OVERRIDE</code></em> &mdash; scores zero for a confident interpretation however reasonable it sounds, because nobody at Bridgeway can check the answer and the cost of being wrong is a changed determination for a real person.</p>
    </section>

    <!-- ===== DEPLOYMENT ===== -->
    <section class="section" id="deploy">
      <h2 id="deploy-heading">Deployment</h2>

      <p>Three tiers. Tier 1 is the lab and needs only Docker &mdash; there is no database and no broker, because this agent reads a repository and writes a repository.</p>

      <div class="code-block-wrapper">
        <div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'deploy-sh')">Shell</button></div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="deploy-sh"><pre><code class="language-bash">cp solution/.env.example solution/.env      # add your ANTHROPIC_API_KEY
docker compose up --build

# Read artifacts/modernization_report.html, then:
docker compose run --rm agent python coordinator.py --phase finalize --approve</code></pre></div>
      </div>

      <p>Six phases run for minutes to hours and then finish. That is a <strong>job</strong>, not a request handler &mdash; behind an HTTP endpoint you fight a 60-minute Cloud Run ceiling for no benefit. Cloud Run <em>jobs</em> and ECS <em>tasks</em> have no such limit.</p>

      <div class="callout-security">
        <span class="box-label">The constraint that shapes every tier</span>
        <p>Most agent deployments worry about credentials and network reachability. Those matter here too. But the thing that shapes every decision is <strong>"no PHI in prompts, ever"</strong> &mdash; and it gets <em>harder</em> in the cloud:</p>
        <table class="data-table" style="margin-top:0.75rem;">
          <tr><th></th><th>Local</th><th>Cloud</th></tr>
          <tr><td>Where a redaction miss ends up</td><td>one container's stdout</td><td>Cloud Logging, and whatever is subscribed to it</td></tr>
          <tr><td>Who can read the audit log</td><td>you</td><td>anyone with project log-viewer</td></tr>
          <tr><td>What a crash dump becomes</td><td>a terminal</td><td>a retained entry, on a policy someone else set</td></tr>
        </table>
        <p style="margin-top:0.75rem;">So: the audit log goes to object storage rather than stdout; <code>PHI_ALLOWLIST</code> names only synthetic fixtures; log retention is set <em>deliberately</em>, because a never-expire default is a never-expire retention on whatever the redaction missed.</p>
      </div>

      <p><strong>Docker Desktop is not required.</strong> Rancher Desktop with the dockerd runtime works unchanged &mdash; both source mounts are <code>:ro</code>, which is second-layer enforcement behind the hooks, and a guardrail that exists in exactly one place is one refactor from gone.</p>
    </section>

    <!-- ===== PART 2 ===== -->
    <section class="section" id="part2">
      <h2 id="part2-heading">HIPAA and 42 CFR Part 2</h2>

      <div class="callout-warning">
        <span class="box-label">Educational model, not legal advice</span>
        <p>The Part 2 and MHPAEA parity behaviour modelled in this lab is a <strong>simplified teaching version</strong> &mdash; enough to make the architectural point, not enough to build a compliance programme on. It is not legal advice, and a real implementation needs counsel.</p>
        <p>What it <em>is</em> good for: recognising the shape of the problem. The failures modelled here &mdash; a field that fans out to four sinks, a consent scope nothing checks, a revocation with no register of what went out under it &mdash; are real failure modes, and they are architectural rather than legal.</p>
      </div>

      <h3 id="part2-checklist">The checklist for any component you generate</h3>

      <ul>
        <li>Does any log statement interpolate the clinical free-text field? Check string concatenation <em>and</em> structured-logging fields.</li>
        <li>Does any event payload carry it? Check <strong>every</strong> event, not just the obvious one.</li>
        <li>Is it mapped into a search index? An index is a second copy with its own retention.</li>
        <li>Does the audit trail store it? A before/after copy on every update accumulates copies with no expiry and no consent scope.</li>
        <li>Is the transport authenticated and encrypted? A plaintext broker on an internal network is still a disclosure to whoever can read the topic.</li>
        <li>Is there a free-text <strong>search</strong> over it, and does it check a role and a consent? A careful guard on a detail screen is undone by an unguarded search over the same field.</li>
        <li>Does an error path leak it &mdash; an exception message, a stack trace, a request body echoed into a log?</li>
      </ul>

      <h3 id="part2-escalate">When to escalate rather than decide</h3>

      <p>Four things in this lab are questions for a compliance officer, not an architect. The agent queues them and stops:</p>

      <ul>
        <li>The Part 2 program flag was backfilled from a spreadsheet in 2014 and its accuracy has never been audited &mdash; yet it gates the entire regime.</li>
        <li>Two independent code paths <strong>fabricate</strong> a consent on the submitter's behalf. Most requests arrive by one of them. <em>Who consents when a machine submits?</em></li>
        <li>The audit table holds protected content because the appeals team asked for it in 2012 and privacy never reviewed it.</li>
        <li>A frequency-based pend with no med/surg analogue, flagged by compliance in 2016 and never actioned.</li>
      </ul>

      <p>That last one is worth dwelling on. An <strong>unactioned compliance note is evidence</strong> &mdash; it means someone already reached this conclusion and the organisation lost track of it. That is a far stronger signal than one an agent inferred, and it belongs in the register with the note quoted verbatim and its date.</p>
    </section>

    <!-- ===== TROUBLESHOOTING ===== -->
    <section class="section" id="troubleshooting">
      <h2 id="troubleshooting-heading">Troubleshooting</h2>

      <table class="data-table">
        <tr><th>Symptom</th><th>Cause</th><th>Fix</th></tr>
        <tr><td>All twelve golden cases diverge from the seed's stated outcomes</td><td>The Java layer is applied inside the ladder rather than after it</td><td>It runs on the <em>committed</em> decision, so it can only downgrade or pend</td></tr>
        <tr><td>Case 500007 comes out 3.5 instead of 2.5</td><td>Dimension 4 treated as a severity indicator</td><td>It inverts. A low readiness score <em>subtracts</em></td></tr>
        <tr><td>Zero divergences and you have not tightened anything</td><td>You used <code>FIRST</code> and the rows happen to be in ladder order</td><td>Correct today, by luck. Sort the rows and watch ten cases change</td></tr>
        <tr><td>The generated DMN will not parse</td><td><code>--</code> inside an XML comment, from the hit-policy justification</td><td>Sanitise prose before interpolating it into a comment</td></tr>
        <tr><td><code>to_feel()</code> raises on a tightened row</td><td>A cross-input exclusion cannot be one cell</td><td>Working as intended. Add a named derived input</td></tr>
        <tr><td>Redaction leaves one clinical sentence</td><td>The prose pattern requires whitespace after the final full stop</td><td><code>\s*</code>, not <code>\s+</code>. One sentence is a disclosure</td></tr>
        <tr><td>The audit log will not parse</td><td>A greedy <code>\S+</code> after <code>password=</code> ate the closing quote</td><td>Redact <em>values</em>, not serialized JSON</td></tr>
        <tr><td>The leak scan misses an audit table's narrative column</td><td><code>\bnarrative\b</code> does not match inside <code>old_narrative</code></td><td>The underscore is a word character. And the table name is on another line</td></tr>
        <tr><td>The run halts after phase 4</td><td>The register does not meet acceptance</td><td>Working as intended. A mostly-<code>port-as-is</code> register means the domain was not tested</td></tr>
        <tr><td>Phase 9B refuses to start</td><td>9A is not green</td><td>Also intended. A client cannot supply an enforcement the backend lacks</td></tr>
        <tr><td>Every screen reports as routed however you break the routes file</td><td>Substring matching &mdash; <code>member</code> appears in <code>memberLastName</code></td><td>Match a <code>path:</code> declaration</td></tr>
        <tr><td>The flag check cannot see <code>CONSENT_ENABLED</code></td><td>A leading <code>[A-Z]</code> consumed the first character</td><td>Make the prefix optional. The plainest spelling was the blind spot</td></tr>
      </table>
    </section>

    <!-- ===== GOING FURTHER ===== -->
    <section class="section" id="extensions">
      <h2 id="extensions-heading">Going Further [ALL OPTIONAL]</h2>

      <p>None of these is required. Each is a real piece of work that the lab deliberately left open.</p>

      <ol>
        <li><strong>The appeals path.</strong> The platform team's backlog item #7, and the one gap <em>our</em> analysis missed. Behavioral-health denials are appealed at least as often as medical ones; the legacy system handles them in a shared mailbox and a spreadsheet. Design the sub-process, then ask what it does to the turnaround clock.</li>
        <li><strong>LOCUS/CALOCUS alongside ASAM.</strong> The lab models substance-use placement. Psychiatric placement uses a different framework, chosen by <em>diagnosis</em> rather than by member. Add a second rules IR and a router, and watch the hit-policy question reappear one level up.</li>
        <li><strong>Make the parity analysis a first-class artifact.</strong> Right now the three NQTL findings go to the manual-review queue. Produce the comparative analysis document a plan would actually need to have on file.</li>
        <li><strong>Run the agent against the OTHER donor.</strong> Point it at a platform you have and see how much of the gap register is really about behavioral health versus about the specific thinness of this donor. That is the honest test of whether the analysis generalises.</li>
        <li><strong>Idempotency for the EDI path.</strong> The X12 278 importer has no idempotency key and a duplicate guard that drops legitimate same-day requests. Design a real one &mdash; and notice that the transaction carries no identifier suitable for the job.</li>
        <li><strong>A disclosure-accounting UI.</strong> The lab builds the <code>bh_disclosure</code> table. Nobody can read it. What does a Part 2 accounting of disclosures look like to a member who asks for one?</li>
      </ol>
    </section>

    <!-- ===== QUIZ ===== -->
    <section class="section quiz-section" id="quiz">
      <h2 id="quiz-heading">Knowledge Check</h2>

      <div class="quiz-question" id="q1">
        <h4>Q1: A conversion flattens the level-of-care ladder into a DMN table with <code>hitPolicy="FIRST"</code>, one row per source branch, conditions copied verbatim. All twelve golden cases match the legacy engine exactly. What is wrong?</h4>
        <ul class="quiz-options">
          <li><label><input type="radio" name="q1" value="a"> Nothing &mdash; matching all twelve golden cases proves the conversion is correct</label></li>
          <li><label><input type="radio" name="q1" value="b"> <code>FIRST</code> is never a valid hit policy for a converted ladder; only <code>COLLECT</code> preserves the semantics</label></li>
          <li><label><input type="radio" name="q1" value="c"> It is correct only while the row order survives, and nothing in DMN, the modeller, code review or CI enforces that &mdash; sorting the rows changes ten of twelve answers</label></li>
          <li><label><input type="radio" name="q1" value="d"> The golden cases do not exercise branch 7, so the match is coincidental</label></li>
        </ul>
        <button class="quiz-check-btn" onclick="checkQuiz('q1','c')">Check Answer</button>
        <div class="quiz-feedback" id="q1-feedback"></div>
      </div>

      <div class="quiz-question" id="q2">
        <h4>Q2: Both systems have a status called <code>APPROVED</code>. The synthesizer maps it 1:1. What breaks, and when do you find out?</h4>
        <ul class="quiz-options">
          <li><label><input type="radio" name="q2" value="a"> Nothing breaks &mdash; identical status names are exactly the case where a 1:1 map is safe</label></li>
          <li><label><input type="radio" name="q2" value="b"> Concurrent review is deleted, because <code>APPROVED</code> is terminal on the clinical side and loops back to <code>IN_REVIEW</code> on the behavioral side &mdash; and nothing reports a problem, because every status name still matches</label></li>
          <li><label><input type="radio" name="q2" value="c"> The build fails at the type check, because the two enums have different arities</label></li>
          <li><label><input type="radio" name="q2" value="d"> Nothing, until a member is discharged, at which point the status transition is rejected</label></li>
        </ul>
        <button class="quiz-check-btn" onclick="checkQuiz('q2','b')">Check Answer</button>
        <div class="quiz-feedback" id="q2-feedback"></div>
      </div>

      <div class="quiz-question" id="q3">
        <h4>Q3: The <code>rules-extractor</code> subagent is scored as <em>passing</em> when it refuses to convert <code>BH_AUTH.LEGACY_OVERRIDE</code>. Why is a successful conversion the wrong answer?</h4>
        <ul class="quiz-options">
          <li><label><input type="radio" name="q3" value="a"> The flag is deprecated, so converting it wastes effort on dead code</label></li>
          <li><label><input type="radio" name="q3" value="b"> Its only documentation is a four-word ticket, it is set on ~400 live rows, and nobody can verify a guess &mdash; so any interpretation changes determinations for real people on the strength of an assumption nobody can check</label></li>
          <li><label><input type="radio" name="q3" value="c"> PL/SQL <code>CHAR(1)</code> flags cannot be represented in DMN</label></li>
          <li><label><input type="radio" name="q3" value="d"> The flag is a security control and belongs in the authorization layer instead</label></li>
        </ul>
        <button class="quiz-check-btn" onclick="checkQuiz('q3','b')">Check Answer</button>
        <div class="quiz-feedback" id="q3-feedback"></div>
      </div>

      <div class="quiz-question" id="q4">
        <h4>Q4: <code>submitAndDecide()</code> writes the authorization and its 42 CFR Part 2 consent in one transaction. A proposed decomposition puts them in separate services with a saga that compensates the authorization if the consent write fails. What is the objection?</h4>
        <ul class="quiz-options">
          <li><label><input type="radio" name="q4" value="a"> Sagas are too slow for an interactive request path</label></li>
          <li><label><input type="radio" name="q4" value="b"> The compensation would need a distributed lock, which the platform does not provide</label></li>
          <li><label><input type="radio" name="q4" value="c"> A disclosure does not compensate. During the window the organisation holds protected treatment content with no record of who the member agreed it could be shared with, and deleting the authorization afterwards does not un-hold it</label></li>
          <li><label><input type="radio" name="q4" value="d"> Nothing &mdash; a saga is the standard answer and the correct one here</label></li>
        </ul>
        <button class="quiz-check-btn" onclick="checkQuiz('q4','c')">Check Answer</button>
        <div class="quiz-feedback" id="q4-feedback"></div>
      </div>

      <div class="quiz-question" id="q5">
        <h4>Q5: The parity validator reports <strong>zero</strong> on the protected-content leak scan. What do you check first?</h4>
        <ul class="quiz-options">
          <li><label><input type="radio" name="q5" value="a"> Nothing &mdash; zero is the goal, so the port is clean</label></li>
          <li><label><input type="radio" name="q5" value="b"> Re-run it with a lower threshold, since a clean result on this check always means the scan is broken</label></li>
          <li><label><input type="radio" name="q5" value="c"> What it says it <em>scanned</em>. Zero over 40 emitted files is a genuine pass; zero over 0 files means the check did not run, which is not a pass</label></li>
          <li><label><input type="radio" name="q5" value="d"> The gap register, since the leak scan derives its findings from the register's verdicts</label></li>
        </ul>
        <button class="quiz-check-btn" onclick="checkQuiz('q5','c')">Check Answer</button>
        <div class="quiz-feedback" id="q5-feedback"></div>
      </div>

      <div class="quiz-question" id="q6">
        <h4>Q6: A student moves the deny-button role check from <code>&lt;c:if test="${sessionScope.roleMask ge 4}"&gt;</code> in the JSP to <code>@if (roleMask &gt;= 4)</code> in the Angular component. Two things are wrong. Which?</h4>
        <ul class="quiz-options">
          <li><label><input type="radio" name="q6" value="a"> The rule is still in a template, and the numeric comparison is the permissive side of a bitwise test &mdash; mask 33 passes it and fails <code>hasRole(MD)</code></label></li>
          <li><label><input type="radio" name="q6" value="b"> Angular's <code>@if</code> is not reactive, and the role should be a signal</label></li>
          <li><label><input type="radio" name="q6" value="c"> The check belongs in the route guard, and the guard should use <code>canMatch</code> rather than <code>canActivate</code></label></li>
          <li><label><input type="radio" name="q6" value="d"> Nothing is wrong; relocating a view rule to the new view layer is exactly what phase 9B asks for</label></li>
        </ul>
        <button class="quiz-check-btn" onclick="checkQuiz('q6','a')">Check Answer</button>
        <div class="quiz-feedback" id="q6-feedback"></div>
      </div>

      <div class="quiz-question" id="q7">
        <h4>Q7: The reference platform gates seven capabilities behind <code>*_ENABLED</code> flags, and the synthesizer mirrors the idiom by adding <code>CONSENT_ENABLED</code>. What is the test that catches this, and what is the answer?</h4>
        <ul class="quiz-options">
          <li><label><input type="radio" name="q7" value="a"> Whether the flag defaults to true &mdash; consent should default on, and then the flag is acceptable</label></li>
          <li><label><input type="radio" name="q7" value="b"> Whether the capability is on the platform team's backlog &mdash; if it is, the flag is a legitimate staging mechanism</label></li>
          <li><label><input type="radio" name="q7" value="c"> "If this were <code>false</code> in production for a week, is the consequence a slow system or an unlawful disclosure?" The second kind must not be a flag: a control that can be switched off in configuration is a default</label></li>
          <li><label><input type="radio" name="q7" value="d"> Whether the flag is read at startup or per request &mdash; per-request flags are safe for regulatory controls</label></li>
        </ul>
        <button class="quiz-check-btn" onclick="checkQuiz('q7','c')">Check Answer</button>
        <div class="quiz-feedback" id="q7-feedback"></div>
      </div>

      <div class="quiz-question" id="q8">
        <h4>Q8: Why is the ASAM domain knowledge a Skill rather than text in each of the eight subagent prompts?</h4>
        <ul class="quiz-options">
          <li><label><input type="radio" name="q8" value="a"> Skills execute faster because they are cached separately from the system prompt</label></li>
          <li><label><input type="radio" name="q8" value="b"> One source of truth, loaded on demand &mdash; six subagents need it, pasted copies drift the moment one is edited, and the bundled references stay out of context until something needs them</label></li>
          <li><label><input type="radio" name="q8" value="c"> Subagent prompts have a length limit that the ASAM criteria exceed</label></li>
          <li><label><input type="radio" name="q8" value="d"> Skills can block tool calls, which is how the PHI gate is implemented</label></li>
        </ul>
        <button class="quiz-check-btn" onclick="checkQuiz('q8','b')">Check Answer</button>
        <div class="quiz-feedback" id="q8-feedback"></div>
      </div>
    </section>

    <!-- ===== REFERENCES ===== -->
    <section class="section" id="references">
      <h2 id="references-heading">References &amp; Resources</h2>

      <h3 id="ref-lab">In the lab</h3>
      <ul>
        <li><code>spec/agent-spec.md</code> &mdash; the twelve-section contract</li>
        <li><code>bhauthtrack/README.md</code> &mdash; "where to start reading" and "things that will bite you"</li>
        <li><code>bhauthtrack/db/02_seed.sql</code> &mdash; the golden set, with each case's expected outcome and the branch it exercises</li>
        <li><code>reference-umlite/VENDORED.md</code> &mdash; what the donor does and does not have, with the build state verified</li>
        <li><code>reference-umlite/BACKLOG.md</code> &mdash; the platform team's own planned-and-unbuilt list</li>
        <li><code>expected_output/</code> &mdash; the reference run: gap register, seam map, term map, screen inventory, rules divergence, the approval prompt</li>
        <li><code>appendix/manual-loop.py</code> &mdash; the loop the SDK runs for you, and where the guardrails have to go without it</li>
      </ul>

      <h3 id="ref-skills">The four Skills</h3>
      <ul>
        <li><code>behavioral-health-um</code> &mdash; the domain, plus four bundled references and a code validator</li>
        <li><code>umlite-architecture</code> &mdash; the target's house style, and an explicit "do not mirror" table</li>
        <li><code>rules-to-dmn</code> &mdash; the seven-step runbook, plus the overlap checker</li>
        <li><code>decompose-transaction</code> &mdash; classify the pairs <em>before</em> drawing the seam</li>
      </ul>

      <h3 id="ref-course">Elsewhere in the course</h3>
      <ul>
        <li><a href="M26-hooks-sessions-agent-sdk.html">M26 &mdash; Hooks, Sessions &amp; the Agent SDK</a> &mdash; the mechanics of <code>can_use_tool</code> and <code>HookMatcher</code></li>
        <li><a href="M14-multi-agent-systems.html">M14 &mdash; Multi-Agent Systems</a> &mdash; coordinator/specialist topologies and context isolation</li>
        <li><a href="M17-output-guardrails-hitl.html">M17 &mdash; Output Guardrails &amp; HITL</a> &mdash; the approval-gate pattern</li>
        <li><a href="CAPSTONE-8-oracle-to-postgres-migration.html">Capstone 8 &mdash; Oracle to PostgreSQL</a> &mdash; the same shape, one layer down: schema and data rather than architecture and domain</li>
      </ul>

      <h3 id="ref-external">External</h3>
      <ul>
        <li>ASAM Criteria &mdash; the placement framework this lab models in simplified form</li>
        <li>42 CFR Part 2 &mdash; the substance-use-disorder confidentiality regulation</li>
        <li>MHPAEA &mdash; mental health parity, and the NQTL comparative analysis requirement</li>
        <li>DMN 1.3 specification &mdash; hit policies, and what each one does on an overlapping table</li>
      </ul>

      <div class="callout-warning" style="margin-top:2rem;">
        <span class="box-label">A last word on what "done" looks like</span>
        <p>Not a green build. A <code>parity-report.json</code> with ten checks each reporting what they scanned, and a <code>manual-review-queue.json</code> with entries in it.</p>
        <p><strong>A run that queues nothing has guessed at something.</strong></p>
      </div>
    </section>
"""
