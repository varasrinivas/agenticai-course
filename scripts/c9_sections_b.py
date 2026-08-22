"""Capstone 9 content, part B: the six animations."""

PART_B = r"""
    <!-- ===== ANIMATION 1 ===== -->
    <section class="section" id="anim-decompose">
      <h2 id="anim-decompose-heading">Animation 1: One WAR Becomes Three Deployables, and a Transaction Is Severed</h2>

      <p>The <span class="term-tooltip">seam map<span class="tooltip-content">The record of where a monolith is cut, which transactional units each cut crosses, and what replaces the atomicity the cut breaks.</span></span> is where a modernization is won or lost. Watch what happens to <code>submitAndDecide()</code> &mdash; five writes, one Oracle transaction &mdash; as the monolith is cut apart.</p>

      <div class="animation-container" id="decompose-container" aria-label="Monolith decomposition animation">
        <div class="animation-title">AuthCaseService.submitAndDecide() &mdash; five writes, one transaction</div>
        <div class="c9-grid" id="decomposeTrack"></div>
        <div class="c9-note" id="decomposeNote">Press play. Each write moves to the service that will own it.</div>
        <div class="animation-controls">
          <button class="anim-btn" onclick="decomposeAnim.toggle()" aria-label="Play or pause the decomposition animation" id="decompose-play">&#9654;</button>
          <button class="anim-btn" onclick="decomposeAnim.restart()" aria-label="Restart the decomposition animation">&#8635;</button>
        </div>
      </div>

      <h3 id="decompose-classify">Classify the pairs before you draw the seam</h3>

      <p>The usual failure is deciding in advance that everything decomposes, then finding a mechanism for each pair. Do it the other way round. Not every pair in one transaction needs the same guarantee:</p>

      <table class="data-table">
        <tr><th>Class</th><th>Meaning</th><th>Mechanism</th></tr>
        <tr><td><strong>Must be atomic</strong></td><td>One existing without the other is unsafe or unlawful</td><td><strong>Keep in one service, one transaction.</strong> Do not split</td></tr>
        <tr><td>Eventual, guaranteed</td><td>Order matters, the gap is tolerable, but it must close</td><td>Transactional outbox + idempotent consumer</td></tr>
        <tr><td>Eventual, best effort</td><td>A delay or a loss is operational, not a correctness problem</td><td>Ordinary publish</td></tr>
        <tr><td>Independent</td><td>No relationship</td><td>Anywhere</td></tr>
      </table>

      <p>In this system, writes 1 and 3 &mdash; the authorization and its Part 2 consent &mdash; are class one. So <code>bh-case-svc</code> owns both, and <strong>the seam moves.</strong></p>

      <div class="callout-warning">
        <span class="box-label">Recording a rejected seam is a result</span>
        <p>The reference answer's seam map contains an entry for <code>authorization | consent</code> marked <strong>rejected</strong>, with the reason:</p>
        <p><em>"The intermediate state &mdash; protected treatment content held with no record of consent &mdash; is one the organisation cannot be in, even briefly, even with a compensation queued. A disclosure does not compensate: you cannot un-hold content you have already held."</em></p>
        <p>An analysis that decomposes everything has not asked the question. The <code>SeamMap</code> class in the lab <em>refuses</em> to record a <code>must-be-atomic</code> seam as cut &mdash; you either move it or record the rejection.</p>
      </div>

      <h3 id="decompose-replacement">What replaces the atomicity you do break</h3>

      <p>For every seam you do cut, five fields. All required, and the data structure enforces it:</p>

      <div class="code-block-wrapper">
        <div class="code-tabs">
          <button class="code-tab active" onclick="switchTab(this,'seam-py')">Python</button>
          <button class="code-tab" onclick="switchTab(this,'seam-ts')">Node / TypeScript</button>
        </div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="seam-py"><pre><code class="language-python"># solution/seam_map.py
sm.add_seam(Seam(
    name="case | notification",
    left="bh-case-svc", right="bh-notify-svc",
    crosses=["AuthCaseService.submitAndDecide"],
    coupling=EVENTUAL_GUARANTEED,
    replacement=AtomicityReplacement(
        mechanism="transactional outbox in bh-case-svc + idempotent consumer "
                  "keyed on (auth_id, review_seq)",
        window="under 60s at the configured relay interval; the legacy cron "
               "polled every 5 minutes, so this is tighter than what it replaces",
        observable="SELECT count(*) FROM outbox_event WHERE published_at IS NULL "
                   "AND created_at &lt; now() - interval '5 minutes'",
        compensation="relay retries with backoff; rows past 3 attempts move to a "
                     "human queue, because the legacy FAILED state was where rows "
                     "went to be forgotten",
        alarm="that count &gt; 0 for 5 consecutive minutes pages the on-call")))</code></pre></div>
        <div class="code-panel" id="seam-ts"><pre><code class="language-typescript">// solution/seam-map.ts
sm.addSeam({
  name: 'case | notification',
  left: 'bh-case-svc', right: 'bh-notify-svc',
  crosses: ['AuthCaseService.submitAndDecide'],
  coupling: Coupling.EventualGuaranteed,
  replacement: {
    mechanism: 'transactional outbox in bh-case-svc + idempotent consumer ' +
               'keyed on (authId, reviewSeq)',
    window: 'under 60s at the configured relay interval; the legacy cron ' +
            'polled every 5 minutes, so this is tighter than what it replaces',
    observable: `SELECT count(*) FROM outbox_event WHERE published_at IS NULL
                   AND created_at &lt; now() - interval '5 minutes'`,
    compensation: 'relay retries with backoff; rows past 3 attempts move to a ' +
                  'human queue, because the legacy FAILED state was where rows ' +
                  'went to be forgotten',
    alarm: 'that count &gt; 0 for 5 consecutive minutes pages the on-call',
  },
});

// All five fields are required by the type, not by a convention. An eventual
// consistency with no observable and no alarm is the same as no guarantee,
// implemented with more moving parts.
interface AtomicityReplacement {
  mechanism: string;
  window: string;
  observable: string;
  compensation: string;
  alarm: string;
}</code></pre></div>
      </div>

      <p>An eventual consistency with no observable and no alarm is the same as no guarantee, implemented with more moving parts. That is why <code>AtomicityReplacement.problems()</code> returns a finding for every missing field, and why <code>Seam.validate()</code> raises rather than warning.</p>
    </section>

    <!-- ===== ANIMATION 2 ===== -->
    <section class="section" id="anim-gap">
      <h2 id="anim-gap-heading">Animation 2: Fifteen Capabilities Resolve Into Four Verdicts</h2>

      <p>This is the deliverable. Watch the distribution, and notice how uncomfortable it is.</p>

      <div class="animation-container" id="gap-container" aria-label="Gap register animation">
        <div class="animation-title">gap-analyst &mdash; one verdict per capability, evidence on every one</div>
        <div class="c9-grid" id="gapTrack"></div>
        <div class="c9-note" id="gapNote">Press play.</div>
        <div class="animation-controls">
          <button class="anim-btn" onclick="gapAnim.toggle()" aria-label="Play or pause the gap register animation" id="gap-play">&#9654;</button>
          <button class="anim-btn" onclick="gapAnim.restart()" aria-label="Restart the gap register animation">&#8635;</button>
        </div>
      </div>

      <div class="callout-why">
        <span class="box-label">Expect an uncomfortable distribution</span>
        <p>If your register comes out mostly <code>port-as-is</code>, you have read the architecture and not the domain. The reference platform is correct for medical prior authorization and thin everywhere behavioral health is demanding &mdash; that asymmetry is the entire premise, and a comfortable register means it was not tested.</p>
        <p>The lab checks this itself. <code>GapRegister.acceptance_problems()</code> reports a failure when more than 60% of entries are <code>port-as-is</code>, when there are fewer than four <code>must-build-new</code>, or when there are no <code>must-not-port</code> at all &mdash; and the coordinator halts the run rather than advancing to synthesis on a register that was not really written.</p>
      </div>

      <h3 id="gap-harm">Naming the harm</h3>

      <p><code>must-not-port</code> is the verdict people soften, and softening it is how a defect gets copied with a note attached. So the tool refuses it:</p>

      <div class="code-block-wrapper">
        <div class="code-tabs">
          <button class="code-tab active" onclick="switchTab(this,'harm-py')">Python</button>
          <button class="code-tab" onclick="switchTab(this,'harm-ts')">Node / TypeScript</button>
        </div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="harm-py"><pre><code class="language-python"># solution/gap_register.py
if self.verdict == MUST_NOT_PORT and not self.harm.strip():
    raise RegisterError(
        f"{self.capability!r}: must-not-port requires a NAMED HARM. "
        f"If you cannot name what goes wrong and for whom, the verdict "
        f"is 'extend'.")</code></pre></div>
        <div class="code-panel" id="harm-ts"><pre><code class="language-typescript">// solution/gap-register.ts
if (entry.verdict === Verdict.MustNotPort &amp;&amp; !entry.harm?.trim()) {
  throw new RegisterError(
    `${entry.capability}: must-not-port requires a NAMED HARM. ` +
    `If you cannot name what goes wrong and for whom, the verdict is 'extend'.`);
}

// Note that this is a THROW, not a warning. A register that accepts a
// must-not-port with no harm is a register whose most important verdict
// means nothing -- and softening that verdict is exactly how a defect gets
// copied forward with a note attached.</code></pre></div>
      </div>

      <p>Not "logging member identifiers is not ideal", but:</p>

      <blockquote style="border-left:3px solid var(--error);padding-left:1rem;margin:1rem 0;color:var(--text-secondary);">This content is 42 CFR Part 2 protected. The monolith had ONE log sink; decomposition multiplies it into one per service plus a broker plus an index. Copying the idiom produces unlawful disclosure at several sinks instead of one &mdash; and nobody decided to make it worse: fan-out is simply what the architecture does with a field.</blockquote>
    </section>

    <!-- ===== ANIMATION 3 ===== -->
    <section class="section" id="anim-hitpolicy">
      <h2 id="anim-hitpolicy-heading">Animation 3: One Case, Two Engines, Two Answers</h2>

      <p>Golden case <strong>500001</strong>. C-SSRS of 4 contributes +6; ASAM dimension 1 of 3 contributes +4. Score reaches 10, dimension 1 is 3, and <em>both</em> branch-7 conditions are true.</p>

      <div class="animation-container" id="hit-container" aria-label="Hit policy comparison animation">
        <div class="animation-title">Case 500001 &mdash; the ladder, and the flattened table</div>
        <div class="c9-split">
          <div>
            <div class="c9-col-title">Legacy ladder &mdash; first commit wins</div>
            <div class="c9-grid" id="hitLadder"></div>
          </div>
          <div>
            <div class="c9-col-title">Flattened table &mdash; <span class="term-tooltip">hit policy<span class="tooltip-content">A DMN decision table's rule for what to do when more than one row matches: FIRST, UNIQUE, PRIORITY, ANY or COLLECT. On an overlapping table there is no neutral choice.</span></span> decides</div>
            <div class="c9-grid" id="hitTable"></div>
          </div>
        </div>
        <div class="c9-note" id="hitNote">Press play.</div>
        <div class="animation-controls">
          <button class="anim-btn" onclick="hitAnim.toggle()" aria-label="Play or pause the hit policy animation" id="hit-play">&#9654;</button>
          <button class="anim-btn" onclick="hitAnim.restart()" aria-label="Restart the hit policy animation">&#8635;</button>
        </div>
      </div>

      <h3 id="hit-policies">There is no neutral choice</h3>

      <table class="data-table">
        <tr><th>Hit policy</th><th>On the overlapping row</th></tr>
        <tr><td><code>FIRST</code></td><td><code>3.7</code> &mdash; <strong>only if row order survives translation</strong></td></tr>
        <tr><td><code>UNIQUE</code></td><td>A runtime error: two rules matched</td></tr>
        <tr><td><code>PRIORITY</code></td><td>Whichever output the priority list ranks higher</td></tr>
        <tr><td><code>COLLECT</code></td><td>Both, and the caller has to choose</td></tr>
      </table>

      <div class="callout-warning">
        <span class="box-label">The uncomfortable finding</span>
        <p>A naive conversion under <code>FIRST</code> <strong>does not diverge</strong>. It reproduces the ladder exactly, on all twelve golden cases, today &mdash; because the rows happen to be in ladder order.</p>
        <p>Then someone sorts the rows by id. A change with no semantic intent whatsoever, that nothing in DMN, in the modeller, in code review or in CI prevents. <strong>Ten of twelve cases change answer.</strong></p>
        <p>So the lesson is not "the naive conversion diverges". It is: <em>the naive conversion is correct by luck</em>, and the luck is an invariant nobody is checking. The lab has a test for each half &mdash; <code>test_first_policy_passes_today</code> exists so that <code>test_first_policy_breaks_when_rows_are_reordered</code> means something.</p>
      </div>

      <h3 id="hit-answer">The reference answer, and what it costs</h3>

      <p><code>UNIQUE</code>, with every lower row tightened by the negation of the rows above it. The exclusions were always there &mdash; they were encoded as <em>position</em>. Now they are encoded as <em>conditions</em>, the table means the same thing whatever order the rows are in, and a future edit that reintroduces an overlap errors loudly instead of silently returning whichever row sits higher.</p>

      <p>It costs something, and the cost is instructive. A decision-table cell constrains exactly <strong>one</strong> input, so this condition cannot be written as a cell at all:</p>

      <div class="code-block-wrapper">
        <div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'tighten-txt')">The condition</button></div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="tighten-txt"><pre><code class="language-python">score &gt;= 8 and not (score &gt;= 10 and dim1 &gt;= 3)
#                    ^^^^^ two inputs, one exclusion -- not expressible as a cell</code></pre></div>
      </div>

      <p>The honest fix is a <strong>named derived input</strong>, <code>overlap_upper</code>, and the row tests <code>overlap_upper &lt; 1</code>. That is better than a workaround: naming the overlap puts it on the face of the table a clinician reads, instead of leaving it implied by which row sits higher.</p>

      <p><code>dmn_writer.to_feel()</code> raises rather than guessing at a cell it cannot express honestly. A guessed cell is a wrong clinical rule that looks finished.</p>
    </section>

    <!-- ===== ANIMATION 4 ===== -->
    <section class="section" id="anim-leak">
      <h2 id="anim-leak-heading">Animation 4: The Narrative Clears HIPAA, Then Fans Out</h2>

      <p>The clinical narrative passes every check the medical platform makes. Watch where it goes.</p>

      <div class="animation-container" id="leak-container" aria-label="Part 2 leak animation">
        <div class="animation-title">One field, four sinks, no consent scope on any of them</div>
        <div class="c9-grid" id="leakTrack"></div>
        <div class="c9-sinkrow" id="leakSinks"></div>
        <div class="c9-note" id="leakNote">Press play.</div>
        <div class="animation-controls">
          <button class="anim-btn" onclick="leakAnim.toggle()" aria-label="Play or pause the leak animation" id="leak-play">&#9654;</button>
          <button class="anim-btn" onclick="leakAnim.restart()" aria-label="Restart the leak animation">&#8635;</button>
        </div>
      </div>

      <div class="callout-security">
        <span class="box-label">Why this is plumbing, not policy</span>
        <p>Nobody decides to leak protected health information. Each of those four sinks is what a normal distributed architecture does with a field: you log the thing you are processing, you put the entity in the event, you index it so it is searchable, you audit before and after.</p>
        <p><strong>Decomposing a monolith multiplies the sinks.</strong> One application log becomes one per service, plus a broker, plus an index &mdash; so a leak that was contained becomes a leak that fans out, without anyone making it worse.</p>
        <p>The count going <em>up</em> is the expected shape of this finding.</p>
      </div>

      <h3 id="leak-scope">The consent scope nobody checks</h3>

      <p>A Part 2 consent states a scope. The common one is <code>AUTH_DECISION_ONLY</code>: the determination may be disclosed and <strong>the narrative may not</strong>. A notification payload carrying both is a violation under the most common consent on file.</p>

      <p>So the emitted event is built from the <em>consent scope</em>, not from the entity:</p>

      <div class="code-block-wrapper">
        <div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'evt-ts')">TypeScript</button></div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="evt-ts"><pre><code class="language-typescript">// libs/events/envelope.ts
//
// The decision event. Carries the determination and NOT the justification:
// the common consent scope is AUTH_DECISION_ONLY, which permits one and not
// the other. Building the payload from the consent scope rather than from
// the entity is the whole difference.
export interface BhDecisioned {
  authId: number;
  planMemberId: string | null;
  outcome: 'APPROVED' | 'PENDED' | 'DENIED';
  grantedLoc: string | null;
  reasonCode: string | null;
  nextReviewDue: string | null;
}</code></pre></div>
      </div>

      <h3 id="leak-checklist">The scan checklist</h3>

      <p><code>validation.check_protected_content_leak()</code> walks every emitted file. Two things it had to learn the hard way, both of which are in the lab's tests:</p>

      <ul>
        <li><strong>An audit table's narrative column spans lines.</strong> <code>CREATE TABLE bh_audit_event</code> and <code>old_narrative TEXT</code> are on different lines, so a line-by-line scan misses the single sink that accumulates one protected copy per update, with no consent scope and no expiry.</li>
        <li><strong>A comment naming the field is not a leak.</strong> Warning the next developer not to log the narrative is exactly what you want a developer to do; flagging it teaches them to stop.</li>
      </ul>
    </section>

    <!-- ===== ANIMATION 5 ===== -->
    <section class="section" id="anim-planes">
      <h2 id="anim-planes-heading">Animation 5: Two Planes &mdash; Knowledge and Control</h2>

      <p>The design decision this capstone exists to teach. Watch which layer each concern lands in.</p>

      <div class="animation-container" id="planes-container" aria-label="Skills and agents layering animation">
        <div class="animation-title">Skills carry knowledge and recipes; agents carry control flow and safety</div>
        <div class="c9-split">
          <div class="c9-plane knowledge">
            <div class="c9-col-title" style="color:var(--info);">Knowledge plane &mdash; .claude/skills/</div>
            <div id="planesKnowledge"></div>
          </div>
          <div class="c9-plane control">
            <div class="c9-col-title" style="color:var(--accent-primary);">Control plane &mdash; Agent SDK</div>
            <div id="planesControl"></div>
          </div>
        </div>
        <div class="c9-note" id="planesNote">Press play.</div>
        <div class="animation-controls">
          <button class="anim-btn" onclick="planesAnim.toggle()" aria-label="Play or pause the planes animation" id="planes-play">&#9654;</button>
          <button class="anim-btn" onclick="planesAnim.restart()" aria-label="Restart the planes animation">&#8635;</button>
        </div>
      </div>

      <p>The rule of thumb, and it decides every case you will meet:</p>

      <div class="tech-def-box">
        <span class="box-label">The test</span>
        <p><strong>Does it decide, branch, parallelize, or block?</strong> Then it is an agent.</p>
        <p><strong>Is it the same steps every time?</strong> Then it is a Skill.</p>
      </div>
    </section>

    <!-- ===== ANIMATION 6 ===== -->
    <section class="section" id="anim-screen">
      <h2 id="anim-screen-heading">Animation 6: A Role Guard Lifts Out of a Template</h2>

      <p>Phase 9B. Three nested JSTL conditionals in <code>decision.jsp</code> <em>are</em> the reviewer-licensure rule. Watch where each piece has to land.</p>

      <div class="animation-container" id="screen-container" aria-label="JSP to route migration animation">
        <div class="animation-title">decision.jsp &rarr; /auth/:id/decide</div>
        <div class="c9-grid" id="screenTrack"></div>
        <div class="c9-note" id="screenNote">Press play.</div>
        <div class="animation-controls">
          <button class="anim-btn" onclick="screenAnim.toggle()" aria-label="Play or pause the screen migration animation" id="screen-play">&#9654;</button>
          <button class="anim-btn" onclick="screenAnim.restart()" aria-label="Restart the screen migration animation">&#8635;</button>
        </div>
      </div>

      <div class="callout-warning">
        <span class="box-label">Moving a rule from JSTL to *ngIf has moved nothing</span>
        <p>It is the same rule, in the same layer, with a different spelling. It looks like migration and is not.</p>
        <p><code>ViewRule.validate()</code> rejects <code>template-conditional</code>, <code>*ngIf</code>, <code>client-side</code>, <code>v-if</code> and <code>css</code> as proposed homes, outright. The permitted homes are a route guard, a server-side check, a computed field on the response, a decision-table input, an API omission, or a workflow candidate group.</p>
      </div>

      <h3 id="screen-guard">A guard is not the enforcement</h3>

      <p>A route guard stops a reviewer reaching a screen they cannot act on. That is a real improvement to the experience and it is <strong>not a control</strong>, because anyone can call the API directly.</p>

      <p>So <code>route_writer.preflight()</code> refuses twice: once when an <em>action</em> gate is proposed for a route guard alone, and again when phase 9A supplied no server-side check for a rule that needs one. The client cannot supply an enforcement the backend does not have &mdash; reporting that is correct; guarding around it and calling the rule migrated is not.</p>

      <h3 id="screen-visibility">Field visibility is a server concern</h3>

      <p>The legacy controller loads the clinical narrative unconditionally and the template hides it with <code>&lt;c:if test="${sessionScope.roleMask ge 2}"&gt;</code>. The guard controls <em>rendering</em>, not <em>retrieval</em> &mdash; the content is in the response body either way, one developer-tools panel from view.</p>

      <p>The fix is that the endpoint does not return the field. Which is why that rule's proposed home is <code>API_OMISSION</code> and the emitted component has no visibility conditional at all: there is nothing to hide.</p>

      <div class="callout-security">
        <span class="box-label">One finding, not two</span>
        <p><code>decision.jsp</code> carefully hides the narrative from intake coordinators. <code>SearchController</code> offers a full-text search across <em>every narrative in the database</em>, to any authenticated user, with no role check and no consent check &mdash; the link is hidden below nurse in the header, and the URL is <code>/search?mode=clinical&amp;q=</code>.</p>
        <p>The control on one screen is undone by its absence on another. Reimplementing that search on an index without adding the missing check reproduces the flaw at higher throughput, with a second copy of the protected content in a second datastore.</p>
      </div>

      <p>The screen inventory finds <strong>twenty rules across seven screens, eleven of which have no server-side enforcement at all.</strong> Those eleven are the ones that vanish in a mechanical port, and each needs a gap-register entry as well as a route.</p>
    </section>
"""
