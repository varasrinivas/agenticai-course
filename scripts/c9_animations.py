"""Capstone 9: the six animation implementations.

Each uses the shared `makeAnim` scaffold lifted from Capstone 8, so play/pause,
restart, autoplay-on-scroll and `prefers-reduced-motion` behave identically
across both modules. Reduced motion jumps to the final state rather than
stepping through it.
"""

ANIMATION_JS = r"""
// ========== ANIMATION 1: MONOLITH -> DISTRIBUTED ==========
// Five writes, one transaction. Watch which of them can be separated and
// which cannot -- and note that the pair that cannot is why the seam moves.
const DECOMPOSE = [
  { table: 'BH_AUTH',        meaning: 'the authorization',        owner: 'bh-case-svc',   cls: 'good',
    note: 'Write 1. The anchor. Everything else relates to this row.' },
  { table: 'BH_ASSESSMENT',  meaning: 'the rules engine inputs',   owner: 'bh-case-svc',   cls: 'good',
    note: 'Write 2. The engine READS these from the database rather than being passed them, so they must exist before it runs.' },
  { table: 'BH_CONSENT',     meaning: 'the Part 2 permission',     owner: 'bh-case-svc',   cls: 'hot',
    note: 'Write 3. MUST BE ATOMIC with write 1. An authorization from a protected program with no consent record is content the organisation cannot lawfully act on -- and a disclosure does not compensate.' },
  { table: 'BH_LOC_REVIEW',  meaning: 'the initial determination', owner: 'bh-case-svc',   cls: 'good',
    note: 'Write 4. Sequence 1 of the review ladder. Its NEXT_REVIEW_DUE is what drives the worklist.' },
  { table: 'BH_AUTH_QUEUE',  meaning: 'the outbound notification', owner: 'bh-notify-svc', cls: 'warn',
    note: 'Write 5. THIS one can cross a seam -- outbox plus an idempotent consumer, with a window, an observable, a compensation and an alarm.' },
];
const decomposeTrack = document.getElementById('decomposeTrack');
const decomposeNote = document.getElementById('decomposeNote');
if (decomposeTrack) {
  decomposeTrack.innerHTML = DECOMPOSE.map((w, i) => `
    <div class="c9-row">
      <div class="c9-mono" style="color:var(--text-muted);">${w.table}</div>
      <div class="c9-lane" id="dec-${i}">
        <div class="lane-title">${w.meaning}</div>
        <div class="lane-note" id="dec-owner-${i}">one Oracle transaction</div>
      </div>
    </div>`).join('');
}
const decomposeAnim = makeAnim('decompose-play',
  DECOMPOSE.map((w, i) => () => {
    const el = document.getElementById('dec-' + i);
    if (!el) return;
    el.className = 'c9-lane on ' + w.cls;
    document.getElementById('dec-owner-' + i).textContent = '-> ' + w.owner;
    if (decomposeNote) decomposeNote.textContent = w.note;
  }).concat([() => {
    if (decomposeNote) decomposeNote.innerHTML =
      '<strong>Four of five stay together.</strong> The authorization/consent pair is ' +
      'must-be-atomic, so bh-case-svc owns both and the seam moves. Recording a ' +
      'seam as <em>rejected</em> is a result, not an omission.';
  }]),
  () => {
    DECOMPOSE.forEach((w, i) => {
      const el = document.getElementById('dec-' + i);
      if (el) el.className = 'c9-lane';
      const o = document.getElementById('dec-owner-' + i);
      if (o) o.textContent = 'one Oracle transaction';
    });
    if (decomposeNote) decomposeNote.textContent =
      'Press play. Each write moves to the service that will own it.';
  }, 1500);
decomposeAnim.autoplay('decompose-container');

// ========== ANIMATION 2: THE GAP REGISTER ==========
// Ordered so must-build-new and must-not-port land LAST. The comfortable
// verdicts arrive first; the uncomfortable distribution is the finding.
const GAPS = [
  { cap: 'transactional outbox',              v: 'port-as-is',     cls: 'good' },
  { cap: 'feature-flag capability layering',  v: 'port-as-is',     cls: 'good' },
  { cap: 'decision table',                    v: 'extend',         cls: 'on' },
  { cap: 'process model',                     v: 'extend',         cls: 'on' },
  { cap: 'referential integrity',             v: 'extend',         cls: 'on' },
  { cap: 'concurrent review',                 v: 'must-build-new', cls: 'warn' },
  { cap: '42 CFR Part 2 consent model',       v: 'must-build-new', cls: 'warn' },
  { cap: 'decision audit + disclosure register', v: 'must-build-new', cls: 'warn' },
  { cap: 'roles and reviewer licensure',      v: 'must-build-new', cls: 'warn' },
  { cap: 'entity resolution across the carve-out', v: 'must-build-new', cls: 'warn' },
  { cap: 'the frontend',                      v: 'must-build-new', cls: 'warn' },
  { cap: 'a test suite',                      v: 'must-build-new', cls: 'warn' },
  { cap: 'cleartext PHI in logs and events',  v: 'must-not-port',  cls: 'hot' },
  { cap: 'consent enforcement as a flag',     v: 'must-not-port',  cls: 'hot' },
  { cap: 'validated-then-discarded free text', v: 'must-not-port', cls: 'hot' },
];
const VERDICT_CLASS = {
  'port-as-is': 'verdict-port', 'extend': 'verdict-extend',
  'must-build-new': 'verdict-build', 'must-not-port': 'verdict-not',
};
const gapTrack = document.getElementById('gapTrack');
const gapNote = document.getElementById('gapNote');
if (gapTrack) {
  gapTrack.innerHTML = GAPS.map((g, i) => `
    <div class="c9-lane" id="gap-${i}" style="display:flex;justify-content:space-between;gap:1rem;align-items:center;">
      <span class="lane-title">${g.cap}</span>
      <span class="c9-chip ${VERDICT_CLASS[g.v]}" id="gap-v-${i}" style="opacity:0;">${g.v}</span>
    </div>`).join('');
}
const gapAnim = makeAnim('gap-play',
  GAPS.map((g, i) => () => {
    const el = document.getElementById('gap-' + i);
    if (!el) return;
    el.className = 'c9-lane on ' + (g.cls === 'on' ? '' : g.cls);
    document.getElementById('gap-v-' + i).style.opacity = '1';
    if (gapNote) {
      if (g.v === 'must-not-port') {
        gapNote.innerHTML = '<strong>must-not-port requires a NAMED HARM.</strong> ' +
          'The tool rejects the entry without one &mdash; softening this verdict is ' +
          'how a defect gets copied with a note attached.';
      } else if (g.v === 'must-build-new') {
        gapNote.innerHTML = '<strong>must-build-new requires a requirement.</strong> ' +
          'Without one it is a wish, and the synthesizer will defer it &mdash; ' +
          'exactly as the platform team deferred all of these.';
      } else {
        gapNote.textContent = 'Every verdict cites evidence. ' +
          '"The audit trail is insufficient" is an opinion.';
      }
    }
  }).concat([() => {
    if (gapNote) gapNote.innerHTML =
      '<strong>2 port-as-is &middot; 3 extend &middot; 7 must-build-new &middot; 3 must-not-port.</strong> ' +
      'A register that came out mostly port-as-is would mean the architecture was ' +
      'read and the domain was not &mdash; and the coordinator halts the run rather ' +
      'than advancing on one.';
  }]),
  () => {
    GAPS.forEach((g, i) => {
      const el = document.getElementById('gap-' + i);
      if (el) el.className = 'c9-lane';
      const v = document.getElementById('gap-v-' + i);
      if (v) v.style.opacity = '0';
    });
    if (gapNote) gapNote.textContent = 'Press play.';
  }, 620);
gapAnim.autoplay('gap-container');

// ========== ANIMATION 3: FIRST-MATCH vs HIT POLICY ==========
const LADDER_STEPS = [
  { id: 'B2',  txt: 'C-SSRS 4', delta: '+6', score: 6,  commits: false },
  { id: 'B3',  txt: 'dim1 = 3', delta: '+4', score: 10, commits: false },
  { id: 'B7a', txt: 'score >= 10 AND dim1 >= 3', delta: '=> 3.7', score: 10, commits: true },
  { id: 'B7b', txt: 'score >= 8', delta: '=> 3.5', score: 10, commits: false, skipped: true },
];
const TABLE_ROWS = [
  { id: 'B7a', txt: 'score >= 10 AND dim1 >= 3 -> 3.7' },
  { id: 'B7b', txt: 'score >= 8 -> 3.5' },
];
const hitLadder = document.getElementById('hitLadder');
const hitTable = document.getElementById('hitTable');
const hitNote = document.getElementById('hitNote');
if (hitLadder) {
  hitLadder.innerHTML = LADDER_STEPS.map((s, i) => `
    <div class="c9-lane" id="hl-${i}">
      <div class="lane-title c9-mono">${s.id} &nbsp; ${s.txt}</div>
      <div class="lane-note" id="hl-n-${i}">${s.delta}</div>
    </div>`).join('');
}
if (hitTable) {
  hitTable.innerHTML = TABLE_ROWS.map((r, i) => `
    <div class="c9-lane" id="ht-${i}">
      <div class="lane-title c9-mono">${r.id}</div>
      <div class="lane-note">${r.txt}</div>
    </div>`).join('');
}
const hitAnim = makeAnim('hit-play', [
  () => {
    const el = document.getElementById('hl-0');
    if (el) el.className = 'c9-lane on';
    document.getElementById('hl-n-0').textContent = '+6   score = 6   (falls through)';
    if (hitNote) hitNote.textContent = 'Branch 2 accumulates and falls through. It is not a table row.';
  },
  () => {
    const el = document.getElementById('hl-1');
    if (el) el.className = 'c9-lane on';
    document.getElementById('hl-n-1').textContent = '+4   score = 10   (falls through)';
    if (hitNote) hitNote.textContent =
      'Branch 3 splits: the dim1 >= 4 arm COMMITS, the dim1 == 3 arm accumulates. ' +
      'One source branch, two kinds.';
  },
  () => {
    const a = document.getElementById('hl-2');
    const b = document.getElementById('hl-3');
    if (a) a.className = 'c9-lane on good';
    if (b) b.className = 'c9-lane on hot';
    document.getElementById('hl-n-2').textContent = '=> 3.7   COMMITS. Returns here.';
    document.getElementById('hl-n-3').textContent = 'true as well -- but never reached';
    if (hitNote) hitNote.innerHTML =
      '<strong>Both conditions are true.</strong> The ladder commits on the first, ' +
      'so the answer is 3.7 and the 3.5 branch never runs. The ordering carries ' +
      'the exclusion.';
  },
  () => {
    document.getElementById('ht-0').className = 'c9-lane on hot';
    document.getElementById('ht-1').className = 'c9-lane on hot';
    if (hitNote) hitNote.innerHTML =
      'Flattened, <strong>both rows match</strong> and the ordering is gone. ' +
      '<code>FIRST</code> gives 3.7 &mdash; but only while the rows stay in this order. ' +
      '<code>UNIQUE</code> errors. <code>COLLECT</code> returns both.';
  },
  () => {
    document.getElementById('ht-1').className = 'c9-lane on good';
    document.querySelector('#ht-1 .lane-note').innerHTML =
      'score &gt;= 8 <strong>AND overlap_upper &lt; 1</strong> -> 3.5';
    if (hitNote) hitNote.innerHTML =
      '<strong>The reference answer.</strong> Tighten the lower row with a named ' +
      'derived input. The exclusion was always there &mdash; it was encoded as ' +
      '<em>position</em>. Now it is a condition, and the table means the same thing ' +
      'whatever order the rows are in.';
  },
], () => {
  LADDER_STEPS.forEach((s, i) => {
    const el = document.getElementById('hl-' + i);
    if (el) el.className = 'c9-lane';
    const n = document.getElementById('hl-n-' + i);
    if (n) n.textContent = s.delta;
  });
  TABLE_ROWS.forEach((r, i) => {
    const el = document.getElementById('ht-' + i);
    if (el) el.className = 'c9-lane';
  });
  const n1 = document.querySelector('#ht-1 .lane-note');
  if (n1) n1.textContent = TABLE_ROWS[1].txt;
  if (hitNote) hitNote.textContent = 'Press play.';
}, 2000);
hitAnim.autoplay('hit-container');

// ========== ANIMATION 4: THE PART 2 LEAK ==========
const LEAK_STAGES = [
  { title: 'Clinician submits', note: 'Free-text clinical justification. Also 42 CFR Part 2 protected content, because the requesting provider is a federally assisted SUD program.', cls: 'on' },
  { title: 'HIPAA check', note: 'Passes. Treatment, payment and operations need no authorization under HIPAA, and this is a utilization review.', cls: 'good' },
  { title: 'Consent on file: AUTH_DECISION_ONLY', note: 'The determination may be disclosed. The narrative may NOT. This is the common scope.', cls: 'warn' },
];
const LEAK_SINKS = [
  { name: 'application log',  why: 'log.info("... narrative=" + auth.getClinicalNarrative())' },
  { name: 'event payload',    why: 'plain JSON on an unauthenticated broker' },
  { name: 'search index',     why: 'a second copy, with its own retention' },
  { name: 'audit table',      why: 'old AND new, on every update, no expiry' },
];
const leakTrack = document.getElementById('leakTrack');
const leakSinks = document.getElementById('leakSinks');
const leakNote = document.getElementById('leakNote');
if (leakTrack) {
  leakTrack.innerHTML = LEAK_STAGES.map((s, i) => `
    <div class="c9-lane" id="lk-${i}">
      <div class="lane-title">${s.title}</div>
      <div class="lane-note">${s.note}</div>
    </div>`).join('');
}
if (leakSinks) {
  leakSinks.innerHTML = LEAK_SINKS.map((s, i) =>
    `<div class="c9-sink" id="lks-${i}">${s.name}</div>`).join('');
}
const leakAnim = makeAnim('leak-play',
  LEAK_STAGES.map((s, i) => () => {
    const el = document.getElementById('lk-' + i);
    if (el) el.className = 'c9-lane on ' + (s.cls === 'on' ? '' : s.cls);
    if (leakNote) leakNote.textContent = s.note;
  }).concat(
    LEAK_SINKS.map((s, i) => () => {
      const el = document.getElementById('lks-' + i);
      if (el) el.className = 'c9-sink lit';
      if (leakNote) leakNote.innerHTML =
        '<strong>' + s.name + '</strong> &mdash; ' + s.why +
        '<br>No consent scope. Nothing here asks who the recipient is.';
    })
  ).concat([() => {
    if (leakNote) leakNote.innerHTML =
      '<strong>Four sinks, none of them consent-scoped.</strong> The monolith had ' +
      'ONE. Nobody made it worse &mdash; fan-out is what a distributed architecture ' +
      'does with a field, and the count going up is the expected shape of this ' +
      'finding.';
  }]),
  () => {
    LEAK_STAGES.forEach((s, i) => {
      const el = document.getElementById('lk-' + i);
      if (el) el.className = 'c9-lane';
    });
    LEAK_SINKS.forEach((s, i) => {
      const el = document.getElementById('lks-' + i);
      if (el) el.className = 'c9-sink';
    });
    if (leakNote) leakNote.textContent = 'Press play.';
  }, 1200);
leakAnim.autoplay('leak-container');

// ========== ANIMATION 5: KNOWLEDGE AND CONTROL PLANES ==========
const KNOWLEDGE = [
  'behavioral-health-um  -- ASAM, Part 2, parity, code sets',
  'umlite-architecture   -- the target house style',
  'rules-to-dmn          -- runbook + overlap checker',
  'decompose-transaction -- runbook',
];
const CONTROL = [
  'coordinator      -- sequences six phases',
  'eight subagents  -- isolated context, narrow tools',
  'PreToolUse hooks -- block a call before it runs',
  'the HITL gate    -- the agent cannot approve itself',
  'budget + breaker -- abort rather than run away',
];
const planesK = document.getElementById('planesKnowledge');
const planesC = document.getElementById('planesControl');
const planesNote = document.getElementById('planesNote');
if (planesK) planesK.innerHTML = KNOWLEDGE.map((t, i) =>
  `<div class="c9-item c9-mono" id="pk-${i}">${t}</div>`).join('');
if (planesC) planesC.innerHTML = CONTROL.map((t, i) =>
  `<div class="c9-item c9-mono" id="pc-${i}">${t}</div>`).join('');
const planesSteps = KNOWLEDGE.map((t, i) => () => {
  const el = document.getElementById('pk-' + i);
  if (el) el.classList.add('on');
  if (planesNote) planesNote.textContent =
    'Knowledge and runbooks. Loaded on demand, shared by every subagent, ' +
    'versioned in one place.';
}).concat(CONTROL.map((t, i) => () => {
  const el = document.getElementById('pc-' + i);
  if (el) el.classList.add('on');
  if (planesNote) planesNote.textContent =
    'Control flow and safety. A Skill cannot sequence a phase, cannot isolate ' +
    'a context window, and cannot block a tool call.';
})).concat([() => {
  if (planesNote) planesNote.innerHTML =
    '<strong>Does it decide, branch, parallelize, or block? Agent.</strong> ' +
    '<strong>Same steps every time? Skill.</strong>';
}]);
const planesAnim = makeAnim('planes-play', planesSteps, () => {
  KNOWLEDGE.forEach((t, i) => {
    const el = document.getElementById('pk-' + i);
    if (el) el.classList.remove('on');
  });
  CONTROL.forEach((t, i) => {
    const el = document.getElementById('pc-' + i);
    if (el) el.classList.remove('on');
  });
  if (planesNote) planesNote.textContent = 'Press play.';
}, 700);
planesAnim.autoplay('planes-container');

// ========== ANIMATION 6: JSP -> ROUTE ==========
const SCREEN_RULES = [
  { rule: 'Three nested JSTL conditionals around the deny button',
    home: 'BPMN candidate group + a server-side check',
    cls: 'good',
    note: 'This IS the reviewer-licensure rule. Where a workflow task encodes licensure, the candidate group is the rule -- and a route guard alone would not be enough, because anyone can call the API directly.' },
  { rule: 'roleMask ge 2 around the clinical narrative',
    home: 'API omission -- the endpoint does not return the field',
    cls: 'good',
    note: 'The legacy controller loads it unconditionally and the template hides it. That guard controls RENDERING, not RETRIEVAL: the content is in the response body either way.' },
  { rule: 'Scriptlet: continued-stay countdown',
    home: 'computed field on the response',
    cls: 'warn',
    note: 'Computed here and NOWHERE ELSE in the codebase. Reporting reimplemented it in Crystal and the two have disagreed since 2015.' },
  { rule: 'Scriptlet: regulatory turnaround clock',
    home: 'computed field + a BPMN boundary timer',
    cls: 'warn',
    note: '72 hours expedited, 14 calendar days standard. The ONLY implementation of that rule in the system, in a JSP scriptlet.' },
  { rule: 'Part 2 banner on provider.part2Program',
    home: 'computed field on the response',
    cls: 'warn',
    note: 'The only place in the application that tells a reviewer the record carries a redisclosure prohibition. No corresponding server-side control.' },
];
const screenTrack = document.getElementById('screenTrack');
const screenNote = document.getElementById('screenNote');
if (screenTrack) {
  screenTrack.innerHTML = SCREEN_RULES.map((r, i) => `
    <div class="c9-lane" id="sc-${i}">
      <div class="lane-title">${r.rule}</div>
      <div class="lane-note" id="sc-h-${i}">still in the template</div>
    </div>`).join('');
}
const screenAnim = makeAnim('screen-play',
  SCREEN_RULES.map((r, i) => () => {
    const el = document.getElementById('sc-' + i);
    if (el) el.className = 'c9-lane on ' + r.cls;
    document.getElementById('sc-h-' + i).innerHTML = '&rarr; ' + r.home;
    if (screenNote) screenNote.textContent = r.note;
  }).concat([() => {
    if (screenNote) screenNote.innerHTML =
      'Across seven screens: <strong>20 rules, 11 with no server-side enforcement ' +
      'at all.</strong> Those eleven vanish in a mechanical port &mdash; and moving ' +
      'one to <code>*ngIf</code> has moved nothing.';
  }]),
  () => {
    SCREEN_RULES.forEach((r, i) => {
      const el = document.getElementById('sc-' + i);
      if (el) el.className = 'c9-lane';
      const h = document.getElementById('sc-h-' + i);
      if (h) h.textContent = 'still in the template';
    });
    if (screenNote) screenNote.textContent = 'Press play.';
  }, 1800);
screenAnim.autoplay('screen-container');
"""
