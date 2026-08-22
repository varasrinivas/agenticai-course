# 42 CFR Part 2 — the redisclosure regime

**Educational model, not legal advice.** This is a simplified working model, enough to classify
architecture and enough to know when to escalate. It is not a compliance programme and it is not a
substitute for counsel.

## What it covers

Records from a **federally assisted substance-use-disorder treatment program**. Not all behavioral
health — a depression admission at a general psychiatric hospital is HIPAA; an admission to a
program whose purpose is SUD treatment is HIPAA *and* Part 2.

The distinction lives in a flag on the provider record. **That flag is data, and data is wrong
sometimes.** A system that applies Part 2 handling only when the flag says so is exactly as
reliable as the flag. If you find a legacy system capturing consent unconditionally rather than
conditionally on the flag, that is a mitigation for an unreliable input — reproduce the
mitigation, not just the flag.

## How it differs from HIPAA

| | HIPAA | 42 CFR Part 2 |
|---|---|---|
| Disclosure for treatment/payment/operations | Permitted without authorization | **Requires consent** |
| Recipient | Class of recipients is fine | **Must be named** |
| Scope | "Minimum necessary" standard | Consent states scope explicitly; no minimum-necessary shortcut |
| Duration | Authorization may be open-ended | **Expires**; revocable |
| Downstream recipients | Bound if a business associate | **Bound by the redisclosure notice** that must accompany the disclosure |
| Accounting | Required for some disclosures | **Required** |

The practical summary: under HIPAA the question is *"is this use appropriate?"*. Under Part 2 it
is *"is this exact recipient named in an unexpired, unrevoked consent that covers this purpose and
this scope?"* — a question a system can only answer if it stores consents that way and checks them
at the point of disclosure.

## Consent scope, and what it gates

A typical consent scope enumeration:

| Scope | What may leave the system |
|---|---|
| `FULL_RECORD` | Everything, including the clinical narrative |
| `AUTH_DECISION_ONLY` | The determination — approved/denied, level, dates. **Not the narrative** |
| `DATES_OF_SERVICE_ONLY` | That care occurred, and when |

**`AUTH_DECISION_ONLY` is the common case, and it is the one that breaks naive ports.** The
determination may go out; the clinical justification may not. A notification payload that carries
both is a violation under the most common consent on file.

## Revocation is prospective

Revoking a consent stops future disclosures. It does not recall past ones. That is defensible —
but it means the system must be able to answer *"what went out under the consent that was just
revoked?"*, and it can only do that if it kept an accounting of disclosures. Most legacy systems
kept an audit of **changes to records** and have no register of **disclosures of records**. Those
are different tables answering different questions, and the second one is usually missing.

## The architecture failure mode

Part 2 violations in modernized systems are almost never policy decisions. They are plumbing:

```
                       ┌─→ application log         (no consent scope)
clinical narrative ────┼─→ event payload → broker  (no consent scope)
                       ├─→ search index            (no consent scope)
                       └─→ audit table             (no consent scope, no expiry)
```

Each of those is what a normal distributed architecture does with a field. None of them asks who
the recipient is. **Decomposing a monolith multiplies the sinks** — one application log becomes one
per service, plus a broker, plus an index — so a leak that was contained becomes a leak that fans
out, without anyone deciding to make it worse.

### Checklist for any generated component

- [ ] Does any log statement interpolate the clinical free-text field? *(Check string concatenation
      and structured-logging fields alike.)*
- [ ] Does any event payload carry it? Check **every** event, not just the obvious one.
- [ ] Is it mapped into a search index? An index is a second copy with its own retention.
- [ ] Does the audit trail store it? Storing a before/after copy on every update is common and
      accumulates copies with no expiry and no consent scope.
- [ ] Is the transport authenticated and encrypted? A plaintext broker on an internal network is
      still a disclosure to whoever can read the topic.
- [ ] Is there a free-text **search** endpoint over it, and does it check a role and a consent? A
      careful role guard on a detail screen is undone by an unguarded search over the same field.
- [ ] Does an error path leak it — an exception message, a stack trace, a request body echoed into
      a log?

## The controls that cannot be feature flags

A modern platform may gate capabilities behind flags so it can be run one layer at a time. That
idiom is worth copying **for capabilities**. It is not appropriate for regulatory controls.

`CACHE_ENABLED=false` degrades performance. A hypothetical `CONSENT_ENABLED=false` removes a legal
control, and a control that can be switched off in configuration is not a control — it is a
default. Consent enforcement, redisclosure notices, and the disclosure accounting must be
unconditional.

When classifying a flag, ask: *if this were false in production for a week, would the consequence
be a slow system or an unlawful disclosure?*

## When to escalate rather than decide

- The Part 2 program flag's accuracy is unknown or unaudited.
- A consent is fabricated on the submitter's behalf by a batch job or a machine interface. *(Very
  common in EDI paths — and it is a policy question, not an engineering one.)*
- An audit or reporting mechanism holds protected content for reasons that were signed off by a
  business function rather than by privacy.
- A rule would change which disclosures happen.

Use `queue_manual_review` with the specific question. "Who consents when a machine submits?" is a
question for a compliance officer, and answering it yourself is out of scope no matter how
reasonable the answer seems.
