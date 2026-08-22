#!/usr/bin/env python3
"""Validate behavioral-health service, diagnosis and instrument codes.

Bundled with the `behavioral-health-um` skill. Run it instead of reasoning about
whether H0018 is a real HCPCS code -- the point of a bundled script is that the
answer is looked up rather than recalled.

    python validate_bh_codes.py --service H0018 --diagnosis F10.20
    python validate_bh_codes.py --check-file artifacts/rules_ir.json
    python validate_bh_codes.py --peer-reviewer-for F11.20

Exit codes: 0 clean, 1 findings, 2 usage error.

This makes NO clinical judgement. A finding is a prompt to look, not a verdict.
"""

import argparse
import json
import re
import sys

# --------------------------------------------------------------------------
# Code sets. Kept deliberately explicit rather than pattern-matched: the whole
# value of this script is that it disagrees with a plausible-looking guess.
# --------------------------------------------------------------------------

CPT_PSYCH = {
    "90791": "Psychiatric diagnostic evaluation, no medical services",
    "90792": "Psychiatric diagnostic evaluation with medical services",
    "90832": "Psychotherapy, 30 minutes",
    "90834": "Psychotherapy, 45 minutes",
    "90837": "Psychotherapy, 60 minutes",
    "90853": "Group psychotherapy",
}

CPT_ABA = {
    "97151": "Behavior identification assessment",
    "97152": "Behavior identification supporting assessment",
    "97153": "Adaptive behavior treatment by protocol",
    "97154": "Group adaptive behavior treatment by protocol",
    "97155": "Adaptive behavior treatment with protocol modification",
    "97156": "Family adaptive behavior treatment guidance",
    "97157": "Multiple-family group adaptive behavior treatment guidance",
    "97158": "Group adaptive behavior treatment with protocol modification",
}

# Rough ASAM mapping. Payer-specific in reality -- see bh-code-sets.md.
HCPCS_LOC = {
    "H0015": ("Intensive outpatient program, SUD", ["2.1"]),
    "H0018": ("Short-term residential, non-hospital", ["3.1", "3.5"]),
    "H0019": ("Long-term residential, non-hospital", ["3.5", "3.7"]),
    "H0035": ("Partial hospitalization, mental health", ["2.5"]),
    "H2036": ("Alcohol/drug treatment program, per diem", ["2.1", "2.5", "3.1", "3.5"]),
    "S9480": ("Intensive outpatient psychiatric services", ["2.1"]),
}

ASAM_LEVELS = ["0.5", "1.0", "2.1", "2.5", "3.1", "3.5", "3.7", "4.0"]

# Continued-stay cadence in days, by level. See asam-levels.md.
ASAM_INTERVAL = {
    "4.0": 3, "3.7": 5, "3.5": 7, "3.1": 14,
    "2.5": 14, "2.1": 30, "1.0": 90, "0.5": 90,
}

ICD10_BLOCKS = [
    (10, 19, "Substance use", "MD_ADDICTION"),
    (20, 29, "Schizophrenia / delusional", "MD_PSYCH"),
    (30, 39, "Mood (affective)", "MD_PSYCH"),
    (40, 48, "Anxiety / stress-related", "MD_PSYCH"),
    (50, 59, "Behavioural syndromes, physiological", "MD_PSYCH"),
    (60, 69, "Adult personality and behaviour", "MD_PSYCH"),
    (70, 79, "Intellectual disabilities", None),
    (80, 89, "Psychological development", None),
    (90, 98, "Childhood-onset behavioural/emotional", None),
]

INSTRUMENT_RANGE = {
    "PHQ9": (0, 27),
    "GAD7": (0, 21),
    "CSSRS": (0, 5),
    "ASAM_DIM": (0, 4),
}

ICD10_RE = re.compile(r"^F(\d{2})(?:\.(\d{1,2}))?$")


class Findings(list):
    def add(self, severity, code, message):
        self.append({"severity": severity, "code": code, "message": message})


# --------------------------------------------------------------------------


def classify_diagnosis(dx):
    """Return (block_label, expected_peer_credential) or (None, None)."""
    m = ICD10_RE.match((dx or "").strip().upper())
    if not m:
        return None, None
    n = int(m.group(1))
    for lo, hi, label, cred in ICD10_BLOCKS:
        if lo <= n <= hi:
            return label, cred
    return None, None


def check_service(code, findings):
    code = (code or "").strip().upper()
    if code in CPT_PSYCH:
        return "cpt_psych"
    if code in CPT_ABA:
        return "cpt_aba"
    if code in HCPCS_LOC:
        return "hcpcs_loc"

    # Distinguish "wrong code" from "code we do not carry", because they call
    # for different responses: the first is a defect, the second is a lookup.
    if re.match(r"^\d{5}$", code):
        findings.add("warn", code,
                     "Numeric CPT not in the behavioral-health sets carried here. "
                     "Verify against the payer's own fee schedule before treating "
                     "it as a BH service.")
    elif re.match(r"^[A-Z]\d{4}$", code):
        findings.add("warn", code,
                     "HCPCS-shaped but not in the level-of-care set carried here.")
    else:
        findings.add("error", code, "Not a structurally valid CPT or HCPCS code.")
    return None


def check_diagnosis(code, findings):
    raw = (code or "").strip().upper()
    if not ICD10_RE.match(raw):
        findings.add("error", raw,
                     "Not a structurally valid ICD-10 chapter F code. Behavioral-health "
                     "diagnoses are F00-F99; anything else on a BH authorization is "
                     "worth questioning.")
        return None, None
    label, cred = classify_diagnosis(raw)
    if label is None:
        findings.add("warn", raw, "Valid chapter F code outside the blocks carried here.")
    return label, cred


def check_pair(service, diagnosis, findings):
    """Structural plausibility only. Not a clinical judgement."""
    kind = check_service(service, findings)
    label, _cred = check_diagnosis(diagnosis, findings)
    if kind is None or label is None:
        return

    if kind == "cpt_aba" and label == "Substance use":
        findings.add("warn", f"{service}+{diagnosis}",
                     "Adaptive-behavior (ABA) service against a substance-use diagnosis. "
                     "Structurally implausible -- check the mapping.")

    if kind == "hcpcs_loc":
        _desc, levels = HCPCS_LOC[service.strip().upper()]
        if label != "Substance use" and service.strip().upper() in ("H0015", "H0018", "H0019"):
            findings.add("info", f"{service}+{diagnosis}",
                         "SUD level-of-care code against a non-SUD diagnosis. Some payers "
                         "permit this for co-occurring presentations; confirm the legacy "
                         "system's own rule rather than assuming.")
        del levels


def check_level(level, findings, ctx=""):
    lv = (level or "").strip()
    if lv not in ASAM_LEVELS:
        findings.add("error", lv or "(empty)",
                     f"Not an ASAM level{ctx}. Expected one of {', '.join(ASAM_LEVELS)}.")
        return False
    return True


def check_interval(level, days, findings):
    """The cadence is a function of LEVEL, not of units approved."""
    lv = (level or "").strip()
    expected = ASAM_INTERVAL.get(lv)
    if expected is None:
        return
    if int(days) != expected:
        findings.add("error", lv,
                     f"Continued-stay interval {days} days does not match the {expected}-day "
                     f"cadence for ASAM {lv}. Interval follows the level, not the unit count.")


def check_instrument(name, score, findings):
    key = (name or "").strip().upper()
    rng = INSTRUMENT_RANGE.get(key)
    if rng is None:
        findings.add("warn", key, "Unknown instrument.")
        return
    lo, hi = rng
    if not (lo <= int(score) <= hi):
        findings.add("error", f"{key}={score}",
                     f"Out of range; {key} scores {lo}-{hi}. An out-of-range dimension score "
                     f"walks a first-match ladder to its most intensive branch without comment.")


# --------------------------------------------------------------------------


def check_file(path, findings):
    """Walk a rules IR / decision-table JSON and check every code it mentions.

    Tolerant by design: it looks for known key names anywhere in the structure
    rather than requiring one schema, because it runs against both the extracted
    IR and hand-written test fixtures.
    """
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)

    seen = {"service": 0, "diagnosis": 0, "level": 0, "instrument": 0}

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                kl = k.lower()
                if kl in ("service_code", "servicecode", "service") and isinstance(v, str):
                    check_service(v, findings); seen["service"] += 1
                elif kl in ("diagnosis_code", "diagnosiscode", "diagnosis", "dx") and isinstance(v, str):
                    check_diagnosis(v, findings); seen["diagnosis"] += 1
                elif kl in ("granted_loc", "grantedloc", "requested_loc", "requestedloc",
                            "reviewed_loc", "level", "loc") and isinstance(v, str):
                    check_level(v, findings, f" (key '{k}')"); seen["level"] += 1
                elif kl in ("instrument",) and isinstance(v, str):
                    score = node.get("score")
                    if score is not None:
                        check_instrument(v, score, findings); seen["instrument"] += 1
                walk(v)
            # Interval consistency, when both halves are present on one node.
            lvl = node.get("granted_loc") or node.get("grantedLoc") or node.get("reviewed_loc")
            iv = node.get("interval_days") or node.get("intervalDays") or node.get("review_interval_days")
            if isinstance(lvl, str) and iv is not None:
                check_interval(lvl, iv, findings)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(doc)
    return seen


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--service")
    ap.add_argument("--diagnosis")
    ap.add_argument("--level")
    ap.add_argument("--instrument", nargs=2, metavar=("NAME", "SCORE"))
    ap.add_argument("--peer-reviewer-for", metavar="ICD10",
                    help="Print the peer-review credential expected for a diagnosis.")
    ap.add_argument("--check-file", metavar="PATH")
    ap.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    args = ap.parse_args(argv)

    findings = Findings()

    if args.peer_reviewer_for:
        label, cred = classify_diagnosis(args.peer_reviewer_for)
        if label is None:
            print(f"{args.peer_reviewer_for}: not a recognised chapter F code", file=sys.stderr)
            return 2
        print(f"{args.peer_reviewer_for}  block={label}  peer_reviewer={cred or 'none required'}")
        return 0

    did_something = False

    if args.service and args.diagnosis:
        check_pair(args.service, args.diagnosis, findings); did_something = True
    else:
        if args.service:
            check_service(args.service, findings); did_something = True
        if args.diagnosis:
            check_diagnosis(args.diagnosis, findings); did_something = True

    if args.level:
        check_level(args.level, findings); did_something = True
    if args.instrument:
        check_instrument(args.instrument[0], args.instrument[1], findings); did_something = True
    if args.check_file:
        seen = check_file(args.check_file, findings); did_something = True
        if not args.json:
            print(f"checked {args.check_file}: " + ", ".join(f"{v} {k}" for k, v in seen.items()))

    if not did_something:
        ap.print_help(sys.stderr)
        return 2

    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        for f in findings:
            print(f"  [{f['severity']:5}] {f['code']}: {f['message']}")
        if not findings:
            print("  clean")

    return 1 if any(f["severity"] == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
