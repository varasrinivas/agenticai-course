# M03: Prompts — Programming in Natural Language — Lab

## What You'll Build

In this lab you will build a **multi-turn conversation manager** that uses system prompts, few-shot examples, and chain-of-thought prompting to interact with Claude effectively. By the end, you will understand how message roles, prompt structure, and conversation history shape the quality and consistency of LLM responses.

You will work through three exercises:

| Exercise | File | What You'll Learn |
|----------|------|-------------------|
| **Message Roles** | `message_roles.py` | How system, user, and assistant messages control Claude's behavior |
| **Few-Shot Prompting** | `few_shot.py` | How to classify UCC filing descriptions using example-based prompts |
| **Conversation Manager** | `conversation_manager.py` | How to manage multi-turn conversations with full history |

---

## Prerequisites

- **M01** (LLM Mental Model) and **M02** (API Basics) completed
- **Python 3.10+** or **Node.js 18+**
- An **Anthropic API key** (set as `ANTHROPIC_API_KEY` in a `.env` file or environment variable)
- Install dependencies:

```bash
# Python
pip install anthropic python-dotenv

# Node.js
npm install @anthropic-ai/sdk dotenv
```

---

## Lab Steps

### Step 1: Explore Message Roles

Message roles are the foundation of prompt engineering with Claude. Every API call uses three role types — `system`, `user`, and `assistant` — and each one changes how Claude interprets and responds to your input.

**Run the starter:**

```bash
cd starter
python message_roles.py
```

**Your task:** Open `starter/message_roles.py` and complete the three TODO sections:

1. **`basic_call(user_message)`** — Send a simple user message to Claude with no system prompt. This is the baseline — Claude uses its default personality and knowledge.

2. **`with_system_prompt(system, user_message)`** — Add a system prompt that makes Claude act as a UCC filing expert. Notice how the same user question produces a more focused, domain-specific answer.

3. **`with_prefill(system, user_message, assistant_prefill)`** — Use assistant prefill to guide the response format. By starting the assistant's reply with `"## Analysis\n"`, you force Claude to continue in that format (Markdown heading followed by structured content).

**Key insight:** The system prompt sets the stage, the user message asks the question, and the assistant prefill steers the format. Mastering all three gives you precise control over Claude's output.

**Check your work:** Compare your output against the solution in `solution/message_roles.py`. All three calls should return meaningful responses, with each successive call producing more focused and better-formatted output.

---

### Step 2: Implement Few-Shot Prompting

Few-shot prompting teaches Claude a classification task by providing labeled examples directly in the prompt. This is one of the most powerful prompt engineering techniques — it lets you define new categories without fine-tuning.

**Run the starter:**

```bash
cd starter
python few_shot.py
```

**Your task:** Open `starter/few_shot.py` and complete the `classify_collateral` function:

1. Build a prompt that includes the three provided examples (collateral description to category mapping)
2. Add the new description to classify
3. Call Claude and extract just the category label from the response

The starter includes three few-shot examples:
- "All accounts receivable and inventory" → **Blanket Lien**
- "Specific equipment: (2) Caterpillar 320 excavators" → **Equipment**
- "All crops, livestock, and farm products" → **Agricultural**

You will classify three new descriptions that Claude has never seen in the examples:
- "All intellectual property, patents, and trademarks"
- "2021 Peterbilt 579 truck, VIN 1XPBD49X1MD123456"
- "All assets of the Debtor, whether now owned or hereafter acquired"

**Key insight:** Few-shot examples act as implicit instructions. Claude infers the pattern (input format, output format, classification logic) from the examples alone. The more consistent your examples, the more consistent the output.

---

### Step 3: Build a Conversation Manager

Multi-turn conversations require managing the full message history. Claude has no built-in memory — every API call is stateless. Your code must store the conversation and replay it on each turn.

**Run the starter:**

```bash
cd starter
python conversation_manager.py
```

**Your task:** Open `starter/conversation_manager.py` and implement the `ConversationManager` class:

1. **`send(user_message)`** — Append the user message to history, call the API with the full message list, append the assistant response, and return the text.
2. The class already has `__init__`, `get_history`, and `reset` — focus on the `send` method.

The main block runs a 3-turn conversation:
1. "What is a UCC-1 filing?"
2. "How long do they last?"
3. "What happens when one expires?"

Notice how turn 2 ("How long do they last?") only makes sense because Claude can see turn 1 in the history. Without history, Claude would not know what "they" refers to. This is the core challenge of multi-turn agents.

**Check your work:** Compare your output against `expected_output/multi_turn_output.txt`. The exact wording will differ (LLM outputs are non-deterministic), but the structure and context-awareness should match.

---

## Final Verification

You have completed the lab when:

- [ ] `message_roles.py` runs three calls and shows how system prompts and prefill change the response
- [ ] `few_shot.py` correctly classifies all three new collateral descriptions
- [ ] `conversation_manager.py` maintains context across three turns (turn 2 references turn 1)
- [ ] You can explain the difference between system, user, and assistant roles
- [ ] You understand why conversation history must be sent on every API call

---

## What You Built

You built three prompt engineering tools that form the foundation of every agent in this course:

- **Message roles** — the three levers (system, user, assistant) that control Claude's behavior
- **Few-shot prompting** — teaching Claude new tasks through examples, not instructions
- **Conversation manager** — stateful multi-turn dialogue with full history replay

These patterns appear in every module from here forward. The system prompt becomes the agent's plan (M05). Few-shot examples become tool selection guidance (M07). The conversation manager becomes agent memory (M10).

---

## Next

Continue to **[M04: Structured Output](../../output/M04-structured-output.html)** to learn how to get Claude to return JSON, XML, and other machine-readable formats reliably.
