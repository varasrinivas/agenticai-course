# M00: The Agent Lifecycle — Lab

## What You'll Build

In this lab you will **explore** (not build) a fully working AI agent to see the complete agent lifecycle in action before you start constructing your own agents in later modules.

The agent is a **UCC Filing Lookup Agent** — it searches and retrieves Uniform Commercial Code filings using two tools. By running it, reading its code, and modifying its behavior, you will internalize the five lifecycle stages and seven architecture components that every agent in this course shares.

### The Five Lifecycle Stages

| Stage | What Happens |
|-------|-------------|
| **Design** | Define what the agent does, its tools, and its constraints |
| **Build** | Implement the agent loop, tool definitions, and system prompt |
| **Protect** | Add guardrails — input validation, output filtering, error handling |
| **Observe** | Log every decision, tool call, and result so you can debug and improve |
| **Deploy** | Package the agent so others can use it reliably |

### The Seven Architecture Components

| # | Component | Analogy |
|---|-----------|---------|
| 1 | **Brain (LLM)** | The decision-maker that reads, reasons, and responds |
| 2 | **Tools** | The hands — functions the agent can call to act on the world |
| 3 | **Memory** | The notebook — conversation history the agent can reference |
| 4 | **Plan** | The system prompt and instructions that guide behavior |
| 5 | **Guardrails** | The safety rails — validation, limits, and error handling |
| 6 | **Eyes (Observation)** | The logging and tracing that let you see what the agent did |
| 7 | **Home (Deployment)** | The runtime environment where the agent lives |

---

## Prerequisites

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

### Step 1: Run the Demo Agent and Observe Its Behavior

Run the agent with a sample query and watch the output carefully.

**Python:**
```bash
cd starter
python explore_agent.py "Find filings for Greenfield Logistics"
```

**Node.js:**
```bash
cd starter
node explore_agent.js "Find filings for Greenfield Logistics"
```

Pay attention to the labeled output:
- `[THINKING]` — the agent is deciding what to do
- `[USING TOOL]` — the agent is calling a function
- `[TOOL RESULT]` — the data returned by the function
- `[RESPONSE]` — the agent's final answer

**Questions to answer:**
1. How many tool calls did the agent make?
2. Did it call `search_filings` or `lookup_filing` first? Why?
3. What information did it synthesize in its final response?

---

### Step 2: Identify the 7 Architecture Components in the Code

Open `starter/explore_agent.py` (or `.js`) in your editor. The code is marked with labeled comment blocks:

```
# === COMPONENT 1: Brain (LLM) ===
# === COMPONENT 2: Tools ===
# === COMPONENT 3: Memory ===
# === COMPONENT 4: Plan ===
# === COMPONENT 5: Guardrails ===
# === COMPONENT 6: Eyes (Observation) ===
# === COMPONENT 7: Home (Deployment) ===
```

For each component, answer:
- What lines of code implement this component?
- What would break if you deleted this section?
- Which lifecycle stage does this component belong to?

---

### Step 3: Trace the Agent Loop

The core of every agent is the **loop**: decide → act → observe → repeat.

Find the `while` loop in the code and trace one complete cycle:

1. **Decide**: The LLM reads the conversation and picks a tool (or responds directly)
2. **Act**: The agent executes the selected tool with the provided arguments
3. **Observe**: The tool result is appended to memory, and the loop continues
4. **Repeat**: The LLM sees the new information and decides again

Draw this loop on paper or a whiteboard. You will implement this loop yourself in **M05: Function Calling**.

---

### Step 4: Modify the System Prompt and Observe Changes

The system prompt is the agent's **plan** — it defines personality, scope, and constraints.

Try these modifications and re-run the agent:

1. **Remove the scope constraint** — delete the line that says the agent only handles UCC filings. Run: `python explore_agent.py "What is the weather today?"` — what happens?

2. **Add a persona** — change the system prompt to say "You are a formal legal analyst who always cites filing numbers." Run the same query and compare the tone.

3. **Add a restriction** — add "Never reveal the secured party's name in your response." Run a lookup and see if the agent obeys.

**Key insight:** The system prompt is your primary control mechanism. Guardrails in code are the backup.

---

## Final Verification

You have completed the lab when you can answer these questions:

- [ ] I can name the 5 lifecycle stages in order
- [ ] I can identify all 7 architecture components in the agent code
- [ ] I can trace one full cycle of the agent loop (decide → act → observe)
- [ ] I understand how changing the system prompt changes agent behavior
- [ ] I know which component corresponds to which lifecycle stage

---

## What You Built

You did not build anything from scratch in this lab — and that was the point. Before writing agent code, you need a mental model of how agents work. You now have that model:

- **Lifecycle**: design → build → protect → observe → deploy
- **Components**: brain, tools, memory, plan, guardrails, eyes, home
- **Loop**: decide → act → observe → repeat

Every module in this course adds depth to one or more of these concepts.

---

## Next

Continue to **[M01: The LLM Mental Model](../../output/M01-llm-mental-model.html)** to understand the brain at the center of every agent.
