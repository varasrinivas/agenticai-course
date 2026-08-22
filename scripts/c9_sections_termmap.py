"""Capstone 9: the term-map section.

Sits between "Why BH is not clinical" and "The Donor and Its Holes", because it
is the bridge — the reader has just learned the two domains differ, and this is
where they learn the two *vocabularies* differ too, in a way that hides.
"""

PART_TERMMAP = r"""
    <!-- ===== THE TERM MAP ===== -->
    <section class="section" id="term-map">
      <h2 id="term-map-heading">The Vocabularies Collide, and One Collision Is Silent</h2>

      <p>Both systems model utilization management. Neither was written with the other in mind, so the vocabulary diverged &mdash; <strong>in two ways, and they carry opposite risks.</strong></p>

      <div class="c9-split" style="margin:1.5rem 0;">
        <div class="c9-plane knowledge">
          <div class="c9-col-title" style="color:var(--info);">A. Different name, same concept</div>
          <p style="font-size:0.9rem;margin:0;"><code>notes</code> and <code>CLINICAL_NARRATIVE</code>. <code>outbox_event</code> and <code>BH_AUTH_QUEUE</code>.</p>
          <p style="font-size:0.9rem;margin-top:0.5rem;">The risk is <strong>missing</strong> the mapping: you build a duplicate concept, or drop a field because nothing on the other side looked like it.</p>
          <p style="font-size:0.9rem;margin-top:0.5rem;color:var(--text-secondary);">This kind announces itself. The names differ, so somebody goes looking.</p>
        </div>
        <div class="c9-plane" style="border-color:var(--error);">
          <div class="c9-col-title" style="color:var(--error);">B. Same name, different meaning</div>
          <p style="font-size:0.9rem;margin:0;"><code>APPROVED</code> is a status in both systems.</p>
          <p style="font-size:0.9rem;margin-top:0.5rem;">The risk is <strong>assuming</strong> the mapping. A 1:1 map compiles, passes review, looks obviously correct, and is wrong.</p>
          <p style="font-size:0.9rem;margin-top:0.5rem;color:#FDA4AF;"><strong>This kind is silent, and it is the one that matters.</strong></p>
        </div>
      </div>

      <h3 id="term-map-statuses">Four of five statuses do not mean what they look like</h3>

      <p>The two enums overlap on five names. Read them side by side:</p>

      <table class="data-table">
        <tr><th>Value</th><th>Clinical platform</th><th>Behavioral health</th><th>1:1?</th></tr>
        <tr><td><code>SUBMITTED</code></td><td>Initial state</td><td>Initial state</td><td><span class="c9-chip verdict-port">yes</span></td></tr>
        <tr><td><code>APPROVED</code></td><td><strong>Terminal</strong></td><td><strong>Re-enters review on its cadence.</strong> The switch loops it to <code>IN_REVIEW</code></td><td><span class="c9-chip verdict-not">no</span></td></tr>
        <tr><td><code>IN_REVIEW</code></td><td>Declared and <strong>never assigned</strong> &mdash; a dead enum value</td><td>The busiest state in the system</td><td><span class="c9-chip verdict-not">no</span></td></tr>
        <tr><td><code>DENIED</code></td><td><strong>Unreachable</strong> &mdash; no DMN rule can output it</td><td>Reachable, but only for an <em>administrative</em> fact: a terminated provider</td><td><span class="c9-chip verdict-not">no</span></td></tr>
        <tr><td><code>PENDED</code></td><td>A generic hold</td><td>A <strong>separation-of-duties control</strong> &mdash; the state a case waits in for someone licensed to deny it</td><td><span class="c9-chip verdict-not">no</span></td></tr>
      </table>

      <div class="callout-security">
        <span class="box-label">Why this is worse than a rename</span>
        <p>A renamed field fails loudly. You go looking for <code>notes</code> on the behavioral side, do not find it, and have to decide something.</p>
        <p><code>APPROVED</code> &rarr; <code>APPROVED</code> is a mapping nobody writes down, because it does not feel like a decision. It compiles. It passes review. Every status name still matches. And it has <strong>deleted concurrent review</strong> &mdash; the single biggest structural difference between the two domains &mdash; with nothing anywhere reporting a problem.</p>
      </div>

      <h3 id="term-map-structure">Making the unexamined pair impossible to record</h3>

      <p>So <code>TermMapping.same_semantics</code> has <strong>no default</strong>. You cannot construct a mapping without answering the question:</p>

      <div class="code-block-wrapper">
        <div class="code-tabs">
          <button class="code-tab active" onclick="switchTab(this,'termmap-py')">Python</button>
          <button class="code-tab" onclick="switchTab(this,'termmap-ts')">Node / TypeScript</button>
        </div>
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <div class="code-panel active" id="termmap-py"><pre><code class="language-python"># solution/term_map.py
@dataclass
class TermMapping:
    kind: str
    clinical: str
    behavioral: str
    #: REQUIRED, NO DEFAULT. The whole point of this module.
    #:
    #: A name-identical pair recorded without answering this is the failure
    #: mode the map exists to prevent, so it cannot be recorded at all.
    same_semantics: bool
    evidence: str
    divergence: str = ""    # required when same_semantics is False
    action: str = ""        # required when same_semantics is False

    @property
    def silent_trap(self) -&gt; bool:
        # Same name, different meaning. The dangerous quadrant.
        return self.name_identical and not self.same_semantics</code></pre></div>
        <div class="code-panel" id="termmap-ts"><pre><code class="language-typescript">// solution/term-map.ts
interface TermMapping {
  kind: TermKind;
  clinical: string;
  behavioral: string;
  /**
   * REQUIRED, NO OPTIONAL MARKER. The whole point of this module.
   *
   * A name-identical pair recorded without answering this is the failure
   * mode the map exists to prevent, so it cannot be recorded at all.
   */
  sameSemantics: boolean;
  evidence: string;
  divergence?: string;   // required when sameSemantics is false
  action?: string;       // required when sameSemantics is false
}

/** Same name, different meaning. The dangerous quadrant. */
function silentTrap(m: TermMapping): boolean {
  return m.clinical.trim().toLowerCase() === m.behavioral.trim().toLowerCase()
      &amp;&amp; !m.sameSemantics;
}</code></pre></div>
      </div>

      <p>And a divergence must state <strong>what the port has to do about it</strong>. A divergence with no action is a note, and notes do not survive a refactor.</p>

      <p>Note also that <code>name_identical</code> compares case-insensitively. <code>member_id</code> and <code>MEMBER_ID</code> are the same name in two conventions, and a comparison that missed that would let the most dangerous pair in the schema through as a harmless rename &mdash; one identifier on the clinical side, <em>two</em> on the behavioral side, with 31% of the second one null.</p>

      <h3 id="term-map-orphans">The rows with no counterpart</h3>

      <p>Usually the most interesting entries, because each names a capability the target platform has never needed:</p>

      <table class="data-table">
        <tr><th>Behavioral only</th><th>Why the clinical platform never needed it</th></tr>
        <tr><td><code>BH_LOC_REVIEW</code></td><td>A medical case is decided once. Concurrent review has no analogue</td></tr>
        <tr><td><code>BH_CONSENT</code></td><td>HIPAA has no named-recipient requirement, so the concept never arose</td></tr>
        <tr><td><code>BH_ASSESSMENT</code></td><td>The clinical engine decides from a procedure code, not a six-dimension assessment</td></tr>
        <tr><td><code>ROLE_MASK</code></td><td>Security is off by default and authentication-only when on &mdash; there is nothing to map roles <em>onto</em></td></tr>
        <tr><td><code>EXPIRED</code></td><td>Only reachable in a domain that has a cadence to miss</td></tr>
        <tr><td><code>LEGACY_OVERRIDE</code></td><td>No counterpart, and <strong>no surviving explanation on the side that has it</strong>. Recorded as <em>do not map</em></td></tr>
      </table>

      <p>And one missing from <em>both</em>: <code>APPEALED</code>. The platform team's backlog lists an appeals path as planned-and-unbuilt; the legacy system handles appeals entirely outside itself, in a shared mailbox and a spreadsheet. Neither side has it and both need it &mdash; a finding the gap analysis only reaches by reading the other team's backlog.</p>

      <div class="callout-why">
        <span class="box-label">Why it matters</span>
        <p>Two of the ten traps in this capstone &mdash; the discarded narrative and the carve-out identifier &mdash; depend entirely on noticing that the two vocabularies collide. Before the term map existed, both rode on downstream checks: you would catch them eventually, at synthesis, when something did not fit.</p>
        <p>Check 10 catches them at excavation, which is where they are cheap.</p>
      </div>
    </section>
"""
