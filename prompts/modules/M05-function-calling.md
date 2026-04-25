# M05: Function Calling Fundamentals

**Track**: 2 — Tool Use | **Position**: 5 of 30 | **Level**: Beginner → Intermediate
**Prerequisites**: M01-M04
**Estimated Time**: 60-75 minutes
**Track Color**: var(--track-tooluse) / #8B5CF6

## Why This Is a Hero Module
This is the first module where Claude goes from "chatbot" to "agent." The learner will see Claude DO things for the first time — not just generate text. This is the pivotal moment in the course.

## Concepts to Cover

### 1. What Is Tool Use / Function Calling?
- Analogy: "Imagine you have a super-smart assistant who can write beautifully but can't see the clock. You give them a tool: 'ask_time()'. Now when someone asks 'What time is it?', instead of guessing, the assistant says 'Let me check' and uses the tool. That's function calling."
- Technical: The Messages API `tools` parameter. Tool definitions = JSON Schema descriptions that tell Claude what tools are available and what inputs they expect. Claude doesn't execute the tool — it returns a `tool_use` content block saying which tool to call and with what arguments. YOUR CODE executes the tool and sends back the result.
- Animation: `TOOL_LOOP` — Step-by-step:
  1. User sends message
  2. Claude receives message + tool definitions
  3. Claude decides to use a tool → returns `tool_use` block
  4. YOUR CODE catches the `tool_use`, runs the function, gets result
  5. You send `tool_result` back to Claude
  6. Claude incorporates the result into its final response
  - Each step highlights in sequence. Pause between steps. Show the actual JSON at each stage.
- KEY INSIGHT: Claude doesn't run tools. Claude ASKS to run tools. You execute them. This is critical for security and control.

### 2. Defining Tools
- Tool definition structure: name, description, input_schema (JSON Schema)
- Why descriptions matter enormously (Claude picks tools based on descriptions)
- JSON Schema basics: types, required fields, descriptions, enums
- Common mistake: Poor tool descriptions = Claude picks the wrong tool
- Show 3-4 example tool definitions ranging from simple to complex

### 3. The Tool Use Loop in Code
- Full implementation: send message → check for tool_use → execute tool → send tool_result → get final response
- The while loop pattern (agent may want to call multiple tools)
- Stop reasons: `end_turn` vs `tool_use`
- Error handling: What if the tool raises an exception? (Return error as tool_result, let Claude adapt)

### 4. Error Handling & Edge Cases
- Tool timeout: Set time limits, return timeout message
- Tool failure: Return error description, not stack traces
- Invalid arguments: Validate before executing
- Claude calling a non-existent tool (rare but possible)
- ⚠️ Security: NEVER let Claude construct arbitrary code/commands to execute. Tools are YOUR pre-defined functions.

## Code Walkthrough
- Build a calculator agent (add, subtract, multiply, divide)
- Show the complete request/response JSON at each step
- Add a weather lookup tool (mock API)
- Show Claude choosing between calculator and weather based on the question

## Hands-On Exercise
- Build a multi-tool agent with:
  1. `get_weather(city)` — returns mock weather data
  2. `calculate(expression)` — evaluates a math expression
  3. `get_time(timezone)` — returns current time in a timezone
- Test with questions that require:
  - Single tool use ("What's the weather in Tokyo?")
  - No tool use ("What's the capital of France?")
  - Multiple sequential tool uses ("What's the weather in the city where it's currently 3pm?")
- Add error handling for all tools
- Stretch: Add a `search_database(query)` tool with mock data and test a 3-tool chain

## Quiz Focus
- Who executes the tool — Claude or your code?
- What JSON field tells you Claude wants to use a tool?
- Given a tool definition, what's wrong with it? (bad description, missing required field)
- Code completion: Fill in the tool_result message format
- What should you do when a tool call fails? (select all correct approaches)
