"""
Procedural Memory — learned rules and patterns from experience.
(Solution — fully implemented)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


@dataclass
class Rule:
    rule_id: str
    category: str
    condition: str
    action: str
    confidence: float
    times_applied: int = 0
    times_succeeded: int = 0
    created_at: str = ""
    last_applied: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


DEFAULT_RULES = [
    Rule(rule_id="state-format-de-xml", category="state_format",
         condition="State is Delaware (DE)",
         action="Use XML parser for filing data ingestion",
         confidence=1.0, metadata={"state": "DE", "format": "XML"}),
    Rule(rule_id="state-format-tx-fixed", category="state_format",
         condition="State is Texas (TX)",
         action="Use fixed-width parser with latin-1 encoding and YYYYMMDD date format",
         confidence=1.0, metadata={"state": "TX", "format": "fixed_width", "encoding": "latin-1"}),
    Rule(rule_id="state-format-fl-pipe", category="state_format",
         condition="State is Florida (FL)",
         action="Use pipe-delimited CSV parser",
         confidence=1.0, metadata={"state": "FL", "delimiter": "|"}),
    Rule(rule_id="entity-alias-pinnacle-transport", category="entity_alias",
         condition="Entity name contains 'Pinnacle Transport'",
         action="This is Trident Logistics Group LLC (renamed 2022-09-01), NOT Pinnacle Systems International",
         confidence=0.95, metadata={"ein": "51-0482193", "current_name": "Trident Logistics Group LLC"}),
    Rule(rule_id="entity-alias-acme-variations", category="entity_alias",
         condition="Entity name matches 'Acme Corp', 'ACME CORPORATION', or 'AcmeTech Solutions'",
         action="All refer to Acme Corporation (EIN 94-3829471). Check for Acme Holdings LLC (EIN 94-5501287) which is the parent company.",
         confidence=0.95, metadata={"ein": "94-3829471"}),
    Rule(rule_id="collateral-blanket-lien", category="collateral_pattern",
         condition="Collateral description contains 'all assets' or 'now owned or hereafter acquired'",
         action="Classify as blanket lien (high risk). This filing claims priority over all debtor assets.",
         confidence=0.9, metadata={"risk_level": "high"}),
    Rule(rule_id="lapse-5-year", category="filing_lifecycle",
         condition="UCC-1 filing is approaching 5-year anniversary without continuation",
         action="Flag as at-risk for lapse. UCC-1 filings lapse 5 years after filing date unless a UCC-3 continuation is filed.",
         confidence=1.0),
    Rule(rule_id="date-format-ca", category="state_format",
         condition="State is California (CA)",
         action="Dates may be in MM/DD/YYYY format instead of YYYY-MM-DD",
         confidence=0.9, metadata={"state": "CA", "date_format": "%m/%d/%Y"}),
]


class ProceduralMemory:
    """Long-term memory of learned rules and patterns."""

    def __init__(self, max_rules: int = 50):
        self._rules: Dict[str, Rule] = {}
        self._max_rules = max_rules
        for rule in DEFAULT_RULES:
            rule.created_at = datetime.now(timezone.utc).isoformat()
            self._rules[rule.rule_id] = rule

    def add_rule(self, rule: Rule) -> None:
        if rule.rule_id in self._rules:
            existing = self._rules[rule.rule_id]
            existing.confidence = (existing.confidence + rule.confidence) / 2
            return
        if len(self._rules) >= self._max_rules:
            lowest = min(self._rules.values(), key=lambda r: r.confidence)
            del self._rules[lowest.rule_id]
        if not rule.created_at:
            rule.created_at = datetime.now(timezone.utc).isoformat()
        self._rules[rule.rule_id] = rule

    def get_rules_for_category(self, category: str) -> List[Rule]:
        rules = [r for r in self._rules.values() if r.category == category]
        rules.sort(key=lambda r: r.confidence, reverse=True)
        return rules

    def find_applicable_rules(
        self, keywords: List[str], min_confidence: float = 0.5,
    ) -> List[Rule]:
        results = []
        for rule in self._rules.values():
            if rule.confidence < min_confidence:
                continue
            condition_lower = rule.condition.lower()
            if any(kw.lower() in condition_lower for kw in keywords):
                results.append(rule)
        results.sort(key=lambda r: r.confidence, reverse=True)
        return results

    def record_outcome(self, rule_id: str, success: bool) -> None:
        rule = self._rules.get(rule_id)
        if not rule:
            return
        rule.times_applied += 1
        if success:
            rule.times_succeeded += 1
            rule.confidence = min(1.0, rule.confidence + 0.02)
        else:
            rule.confidence = max(0.0, rule.confidence - 0.05)
        rule.last_applied = datetime.now(timezone.utc).isoformat()

    def get_stats(self) -> Dict[str, Any]:
        if not self._rules:
            return {"total_rules": 0, "rules_by_category": {}, "avg_confidence": 0.0,
                    "most_applied_rule": None, "least_confident_rule": None}
        categories = {}
        for r in self._rules.values():
            categories[r.category] = categories.get(r.category, 0) + 1
        avg_conf = sum(r.confidence for r in self._rules.values()) / len(self._rules)
        most_applied = max(self._rules.values(), key=lambda r: r.times_applied)
        least_conf = min(self._rules.values(), key=lambda r: r.confidence)
        return {
            "total_rules": len(self._rules),
            "rules_by_category": categories,
            "avg_confidence": round(avg_conf, 3),
            "most_applied_rule": most_applied.rule_id,
            "least_confident_rule": least_conf.rule_id,
        }

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        return self._rules.get(rule_id)

    @property
    def rules(self) -> Dict[str, Rule]:
        return self._rules

    def __len__(self) -> int:
        return len(self._rules)
