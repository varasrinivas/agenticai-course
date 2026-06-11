"""
M14 Lab: Multi-Agent Content Pipeline
======================================
Researcher → Writer → Editor → Reviewer, orchestrated by a supervisor.
Run: python content_pipeline.py
"""

import json
import time
import uuid

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


# ── Handoff Message Structure (COMPLETE) ─────────────────────
def create_handoff(sender: str, receiver: str, task_id: str,
                   msg_type: str, payload: str, goal: str,
                   instructions: str = "") -> dict:
    """Structured envelope — note original_goal travels with EVERY message."""
    return {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "sender": sender,
        "receiver": receiver,
        "task_id": task_id,
        "type": msg_type,
        "payload": payload,
        "original_goal": goal,
        "instructions": instructions,
        "timestamp": time.time(),
    }


# ── Specialized Agents (COMPLETE) ────────────────────────────
# Same model, four different system prompts — specialization is prompt-deep.
AGENT_PROMPTS = {
    "researcher": (
        "You are a research specialist. Given a topic, produce a concise "
        "research brief with 3-5 key findings, each with a source reference. "
        "Focus on facts and data points. Output structured markdown."
    ),
    "writer": (
        "You are a professional writer. Given research findings, write a "
        "well-structured article of 200-300 words. Use clear language, "
        "include an introduction and conclusion. Incorporate the research "
        "findings naturally with citations."
    ),
    "editor": (
        "You are an experienced editor. Review the article for clarity, "
        "grammar, flow, and factual consistency. Make direct edits (don't "
        "just suggest changes). Return the improved article."
    ),
    "reviewer": (
        "You are a quality reviewer. Score the article 0-100 on:\n"
        "- Accuracy (0-25): Are facts correct and well-sourced?\n"
        "- Clarity (0-25): Is the writing clear and well-organized?\n"
        "- Completeness (0-25): Does it cover the topic adequately?\n"
        "- Engagement (0-25): Is it interesting to read?\n\n"
        'Respond with JSON: {"score": N, "feedback": "...", "approved": true/false}\n'
        "Approve only if total score >= 75."
    ),
}


def run_agent(agent_name: str, content: str) -> str:
    """(COMPLETE) Run a single specialized agent."""
    response = client.chat.completions.create(
        model="mistral",
        messages=[
            {"role": "system", "content": AGENT_PROMPTS[agent_name]},
            {"role": "user", "content": content},
        ],
    )
    return response.choices[0].message.content


# ── Supervisor (YOUR JOB) ────────────────────────────────────
def run_pipeline(topic: str, max_review_attempts: int = 2, verbose: bool = True) -> dict:
    """Orchestrate the 4-agent content pipeline with retry on rejection.

    TODO:
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    goal = f"Write a high-quality article about: {topic}"
    message_log = []

    Stage 1 — RESEARCH:
      research = run_agent("researcher", f"Research this topic: {topic}")
      message_log.append(create_handoff("researcher", "writer", task_id,
          "research_complete", research, goal, "Use these findings to write an article."))

    Stage 2 — WRITE (pass the GOAL and the research, not the whole log):
      article = run_agent("writer", f"Original goal: {goal}\\n\\nResearch findings:\\n"
          f"{research}\\n\\nWrite a 200-300 word article based on these findings.")
      log a writer→editor handoff

    Stage 3 — EDIT:
      edited = run_agent("editor", f"Original goal: {goal}\\n\\nArticle to edit:\\n{article}")
      log an editor→reviewer handoff

    Stage 4 — REVIEW with retry loop, for attempt in 1..max_review_attempts:
      review_text = run_agent("reviewer", f"Original goal: {goal}\\n\\n"
                              f"Article to review:\\n{edited}")
      log a reviewer→supervisor handoff
      Parse review_text DEFENSIVELY (strip ``` fences before json.loads):
        on failure: review = {"score": 80, "feedback": review_text, "approved": True}
        ← a malformed review fails OPEN here; a human reads the article anyway
      If review.get("approved"): break
      If rejected and attempts remain: edited = run_agent("editor",
          goal + current article + reviewer feedback + "revise to address this")
        and log the revision handoff

    If verbose: print each stage as you go, then the message-log timeline:
      [HH:MM:SS] sender -> receiver: type / payload[:60]

    Return {"topic": topic, "article": edited, "review": review,
            "message_log": message_log,
            "stages_completed": len(set(m["sender"] for m in message_log))}
    """
    pass  # Remove this line when you add your code


# ── Tests (COMPLETE) ─────────────────────────────────────────
if __name__ == "__main__":
    print("\n> TEST 1: Full content pipeline (4-6 model calls, be patient on CPU)")
    result = run_pipeline("The benefits of walking 30 minutes daily")
    print(f"\n  Final article ({len(result['article'].split())} words):")
    print(f"  {result['article'][:200]}...")
    print(f"  Review score: {result['review'].get('score', '?')}/100")
    print(f"  Total handoffs: {len(result['message_log'])}")

    print(f"\n{'=' * 55}")
    print("> TEST 2: Individual agent test (Researcher only)")
    research = run_agent("researcher", "Research: impact of AI on healthcare")
    print(f"  Research output: {research[:200]}...")
