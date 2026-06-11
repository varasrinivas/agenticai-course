/**
 * M00B Lab - Step 1: Raw OpenAI SDK Tool-Use Loop — SOLUTION
 * ===========================================================
 * Run: node raw_agent.js
 */

import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://localhost:11434/v1", // Ollama local endpoint
  apiKey: "ollama",                     // required by SDK but ignored by Ollama
});

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

async function runAgent(userMessage) {
  const messages = [{ role: "user", content: userMessage }];
  while (true) {
    let resp;
    try {
      resp = await client.chat.completions.create({
        model: "mistral",
        messages,
        tools: TOOLS,
        tool_choice: "auto",
      });
    } catch (error) {
      return `API error: ${error.message} (is Ollama running? ollama serve)`;
    }

    const msg = resp.choices[0].message;

    // Did the model finish?
    if (!msg.tool_calls) return msg.content;

    // The model requested tool calls — dispatch each one.
    messages.push(msg);
    for (const tc of msg.tool_calls) {
      const args = JSON.parse(tc.function.arguments); // arguments is a JSON string
      const text = tc.function.name === "get_time"
        ? getTime(args.city)
        : `Unknown tool: ${tc.function.name}`;
      messages.push({ role: "tool", tool_call_id: tc.id, content: text });
    }
    // Loop back — the model reads the tool result and answers
  }
}

console.log(await runAgent("What time is it in Tokyo right now?"));
