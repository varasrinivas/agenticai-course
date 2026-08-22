# Behavioral health code sets

Use `scripts/validate_bh_codes.py` rather than judging a code by eye. This reference explains what
the codes mean so you can tell whether a rule that branches on one is doing something sensible.

## Service codes

### CPT — psychiatric and psychotherapy

| Code | Service |
|---|---|
| 90791 | Psychiatric diagnostic evaluation, no medical services |
| 90792 | Psychiatric diagnostic evaluation **with** medical services |
| 90832 | Psychotherapy, 30 minutes |
| 90834 | Psychotherapy, 45 minutes |
| 90837 | Psychotherapy, 60 minutes |
| 90853 | Group psychotherapy |

### CPT — adaptive behavior (ABA)

| Code | Service |
|---|---|
| 97151 | Behavior identification assessment, by the physician or other qualified professional |
| 97152 | Behavior identification supporting assessment, by a technician |
| 97153 | Adaptive behavior treatment by protocol, by a technician |
| 97154 | Group adaptive behavior treatment by protocol |
| 97155 | Adaptive behavior treatment with protocol modification |
| 97156 | Family adaptive behavior treatment guidance |
| 97157 | Multiple-family group adaptive behavior treatment guidance |
| 97158 | Group adaptive behavior treatment with protocol modification |

ABA authorizations are usually **unit-based and long-running** — hundreds of units over months —
which makes them behave differently from a residential day count. A rule that caps "units" without
knowing which kind of unit it is capping will produce nonsense for one of the two.

### HCPCS — the level-of-care codes

These are the ones that matter for placement, because they map onto the ASAM ladder:

| Code | Service | Rough ASAM level |
|---|---|---|
| H0015 | Intensive outpatient program, SUD | 2.1 |
| H0018 | Short-term residential, non-hospital | 3.1 / 3.5 |
| H0019 | Long-term residential, non-hospital | 3.5 / 3.7 |
| H0035 | Partial hospitalization, mental health, under 24 hours | 2.5 |
| H2036 | Alcohol/drug treatment program, per diem | varies |
| S9480 | Intensive outpatient psychiatric services, per diem | 2.1 |

**The mapping is approximate and payer-specific.** A legacy system will have its own table, often
undocumented. Record what it maps rather than substituting this one.

## Diagnosis codes — ICD-10 chapter F

The block boundaries carry meaning for the reviewer-licensure rule, so they matter more than the
individual codes.

| Block | Category | Peer reviewer expected |
|---|---|---|
| **F10–F19** | Mental and behavioural disorders due to psychoactive substance use | **Addiction medicine** |
| **F20–F29** | Schizophrenia, schizotypal and delusional disorders | Psychiatry |
| **F30–F39** | Mood (affective) disorders | Psychiatry |
| **F40–F48** | Anxiety, dissociative, stress-related, somatoform | Psychiatry |
| F50–F59 | Behavioural syndromes with physiological disturbance | Psychiatry |
| F60–F69 | Disorders of adult personality and behaviour | Psychiatry |
| F70–F79 | Intellectual disabilities | — |
| F80–F89 | Disorders of psychological development (includes F84.0, autism) | — |
| F90–F98 | Behavioural and emotional disorders with onset in childhood | — |

Common specific codes in these systems:

| Code | Meaning |
|---|---|
| F10.20 | Alcohol dependence, uncomplicated |
| F11.20 | Opioid dependence, uncomplicated |
| F31.32 | Bipolar disorder, current episode depressed, moderate |
| F32.2 | Major depressive disorder, single episode, severe without psychotic features |
| F33.2 | Major depressive disorder, recurrent, severe without psychotic features |
| F41.1 | Generalised anxiety disorder |
| F84.0 | Autistic disorder |

### The F1x test, and how it goes wrong

Substance-use diagnoses are **F10 through F19**. Code that tests for them will typically do one of:

```java
icd10.startsWith("F1")                             // correct for F10-F19
icd10.compareTo("F10") >= 0 && icd10.compareTo("F20") < 0   // also correct
icd10.startsWith("F")                              // WRONG - catches all of chapter F
```

In a template you will see the same test as `fn:startsWith(dx, 'F1')`. It is the same rule, in a
place where nothing tests it.

An off-by-one here routes a psychiatric denial to an addiction-medicine reviewer or vice versa.
Both are licensure findings.

## Instruments

| Instrument | Range | Reading |
|---|---|---|
| **PHQ-9** | 0–27 | Depression severity. 20+ is severe |
| **GAD-7** | 0–21 | Anxiety severity. 15+ is severe |
| **C-SSRS** | 0–5 | Suicide severity. **4 and 5 are active ideation with intent** — the threshold that drives acute placement |
| **ASAM dimension** | 0–4 each, six of them | See `asam-levels.md`. Dimension 4 inverts |

C-SSRS 4 and 5 are the scores that justify immediate acute care. A rules engine that treats C-SSRS
as a smooth severity gradient rather than a threshold at 4 will under-place people in crisis.

## Validating

```bash
python scripts/validate_bh_codes.py --service H0018 --diagnosis F10.20
python scripts/validate_bh_codes.py --check-file rules_ir.json
```

The script reports unknown codes, codes used outside their block, and service/diagnosis pairs that
are structurally implausible — an ABA code with a substance-use diagnosis, for instance. It does
**not** make clinical judgements, and a warning is a prompt to look, not a verdict.
