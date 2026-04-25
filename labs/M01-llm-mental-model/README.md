# M01: The LLM Mental Model -- Lab

## What You'll Build

Make your first Claude API call and experiment with temperature, model selection, and system prompts. By the end of this lab you will understand how small parameter changes produce dramatically different outputs.

---

## Prerequisites

- Python 3.10+
- An Anthropic API key (get one at https://console.anthropic.com/)
- Node.js 18+ (optional, for JavaScript solutions)

## Setup

```bash
cd labs/M01-llm-mental-model
pip install anthropic python-dotenv
```

Set your API key as an environment variable:

```bash
# Linux / macOS
export ANTHROPIC_API_KEY=your-key-here

# Windows PowerShell
$env:ANTHROPIC_API_KEY = "your-key-here"
```

Alternatively, create a `.env` file in this directory:

```
ANTHROPIC_API_KEY=your-key-here
```

> **Security reminder:** Never commit your `.env` file or API key to version control.

---

## Step 1: Make Your First API Call

**Goal:** Send a single message to Claude and print the response.

| | |
|---|---|
| **Starter code** | `starter/first_call.py` |
| **Solution** | `solution/first_call.py` (Python) / `solution/first_call.js` (Node.js) |

### Instructions

1. Open `starter/first_call.py`.
2. Find the `TODO` comment and complete the code:
   - Call `client.messages.create()` with model `claude-sonnet-4-20250514`.
   - Set `max_tokens` to `1024`.
   - Send a single user message: *"What is an AI agent? Explain in 2-3 sentences."*
   - Print the response text.
3. Run the file:

```bash
python starter/first_call.py
```

### Expected Output

```
--- First Claude API Call ---
Response from Claude:
An AI agent is a software system that uses a large language model to
autonomously reason about tasks, make decisions, and take actions ...
```

(Your exact wording will vary -- the key is that you receive a coherent multi-sentence answer.)

### Checkpoint

- [ ] The script runs without errors.
- [ ] You see a 2-3 sentence answer printed in your terminal.
- [ ] You understand the four required parameters: `model`, `max_tokens`, `messages`, and role/content structure.

### Troubleshooting

| Problem | Fix |
|---|---|
| `anthropic.AuthenticationError` | Check that `ANTHROPIC_API_KEY` is set and valid. |
| `ModuleNotFoundError: No module named 'anthropic'` | Run `pip install anthropic python-dotenv`. |
| Empty or `None` response | Make sure you are reading `response.content[0].text`. |

---

## Step 2: Experiment with Temperature

**Goal:** See how temperature controls randomness by sending the *same* prompt three times at different temperature values.

| | |
|---|---|
| **Starter code** | `starter/temperature_lab.py` |
| **Solution** | `solution/temperature_lab.py` (Python) / `solution/temperature_lab.js` (Node.js) |

### Instructions

1. Open `starter/temperature_lab.py`.
2. Complete the `call_with_temperature(prompt, temp)` function:
   - Call `client.messages.create()` with the given `temp` as the `temperature` parameter.
   - Return the response text.
3. Run the file:

```bash
python starter/temperature_lab.py
```

### Expected Output

```
--- Temperature Experiment ---

Temperature 0.0:
"Your AI pair programmer that never sleeps."

Temperature 0.5:
"Code smarter, ship faster -- your AI co-pilot awaits."

Temperature 1.0:
"Unleash brilliance in every bracket -- where silicon intuition meets human ambition."
```

(Exact text will differ. Notice that temp 0.0 outputs are more predictable and conservative, while temp 1.0 outputs are more creative and varied.)

### Checkpoint

- [ ] You get three different responses printed with clear temperature labels.
- [ ] You can explain in your own words: *lower temperature = more deterministic, higher = more creative*.

### Troubleshooting

| Problem | Fix |
|---|---|
| All three responses are identical | Make sure you are passing `temperature=temp` to `messages.create()`. |
| `ValidationError` on temperature | Temperature must be a float between 0.0 and 1.0. |

---

## Step 3: Compare Models

**Goal:** Send the same prompt to two different Claude models and compare speed, cost, and quality.

| | |
|---|---|
| **Starter code** | `starter/model_comparison.py` |
| **Solution** | `solution/model_comparison.py` (Python) / `solution/model_comparison.js` (Node.js) |

### Instructions

1. Open `starter/model_comparison.py`.
2. Complete the `call_model(model_name, prompt)` function:
   - Call `client.messages.create()` with the given `model_name`.
   - Time the call and return both the response text and elapsed time.
3. Run the file:

```bash
python starter/model_comparison.py
```

### Expected Output

```
--- Model Comparison ---

Model: claude-haiku-4-5-20251001
Time: 1.23s
Response:
A UCC filing is a legal document ...

Model: claude-sonnet-4-20250514
Time: 2.87s
Response:
A Uniform Commercial Code (UCC) filing is a public notice ...
```

### Checkpoint

- [ ] Both models return valid responses.
- [ ] You can see a measurable difference in response time.
- [ ] You understand the trade-off: Haiku is faster and cheaper; Sonnet is more thorough.

### Troubleshooting

| Problem | Fix |
|---|---|
| `NotFoundError` on model name | Double-check the model string -- use the exact IDs shown above. |
| One model is much slower | This is expected. Larger models take longer to respond. |

---

## Final Verification

Run all three exercises and confirm:

```bash
python starter/first_call.py
python starter/temperature_lab.py
python starter/model_comparison.py
```

All three scripts should execute without errors and produce labeled output.

## What You Built

1. **First API call** -- You connected to the Anthropic Messages API and received a structured response.
2. **Temperature exploration** -- You proved that temperature controls output randomness.
3. **Model comparison** -- You benchmarked two Claude models on the same prompt and observed quality/speed trade-offs.

These three skills -- calling the API, tuning generation parameters, and choosing the right model -- are the foundation for everything you will build in this course.

---

**Next:** [M02 -- Tokens, Context Windows, and Billing](../M02-tokens/README.md)
