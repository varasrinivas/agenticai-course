"""
M26 Lab — Step 4: Coordinator + Subagent Pattern

The coordinator decomposes complex tasks and delegates to specialized
subagents with isolated contexts. Each subagent sees only what it needs.

Usage:
    python subagent_coordinator.py
"""

import json
import copy
from datetime import datetime


# --- Mock data for subagent responses ---

MOCK_FILING_DATA = {
    "UCC-2024-NY-0012847": {
        "filing_number": "UCC-2024-NY-0012847",
        "status": "Active",
        "state": "NY",
        "debtor": "Greenfield Logistics LLC",
        "secured_party": "Atlantic Capital Partners",
        "filing_date": "2024-03-15",
        "collateral": "All accounts receivable, inventory, equipment"
    },
    "UCC-2023-CA-0098312": {
        "filing_number": "UCC-2023-CA-0098312",
        "status": "Active",
        "state": "CA",
        "debtor": "Greenfield Logistics West LLC",
        "secured_party": "Pacific Trust Holdings",
        "filing_date": "2023-09-01",
        "collateral": "Inventory and warehouse equipment"
    }
}

MOCK_ENTITY_DATA = {
    "Greenfield Logistics LLC": {
        "canonical_name": "Greenfield Logistics LLC",
        "aliases": ["Greenfield Logistics", "Greenfield Log. LLC", "GL LLC"],
        "state_of_formation": "NY",
        "related_entities": ["Greenfield Logistics West LLC", "Greenfield Transport Inc"],
        "ucc_filings": ["UCC-2024-NY-0012847"],
        "confidence": 0.95
    },
    "Greenfield Logistics West LLC": {
        "canonical_name": "Greenfield Logistics West LLC",
        "aliases": ["GL West", "Greenfield West"],
        "state_of_formation": "CA",
        "related_entities": ["Greenfield Logistics LLC"],
        "ucc_filings": ["UCC-2023-CA-0098312"],
        "confidence": 0.92
    }
}

MOCK_RISK_DATA = {
    "Greenfield Logistics LLC": {
        "risk_score": 0.35,
        "risk_level": "LOW",
        "factors": ["No prior defaults", "Active 5+ years", "Single active lien"],
        "total_lien_value": 250000,
        "last_updated": "2024-12-01"
    },
    "Greenfield Logistics West LLC": {
        "risk_score": 0.42,
        "risk_level": "LOW",
        "factors": ["No prior defaults", "Active 2+ years", "Single active lien"],
        "total_lien_value": 120000,
        "last_updated": "2024-11-15"
    }
}


class SubAgent:
    """
    A specialized agent with its own system prompt, tools, and isolated context.

    Key principle: Subagents see ONLY the information explicitly passed to them
    by the coordinator. They never see the full conversation or other subagents' data.
    """

    def __init__(self, name, role, system_prompt, tools=None):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.messages = []  # Isolated message history
        self.result = None
        self.execution_time_ms = 0

    def execute(self, task_description, context=None):
        """
        Execute a task with optional context from the coordinator.

        In production, this would call the Agent SDK's query() with
        isolated context. Here we simulate the subagent's work.
        """
        start_time = datetime.now()

        print(f"\n    [{self.name}] Starting: {task_description[:60]}...")
        if context:
            print(f"    [{self.name}] Received context: {json.dumps(context)[:80]}...")

        # Add the task to this subagent's isolated history
        self.messages.append({
            "role": "user",
            "content": task_description,
            "context": context
        })

        # Simulate subagent work based on role
        self.result = self._simulate_work(task_description, context)

        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        self.execution_time_ms = elapsed

        print(f"    [{self.name}] Complete ({elapsed:.0f}ms)")
        print(f"    [{self.name}] Result keys: {list(self.result.keys()) if isinstance(self.result, dict) else 'N/A'}")

        return self.result

    def _simulate_work(self, task, context):
        """Simulate subagent-specific work based on role."""
        if self.role == "filing_search":
            return self._filing_search(context)
        elif self.role == "entity_resolution":
            return self._entity_resolution(context)
        elif self.role == "risk_scoring":
            return self._risk_scoring(context)
        else:
            return {"error": f"Unknown role: {self.role}"}

    def _filing_search(self, context):
        entity_name = context.get("entity_name", "") if context else ""
        results = []
        for filing_id, filing in MOCK_FILING_DATA.items():
            if entity_name.lower() in filing["debtor"].lower():
                results.append(filing)
        # Also check related entities
        entity_info = MOCK_ENTITY_DATA.get(entity_name, {})
        for related in entity_info.get("related_entities", []):
            for filing_id, filing in MOCK_FILING_DATA.items():
                if related.lower() in filing["debtor"].lower() and filing not in results:
                    results.append(filing)
        return {
            "filings_found": len(results),
            "filings": results,
            "search_entity": entity_name,
            "states_covered": list(set(f["state"] for f in results))
        }

    def _entity_resolution(self, context):
        entity_name = context.get("entity_name", "") if context else ""
        entity = MOCK_ENTITY_DATA.get(entity_name, {})
        related_entities = []
        for related_name in entity.get("related_entities", []):
            related = MOCK_ENTITY_DATA.get(related_name, {})
            if related:
                related_entities.append(related)
        return {
            "canonical_entity": entity,
            "related_entities": related_entities,
            "total_entities": 1 + len(related_entities),
            "resolution_confidence": entity.get("confidence", 0.0)
        }

    def _risk_scoring(self, context):
        entities = context.get("entities", []) if context else []
        risk_profiles = []
        for entity_name in entities:
            risk = MOCK_RISK_DATA.get(entity_name, {})
            if risk:
                risk_profiles.append({"entity": entity_name, **risk})
        # Compute aggregate risk
        if risk_profiles:
            avg_score = sum(r["risk_score"] for r in risk_profiles) / len(risk_profiles)
            total_lien = sum(r["total_lien_value"] for r in risk_profiles)
        else:
            avg_score = 0.0
            total_lien = 0
        return {
            "individual_profiles": risk_profiles,
            "aggregate_risk_score": round(avg_score, 3),
            "aggregate_risk_level": "LOW" if avg_score < 0.4 else "MEDIUM" if avg_score < 0.7 else "HIGH",
            "total_lien_exposure": total_lien
        }


class Coordinator:
    """
    Decomposes complex tasks and delegates to specialized subagents.

    The coordinator:
    1. Analyzes the incoming request
    2. Decomposes it into subtasks
    3. Assigns subtasks to subagents with ONLY the context they need
    4. Aggregates results with provenance tracking
    """

    def __init__(self):
        self.subagents = {}
        self.execution_log = []

    def register_subagent(self, subagent):
        """Register a subagent for task delegation."""
        self.subagents[subagent.role] = subagent
        print(f"  [Coordinator] Registered subagent: {subagent.name} (role: {subagent.role})")

    def process_request(self, request):
        """
        Full coordinator workflow:
        1. Decompose the request into subtasks
        2. Execute subtasks (with context isolation)
        3. Aggregate results with provenance
        """
        print(f"\n{'='*60}")
        print(f"Coordinator: Processing request")
        print(f"{'='*60}")
        print(f"  Request: {request[:80]}...")

        # Step 1: Decompose
        subtasks = self.decompose_task(request)
        print(f"\n  Decomposed into {len(subtasks)} subtasks:")
        for st in subtasks:
            print(f"    - [{st['role']}] {st['description'][:60]}...")

        # Step 2: Execute subtasks
        results = {}
        for subtask in subtasks:
            role = subtask["role"]
            if role not in self.subagents:
                print(f"    [!] No subagent for role: {role}")
                continue

            subagent = self.subagents[role]

            # CRITICAL: Pass only the context this subagent needs
            # The coordinator explicitly controls what each subagent sees
            result = subagent.execute(
                task_description=subtask["description"],
                context=subtask.get("context", {})
            )
            results[role] = result

            self.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "subagent": subagent.name,
                "role": role,
                "task": subtask["description"][:60],
                "execution_time_ms": subagent.execution_time_ms
            })

            # Pass results to downstream subtasks that need them
            # (e.g., risk scoring needs entity names from entity resolution)
            if role == "entity_resolution" and "risk_scoring" in [s["role"] for s in subtasks]:
                entities = [result["canonical_entity"].get("canonical_name", "")]
                entities += [e.get("canonical_name", "") for e in result.get("related_entities", [])]
                for st in subtasks:
                    if st["role"] == "risk_scoring":
                        st["context"]["entities"] = [e for e in entities if e]

        # Step 3: Aggregate
        report = self.aggregate_results(results)
        return report

    def decompose_task(self, request):
        """
        Break a request into subtasks for specialized subagents.

        In production, you might use Claude to do this decomposition.
        Here we use pattern matching for demonstration.
        """
        # Extract entity name (simplified)
        entity_name = "Greenfield Logistics LLC"  # In production, extract from request

        subtasks = [
            {
                "role": "filing_search",
                "description": f"Search for all UCC filings related to {entity_name} across all states",
                "context": {"entity_name": entity_name}
            },
            {
                "role": "entity_resolution",
                "description": f"Resolve {entity_name} to canonical form and find all related entities",
                "context": {"entity_name": entity_name}
            },
            {
                "role": "risk_scoring",
                "description": f"Calculate risk scores for {entity_name} and all related entities",
                "context": {"entities": [entity_name]}  # Will be enriched after entity resolution
            }
        ]

        return subtasks

    def aggregate_results(self, results):
        """
        Combine subagent outputs into a single report with provenance.

        Provenance tracking answers: "Where did this information come from?"
        This is critical for compliance and auditability.
        """
        print(f"\n  [Coordinator] Aggregating results from {len(results)} subagents...")

        filing_results = results.get("filing_search", {})
        entity_results = results.get("entity_resolution", {})
        risk_results = results.get("risk_scoring", {})

        report = {
            "summary": {
                "request_type": "Cross-state UCC entity research",
                "timestamp": datetime.now().isoformat(),
                "subagents_used": list(results.keys()),
            },
            "findings": {
                "total_filings": filing_results.get("filings_found", 0),
                "states_covered": filing_results.get("states_covered", []),
                "total_related_entities": entity_results.get("total_entities", 0),
                "resolution_confidence": entity_results.get("resolution_confidence", 0),
                "aggregate_risk_level": risk_results.get("aggregate_risk_level", "UNKNOWN"),
                "aggregate_risk_score": risk_results.get("aggregate_risk_score", 0),
                "total_lien_exposure": risk_results.get("total_lien_exposure", 0),
            },
            "provenance": {
                "filing_data": {
                    "source": "filing_search subagent",
                    "filings": filing_results.get("filings", [])
                },
                "entity_data": {
                    "source": "entity_resolution subagent",
                    "canonical": entity_results.get("canonical_entity", {}),
                    "related": entity_results.get("related_entities", [])
                },
                "risk_data": {
                    "source": "risk_scoring subagent",
                    "profiles": risk_results.get("individual_profiles", [])
                }
            }
        }

        return report


# --- Main demo ---

def main():
    print("=" * 60)
    print("M26 Lab — Coordinator + Subagent Pattern")
    print("=" * 60)

    # --- Create coordinator ---
    coordinator = Coordinator()

    # --- Create specialized subagents ---
    filing_agent = SubAgent(
        name="FilingSearchAgent",
        role="filing_search",
        system_prompt="You search UCC filing databases across all US states. Return all filings for the given entity and related entities.",
        tools=["search_filings", "search_by_debtor", "search_by_secured_party"]
    )

    entity_agent = SubAgent(
        name="EntityResolutionAgent",
        role="entity_resolution",
        system_prompt="You resolve entity names to canonical forms, find aliases, and identify related entities across jurisdictions.",
        tools=["resolve_entity", "find_aliases", "find_related"]
    )

    risk_agent = SubAgent(
        name="RiskScoringAgent",
        role="risk_scoring",
        system_prompt="You calculate risk scores based on filing history, lien exposure, and entity relationships.",
        tools=["calculate_risk", "get_lien_history", "check_defaults"]
    )

    # Register subagents
    print("\n--- Registering subagents ---")
    coordinator.register_subagent(filing_agent)
    coordinator.register_subagent(entity_agent)
    coordinator.register_subagent(risk_agent)

    # --- Process a complex request ---
    print("\n--- Processing request ---")
    report = coordinator.process_request(
        "Research Greenfield Logistics LLC across all states. Find all filings, "
        "resolve related entities, and calculate aggregate risk exposure."
    )

    # --- Print the final report ---
    print(f"\n{'='*60}")
    print("Final Aggregated Report")
    print(f"{'='*60}")

    summary = report["summary"]
    findings = report["findings"]

    print(f"\n  Request type: {summary['request_type']}")
    print(f"  Subagents used: {', '.join(summary['subagents_used'])}")

    print(f"\n  Findings:")
    print(f"    Total filings found: {findings['total_filings']}")
    print(f"    States covered: {', '.join(findings['states_covered'])}")
    print(f"    Related entities: {findings['total_related_entities']}")
    print(f"    Entity resolution confidence: {findings['resolution_confidence']:.0%}")
    print(f"    Aggregate risk level: {findings['aggregate_risk_level']}")
    print(f"    Aggregate risk score: {findings['aggregate_risk_score']}")
    print(f"    Total lien exposure: ${findings['total_lien_exposure']:,}")

    print(f"\n  Provenance:")
    for source_name, source_data in report["provenance"].items():
        print(f"    {source_name}: from {source_data['source']}")

    # --- Execution log ---
    print(f"\n{'='*60}")
    print("Execution Log")
    print(f"{'='*60}")
    for entry in coordinator.execution_log:
        print(f"  [{entry['subagent']}] {entry['task']} ({entry['execution_time_ms']:.0f}ms)")

    # --- Context isolation verification ---
    print(f"\n{'='*60}")
    print("Context Isolation Verification")
    print(f"{'='*60}")
    print(f"  FilingSearchAgent messages: {len(filing_agent.messages)}")
    print(f"  EntityResolutionAgent messages: {len(entity_agent.messages)}")
    print(f"  RiskScoringAgent messages: {len(risk_agent.messages)}")
    print(f"  Each subagent saw ONLY its own task + coordinator-provided context.")
    print(f"  No subagent had access to other subagents' messages or results")
    print(f"  (unless explicitly passed by the coordinator).")

    print(f"\n{'='*60}")
    print("Key Takeaways")
    print(f"{'='*60}")
    print("""
    1. Decompose complex tasks into specialized subtasks
    2. Each subagent has isolated context (security + efficiency)
    3. Coordinator explicitly controls what context each subagent receives
    4. Results are aggregated with provenance tracking
    5. Downstream subtasks can receive enriched context from earlier results
    """)

    print("[OK] Lab Step 4 complete — Coordinator + subagent pattern\n")


if __name__ == "__main__":
    main()
