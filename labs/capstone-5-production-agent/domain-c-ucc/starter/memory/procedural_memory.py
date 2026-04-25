"""
Procedural Memory — learned rules and patterns from experience.

Stores rules that the system has learned (or been configured with),
such as "Delaware filings always use XML format" or "Pinnacle Transport
Services was renamed to Trident Logistics Group in 2022."

Rules have confidence scores that increase with successful application
and decrease when they lead to errors.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class Rule:
    """A learned rule or pattern."""
    rule_id: str
    category: str           # "state_format", "entity_alias", "collateral_pattern", etc.
    condition: str          # When this rule applies (human-readable)
    action: str             # What to do when condition is met
    confidence: float       # 0.0 to 1.0
    times_applied: int = 0
    times_succeeded: int = 0
    created_at: str = ""
    last_applied: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pre-loaded rules — things the system "knows" from configuration
# ---------------------------------------------------------------------------
DEFAULT_RULES = [
    Rule(
        rule_id="state-format-de-xml",
        category="state_format",
        condition="State is Delaware (DE)",
        action="Use XML parser for filing data ingestion",
        confidence=1.0,
        metadata={"state": "DE", "format": "XML"},
    ),
    Rule(
        rule_id="state-format-tx-fixed",
        category="state_format",
        condition="State is Texas (TX)",
        action="Use fixed-width parser with latin-1 encoding and YYYYMMDD date format",
        confidence=1.0,
        metadata={"state": "TX", "format": "fixed_width", "encoding": "latin-1"},
    ),
    Rule(
        rule_id="state-format-fl-pipe",
        category="state_format",
        condition="State is Florida (FL)",
        action="Use pipe-delimited CSV parser",
        confidence=1.0,
        metadata={"state": "FL", "delimiter": "|"},
    ),
    Rule(
        rule_id="entity-alias-pinnacle-transport",
        category="entity_alias",
        condition="Entity name contains 'Pinnacle Transport'",
        action="This is Trident Logistics Group LLC (renamed 2022-09-01), NOT Pinnacle Systems International",
        confidence=0.95,
        metadata={"ein": "51-0482193", "current_name": "Trident Logistics Group LLC"},
    ),
    Rule(
        rule_id="entity-alias-acme-variations",
        category="entity_alias",
        condition="Entity name matches 'Acme Corp', 'ACME CORPORATION', or 'AcmeTech Solutions'",
        action="All refer to Acme Corporation (EIN 94-3829471). Check for Acme Holdings LLC (EIN 94-5501287) which is the parent company.",
        confidence=0.95,
        metadata={"ein": "94-3829471"},
    ),
    Rule(
        rule_id="collateral-blanket-lien",
        category="collateral_pattern",
        condition="Collateral description contains 'all assets' or 'now owned or hereafter acquired'",
        action="Classify as blanket lien (high risk). This filing claims priority over all debtor assets.",
        confidence=0.9,
        metadata={"risk_level": "high"},
    ),
    Rule(
        rule_id="lapse-5-year",
        category="filing_lifecycle",
        condition="UCC-1 filing is approaching 5-year anniversary without continuation",
        action="Flag as at-risk for lapse. UCC-1 filings lapse 5 years after filing date unless a UCC-3 continuation is filed.",
        confidence=1.0,
    ),
    Rule(
        rule_id="date-format-ca",
        category="state_format",
        condition="State is California (CA)",
        action="Dates may be in MM/DD/YYYY format instead of YYYY-MM-DD",
        confidence=0.9,
        metadata={"state": "CA", "date_format": "%m/%d/%Y"},
    ),
]


class ProceduralMemory:
    """
    Long-term memory of learned rules and patterns.

    Think of this like a playbook or operations manual that gets updated
    as the team encounters new situations. Rules start with a confidence
    score and that score adjusts based on outcomes.
    """

    def __init__(self, max_rules: int = 50):
        self._rules: Dict[str, Rule] = {}
        self._max_rules = max_rules
        # Load default rules
        for rule in DEFAULT_RULES:
            rule.created_at = datetime.utcnow().isoformat()
            self._rules[rule.rule_id] = rule

    # ------------------------------------------------------------------
    # TODO 1: Implement add_rule()
    # Add a new rule to procedural memory.
    # If rule_id already exists, update confidence (average old and new).
    # If at capacity, remove the rule with lowest confidence.
    # ------------------------------------------------------------------
    def add_rule(self, rule: Rule) -> None:
        """Add or update a rule in procedural memory."""
        # TODO: If rule_id exists, update confidence = avg(old, new)
        # TODO: If at capacity, find and remove lowest-confidence rule
        # TODO: Set created_at if not set
        # TODO: Store in self._rules
        pass

    # ------------------------------------------------------------------
    # TODO 2: Implement get_rules_for_category()
    # Return all rules matching the given category, sorted by
    # confidence descending.
    # ------------------------------------------------------------------
    def get_rules_for_category(self, category: str) -> List[Rule]:
        """Get all rules for a specific category."""
        # TODO: Filter by category, sort by confidence descending
        pass

    # ------------------------------------------------------------------
    # TODO 3: Implement find_applicable_rules()
    # Search rules whose condition text contains any of the given keywords.
    # Return rules sorted by confidence descending.
    # Parameters:
    #   - keywords: list of strings to search for in rule conditions
    #   - min_confidence: minimum confidence threshold (default 0.5)
    # ------------------------------------------------------------------
    def find_applicable_rules(
        self,
        keywords: List[str],
        min_confidence: float = 0.5,
    ) -> List[Rule]:
        """Find rules whose conditions match the given keywords."""
        # TODO: For each rule, check if any keyword appears in rule.condition (case-insensitive)
        # TODO: Filter by min_confidence
        # TODO: Sort by confidence descending
        pass

    # ------------------------------------------------------------------
    # TODO 4: Implement record_outcome()
    # Record whether applying a rule succeeded or failed.
    # Update times_applied, times_succeeded, last_applied.
    # Adjust confidence:
    #   - success: confidence = min(1.0, confidence + 0.02)
    #   - failure: confidence = max(0.0, confidence - 0.05)
    # ------------------------------------------------------------------
    def record_outcome(self, rule_id: str, success: bool) -> None:
        """Record the outcome of applying a rule."""
        # TODO: Look up rule by ID
        # TODO: Increment times_applied
        # TODO: If success, increment times_succeeded and boost confidence
        # TODO: If failure, decrease confidence
        # TODO: Update last_applied timestamp
        pass

    # ------------------------------------------------------------------
    # TODO 5: Implement get_stats()
    # Return a dict with:
    #   - total_rules, rules_by_category (dict of category: count),
    #   - avg_confidence, most_applied_rule (rule_id or None),
    #   - least_confident_rule (rule_id or None)
    # ------------------------------------------------------------------
    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about stored rules."""
        # TODO: Compute and return stats
        pass

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a specific rule by ID."""
        return self._rules.get(rule_id)

    @property
    def rules(self) -> Dict[str, Rule]:
        """Return all rules."""
        return self._rules

    def __len__(self) -> int:
        return len(self._rules)
