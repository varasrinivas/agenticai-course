/**
 * M05 Lab - Step 2: Multi-Tool Agent Loop (Starter)
 * ===================================================
 * Build the CORE PATTERN of every AI agent: the tool-use while loop.
 * Three tools, multiple turns, and the decide-act-observe-repeat cycle.
 *
 * Usage:
 *     node multi_tool.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

// =============================================================================
// MOCK DATA AND TOOL FUNCTIONS (complete -- do not modify)
// =============================================================================

const WEATHER_DATA = {
  "new york": { temp_f: 72, condition: "Partly Cloudy", humidity: 65 },
  london: { temp_f: 58, condition: "Rainy", humidity: 80 },
  tokyo: { temp_f: 85, condition: "Sunny", humidity: 45 },
  sydney: { temp_f: 64, condition: "Windy", humidity: 55 },
  paris: { temp_f: 68, condition: "Overcast", humidity: 70 },
};

function getWeather(city) {
  const cityLower = city.toLowerCase().trim();
  if (cityLower in WEATHER_DATA) {
    return { city, ...WEATHER_DATA[cityLower] };
  }
  return {
    error: `No weather data available for '${city}'. Available cities: ${Object.keys(WEATHER_DATA).join(", ")}`,
  };
}

function calculate(expression) {
  try {
    const allowed = new Set("0123456789+-*/.(). ".split(""));
    for (const c of expression) {
      if (!allowed.has(c)) {
        return { error: `Invalid characters in expression: ${expression}` };
      }
    }
    // eslint-disable-next-line no-eval
    const result = eval(expression); // Safe because we validated characters
    return {
      expression,
      result: Math.round(result * 1000000) / 1000000,
    };
  } catch (e) {
    return { error: `Calculation failed: ${e.message}` };
  }
}

function getTime(timezone) {
  const MOCK_TIMES = {
    EST: "2024-03-15 14:30:00 EST",
    PST: "2024-03-15 11:30:00 PST",
    UTC: "2024-03-15 19:30:00 UTC",
    JST: "2024-03-16 04:30:00 JST",
    GMT: "2024-03-15 19:30:00 GMT",
  };
  const tz = timezone.toUpperCase().trim();
  if (tz in MOCK_TIMES) {
    return { timezone: tz, current_time: MOCK_TIMES[tz] };
  }
  return {
    error: `Unknown timezone: ${timezone}. Available: ${Object.keys(MOCK_TIMES).join(", ")}`,
  };
}

// =============================================================================
// TOOL DEFINITIONS (complete -- do not modify)
// =============================================================================

const TOOLS = [
  {
    name: "get_weather",
    description:
      "Get current weather data for a city. Returns temperature (Fahrenheit), " +
      "condition, and humidity.",
    input_schema: {
      type: "object",
      properties: {
        city: {
          type: "string",
          description: "The city name, e.g. 'Tokyo' or 'New York'",
        },
      },
      required: ["city"],
    },
  },
  {
    name: "calculate",
    description:
      "Evaluate a mathematical expression. Supports +, -, *, /, and parentheses. " +
      "Use this for any math calculations the user asks about.",
    input_schema: {
      type: "object",
      properties: {
        expression: {
          type: "string",
          description:
            "The math expression to evaluate, e.g. '15 * 340 / 100'",
        },
      },
      required: ["expression"],
    },
  },
  {
    name: "get_time",
    description:
      "Get the current time in a given timezone. " +
      "Supported timezones: EST, PST, UTC, JST, GMT.",
    input_schema: {
      type: "object",
      properties: {
        timezone: {
          type: "string",
          description: "The timezone abbreviation, e.g. 'EST', 'JST', 'UTC'",
        },
      },
      required: ["timezone"],
    },
  },
];

// Dispatch map: tool name -> function that executes it
const TOOL_FUNCTIONS = {
  get_weather: (args) => getWeather(args.city),
  calculate: (args) => calculate(args.expression),
  get_time: (args) => getTime(args.timezone),
};

const MAX_TURNS = 10;

const SYSTEM_PROMPT = `You are a helpful assistant with access to three tools:
- get_weather: look up current weather for a city
- calculate: evaluate math expressions
- get_time: get the current time in a timezone

Use the appropriate tool(s) to answer the user's questions. You may use
multiple tools in a single response if needed. Always explain the results
in clear, natural language after receiving tool results.`;

// =============================================================================
// OBSERVATION HELPERS (complete -- do not modify)
// =============================================================================

function observe(label, message) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`[${label}] ${message}`);
  console.log("=".repeat(60));
}

function observeToolCall(toolName, toolInput) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`[USING TOOL] ${toolName}`);
  console.log(`[INPUT]      ${JSON.stringify(toolInput, null, 2)}`);
  console.log("─".repeat(60));
}

function observeToolResult(result) {
  console.log(`\n${"─".repeat(60)}`);
  console.log("[TOOL RESULT]");
  console.log(JSON.stringify(result, null, 2));
  console.log("─".repeat(60));
}

// =============================================================================
// YOUR CODE: Implement the agent loop
// =============================================================================

async function runAgent(userMessage) {
  /**
   * Run the multi-tool agent loop.
   *
   * The pattern:
   *     1. Send messages to Claude (with tools available)
   *     2. If stop_reason === "tool_use": execute ALL tool calls, send results back
   *     3. If stop_reason === "end_turn": return the final text
   *     4. Repeat until done or MAX_TURNS exceeded
   *
   * Returns Claude's final text response.
   */
  observe("QUERY", userMessage);

  // ------------------------------------------------------------------
  // TODO 1: Initialize the messages array with the user's message
  //   const messages = [{ role: "user", content: userMessage }];
  // ------------------------------------------------------------------

  // ------------------------------------------------------------------
  // TODO 2: Start the agent loop
  //   let turn = 0;
  //   while (turn < MAX_TURNS) {
  //       turn++;
  //       observe("THINKING", `Turn ${turn}...`);
  // ------------------------------------------------------------------

      // --------------------------------------------------------------
      // TODO 3: Call client.messages.create with:
      //   model: MODEL, max_tokens: 1024, system: SYSTEM_PROMPT,
      //   tools: TOOLS, messages
      // (remember to await the call)
      // --------------------------------------------------------------

      // --------------------------------------------------------------
      // TODO 4: Handle stop_reason === "tool_use"
      //   - Loop through response.content
      //   - For each block where block.type === "tool_use":
      //       - Log with observeToolCall
      //       - Execute TOOL_FUNCTIONS[block.name](block.input)
      //       - Log with observeToolResult
      //       - Collect { type: "tool_result", tool_use_id: block.id,
      //                   content: JSON.stringify(result) }
      //   - Push assistant message: { role: "assistant", content: response.content }
      //   - Push tool results: { role: "user", content: toolResults }
      //   - Continue the loop (Claude will see results on next turn)
      // --------------------------------------------------------------

      // --------------------------------------------------------------
      // TODO 5: Handle stop_reason === "end_turn"
      //   - Extract text from response.content (check if block.text exists)
      //   - observe("RESPONSE", finalText)
      //   - Return the final text
      // --------------------------------------------------------------

  // } // end while

  // ------------------------------------------------------------------
  // TODO 6: If we exit the loop, return a max-turns error message
  //   observe("ERROR", `Agent exceeded maximum turns (${MAX_TURNS})`);
  //   return "Error: Agent exceeded maximum number of turns.";
  // ------------------------------------------------------------------
  return "";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M05 Lab - Step 2: Multi-Tool Agent Loop");
console.log("=".repeat(60));

// Test 1: Single tool (weather)
console.log("\n\n>>> Test 1: Single tool (weather)");
const result1 = await runAgent("What's the weather in Paris?");
console.log(`\nFINAL ANSWER: ${result1}`);

// Test 2: Single tool (calculate)
console.log("\n\n>>> Test 2: Single tool (calculate)");
const result2 = await runAgent("What is 15% of 340?");
console.log(`\nFINAL ANSWER: ${result2}`);

// Test 3: Multi-tool (weather + time)
console.log("\n\n>>> Test 3: Multi-tool");
const result3 = await runAgent(
  "What's the weather in Tokyo and what time is it there?"
);
console.log(`\nFINAL ANSWER: ${result3}`);

// Test 4: No tool needed
console.log("\n\n>>> Test 4: No tool needed");
const result4 = await runAgent("Hello, how are you?");
console.log(`\nFINAL ANSWER: ${result4}`);
