# M05 Lab: Function Calling Fundamentals

> **The Hero Module** -- this is where Claude goes from chatbot to agent.
> Claude ASKS to run tools, YOUR CODE executes them.

## Prerequisites

- Python 3.10+ or Node.js 18+
- Anthropic API key in `.env` file (`ANTHROPIC_API_KEY=sk-ant-...`)
- Install dependencies:
  ```bash
  # Python
  pip install anthropic python-dotenv

  # Node.js
  npm install @anthropic-ai/sdk dotenv
  ```

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `single_tool.py` / `single_tool.js` | Single tool call (get_weather) | Tool definitions, `stop_reason == "tool_use"`, tool_result message |
| 2 | `multi_tool.py` / `multi_tool.js` | Multi-tool agent loop (get_weather + calculate + get_time) | The agent while-loop, processing multiple tool_use blocks |
| 3 | `error_handling.py` / `error_handling.js` | Robust error-handling agent | API errors, unknown tools, tool execution failures, max turns |

## Step 1: Define Tools and Make a Single Tool Call

**File:** `starter/single_tool.py` (or `.js`)

You will:
1. Use the pre-defined `get_weather` tool and its JSON Schema definition
2. Implement `run_single_tool()` to make ONE API call with tools
3. Check if `stop_reason` is `"tool_use"`
4. Extract the tool_use block, execute `get_weather`, send the result back
5. Return Claude's final text response

**Test queries:**
- `"What's the weather in Tokyo?"` -- should return weather data
- `"What's the weather in Atlantis?"` -- should return an error gracefully

**Run it:**
```bash
python starter/single_tool.py
# or
node starter/single_tool.js
```

## Step 2: Multi-Tool Agent with a Loop

**File:** `starter/multi_tool.py` (or `.js`)

You will:
1. Use 3 pre-defined tools: `get_weather`, `calculate`, `get_time`
2. Implement the **agent loop** -- a `while` loop that keeps running until Claude says `"end_turn"`
3. Handle multiple tool_use blocks in a single response
4. Collect ALL tool results and send them back together

**Test queries:**
- `"What's the weather in Paris?"` -- single tool
- `"What is 15% of 340?"` -- single tool (calculate)
- `"What's the weather in Tokyo and what time is it there?"` -- multi-tool in one turn
- `"Hello, how are you?"` -- no tool needed

**Run it:**
```bash
python starter/multi_tool.py
# or
node starter/multi_tool.js
```

## Step 3: Error Handling and Edge Cases

**File:** `starter/error_handling.py` (or `.js`)

You will:
1. Add `try/except` around the API call (handle `anthropic.APIError`)
2. Validate tool names before dispatching
3. Add `try/except` around tool execution
4. Return error info as `tool_result` so Claude can recover and explain
5. Handle the max-turns timeout gracefully

**Test queries:**
- `"What's the weather in Atlantis?"` -- unknown city, tool returns error, Claude explains
- `"Calculate 1/0"` -- division by zero, tool error, Claude explains
- `"What's the weather in Tokyo and calculate 25 * 4?"` -- multi-tool with mixed results

**Run it:**
```bash
python starter/error_handling.py
# or
node starter/error_handling.js
```

## Verification

After completing all three steps, run the solutions to see expected behavior:

```bash
# Python
python solution/single_tool.py
python solution/multi_tool.py
python solution/error_handling.py

# Node.js
node solution/single_tool.js
node solution/multi_tool.js
node solution/error_handling.js
```

Compare your output against `expected_output/sample_output.txt`.

## What You Built

By completing this lab, you have implemented:

1. **Tool definitions** with JSON Schema -- the contract between Claude and your code
2. **Single tool call** -- the basic request/response pattern for tool use
3. **The agent loop** -- the CORE PATTERN of every AI agent: decide -> act -> observe -> repeat
4. **Multi-tool handling** -- processing multiple tool calls in a single response
5. **Error recovery** -- making agents resilient to API failures, bad inputs, and tool crashes

This is the foundation for everything that follows in the course.

## Next

- **M06**: Structured Output and Parsing
- **M07**: Multi-Turn Conversation Management
