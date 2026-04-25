/**
 * M06 Lab - Step 1: Parallel Tool Dispatch (Solution)
 * =====================================================
 * Complete solution: handling multiple tool_use blocks in a single response.
 * Claude requests tools in parallel when inputs are independent.
 *
 * Usage:
 *     node parallel_tools.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

// =============================================================================
// MOCK DATA AND TOOL FUNCTIONS
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
// TOOL DEFINITIONS
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
// OBSERVATION HELPERS
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
// SOLUTION: The Parallel-Aware Agent Loop
// =============================================================================

async function runAgent(userMessage) {
  /**
   * Run the agent loop with explicit parallel tool dispatch.
   *
   * WHY parallel matters: When Claude requests 3 weather lookups at once,
   * a production system could execute them concurrently (Promise.all).
   * Here we execute sequentially but track the parallel pattern -- the key
   * insight is that ALL tool_use blocks in one response are independent.
   */
  observe("QUERY", userMessage);

  // Initialize conversation memory
  const messages = [{ role: "user", content: userMessage }];
  let totalToolCalls = 0;

  // === THE AGENT LOOP ===
  let turn = 0;
  while (turn < MAX_TURNS) {
    turn++;
    observe(
      "THINKING",
      `Turn ${turn} -- sending ${messages.length} message(s) to Claude...`
    );

    // DECIDE: Ask Claude what to do next
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 1024,
      system: SYSTEM_PROMPT,
      tools: TOOLS,
      messages,
    });

    if (response.stop_reason === "tool_use") {
      // ACT: Execute ALL tool calls from this response
      // WHY we collect them all: Claude emits multiple tool_use blocks
      // when the calls are independent. We process them all before
      // sending results back -- this is the parallel dispatch pattern.
      const toolUseBlocks = response.content.filter(
        (b) => b.type === "tool_use"
      );
      const toolResults = [];

      for (const block of toolUseBlocks) {
        observeToolCall(block.name, block.input);

        // Execute the tool (with error handling for unknown tools)
        let result;
        if (block.name in TOOL_FUNCTIONS) {
          result = TOOL_FUNCTIONS[block.name](block.input);
        } else {
          result = { error: `Unknown tool: ${block.name}` };
        }

        observeToolResult(block.name, result);

        toolResults.push({
          type: "tool_result",
          tool_use_id: block.id,
          content: JSON.stringify(result),
        });
      }

      // Track parallel tool call count for this turn
      const parallelCount = toolUseBlocks.length;
      totalToolCalls += parallelCount;
      console.log(
        `\n[PARALLEL] Processed ${parallelCount} tool calls in this turn`
      );

      // OBSERVE: Add assistant message + tool results to memory
      messages.push({ role: "assistant", content: response.content });
      messages.push({ role: "user", content: toolResults });
    } else if (response.stop_reason === "end_turn") {
      // Claude is done -- extract text
      let finalText = "";
      for (const block of response.content) {
        if (block.text) {
          finalText += block.text;
        }
      }

      console.log(`\n[SUMMARY] Total tool calls: ${totalToolCalls}`);
      observe("RESPONSE", finalText);
      return finalText;
    } else {
      observe("WARNING", `Unexpected stop reason: ${response.stop_reason}`);
      return "Agent stopped unexpectedly.";
    }
  }

  observe("ERROR", `Agent exceeded maximum turns (${MAX_TURNS})`);
  return "Error: Agent exceeded maximum number of turns.";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M06 Lab - Step 1: Parallel Tool Dispatch (SOLUTION)");
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
