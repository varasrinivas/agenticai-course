# M27B: Cert Domain 5.6 Deep Dive — Provenance, Temporal Data, Stratified Review, Synthesis

**Track**: 9 — Cert Prep | **Position**: After M27, before exam
**Prerequisites**: M09, M11, M17, M18, M27
**Estimated Time**: 60-75 minutes
**Level**: Intermediate → Advanced
**Track Color**: var(--track-capstones) / #D4A843 (gold — cert track signature)
**SDK Tier**: 3 (SDK-default). All examples use `claude-agent-sdk`. See `prompts/19-sdk-tier-policy.md`.

## Why This Module Must Exist
A coverage audit against the Claude Certified Architect study guide showed Domain 5.6 ("Information Provenance, Temporal Reliability, and Synthesis Output") is the **single biggest gap** in the course. Four named cert topics get zero or surface-only coverage in M00–M27:
- Information provenance / claim-source mappings
- Temporal data handling (as-of reasoning, valid_from/valid_to, freshness)
- Stratified sampling for human review + field-level confidence scores
- Synthesis output: well-established vs. contested claims with source characterizations

Each topic appears as a recurring scenario in the cert exam's Phase 3 weeks (9–10) and in the full practice exams. Cert tips have been added to M09, M11, M17, and M18 to flag these topics in context, but the cert exam tests them as a unified discipline — not as four scattered footnotes. M27B exists to teach Domain 5.6 as one coherent topic, with one hands-on lab that exercises all four sub-topics end-to-end.

## Concepts

### 1. Information Provenance — Claim-Source Mappings
Every claim a knowledge agent emits must be tagged to its source. Without provenance, you can't audit, can't recover from an error, and can't honestly answer "where did this come from?" The cert tests whether your output schema *enforces* the claim → source link, not whether the answer happens to be right.

- **Analogy**: A Wikipedia article without citations vs. one with [1][2] markers on every sentence. Same content, very different trustworthiness.
- **Animation**: Claim list with source pointers; one source struck through (retracted) and watch which downstream claims now show "unsourced — needs review" badges.
- **Key insight**: Provenance is a schema property, not a writing style. Claims must come back as `{claim, source_id, confidence}`, not as prose with parenthetical citations.

### 2. Temporal Data — As-Of Reasoning
Facts have lifespans. "CEO is Alice" was true once and is now false. Memory layers without temporal metadata cause agents to confidently report stale facts as current. The cert tests whether you store `{value, valid_from, valid_to, source}` and query with explicit temporal predicates.

- **Analogy**: A weather forecast vs. a weather record. The forecast for tomorrow expires tonight; the record of yesterday's high is permanent. Confusing the two is the bug.
- **Animation**: Knowledge graph timeline showing the same field's value changing over time; query slider lets the learner ask "as-of 2024-Q1" vs. "current" and see different answers.
- **Key insight**: `valid_to IS NULL` means "current." Most temporal bugs come from omitting the `valid_to` filter, returning every historical version.

### 3. Stratified Sampling + Field-Level Confidence
Aggregate confidence is a weak signal. Field-level confidence is the right grain. And when you route extractions to human reviewers, sampling matters: uniform sampling under-reviews low-confidence cases; top-N-by-confidence over-reviews easy ones. The cert pattern is *stratified sampling* — N samples from each confidence bucket so reviewers see the full distribution.

- **Analogy**: Quality control on a factory line. You don't inspect every widget (uniform), you don't only inspect the shiniest (top-N) — you sample from each batch tier so defects across grades surface evenly.
- **Animation**: Distribution chart with three buckets (high/med/low confidence); animated sampler picks N from each bucket, side-by-side compared with naive top-N sampling that all turn out correct.
- **Key insight**: Field-level + stratified compose. Extract per-field confidence, then stratify the *fields* (not the documents) for human review.

### 4. Synthesis Output — Well-Established vs. Contested Claims
When sources agree, the agent should say so confidently. When sources disagree, the agent must surface the disagreement, not silently pick one. The cert tests whether your synthesis layer distinguishes these cases in the output schema and surfaces both source pointers when contested.

- **Analogy**: A meta-analysis paper. "Result X is replicated across 7 studies (well-established)" reads very differently from "Result Y is supported by 3 studies and contradicted by 2 (contested)." A reader can act on the first; the second requires more digging. Don't collapse them.
- **Animation**: Two source documents side-by-side; the synthesis layer reads both and emits two output cards — a green "well-established" card when they agree, a yellow "contested" card with both source IDs when they disagree.
- **Key insight**: A 1-line agreement check on extracted claims is enough to fork the output category. The schema must allow `claim_status: "established" | "contested" | "single_source"`.

## Code Walkthrough
Build a `ProvenancedSynthesizer` class (Python and Node.js) that takes a list of retrieved chunks and a target query, and returns a synthesis object:

```json
{
  "well_established": [
    {"claim": "...", "sources": ["chunk_3", "chunk_7", "chunk_12"], "confidence": 0.92}
  ],
  "contested": [
    {"claim_a": "...", "sources_a": ["chunk_5"], "claim_b": "...", "sources_b": ["chunk_9"], "topic": "..."}
  ],
  "single_source": [
    {"claim": "...", "source": "chunk_2", "confidence": 0.75, "needs_review": true}
  ],
  "temporal_warnings": [
    {"claim": "...", "as_of": "2024-Q3", "freshness": "stale", "source": "chunk_4"}
  ]
}
```

Annotated in 4 chunks: extraction (per-chunk claim + confidence), agreement detection (cluster claims by entailment), temporal flagging (compare `valid_to` against query time), output assembly. Each chunk has WHAT/WHY/GOTCHA. The GOTCHA on agreement detection covers the difference between *paraphrase* (still well-established) and *contradiction* (contested) — confidence + entailment classifier, not raw string match.

## Hands-On Lab
**Build a Healthcare Pre-Auth Synthesizer.** Domain A. Learner is given a fixture of 8 retrieved chunks about a single CPT code's coverage policy across multiple payer documents from different dates. Three of the chunks agree on the policy. Two contradict (different payers). One is from 2022 and may be stale. Two are single-source claims about exclusion criteria.

Tasks:
1. Run the synthesizer; verify it produces 4 output buckets matching the fixture's known structure
2. Add a stratified human-review sampler that picks 1 from each bucket (well-established, contested, single-source, temporal-warning) for review
3. Implement the `valid_to` temporal filter; flip the 2022 chunk's freshness flag and re-run
4. Add a regression test that asserts contested claims always include both source pointers (the most common cert exam trap)

**Stretch goals**:
- Build a per-field confidence extractor (not just per-claim) for structured tasks like extracting `{cpt_code, coverage, copay, exclusions[]}`
- Add a `provenance_audit()` method that returns "every claim → which chunk(s)" for compliance review
- Implement temporal diff: given two synthesis runs at different times, list which claims changed, became stale, or got new sources

## Quiz Focus (8 questions — denser than typical because this is cert prep)
1. **Multiple choice**: Which output is exam-compliant for a RAG synthesis layer? (One option has prose with parenthetical citations, one has structured `{claim, source_id}` pairs — the latter wins.)
2. **Code completion**: Given a knowledge-base row schema, fill in the missing temporal fields. (`valid_from`, `valid_to`)
3. **Scenario**: You have two payer documents disagreeing on CPT coverage. The agent picks one and reports it. What's wrong? (Silent disagreement resolution; should be a contested claim with both source pointers.)
4. **Multiple choice**: Which sampling strategy for human review aligns with cert recommendations? (Stratified — N from each confidence bucket — over uniform or top-N.)
5. **Conceptual**: Why does field-level confidence beat document-level for high-stakes extraction? (A document at 88% overall might have one field at 30%; aggregate hides it.)
6. **Code completion**: Given a synthesizer output, complete the assert that contested claims contain both `sources_a` and `sources_b`.
7. **Trap question**: An agent reports "Acme's CEO is Bob" — the user is confused because it's been Alice for 6 months. What's the most likely bug class? (Temporal: missing `valid_to` filter; query returned the historical row, not the current one.)
8. **Multiple choice**: When sources agree, should the agent collapse them? (No — preserve all source pointers; "well-established" status is itself an output property.)

## Forward References
- Reinforces and operationalizes the cert tips added to M09 (provenance), M11 (temporal), M17 (stratified sampling + field confidence), M18 (multi-pass review)
- Final cert prep checkpoint before M27 (Cert Exam Prep) — students should complete M27B before sitting any practice exam

## Cert Exam Mapping
- **Domain 5.6**: full coverage (provenance, synthesis output, source characterization, temporal handling, stratified review, field-level confidence)
- **Domain 4.6**: reinforces multi-pass review (the synthesis stage is itself a "second pass" over the per-chunk extractions)
- **Domain 5.4**: reinforces crash-recovery + stale-context theme through temporal handling
