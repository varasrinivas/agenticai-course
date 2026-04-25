/**
 * M06 Lab - Step 1: Parallel Tool Dispatch (Starter)
 * ====================================================
 * Build an agent that handles MULTIPLE tool_use blocks in a single response.
 * Claude can request several tools at once -- your code must process them all
 * and send all results back together.
 *
 * Usage:
 *     node parallel_tools.js
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
    const result = eval(expression);
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

When the user asks about multiple things at once, call ALL relevant tools
in a single response (parallel tool use). Do not call them one at a time
when they are independent of each other.

Always explain the results in clear, natural language after receiving tool results.`;

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

function observeToolResult(toolName, result) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`[TOOL RESULT] ${toolName} -> ${JSON.stringify(result)}`);
  console.log("─".repeat(60));
}

// =============================================================================
// YOUR CODE: Implement the parallel-aware agent loop
// =============================================================================

async function runAgent(userMessage) {
  /**
   * Run the agent loop with explicit parallel tool dispatch.
   *
   * The pattern:
   *     1. Send messages to Claude (with tools available)
   *     2. If stop_reason === "tool_use": find ALL tool_use blocks, execute them,
   *        count how many ran in parallel, send ALL results back at once
   *     3. If stop_reason === "end_turn": return the final text
   *     4. Repeat until done or MAX_TURNS exceeded
   *
   * Returns Claude's final text response.
   */
  observe("QUERY", userMessage);

  // ------------------------------------------------------------------
  // TODO 1: Initialize messages and turn tracking
  //   const messages = [{ role: "user", content: userMessage }];
  //   let totalToolCalls = 0;
  // ------------------------------------------------------------------
  const messages = [{ role: "user", content: userMessage }];
  let totalToolCalls = 0;

  let turn = 0;
  while (turn < MAX_TURNS) {
    turn++;
    observe(
      "THINKING",
      `Turn ${turn} -- sending ${messages.length} message(s) to Claude...`
    );

    // --------------------------------------------------------------
    // TODO 2: Call the Claude API with tools (remember to await)
    //   const response = await client.messages.create({
    //       model: MODEL, max_tokens: 1024, system: SYSTEM_PROMPT,
    //       tools: TOOLS, messages,
    //   });
    // --------------------------------------------------------------

    // --------------------------------------------------------------
    // TODO 3: Handle stop_reason === "tool_use" with PARALLEL dispatch
    //   - Filter response.content for blocks where block.type === "tool_use"
    //   - Log each with observeToolCall
    //   - Execute each tool using TOOL_FUNCTIONS[block.name](block.input)
    //   - Log each result with observeToolResult
    //   - Print how many tool calls were processed:
    //     console.log(`\n[PARALLEL] Processed ${count} tool calls in this turn`);
    //   - Build toolResults array with:
    //     { type: "tool_result", tool_use_id: block.id,
    //       content: JSON.stringify(result) }
    //   - Push assistant message and tool results to messages
    //   - Update totalToolCalls
    //
    // KEY INSIGHT: All tool_use blocks in a single response are
    // INDEPENDENT -- Claude requested them in parallel because their
    // inputs don't depend on each other's outputs.
    // --------------------------------------------------------------

    // --------------------------------------------------------------
    // TODO 4: Handle stop_reason === "end_turn"
    //   - Extract text from response.content
    //   - Print summary: `[SUMMARY] Total tool calls: ${totalToolCalls}`
    //   - observe("RESPONSE", finalText)
    //   - Return finalText
    // --------------------------------------------------------------

    // Remove this line once you implement the above:
    return "";
  }

  observe("ERROR", `Agent exceeded maximum turns (${MAX_TURNS})`);
  return "Error: Agent exceeded maximum number of turns.";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M06 Lab - Step 1: Parallel Tool Dispatch");
console.log("=".repeat(60));

// Test 1: Parallel weather lookups (3 cities)
console.log("\n\n>>> Test 1: Parallel weather lookups (3 cities)");
const result1 = await runAgent(
  "What's the weather in Tokyo, New York, and London?"
);
console.log(`\nFINAL ANSWER: ${result1}`);

// Test 2: Parallel across different tools
console.log("\n\n>>> Test 2: Parallel across different tools");
const result2 = await runAgent(
  "What's the weather in Paris and what time is it in EST?"
);
console.log(`\nFINAL ANSWER: ${result2}`);

// Test 3: Parallel calculate calls
console.log("\n\n>>> Test 3: Parallel calculate calls");
const result3 = await runAgent("What is 25 * 4 and what is 100 / 3?");
console.log(`\nFINAL ANSWER: ${result3}`);
