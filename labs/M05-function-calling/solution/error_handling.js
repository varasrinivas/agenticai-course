/**
 * M05 Lab - Step 3: Error Handling and Edge Cases (Solution)
 * ===========================================================
 * Complete solution: robust agent loop with comprehensive error handling.
 * Handles API errors, unknown tools, tool execution failures, and max turns.
 *
 * Usage:
 *     node error_handling.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

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

Use the appropriate tool(s) to answer the user's questions. If a tool returns
an error, explain the problem to the user in plain language and suggest
alternatives if possible.`;

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

function observeToolResult(result) {
  console.log(`\n${"─".repeat(60)}`);
  console.log("[TOOL RESULT]");
  console.log(JSON.stringify(result, null, 2));
  console.log("─".repeat(60));
}

// =============================================================================
// SOLUTION: Error-Handling Agent Loop
// =============================================================================

async function runAgentSafe(userMessage) {
  observe("QUERY", userMessage);

  const messages = [{ role: "user", content: userMessage }];

  let turn = 0;
  while (turn < MAX_TURNS) {
    turn++;
    observe("THINKING", `Turn ${turn} of ${MAX_TURNS}...`);

    // ---- Layer 1: API call error handling ----
    let response;
    try {
      response = await client.messages.create({
        model: MODEL,
        max_tokens: 1024,
        system: SYSTEM_PROMPT,
        tools: TOOLS,
        messages,
      });
    } catch (error) {
      if (error instanceof Anthropic.APIError) {
        observe("API ERROR", `API call failed: ${error.message}`);
        return `Error: API call failed — ${error.message}`;
      }
      throw error; // Re-throw unexpected errors
    }

    if (response.stop_reason === "tool_use") {
      const toolResults = [];
      for (const block of response.content) {
        if (block.type === "tool_use") {
          observeToolCall(block.name, block.input);

          let result;

          // ---- Layer 2: Unknown tool validation ----
          if (!(block.name in TOOL_FUNCTIONS)) {
            result = { error: `Unknown tool: ${block.name}` };
            observe("WARNING", `Claude requested unknown tool: ${block.name}`);
          } else {
            // ---- Layer 3: Tool execution error handling ----
            try {
              result = TOOL_FUNCTIONS[block.name](block.input);
            } catch (e) {
              result = {
                error: `Tool '${block.name}' failed: ${e.message}`,
              };
              observe("ERROR", `Tool execution failed: ${e.message}`);
            }
          }

          observeToolResult(result);

          // ALWAYS send the result back, even if it's an error.
          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: JSON.stringify(result),
          });
        }
      }

      messages.push({ role: "assistant", content: response.content });
      messages.push({ role: "user", content: toolResults });
    } else if (response.stop_reason === "end_turn") {
      let finalText = "";
      for (const block of response.content) {
        if (block.text) {
          finalText += block.text;
        }
      }

      observe("RESPONSE", finalText);
      return finalText;
    } else {
      observe("WARNING", `Unexpected stop reason: ${response.stop_reason}`);
      return "Agent stopped unexpectedly.";
    }
  }

  // ---- Layer 4: Max turns exceeded ----
  observe("ERROR", `Agent exceeded maximum turns (${MAX_TURNS})`);
  return "Error: Agent exceeded maximum number of turns.";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M05 Lab - Step 3: Error Handling and Edge Cases (SOLUTION)");
console.log("=".repeat(60));

// Test 1: Unknown city (tool returns error -> Claude explains)
console.log("\n\n>>> Test 1: Unknown city");
const result1 = await runAgentSafe("What's the weather in Atlantis?");
console.log(`\nFINAL ANSWER: ${result1}`);

// Test 2: Division by zero (tool error -> Claude explains)
console.log("\n\n>>> Test 2: Division by zero");
const result2 = await runAgentSafe("Calculate 1/0");
console.log(`\nFINAL ANSWER: ${result2}`);

// Test 3: Multi-tool with mixed results
console.log("\n\n>>> Test 3: Multi-tool");
const result3 = await runAgentSafe(
  "What's the weather in Tokyo and calculate 25 * 4?"
);
console.log(`\nFINAL ANSWER: ${result3}`);

// Test 4: Normal query (no errors)
console.log("\n\n>>> Test 4: Normal query");
const result4 = await runAgentSafe("What time is it in EST?");
console.log(`\nFINAL ANSWER: ${result4}`);
