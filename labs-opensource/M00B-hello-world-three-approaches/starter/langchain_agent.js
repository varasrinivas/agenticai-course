/**
 * M00B Lab - Step 3: LangChain.js Agent
 * ======================================
 * The tool body is provided. You build the LLM, prompt, agent, and executor.
 * Run: node langchain_agent.js
 */

import { ChatOllama } from "@langchain/ollama";
import { createOpenAIToolsAgent, AgentExecutor } from "langchain/agents";
import { tool } from "@langchain/core/tools";
import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";
import { z } from "zod";

const TIMEZONES = {
  "new york": "America/New_York", "london": "Europe/London",
  "tokyo": "Asia/Tokyo", "sydney": "Australia/Sydney",
  "san francisco": "America/Los_Angeles",
};

function getTimeImpl(city) {
  const tz = TIMEZONES[city.toLowerCase()];
  if (!tz) return `Unknown city: ${city}. Known: ${Object.keys(TIMEZONES).join(", ")}.`;
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: tz, hour: "2-digit", minute: "2-digit",
    weekday: "long", day: "2-digit", month: "short", year: "numeric",
  }).format(new Date());
}

// TODO 1: Wrap getTimeImpl with LangChain's tool():
// const getTime = tool(({ city }) => getTimeImpl(city), {
//   name: "get_time",
//   description: "Get the current local time in a major city.",
//   schema: z.object({ city: z.string().describe("City name, e.g. Tokyo") }),
// });
const getTime = null;

// TODO 2: Create the LLM — new ChatOllama({ model: "mistral" })
const llm = null;

// TODO 3: Build the prompt with ChatPromptTemplate.fromMessages([...]):
// - ["system", "You help users find the current local time in any city."]
// - ["human", "{input}"]
// - new MessagesPlaceholder("agent_scratchpad")
const prompt = null;

// TODO 4: Wire it together and run:
// const agent = await createOpenAIToolsAgent({ llm, tools: [getTime], prompt });
// const executor = new AgentExecutor({ agent, tools: [getTime], verbose: false });
// const result = await executor.invoke({ input: "What time is it in Tokyo right now?" });
// console.log(result.output);
