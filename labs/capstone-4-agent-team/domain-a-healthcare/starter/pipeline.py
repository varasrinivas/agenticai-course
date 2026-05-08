"""pipeline.py — Multi-Agent Pre-Auth Pipeline Orchestrator (Capstone 4-A)

Runs 4 agents in sequence with circuit breaker and HITL.

  Agent 1 (Intake)        -> validates request + member + provider
  Agent 2 (Clinical)      -> evaluates each policy criterion
  Agent 3 (Decision)      -> LLM-driven routing (approve/HITL/deny)
  Agent 4 (Communication) -> drafts letter + HIPAA guardrail + sends

YOUR JOB: complete the TODOs, in order.

Usage (after completion):
  export ANTHROPIC_API_KEY=your-key-here
  python pipeline.py        # interactive: type 'demo'
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# ── Pipeline State ────────────────────────────────────────────────
@dataclass
class PipelineState:
    request_id: str
    stage: str = "intake"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    raw_request: dict = field(default_factory=dict)
    intake_output: Optional[dict] = None
    criteria_output: Optional[dict] = None
    decision_output: Optional[dict] = None
    communication_output: Optional[dict] = None
    circuit_breaker: dict = field(default_factory=lambda: {
        "consecutive_failures": 0, "threshold": 3, "status": "healthy"
    })


# ── Circuit Breaker ───────────────────────────────────────────────
def check_circuit_breaker(state: PipelineState) -> bool:
    """Return True iff state.circuit_breaker['status'] == 'tripped'."""
    # TODO: implement (one-liner).
    raise NotImplementedError("Complete check_circuit_breaker")


def record_failure(state: PipelineState) -> None:
    """Increment consecutive_failures; trip if >= threshold."""
    # TODO: implement. Print '[CIRCUIT BREAKER] TRIPPED ...' on trip.
    raise NotImplementedError("Complete record_failure")


def record_success(state: PipelineState) -> None:
    """Reset consecutive_failures to 0."""
    # TODO: implement (one-liner).
    raise NotImplementedError("Complete record_success")


# ── Agent Runner ──────────────────────────────────────────────────
def run_agent(name: str, system_prompt: str, tools: list,
              tool_handlers: dict, user_message: str,
              state: PipelineState) -> dict:
    """Run one Claude-driven agent loop with the given tools.

    All four pipeline agents use this. The structure:
      1. Bail early if the circuit breaker is tripped.
      2. history = [user_message]
      3. while True:
         resp = client.messages.create(model, system, tools, history)
         if resp.stop_reason == 'tool_use':
             - append assistant content to history
             - for each tool_use block in resp.content:
                 result = tool_handlers[block.name](block.input)
                 build a tool_result block with tool_use_id
             - append a {role: 'user', content: results} message
             - continue
         else (text response):
             - join text blocks
             - record_success(state)
             - return {'text': ..., 'raw_content': resp.content}
      4. except Exception:
         - record_failure(state)
         - return {'error': str(e)}
    """
    if check_circuit_breaker(state):
        return {"error": "CIRCUIT_BREAKER_TRIPPED",
                "message": "Pipeline halted."}

    print(f"\n[{name}] Starting...")
    history = [{"role": "user", "content": user_message}]

    # TODO: implement the tool-use loop described above.
    raise NotImplementedError("Complete run_agent")


# ── HITL Review (offline human step, OUTSIDE run_agent) ───────────
def human_review(state: PipelineState) -> dict:
    """Print case details, prompt reviewer, return their decision."""
    # TODO: implement using `input(...)` with EOFError fallback.
    # See solution/pipeline.py if stuck.
    raise NotImplementedError("Complete human_review")


# ── Pipeline Orchestrator ─────────────────────────────────────────
def run_pipeline(raw_request: dict) -> PipelineState:
    """Execute the full 4-agent pipeline.

    BUILD ORDER (from solution/pipeline.py):
      1. Build PipelineState from raw_request.
      2. Agent 1 (Intake): wire intake_tools + intake_handlers,
         call run_agent, populate state.intake_output.
      3. Agent 2 (Clinical): wire clinical_tools + clinical_handlers,
         call run_agent, then directly evaluate each policy criterion
         against the clinical notes to populate
         state.criteria_output.
      4. Agent 3 (Decision): wire decision_tools (just
         compute_decision_confidence) + a scratchpad-based handler.
         The system prompt instructs the LLM to compute confidence
         and reply with a JSON object. Parse the reply, fall back
         to the scratchpad. If human_review_required, run the
         offline human_review() and override the determination.
      5. Finalize the determination via finalize_determination.
      6. Agent 4 (Communication): wire comm_tools (draft / hipaa /
         send) + scratchpad handlers. After run_agent returns,
         re-check the HIPAA guardrail in the orchestrator (belt and
         suspenders). If not compliant, set state.stage = 'error'
         and record the issues.
      7. send_notification, populate state.communication_output,
         set state.stage = 'complete'.
    """
    # TODO: implement step by step. The solution is ~250 lines.
    raise NotImplementedError("Complete run_pipeline")


def main() -> None:
    print("=" * 60)
    print("  Pre-Auth Processing Pipeline — Capstone 4-A")
    print("  Type 'demo' for sample request, or 'quit' to exit.")
    print("=" * 60)

    sample = {
        "request_id": "AR-2024-09821",
        "member_id": "MBR-555-1234",
        "provider_npi": "1234567890",
        "procedure_code": "27447",
        "diagnosis_codes": ["M17.11"],
        "clinical_notes": (
            "Severe right knee osteoarthritis (M17.11). "
            "KL Grade IV on weight-bearing films. "
            "8 months physical therapy (PT). Failed conservative "
            "NSAIDs, 2 corticosteroid injections. "
            "WOMAC score 68. BMI 31."),
    }

    while True:
        try:
            cmd = input("\nCommand: ").strip()
        except EOFError:
            break
        if cmd.lower() in ("quit", "exit", "q"):
            break
        if cmd.lower() == "demo":
            state = run_pipeline(sample)
            print(f"\nFinal state:\n"
                  f"{json.dumps(asdict(state), indent=2, default=str)}")


if __name__ == "__main__":
    main()
