# M01: The LLM Mental Model

**Track**: 1 — Foundations | **Position**: 1 of 30 | **Level**: Beginner
**Prerequisites**: None (this is the first module)
**Estimated Time**: 45-60 minutes
**Track Color**: var(--track-foundations) / #6366F1

## Concepts to Cover

### 1. What is a Large Language Model?
- Analogy: "The world's most well-read autocomplete" — it's read billions of documents and predicts what comes next
- Technical: Neural network trained on text data to predict the next token in a sequence
- Animation: `TOKEN_FLOW` — Show a sentence being generated token by token, with probability bars for each predicted token
- NOT to teach: Don't go deep into transformer architecture, attention mechanisms, or training. Save that for supplementary material.

### 2. How Claude Processes Text
- Analogy: "Claude reads your entire message at once (not word by word like a human), then writes its response one piece at a time"
- Technical: Input processing (tokenization → embedding → attention) vs. output generation (autoregressive, one token at a time)
- Animation: Input text flows in as a batch → processing "cloud" → output tokens emerge one at a time
- Key insight: Claude doesn't "understand" — it predicts. But the predictions are so good that the distinction becomes philosophical.

### 3. Temperature, Top-p, Top-k
- Analogy: "Temperature is the creativity dial. Low = playing it safe, high = taking risks"
- Technical: Temperature scales logits before softmax. Top-p (nucleus sampling) truncates the probability distribution. Top-k limits to K most likely tokens.
- Animation: Interactive sliders — learner adjusts temperature/top-p/top-k and sees how the probability distribution changes. Show the same prompt generating different outputs at different settings.
- This is the module's centerpiece interactive element.

### 4. The "Calculator vs. Thinker" Mental Model
- Key framing for the entire course: LLMs are not calculators (deterministic input→output). They're more like very well-read thinkers who can surprise you, make mistakes, and need guardrails.
- This mental model will be referenced throughout the course.

## Code Walkthrough
- First Claude API call in three formats:
  1. `curl` command (for understanding the raw HTTP)
  2. Python SDK (`anthropic` package)
  3. Node.js SDK (`@anthropic-ai/sdk` package)
- Show: sending a message, receiving a response, printing it
- Include: API key setup via environment variable

## Hands-On Exercise
- "Hello Claude" — Make your first API call
- Modify the system prompt and observe how behavior changes
- Experiment with temperature settings on the same prompt (generate 5 responses at temp 0.0 vs 1.0)
- Stretch: Build a simple CLI that takes user input and sends to Claude

## Quiz Focus
- What is a token? (preview for M02, basic understanding)
- What does temperature control?
- Why is an LLM not a calculator?
- What's the difference between system and user messages?
- Code completion: Fill in the missing line to make a basic API call
