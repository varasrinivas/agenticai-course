/**
 * M00B Lab - Step 1: Raw OpenAI SDK Tool-Use Loop
 * ================================================
 * The tool and its schema are provided. You implement the agent loop.
 * Run: node raw_agent.js
 */

import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://localhost:11434/v1", // Ollama local endpoint
  apiKey: "ollama",                     // required by SDK but ignored by Ollama
});

// ---- Tool implementation (COMPLETE) ----
const TIMEZONES = {
  "new york": "America/New_York",
  "london": "Europe/London",
  "tokyo": "Asia/Tokyo",
  "sydney": "Australia/Sydney",
  "san francisco": "America/Los_Angeles",
};

function getTime(city) {
  const tz = TIMEZONES[city.toLowerCase()];
  if (!tz) return `Unknown city: ${city}. Known cities: ${Object.keys(TIMEZONES).join(", ")}.`;
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: tz, hour: "2-digit", minute: "2-digit",
    weekday: "long", day: "2-digit", month: "short", year: "numeric",
  }).format(new Date());
}

// ---- Tool schema (OpenAI function-calling format — COMPLETE) ----
const TOOLS = [{
  type: "function",
  function: {
    name: "get_time",
    description: "Get the current local time in a major city.",
    parameters: {
      type: "object",
      properties: { city: { type: "string", description: "City name, e.g. Tokyo" } },
      required: ["city"],
    },
  },
}];

// ---- The loop (YOUR JOB) ----
async function runAgent(userMessage) {
  // TODO: Implement the tool-use loop.
  // 1. const messages = [{ role: "user", content: userMessage }];
  // 2. Loop forever:
  //    a. const resp = await client.chat.completions.create({
  //         model: "mistral", messages, tools: TOOLS, tool_choice: "auto" });
  //    b. const msg = resp.choices[0].message;
  //    c. If !msg.tool_calls → the model is done: return msg.content;
  //    d. Otherwise: messages.push(msg), then for each tc of msg.tool_calls:
  //       - const args = JSON.parse(tc.function.arguments);  // arguments is a JSON STRING
  //       - call getTime(args.city) if tc.function.name === "get_time",
  //         else produce an "Unknown tool" error string
  //       - messages.push({ role: "tool", tool_call_id: tc.id, content: result });
  //    e. Loop back — the model will read the tool result and answer (or call again)
  // Wrap the API call in try/catch and return an error string on failure.
}

console.log(await runAgent("What time is it in Tokyo right now?"));
