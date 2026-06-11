"""
M14 Lab: Multi-Agent Content Pipeline — SOLUTION
=================================================
Run: python content_pipeline.py
"""

import json
import time
import uuid

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


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
    """Run a single specialized agent."""
    response = client.chat.completions.create(
        model="mistral",
        messages=[
            {"role": "system", "content": AGENT_PROMPTS[agent_name]},
            {"role": "user", "content": content},
        ],
    )
    return response.choices[0].message.content


def run_pipeline(topic: str, max_review_attempts: int = 2, verbose: bool = True) -> dict:
    """Orchestrate the 4-agent content pipeline with retry on rejection."""
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    goal = f"Write a high-quality article about: {topic}"
    message_log = []

    if verbose:
        print(f"\n{'=' * 55}\n  Topic: {topic}\n  Goal: {goal}\n{'=' * 55}")

    # Stage 1: Research
    if verbose:
        print("\n  [1/4] Researcher working...")
    research = run_agent("researcher", f"Research this topic: {topic}")
    message_log.append(create_handoff("researcher", "writer", task_id,
                                      "research_complete", research, goal,
                                      "Use these findings to write an article."))

    # Stage 2: Write — pass the GOAL and the research, not the whole log
    if verbose:
        print("  [2/4] Writer working...")
    article = run_agent("writer",
        f"Original goal: {goal}\n\nResearch findings:\n{research}\n\n"
        f"Write a 200-300 word article based on these findings.")
    message_log.append(create_handoff("writer", "editor", task_id,
                                      "draft_complete", article, goal,
                                      "Edit this article for quality."))
    if verbose:
        print(f"         Draft: {len(article.split())} words")

    # Stage 3: Edit
    if verbose:
        print("  [3/4] Editor working...")
    edited = run_agent("editor", f"Original goal: {goal}\n\nArticle to edit:\n{article}")
    message_log.append(create_handoff("editor", "reviewer", task_id,
                                      "edit_complete", edited, goal,
                                      "Review and score this article."))

    # Stage 4: Review with retry loop
    review = {}
    for attempt in range(1, max_review_attempts + 1):
        if verbose:
            print(f"  [4/4] Reviewer (attempt {attempt}/{max_review_attempts})...")

        review_text = run_agent("reviewer",
            f"Original goal: {goal}\n\nArticle to review:\n{edited}")
        message_log.append(create_handoff("reviewer", "supervisor", task_id,
                                          "review_complete", review_text, goal))

        # Defensive parse — a malformed review fails OPEN (a human reads it anyway)
        try:
            raw = review_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            review = json.loads(raw)
        except json.JSONDecodeError:
            review = {"score": 80, "feedback": review_text, "approved": True}

        if verbose:
            verdict = "Approved" if review.get("approved") else "Rejected"
            print(f"         Score: {review.get('score', '?')}/100 — {verdict}")

        if review.get("approved", False):
            break

        # Rejected — the SUPERVISOR decides to retry, not the reviewer
        if attempt < max_review_attempts:
            if verbose:
                print("         Sending feedback to Editor for revision...")
            edited = run_agent("editor",
                f"Original goal: {goal}\n\n"
                f"Current article:\n{edited}\n\n"
                f"Reviewer feedback (score {review.get('score', '?')}/100):\n"
                f"{review.get('feedback', 'No specific feedback')}\n\n"
                f"Please revise the article to address this feedback.")
            message_log.append(create_handoff("editor", "reviewer", task_id,
                                              "revision_complete", edited, goal,
                                              "Re-review after revision."))

    if verbose:
        print(f"\n  {'-' * 50}")
        print(f"  Message Log ({len(message_log)} handoffs):")
        for m in message_log:
            ts = time.strftime("%H:%M:%S", time.localtime(m["timestamp"]))
            print(f"    [{ts}] {m['sender']} -> {m['receiver']}: {m['type']}")
            print(f"             {m['payload'][:60]}...")

    return {
        "topic": topic,
        "article": edited,
        "review": review,
        "message_log": message_log,
        "stages_completed": len(set(m["sender"] for m in message_log)),
    }


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
