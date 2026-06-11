/**
 * M05 Lab: Tool Definitions + Mock Implementations (shared helper —
 * identical to starter version; tools are never the exercise here)
 */

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

const MOCK_WEATHER = {
  tokyo: { temp: 22, condition: "sunny", humidity: 45 },
  london: { temp: 14, condition: "cloudy", humidity: 72 },
  "new york": { temp: 28, condition: "partly cloudy", humidity: 60 },
};

const MOCK_TIMES = { "us/eastern": "14:30", "asia/tokyo": "03:30", "europe/london": "19:30" };

export function runTool(name, args) {
  if (name === "get_weather") {
    const data = MOCK_WEATHER[args.city?.toLowerCase()];
    if (data) return JSON.stringify(data);
    return JSON.stringify({ error: `City '${args.city}' not found. Available: Tokyo, London, New York` });
  }

  if (name === "calculate") {
    const expr = args.expression ?? "";
    try {
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
