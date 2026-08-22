"""Capstone 9's quiz explanations.

These MUST replace the block inherited from Capstone 8. The shared-JS slice the
builder lifts runs from `// ===== SHARED UI` to `// ===== ANIMATION 1`, and
`QUIZ_EXPLANATIONS` sits inside it -- so without this substitution every
"Check Answer" in Capstone 9 returns a confident, well-written explanation
about Oracle DATE truncation.

One explanation per option, including the correct one. A shared "not quite,
try again" teaches nothing, and the interesting part of a distractor is why it
was tempting.
"""

QUIZ_EXPLANATIONS_JS = r"""const QUIZ_EXPLANATIONS = {
  q1: {
    a: 'Twelve matching cases is real evidence, and it is evidence of the wrong thing. It shows the table agrees with the ladder <em>in the order the rows currently sit</em>. Nothing tested the property the conversion actually depends on.',
    b: 'FIRST is a perfectly valid choice for a converted ladder &mdash; it is the mechanically faithful one. COLLECT returns every match and leaves the caller to choose, which is not what the ladder did either.',
    c: 'Correct. Sorting the rows by id &mdash; a change with no semantic intent, that nothing prevents &mdash; changes ten of twelve answers. The conversion is correct today by luck, and the luck is an invariant no test checks. Tightening the lower rows with the negation of the upper ones makes the table order-independent.',
    d: 'They do exercise it: case 500001 reaches score 10 with dimension 1 at 3, so both branch-7 rows match. That is precisely why the FIRST table gets it right &mdash; and why reordering breaks it.',
  },
  q2: {
    a: 'This is the intuition the trap depends on. Identical names feel like the safest possible mapping, which is exactly why nobody writes the mapping down or examines it.',
    b: 'Correct. APPROVED is terminal on the clinical side; the behavioral switch loops it back to IN_REVIEW on the level-of-care cadence. Every status name still matches, so the build passes, review passes, and the single biggest structural difference between the domains is gone.',
    c: 'Arity is not the issue &mdash; and a type check would be a gift here, because it would fail loudly. The enums overlap on five names; the behavioral side merely adds EXPIRED.',
    d: 'Nothing rejects the transition, because no state machine survived the port. The failure is silent from the moment of the mapping onward: reviews are simply never scheduled.',
  },
  q3: {
    a: 'It is not deprecated &mdash; it is set on roughly 400 live rows and read in two code paths. Dead code would be the easy case.',
    b: 'Correct. Its entire documentation is the ticket body &ldquo;per DM request&rdquo;. Nobody at Bridgeway can say which determinations it covers or who authorised it, so no interpretation can be checked &mdash; and the cost of an unverifiable wrong guess is a changed determination for a real person. Reproduce the behaviour, queue the question.',
    c: 'A CHAR(1) flag maps to a DMN input without difficulty. The obstacle is semantic, not representational.',
    d: 'It is not an authorization control. It short-circuits the level-of-care engine before any clinical input is read, which is closer to a decision override than a permission.',
  },
  q4: {
    a: 'Saga latency is not the objection. Even an instantaneous saga would not help, because the problem is what is true <em>during</em> the window rather than how long the window is.',
    b: 'A distributed lock would narrow the window, not close it. And the platform&rsquo;s outbox already provides an ordering guarantee &mdash; ordering is not what is missing.',
    c: 'Correct. During the window the organisation holds 42 CFR Part 2 protected treatment content with no record of who the member agreed it could be shared with. Deleting the authorization afterwards does not un-hold it. Some writes do not compensate, and the honest answer is that this seam moves: one service owns both writes.',
    d: 'A saga is the standard answer to a distributed transaction, and this is the case where the standard answer is wrong. Recognising which pairs cannot be split is the point of classifying them before drawing the seam.',
  },
  q5: {
    a: 'Zero is the goal, and it is only meaningful once you know the check could have fired. This is the reading the <code>scanned</code> field exists to prevent.',
    b: 'Treating every clean result as broken is the opposite error, and it is worse: a check that can never pass is a check people learn to ignore. A good port really does come back clean on all four.',
    c: 'Correct. What distinguishes &ldquo;found nothing&rdquo; from &ldquo;looked at nothing&rdquo; is the scan count. Every check reports it, and a clean result is flagged suspicious only when it scanned nothing or when its inputs cannot exercise what it is for &mdash; a case set with no case at the overlap boundary, an empty emitted tree.',
    d: 'The leak scan walks the emitted files directly. It shares no inputs with the gap register, which is why the two can disagree and why that disagreement is informative.',
  },
  q6: {
    a: 'Correct. Both. The rule has moved from one template to another, which is the same layer with a different spelling &mdash; and <code>roleMask &gt;= 4</code> is the approximation JSTL was forced into because it has no bitwise operator. Mask 33, intake + admin, passes the comparison and fails <code>hasRole(MD)</code>: the view is the permissive side.',
    b: 'Reactivity is a real Angular concern and not the problem here. A perfectly reactive signal holding the wrong comparison is still the wrong comparison.',
    c: 'A route guard <em>is</em> part of the answer, and canMatch versus canActivate is a detail either way. But the deeper point is that a guard is not the enforcement at all &mdash; anyone can call the API directly, so an action gate needs a server-side check too.',
    d: 'This is the tempting reading of &ldquo;port the screens&rdquo;, and it is what produces a component that renders the deny button for everyone. Relocation means leaving the view layer, not changing which view layer.',
  },
  q7: {
    a: 'A default of true is better than a default of false and still not a control. The question is whether it can be turned off at all, not what it does when nobody touches it.',
    b: 'The backlog tells you what the platform team planned. It says nothing about whether a given capability is safe to make optional in a domain they were not building for.',
    c: 'Correct. Ask what a week of <code>false</code> in production would cost. Slow page &rarr; a flag is fine, and the idiom is worth mirroring. Unlawful disclosure, unlicensed determination, missing audit trail &rarr; it must not be a flag: a regulatory control that can be switched off in configuration is a default.',
    d: 'Read frequency changes how fast the switch takes effect, not whether the switch should exist. A per-request flag is still a flag.',
  },
  q8: {
    a: 'Skills are loaded on demand rather than cached separately, and speed is not the argument. The argument is about drift and about what occupies context when.',
    b: 'Correct. Six of the eight subagents need the same domain knowledge. Pasted copies drift the moment one is edited, cost tokens on every turn whether or not the turn needs them, and leave no single place to correct a clinical-policy change. The bundled references stay out of context until something asks for them.',
    c: 'There is no such limit, and the ASAM criteria would fit comfortably. The problem is having six copies of them, not the size of one.',
    d: 'Skills cannot block a tool call &mdash; that is what <code>can_use_tool</code> and <code>PreToolUse</code> hooks do. Confusing the two is one of the three anti-patterns the module names.',
  },
};"""
