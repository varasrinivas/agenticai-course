"""Capstone 9 content, sections 1-11: brief through the six animations."""

PART_A = r"""
    <!-- ===== PROJECT BRIEF ===== -->
    <section class="section" id="brief">
      <h2 id="brief-heading">Project Brief</h2>

      <p>A health plan has spent thirty years contracting its behavioral health out to a separate company. That company &mdash; Bridgeway Behavioral Health &mdash; had its own provider network, its own clinical criteria, its own claims platform and, crucially, <strong>its own member identifiers</strong>. The plan has now in-sourced the whole thing.</p>

      <p>Medical prior authorization already runs on a modern distributed platform: an Nx monorepo, an Angular client, a NestJS intake service, a Spring Boot case service, Kafka, Camunda BPMN and DMN, Flyway migrations, a <span class="term-tooltip">transactional outbox<span class="tooltip-content">Write the entity and an outbox row in one local transaction; a separate worker publishes the row and marks it published. Makes persist-and-publish atomic within ONE service -- it does not make two services' writes atomic with each other.</span></span>. Behavioral health runs on <strong>BHAuthTrack 4.2</strong> &mdash; one WAR on Tomcat 8, Java 8, Spring MVC 4.3, JSP, Oracle 11g. Deployed 2011. Last schema change March 2016. The original author left the following month.</p>

      <p>Your job is to build the agent that moves the second onto the first.</p>

      <div class="analogy-box">
        <span class="box-label">Analogy</span>
        <p>Two hospitals merge, and one of them has to move onto the other's records system.</p>
        <p><strong>Before:</strong> you might reasonably assume the work is data entry at scale. Both are hospitals. Both admit patients, treat them, discharge them, bill someone. Map the fields, move the rows, retire the old server.</p>
        <p><strong>The pain:</strong> the receiving system was built for surgery. It records an operation: one decision, one date, one outcome. The arriving department is addiction medicine, where a patient is admitted at one level of intensity and reviewed every three days to decide whether they still need it &mdash; and where the notes are protected by a federal rule the surgical side has never had to think about. There is no field to map "the review that has to happen on Thursday" onto, because the receiving system has never had a Thursday.</p>
        <p><strong>The mapping:</strong> that is this capstone. The modern platform is the surgical records system. It is correct, well built, and missing whole concepts. Your agent has to port onto it <em>and</em> produce the list of things it cannot express &mdash; because a port that silently drops the Thursday review is worse than no port at all.</p>
      </div>

      <h3 id="brief-deliverable">What you are actually delivering</h3>

      <p>Not a repository. A repository <strong>and a gap register</strong>: every capability in the target platform classified against the arriving domain, with the evidence for the verdict.</p>

      <table class="data-table">
        <tr><th>Verdict</th><th>Meaning</th><th>Required</th></tr>
        <tr><td><span class="c9-chip verdict-port">port-as-is</span></td><td>Copy the platform's approach unchanged</td><td>Evidence it is domain-agnostic</td></tr>
        <tr><td><span class="c9-chip verdict-extend">extend</span></td><td>The shape is right, the content is insufficient</td><td>What specifically must be added</td></tr>
        <tr><td><span class="c9-chip verdict-build">must-build-new</span></td><td>Nothing corresponds. Someone has to build it</td><td>What it must do</td></tr>
        <tr><td><span class="c9-chip verdict-not">must-not-port</span></td><td>The platform does this, and copying it here is harmful</td><td><strong>The named harm</strong></td></tr>
      </table>

      <div class="callout-why">
        <span class="box-label">Why it matters</span>
        <p>The register is the reason this is a five-star capstone and not a transpiler exercise. An agent that emits a working Nx workspace has done something a good scaffolding tool does. An agent that emits a working Nx workspace <em>and</em> says <em>"your decision table cannot express a denial, and in this domain the denial is the regulated event"</em> has done something a consultant does.</p>
        <p>The lab enforces that distinction in code. <code>must-not-port</code> without a named harm is rejected by the tool, not by a prompt &mdash; because softening that verdict is exactly how a defect gets copied with a note attached.</p>
      </div>

      <h3 id="brief-topology">The agent topology</h3>

      <p>A coordinator and eight specialists. The coordinator <strong>has no file tools</strong>, deliberately: every read happens inside a subagent with its own context window, so the archaeologist's fifty-four files do not crowd out the rules extraction that follows.</p>

      <table class="data-table">
        <tr><th>Phase</th><th>Subagent</th><th>Produces</th></tr>
        <tr><td>1 Map</td><td><code>architecture-cartographer</code></td><td>Architecture manifest, each capability tagged for BH sufficiency</td></tr>
        <tr><td rowspan="2">2 Excavate</td><td><code>monolith-archaeologist</code></td><td>Domain model, seam map, <strong>term map</strong>, unknowns queue</td></tr>
        <tr><td><code>jsp-archaeologist</code></td><td>Screen inventory and the rules found inside views</td></tr>
        <tr><td>3 Extract rules</td><td><code>rules-extractor</code></td><td>Decision-table IR with a justified hit policy</td></tr>
        <tr><td>4 Gap-analyse</td><td><code>gap-analyst</code></td><td><strong>The gap register</strong></td></tr>
        <tr><td>5A Synthesize</td><td><code>repo-synthesizer</code></td><td>Services, migrations, events, BPMN, DMN</td></tr>
        <tr><td>5B Synthesize</td><td><code>frontend-synthesizer</code></td><td>Routed, role-guarded client</td></tr>
        <tr><td>6 Validate</td><td><code>parity-validator</code></td><td>Ten checks, each reporting what it scanned</td></tr>
      </table>

      <p>The run ships in two gated phases. <strong>9A</strong> is backend and workflow, 10&ndash;12 hours. <strong>9B</strong> is the frontend, 4&ndash;6 hours, and it does not start until 9A is green &mdash; because the screen inventory is its input, and a client cannot supply an enforcement the backend does not have.</p>
    </section>

    <!-- ===== PREREQUISITES ===== -->
    <section class="section" id="prerequisites">
      <h2 id="prerequisites-heading">Prerequisites</h2>

      <p>This capstone assumes the whole agent track. It is the only one that uses
      <code>.claude/skills/</code>, so that part is taught here from scratch &mdash; everything else
      below is assumed knowledge, not revision.</p>

      <div class="table-scroll">
      <table class="data-table">
        <thead><tr><th>Module</th><th>What you need from it</th></tr></thead>
        <tbody>
          <tr><td><a href="M07-mcp-model-context-protocol.html">M07 &mdash; MCP</a></td><td>Both source trees and the emitted workspace are reached through MCP tools. You need <code>create_sdk_mcp_server</code> and the <code>@tool</code> decorator to be unremarkable.</td></tr>
          <tr><td><a href="M13-planning-task-decomposition.html">M13 &mdash; Planning</a></td><td>Six ordered phases with real dependencies, and a gate between 9A and 9B that refuses to open early.</td></tr>
          <tr><td><a href="M14-multi-agent-systems.html">M14 &mdash; Multi-Agent</a></td><td>A coordinator delegating to eight specialists, each reading a different slice of two codebases in its own context.</td></tr>
          <tr><td><a href="M15B-build-agent-subagent-system.html">M15B &mdash; Build Lab</a></td><td>The <code>.claude/agents/</code> pattern and <code>.claude/settings.json</code>. This capstone adds <code>.claude/skills/</code> on top, and assumes you already know what a subagent is.</td></tr>
          <tr><td><a href="M16-input-guardrails.html">M16 &mdash; Input Guardrails</a></td><td><code>PreToolUse</code> denial through <code>can_use_tool</code>. Four of the five hooks here are denials.</td></tr>
          <tr><td><a href="M17-output-guardrails-hitl.html">M17 &mdash; Output Guardrails &amp; HITL</a></td><td>The finalization gate always denies. If you have not met a human-approval gate before, that will read as a bug.</td></tr>
          <tr><td><a href="M18-evaluation-testing.html">M18 &mdash; Evaluation</a></td><td>242 offline tests and a 24-scenario eval harness. Several scenarios score a <em>refusal</em> rather than an answer.</td></tr>
          <tr><td><a href="M22B-deploy-local-cloud.html">M22B &mdash; Deploy</a></td><td>Local Docker first, then GCP and AWS. Only needed if you do the deployment section.</td></tr>
        </tbody>
      </table>
      </div>

      <p><strong>Tooling.</strong> Python 3.10+ and an Anthropic API key. Node 18+ only for phase 9B.
      Docker is optional and only for the deployment section &mdash; every test and eval in this lab
      runs offline without it.</p>
    </section>

    <!-- ===== WHY BH != CLINICAL ===== -->
    <section class="section" id="why-bh">
      <h2 id="why-bh-heading">Why Behavioral Health Is Not Clinical With Different Codes</h2>

      <p>Four differences, and each one breaks an assumption the medical platform is built on. If you take nothing else from this capstone, take these.</p>

      <h3 id="why-ladder">1. The criteria are a ladder, not a yes/no</h3>

      <p>Medical prior auth asks: <em>is this procedure medically necessary for this diagnosis?</em> One question, one answer.</p>

      <p>Behavioral health asks: <strong>at what intensity of care should this person be treated right now?</strong> The answer is a rung on the <span class="term-tooltip">ASAM<span class="tooltip-content">American Society of Addiction Medicine. Its criteria place a person at one of several levels of care, from outpatient through medically managed inpatient, using six independently scored dimensions.</span></span> ladder &mdash; 1.0 outpatient through 4.0 medically managed intensive inpatient &mdash; chosen from six independently scored dimensions.</p>

      <p>So an engine that can only approve or deny <em>the level that was requested</em> is missing the domain. It has to be able to grant a different level than the one asked for, in either direction, and say why.</p>

      <div class="callout-warning">
        <span class="box-label">The one that catches people</span>
        <p><strong>Dimension 4 is readiness to change, and a LOW score argues AGAINST residential placement.</strong></p>
        <p>Every other dimension reads "higher means more care". Dimension 4 inverts, because placing someone with no engagement into a residential setting historically produces an against-medical-advice discharge within 72 hours &mdash; consuming a bed, achieving nothing, and often making the next engagement harder.</p>
        <p>Treat all six as severity indicators and you will get this backwards and never notice, because the answer is still a plausible level of care.</p>
      </div>

      <h3 id="why-concurrent">2. Authorization is a series, not an event</h3>

      <p>A medical case is decided once. A behavioral-health case is decided, and then <strong>reviewed again on a cadence set by the level of care</strong>, until the member is discharged or steps down. This is <span class="term-tooltip">concurrent review<span class="tooltip-content">The recurring continued-stay review that runs for the life of an authorization. Every three days at ASAM 4.0, every seven at 3.5, every fourteen at partial hospitalization.</span></span>.</p>

      <table class="data-table">
        <tr><th>ASAM level</th><th>What it is</th><th>Review cadence</th></tr>
        <tr><td><code>4.0</code></td><td>Medically managed intensive inpatient</td><td>3 days</td></tr>
        <tr><td><code>3.7</code></td><td>Medically monitored intensive inpatient</td><td>5 days</td></tr>
        <tr><td><code>3.5</code></td><td>Clinically managed high-intensity residential</td><td>7 days</td></tr>
        <tr><td><code>3.1</code></td><td>Clinically managed low-intensity residential</td><td>14 days</td></tr>
        <tr><td><code>2.5</code></td><td>Partial hospitalization</td><td>14 days</td></tr>
        <tr><td><code>2.1</code></td><td>Intensive outpatient</td><td>30 days</td></tr>
        <tr><td><code>1.0</code></td><td>Outpatient</td><td>90 days</td></tr>
      </table>

      <p>Three consequences for any system design:</p>

      <ul>
        <li>An approval is <strong>not terminal</strong>. It must schedule its own next review.</li>
        <li>A next-review date is a <strong>regulatory deadline</strong>, not a reminder. A residential authorization not re-reviewed inside its interval is out of compliance, whether or not anyone was told.</li>
        <li>The process model needs a <strong>timer-driven loop</strong>. A workflow that terminates after the first decision cannot express the domain at all.</li>
      </ul>

      <p>Note also that the cadence follows the <em>level</em>, not the units approved. A fourteen-day approval at ASAM 3.5 still comes back for review in seven days. Systems get this wrong by deriving the next review from the authorization's end date, which is a reasonable-looking mistake that quietly halves the number of reviews.</p>

      <h3 id="why-part2">3. Two privacy regimes, not one</h3>

      <p>HIPAA covers everything. <strong><span class="term-tooltip">42 CFR Part 2<span class="tooltip-content">The federal rule protecting records from federally assisted substance-use-disorder treatment programs. Disclosure requires a consent that NAMES the recipient, states a purpose and scope, and expires.</span></span> additionally covers records from federally assisted substance-use-disorder treatment programs</strong>, and it is much stricter.</p>

      <table class="data-table">
        <tr><th></th><th>HIPAA</th><th>42 CFR Part 2</th></tr>
        <tr><td>Disclosure for treatment, payment, operations</td><td>Permitted without authorization</td><td><strong>Requires consent</strong></td></tr>
        <tr><td>Recipient</td><td>A class of recipients is fine</td><td><strong>Must be named</strong></td></tr>
        <tr><td>Scope</td><td>"Minimum necessary" standard</td><td>Consent states scope explicitly</td></tr>
        <tr><td>Duration</td><td>May be open-ended</td><td><strong>Expires</strong>; revocable</td></tr>
        <tr><td>Downstream recipients</td><td>Bound if a business associate</td><td>Bound by the <strong>redisclosure notice</strong></td></tr>
        <tr><td>Accounting of disclosures</td><td>Required for some</td><td><strong>Required</strong></td></tr>
      </table>

      <p>The practical summary: under HIPAA the question is <em>"is this use appropriate?"</em>. Under Part 2 it is <em>"is this exact recipient named in an unexpired, unrevoked consent that covers this purpose and this scope?"</em> &mdash; a question a system can only answer if it stores consents that way and checks them at the point of disclosure.</p>

      <p><strong>A system can be fully HIPAA-compliant and violate Part 2 on every request.</strong> That is the usual failure, and it is almost always plumbing rather than policy. You will build it, watch it happen, and then fix it.</p>

      <h3 id="why-parity">4. Parity is a design constraint</h3>

      <p><span class="term-tooltip">MHPAEA<span class="tooltip-content">The Mental Health Parity and Addiction Equity Act. A limitation applied to behavioral-health benefits may be no more restrictive than the comparable limitation on medical/surgical benefits &mdash; both as written and as applied.</span></span> requires that a limitation applied to behavioral health be no more restrictive than the comparable limitation on medical/surgical care. The hard ones are <strong><span class="term-tooltip">non-quantitative treatment limitations<span class="tooltip-content">NQTLs. Process-level limits &mdash; review frequency, step therapy, criteria strictness, network standards &mdash; that parity puts in scope alongside numeric caps. A BH-only limitation with no med/surg analogue is an exposure.</span></span></strong>: review frequency, step-therapy requirements, criteria strictness, network standards.</p>

      <p>You will find these in the legacy code as rules that look entirely reasonable in isolation. When you do, <strong>neither port them silently nor drop them silently.</strong> Porting carries the exposure forward; dropping changes outcomes for real members. Escalate.</p>

      <div class="tech-def-box">
        <span class="box-label">The reviewer-licensure rule</span>
        <p>One more, and it is load-bearing throughout this capstone:</p>
        <p><strong>A nurse reviewer may approve. A nurse may never deny. Only a physician may issue an <span class="term-tooltip">adverse determination<span class="tooltip-content">A denial, or an approval at a level lower than the one requested. The regulated event in behavioral health, and the one that must trace to a published, applied criterion.</span></span></strong> &mdash; and for substance-use or psychiatric level of care, a same-specialty peer reviewer.</p>
        <p>It is a separation of duties required by accreditation. It is also why a <code>PENDED</code> status exists at all: that is the state a case waits in for someone licensed to deny it. A system without <code>PENDED</code> has either auto-denials or no denials.</p>
        <p>You will find this rule implemented four times, in four places, none of which is a permission system.</p>
      </div>
    </section>

    <!-- ===== THE DONOR ===== -->
    <section class="section" id="donor">
      <h2 id="donor-heading">The Donor, and Its Holes</h2>

      <p>The modern platform describes itself, in its own README, as a <em>"clean-room learning rebuild."</em> That is an honest description and you should take it seriously. It is deliberately thin, and the thinness is invisible until you point a new domain at it.</p>

      <p>Here is what the <code>architecture-cartographer</code> subagent finds when it opens the files rather than the documentation:</p>

      <table class="data-table">
        <tr><th>What the platform has</th><th>Fine for medical prior auth because&hellip;</th><th>Fatal for behavioral health because&hellip;</th></tr>
        <tr><td><strong>Two tables. Zero foreign keys.</strong> <code>member_id VARCHAR(32)</code>, opaque, no member table</td><td>One case, one decision, nothing to relate it to</td><td>Concurrent review has nowhere to live, and the <span class="term-tooltip">carve-out<span class="tooltip-content">Behavioral health contracted to a separate vendor with its own network, criteria, claims platform and member identifiers. Explains why a BH system keys on an identifier the health plan does not recognise.</span></span> has two member identifiers that are not interchangeable</td></tr>
        <tr><td><code>notes</code> is validated with <code>@IsOptional @IsString @Length(0,2000)</code> and then <strong>silently discarded</strong> &mdash; not a column, not an entity field, not in either event payload</td><td>Nobody reads it</td><td>It is simultaneously the medical-necessity evidence <em>and</em> the Part 2 protected content. The caller gets a <code>201</code> and believes it landed</td></tr>
        <tr><td>A decision table with <code>hitPolicy="FIRST"</code>, three rules, inputs of procedure code and requested units. <strong>No rule can output <code>DENIED</code>.</strong> One row is dead code</td><td>Denials are rare and handled by a person</td><td>The denial is the regulated event, and parity requires each one to trace to a published criterion</td></tr>
        <tr><td>A one-shot process: start &rarr; decide &rarr; gateway &rarr; maybe review &rarr; notify &rarr; end. <strong>The manual-review task has no assignee and no candidate group</strong></td><td>Correct: a medical case is decided once</td><td>No continued-stay loop &mdash; and the licensure rule disappears with the missing candidate group, while the diagram still looks complete</td></tr>
        <tr><td><strong>No audit table.</strong> No <code>createdBy</code>, no <code>updatedBy</code>, no transition history. <code>transitionTo()</code> is unguarded</td><td>Deferred; it is on their backlog</td><td>Part 2 requires an accounting of disclosures, and there is nothing to build one from</td></tr>
        <tr><td><code>um.security.enabled=false</code> by default; even enabled it is <strong>authentication-only</strong> &mdash; no roles, no scopes, no method security</td><td>Deferred</td><td>No way to scope a consent-limited disclosure, and no way to express the licensure rule</td></tr>
        <tr><td>PHI in cleartext logs; event payloads as plain JSON on an <strong>unauthenticated broker</strong>; an Elasticsearch index; no TLS anywhere</td><td>Member identifiers only, in a teaching environment</td><td>Decomposition turns one leak into several, and this content is federally protected</td></tr>
        <tr><td><strong>Zero tests.</strong> CI runs <code>npm test --if-present</code>, so their absence never fails the build</td><td>&mdash;</td><td>Nothing catches any of the above</td></tr>
        <tr><td>A single unrouted form. <code>app.config.ts</code> provides only <code>provideHttpClient()</code>; <code>@angular/router</code> is a <em>declared dependency that was never wired</em>. Three shared components are exported and never imported</td><td>It demonstrates the intake call</td><td>A UM client is multi-screen, session-based, role-gated and worklist-driven. None of that is demonstrated</td></tr>
      </table>

      <div class="callout-why">
        <span class="box-label">Why it matters</span>
        <p>None of that is a defect <em>for the slice it teaches</em>. Every one is fatal here. <strong>Detecting that is the capstone.</strong></p>
        <p>And the platform team knows. Their own enhancement backlog &mdash; vendored into the lab as <code>reference-umlite/BACKLOG.md</code>, and readable by the <code>gap-analyst</code> through <code>ref_read_backlog</code> &mdash; lists guarded status transitions (#1), persisting decision rationale (#2), extended DMN criteria (#6), an appeals path (#7) and SLA turnaround timers (#8) as <strong>planned and unbuilt</strong>.</p>
        <p>When your register agrees with their backlog, that is your strongest kind of finding: two independent readings reached the same conclusion. Which is why the <code>gap-analyst</code> reports agreements and disagreements as <em>separate lists</em>. A register that reports only agreements has been confirmed, not checked.</p>
      </div>

      <div class="callout-warning">
        <span class="box-label">Do not infer a capability from a dependency</span>
        <p><code>@angular/router</code> is in <code>package.json</code>. Nothing calls <code>provideRouter</code>.</p>
        <p>An architecture manifest that reports "routing: present" because the package is on the classpath is the single most damaging mistake available to the cartographer, because everyone downstream trusts the manifest instead of re-reading. The same trap exists for a declared Kafka topic with no producer and no consumer, and for an enum value that is never assigned.</p>
        <p>Report what is <strong>wired</strong>. List declared-but-unused separately.</p>
      </div>

      <h3 id="donor-good">The one trait worth copying wholesale</h3>

      <p>Capability layering behind feature flags: <code>EVENTS_ENABLED</code>, <code>OUTBOX_ENABLED</code>, <code>WORKFLOW_ENABLED</code>, <code>CACHE_ENABLED</code>, <code>SEARCH_ENABLED</code>, <code>REPLICA_ENABLED</code>, <code>SECURITY_ENABLED</code>. Seven flags, each gating one capability, so the stack stays runnable with any subset enabled. It is the platform's best structural idea.</p>

      <p>Mirror the idiom. But <strong>classify each flag before you do</strong>, and the test is one question:</p>

      <div class="callout-security">
        <span class="box-label">The flag test</span>
        <p><em>If this were <code>false</code> in production for a week, what would the consequence be?</em></p>
        <p>A slow page &rarr; a flag is fine.</p>
        <p>An unlawful disclosure, an unlicensed determination, or a missing audit trail &rarr; <strong>it must not be a flag at all.</strong> A regulatory control that can be switched off in configuration is not a control; it is a default.</p>
        <p>Note that the donor ships <code>SECURITY_ENABLED=false</code>. That is a defensible default for a teaching platform and an indefensible one here.</p>
      </div>
    </section>

    <!-- ===== THE MONOLITH ===== -->
    <section class="section" id="monolith">
      <h2 id="monolith-heading">The Monolith: A Guided Tour of BHAuthTrack 4.2</h2>

      <p>Fifty-four files. Java 8, Spring MVC 4.3, JSP/JSTL, one WAR on Tomcat 8, Oracle 11g, Quartz, Log4j 1.x. Read five of them, in this order, and you will have met everything that makes this hard.</p>

      <h3 id="monolith-1">1. <code>db/schema_changes.txt</code> &mdash; read this before the schema</h3>

      <p>There is no migration tool. DDL is applied by hand in each environment by whoever is doing the release, and this file is the only record of what was applied and when. It says so itself:</p>

      <blockquote style="border-left:3px solid var(--accent-primary);padding-left:1rem;margin:1rem 0;color:var(--text-secondary);">Where this file and <code>01_schema.sql</code> disagree, THIS FILE IS CLOSER TO PRODUCTION.</blockquote>

      <p>It records two production drifts, one prod hotfix never back-ported, and &mdash; the important one &mdash; <strong>BHA-1180</strong>, the carve-out identifier problem. It also names two tables the application reads that no release ever created, both owned by other teams, both load-bearing inputs to a clinical decision. An inventory built from the schema file alone misses both.</p>

      <h3 id="monolith-2">2. <code>db/03_PKG_LOC_RULES.sql</code> &mdash; the level-of-care engine</h3>

      <p>Not a rule set. A <strong>stateful first-match ladder</strong>: it accumulates into <code>v_score</code> across branches, and returns at the first branch that commits. Several branches fall through deliberately. The order is load-bearing.</p>

      <div class="code-block-wrapper">
        <div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'ladder-sql')">PL/SQL</button></div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="ladder-sql"><pre><code class="language-sql">-- BRANCH 7 -- THE OVERLAP. Read carefully.
--
-- Both of the next two conditions can be true at once. A case with
-- v_score = 10 and v_d1 = 3 -- reached by <span class="term-tooltip">C-SSRS<span class="tooltip-content">Columbia Suicide Severity Rating Scale, 0-5. Scores of 4 and 5 are active ideation with intent -- a threshold, not a gradient.</span></span> 4 (+6) and dimension 1
-- of 3 (+4) -- satisfies the 3.7 test AND would satisfy the 3.5 test
-- below it. Because this is a first-commit ladder, it lands on 3.7 --
-- the MORE intensive level -- and the 3.5 branch never runs.
--
-- Flatten these into an unordered decision table and the answer depends
-- entirely on the hit policy you pick.
IF v_score &gt;= 10 AND v_d1 &gt;= 3 THEN
    r.granted_loc := '3.7'; ... RETURN r;
END IF;

IF v_score &gt;= 8 THEN
    r.granted_loc := '3.5'; ... RETURN r;
END IF;</code></pre></div>
      </div>

      <p>There is a second engine. <code>LocRulesService.java</code> layers three more adjustments in Java <em>after</em> the PL/SQL has already committed to an outcome &mdash; so it can only downgrade or pend, never upgrade. <strong>Neither layer alone is the rule set.</strong> Convert one and three of the twelve golden cases come back wrong, plausibly.</p>

      <h3 id="monolith-3">3. <code>service/AuthCaseService.java</code> &mdash; the transaction</h3>

      <p><code>submitAndDecide()</code> is <code>@Transactional</code> and performs five writes: the authorization, the assessments, the <strong>Part 2 consent</strong>, the initial level-of-care review, and an outbound queue row. One Oracle transaction. All of them or none.</p>

      <p>The class comment explains why, and it is a requirement rather than an accident:</p>

      <blockquote style="border-left:3px solid var(--accent-primary);padding-left:1rem;margin:1rem 0;color:var(--text-secondary);">This started in 2011 as three separate services. They were merged in 2013 because the transaction boundaries kept producing orphaned consent rows when the JTA config drifted between environments.</blockquote>

      <p>An authorization from a Part 2 program that exists without its consent record is protected content held with no record of who the member agreed it could be shared with. Under this design that state is <em>unrepresentable</em>. Any redesign has to say what makes it unrepresentable instead.</p>

      <p>The same method also logs the clinical narrative, on purpose, so the appeals team can reconstruct a challenged determination. That log rolls to a file that is backed up nightly to the share the reporting team reads from. On this system that is <strong>one</strong> sink.</p>

      <h3 id="monolith-4">4. <code>service/AuthStatusService.java</code> &mdash; the workflow that is not one</h3>

      <p>There is no process engine. There is a <code>STATUS</code> column and a <code>switch</code>, and reading that switch is how you recover the process model. The thing to notice:</p>

      <div class="code-block-wrapper">
        <div class="code-tabs"><button class="code-tab active" onclick="switchTab(this,'status-java')">Java</button></div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="status-java"><pre><code class="language-java">case "APPROVED":
    // Continued stay. An approved authorization is not finished; it comes
    // back around on its cadence. This is the single biggest structural
    // difference from medical prior auth, and it is expressed here as a
    // status that loops.
    auth.setStatus("IN_REVIEW");
    break;</code></pre></div>
      </div>

      <p>It also branches on <code>LEGACY_OVERRIDE</code>, which is where this capstone puts its deliberate dead end. More on that below.</p>

      <h3 id="monolith-5">5. <code>webapp/WEB-INF/jsp/decision.jsp</code> &mdash; rules in a template</h3>

      <p>Three business rules and two derived values, implemented in a view. The file's own maintenance note says:</p>

      <blockquote style="border-left:3px solid var(--accent-primary);padding-left:1rem;margin:1rem 0;color:var(--text-secondary);">The role checks below are the ONLY thing standing between a nurse reviewer and the deny button on most deployments. <code>AuthCaseService.issueDenial()</code> re-checks, but that was added after the fact and there are two other call paths that do not go through it. Treat this file as security-relevant.</blockquote>

      <p>And, further down, two scriptlets computing the continued-stay countdown and the regulatory turnaround clock &mdash; <strong>the only implementation of either rule in the codebase</strong>. Reporting reimplemented both in Crystal and the two have disagreed since 2015.</p>

      <div class="callout-security">
        <span class="box-label">The deliberate dead end</span>
        <p><code>BH_AUTH.LEGACY_OVERRIDE</code>, added under ticket BHA-2291 in February 2013. The ticket body reads, <em>in full</em>: <strong>"per DM request"</strong>.</p>
        <p>No design note. No acceptance criteria. No test. It is handled in two places and set on roughly 400 live rows. Nobody currently at Bridgeway can say what it means, which determinations it was meant to cover, or who "DM" was.</p>
        <p><strong>This belongs in the manual-review queue, not in a decision table.</strong> A run that reports 100% automated coverage has guessed at it &mdash; and the cost of guessing wrong is a changed determination for a real person. The evaluation suite scores a refusal here, and scores a confident interpretation as zero however reasonable it sounds.</p>
      </div>
    </section>

    <!-- ===== GLOSSARY ===== -->
    <section class="section" id="glossary">
      <h2 id="glossary-heading">Domain Glossary</h2>

      <p>Read this once before the build guide. Every term appears in the fixtures.</p>

      <table class="data-table">
        <tr><th>Term</th><th>Meaning</th></tr>
        <tr><td><strong>Carve-out</strong></td><td>Behavioral health contracted to a separate vendor with its own network, criteria, claims platform <strong>and member identifiers</strong>. Explains why BH systems key on an identifier the health plan does not recognise</td></tr>
        <tr><td><strong>ASAM</strong></td><td>American Society of Addiction Medicine. Levels 0.5&ndash;4.0, placed using six dimensions</td></tr>
        <tr><td><strong>The six dimensions</strong></td><td>1 withdrawal potential &middot; 2 biomedical &middot; 3 emotional/behavioral/cognitive &middot; <strong>4 readiness to change (inverts)</strong> &middot; 5 relapse potential &middot; 6 recovery environment</td></tr>
        <tr><td><strong>LOCUS / CALOCUS</strong></td><td>Level of Care Utilization System &mdash; the psychiatric analogue of ASAM. CALOCUS is the child and adolescent version</td></tr>
        <tr><td><strong>Concurrent review</strong></td><td>The recurring continued-stay review that runs for the life of an authorization</td></tr>
        <tr><td><strong>PHP</strong></td><td>Partial hospitalization, ASAM 2.5. Day treatment; the member goes home at night</td></tr>
        <tr><td><strong>IOP</strong></td><td>Intensive outpatient, ASAM 2.1</td></tr>
        <tr><td><strong>C-SSRS</strong></td><td>Columbia Suicide Severity Rating Scale, 0&ndash;5. <strong>4 and 5 are active ideation with intent</strong> &mdash; a threshold, not a gradient</td></tr>
        <tr><td><strong>PHQ-9 / GAD-7</strong></td><td>Depression (0&ndash;27) and anxiety (0&ndash;21) severity instruments</td></tr>
        <tr><td><strong>42 CFR Part 2</strong></td><td>Federal rule protecting records from federally assisted substance-use-disorder treatment programs. Consent must name the recipient</td></tr>
        <tr><td><strong>Redisclosure notice</strong></td><td>The notice that must accompany a Part 2 disclosure, binding the recipient too</td></tr>
        <tr><td><strong>NQTL</strong></td><td>Non-quantitative treatment limitation. A process-level limit &mdash; review frequency, step therapy, network standards &mdash; that parity puts in scope</td></tr>
        <tr><td><strong>Adverse determination</strong></td><td>A denial, or an approval at a lower level than requested. The regulated event</td></tr>
        <tr><td><strong>Step-down</strong></td><td>Moving to a less intensive level. Normal and expected; <em>not</em> a denial</td></tr>
        <tr><td><strong><code>PENDED</code></strong></td><td>The state a case waits in for someone licensed to decide it. A separation of duties encoded as a status</td></tr>
        <tr><td><strong>TAT</strong></td><td>Turnaround time. Expedited 72 hours, standard 14 calendar days. Missing it can force an automatic approval depending on line of business</td></tr>
        <tr><td><strong>X12 278</strong></td><td>The EDI transaction for a health-care services review request. Carries no clinical narrative and no assessment</td></tr>
      </table>
    </section>
"""
