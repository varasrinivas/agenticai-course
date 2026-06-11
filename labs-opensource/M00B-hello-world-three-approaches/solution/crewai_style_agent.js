/**
 * M00B Lab - Step 2 (Node.js reference): CrewAI-style agent
 * ==========================================================
 * CrewAI is Python-only. This file mimics CrewAI's declarative role/goal/tool
 * structure as a thin wrapper around the raw OpenAI SDK loop.
 * Run: node crewai_style_agent.js
 */

import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

const TIMEZONES = {
  "new york": "America/New_York", "london": "Europe/London",
  "tokyo": "Asia/Tokyo", "sydney": "Australia/Sydney",
  "san francisco": "America/Los_Angeles",
};

// Declarative agent config (like CrewAI's Agent class)
const agent = {
  role: "World Clock Assistant",
  goal: "Answer questions about the current time in any major city.",
  tools: {
    get_time: {
      description: "Get the current local time in a major city.",
      parameters: {
        type: "object",
        properties: { city: { type: "string", description: "City name, e.g. Tokyo" } },
        required: ["city"],
      },
      fn: ({ city }) => {
        const tz = TIMEZONES[city.toLowerCase()];
        if (!tz) return `Unknown city: ${city}.`;
        return new Intl.DateTimeFormat("en-GB", {
          timeZone: tz, hour: "2-digit", minute: "2-digit",
          weekday: "long", day: "2-digit", month: "short", year: "numeric",
        }).format(new Date());
      },
    },
  },
};

async function kickoff(taskDescription) {
  const messages = [
    { role: "system", content: `You are a ${agent.role}. Goal: ${agent.goal}` },
    { role: "user", content: taskDescription },
  ];
  const tools = Object.entries(agent.tools).map(([name, t]) => ({
    type: "function",
    function: { name, description: t.description, parameters: t.parameters },
  }));

  while (true) {
    let resp;
    try {
      resp = await client.chat.completions.create({
        model: "mistral", messages, tools, tool_choice: "auto",
      });
    } catch (error) {
      return `API error: ${error.message}`;
    }
    const msg = resp.choices[0].message;
    if (!msg.tool_calls) return msg.content;

    messages.push(msg);
    for (const tc of msg.tool_calls) {
      const toolDef = agent.tools[tc.function.name];
      const args = JSON.parse(tc.function.arguments);
      const content = toolDef ? toolDef.fn(args) : `Unknown tool: ${tc.function.name}`;
      messages.push({ role: "tool", tool_call_id: tc.id, content });
    }
  }
}

console.log(await kickoff("What time is it in Tokyo right now?"));
