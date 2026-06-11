/**
 * M05 Lab - Step 1: Tool Definitions + Mock Implementations (COMPLETE)
 * =====================================================================
 * Three tools: get_weather, calculate, get_time. Imported by tool_agent.js.
 * Run standalone to sanity-check: node tools.js
 */

import { pathToFileURL } from "node:url";

// --- Tool definitions (OpenAI function-calling format) ---
export const TOOLS = [
  {
    type: "function",
    function: {
      name: "get_weather",
      description: "Get current weather for a city. Returns temperature (Celsius), condition, and humidity.",
      parameters: {
        type: "object",
        properties: {
          city: { type: "string", description: "City name, e.g. 'Tokyo' or 'New York'" },
        },
        required: ["city"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "calculate",
      description: "Evaluate a mathematical expression. Use for any math computation. Supports +, -, *, /, **, parentheses.",
      parameters: {
        type: "object",
        properties: {
          expression: { type: "string", description: "Math expression, e.g. '(15 * 7) + 23'" },
        },
        required: ["expression"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "get_time",
      description: "Get the current time in a specific timezone. Returns time in HH:MM format.",
      parameters: {
        type: "object",
        properties: {
          timezone: { type: "string", description: "Timezone, e.g. 'US/Eastern', 'Asia/Tokyo', 'Europe/London'" },
        },
        required: ["timezone"],
      },
    },
  },
];

// --- Mock data (what your code runs — no external APIs) ---
const MOCK_WEATHER = {
  tokyo: { temp: 22, condition: "sunny", humidity: 45 },
  london: { temp: 14, condition: "cloudy", humidity: 72 },
  "new york": { temp: 28, condition: "partly cloudy", humidity: 60 },
};

const MOCK_TIMES = { "us/eastern": "14:30", "asia/tokyo": "03:30", "europe/london": "19:30" };

/**
 * Execute a tool and return the result as a JSON string.
 * NOTE: errors are returned as DATA, never thrown — the model can read
 * an error string and recover; a crash it cannot.
 */
export function runTool(name, args) {
  if (name === "get_weather") {
    const data = MOCK_WEATHER[args.city?.toLowerCase()];
    if (data) return JSON.stringify(data);
    return JSON.stringify({ error: `City '${args.city}' not found. Available: Tokyo, London, New York` });
  }

  if (name === "calculate") {
    const expr = args.expression ?? "";
    try {
      // Safe eval: only allow math characters
      if (!/^[0-9+\-*/.()% ]+$/.test(expr)) {
        return JSON.stringify({ error: `Invalid characters in expression: ${expr}` });
      }
      const result = Function(`"use strict"; return (${expr})`)();
      return JSON.stringify({ result });
    } catch (e) {
      return JSON.stringify({ error: `Calculation failed: ${e.message}` });
    }
  }

  if (name === "get_time") {
    const tz = args.timezone ?? "";
    return JSON.stringify({ timezone: tz, time: MOCK_TIMES[tz.toLowerCase()] ?? "12:00" });
  }

  return JSON.stringify({ error: `Unknown tool: ${name}` });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const names = TOOLS.map((t) => t.function.name);
  console.log(`Defined ${TOOLS.length} tools: ${names.join(", ")}`);
  console.log(`Test: ${runTool("get_weather", { city: "Tokyo" })}`);
  console.log(`Test: ${runTool("calculate", { expression: "(15 * 7) + 23" })}`);
  console.log(`Test: ${runTool("get_weather", { city: "Atlantis" })}`);
}
