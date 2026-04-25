"""
Configuration for the Production Agent system.
(Solution — identical to starter/config.py)
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

@dataclass
class ModelTier:
    name: str
    model_id: str
    input_cost_per_1k: float
    output_cost_per_1k: float
    max_tokens: int
    strengths: List[str]

MODEL_TIERS = {
    "fast": ModelTier(
        name="fast", model_id="claude-sonnet-4-20250514",
        input_cost_per_1k=0.003, output_cost_per_1k=0.015,
        max_tokens=4096,
        strengths=["classification", "formatting", "simple_lookup", "validation"],
    ),
    "balanced": ModelTier(
        name="balanced", model_id="claude-sonnet-4-20250514",
        input_cost_per_1k=0.003, output_cost_per_1k=0.015,
        max_tokens=8192,
        strengths=["entity_resolution", "multi_step_reasoning", "data_transformation", "summarization"],
    ),
    "powerful": ModelTier(
        name="powerful", model_id="claude-sonnet-4-20250514",
        input_cost_per_1k=0.003, output_cost_per_1k=0.015,
        max_tokens=8192,
        strengths=["risk_analysis", "complex_reasoning", "ambiguous_cases", "collateral_classification"],
    ),
}

@dataclass
class RoutingRule:
    task_type: str
    default_tier: str
    upgrade_conditions: Dict[str, any] = field(default_factory=dict)
    description: str = ""

ROUTING_RULES = [
    RoutingRule("filing_lookup", "fast",
                {"multi_state": "balanced", "ambiguous_name": "balanced"},
                "Simple filing lookups go to fast tier; multi-state or fuzzy searches upgrade"),
    RoutingRule("entity_resolution", "balanced",
                {"confidence_below_70": "powerful", "name_variations_above_3": "powerful"},
                "Entity resolution defaults to balanced; complex cases upgrade"),
    RoutingRule("risk_assessment", "powerful", {},
                "Risk assessments always go to the powerful tier"),
    RoutingRule("collateral_classification", "balanced",
                {"ambiguous_description": "powerful"},
                "Collateral classification defaults to balanced; ambiguous cases upgrade"),
    RoutingRule("data_validation", "fast", {},
                "Format validation and schema checks always go to fast tier"),
    RoutingRule("report_generation", "balanced",
                {"multi_entity": "powerful"},
                "Report generation defaults to balanced; multi-entity reports upgrade"),
]

COMPLEXITY_WEIGHTS = {
    "token_count": 0.2, "tool_count": 0.3, "entity_count": 0.2,
    "state_count": 0.15, "ambiguity_score": 0.15,
}

COMPLEXITY_THRESHOLDS = {
    "fast": (0.0, 0.3), "balanced": (0.3, 0.7), "powerful": (0.7, 1.0),
}

SYSTEM_PROMPTS = {
    "router": """You are the Router Agent for a UCC (Uniform Commercial Code) data platform.
Your job is to analyze incoming queries and route them to the appropriate specialist agent.

Available agents:
- filing_agent: Handles UCC filing lookups, searches, and status checks
- entity_agent: Handles entity resolution, name matching, and business registry lookups
- risk_agent: Handles lien risk assessment, collateral analysis, and portfolio exposure reports

Analyze the user's query and determine:
1. Which agent(s) should handle this request
2. What specific task type this is (filing_lookup, entity_resolution, risk_assessment, etc.)
3. The complexity level (simple, medium, complex)

Respond with a JSON object containing your routing decision.""",

    "filing": """You are the Filing Agent for a UCC data platform.
You specialize in UCC filing lookups, searches, and status analysis.

You have access to these tools:
- search_filings: Search UCC filings by debtor name, state, or filing number
- get_filing_details: Get full details for a specific filing
- check_filing_status: Check if a filing is active, lapsed, or terminated
- get_amendments: Get amendment history for a filing

Always provide complete, accurate information about filing status, dates, and parties.""",

    "entity": """You are the Entity Resolution Agent for a UCC data platform.
You specialize in matching business entities across different filings and states.

You have access to these tools:
- search_filings: Search filings across states
- fuzzy_match: Compare entity names for similarity
- get_business_registry: Look up official business registration data
- merge_entity_profile: Combine data from multiple sources into a unified profile

Consider name variations, DBAs, abbreviations, and historical name changes.""",

    "risk": """You are the Risk Assessment Agent for a UCC data platform.
You specialize in analyzing lien exposure, collateral coverage, and credit risk.

You have access to these tools:
- search_filings: Find all filings for an entity
- classify_collateral: Categorize collateral descriptions
- calculate_exposure: Compute total lien exposure
- generate_risk_report: Create a structured risk assessment

Consider filing priority (first-in-time), collateral overlap, and blanket liens.""",
}

@dataclass
class ObservabilityConfig:
    enable_tracing: bool = True
    enable_metrics: bool = True
    trace_sample_rate: float = 1.0
    log_level: str = "INFO"
    export_format: str = "console"
    max_trace_depth: int = 10

OBSERVABILITY = ObservabilityConfig()

APP_CONFIG = {
    "app_name": "UCC Production Agent",
    "version": "1.0.0",
    "max_retries": 3,
    "retry_delay_seconds": 1.0,
    "request_timeout_seconds": 30.0,
    "max_concurrent_requests": 5,
    "memory_ttl_seconds": 3600,
    "episodic_memory_limit": 100,
    "procedural_memory_limit": 50,
}
