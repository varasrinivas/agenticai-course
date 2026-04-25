/**
 * M05 Lab - Step 1: Single Tool Call (Solution)
 * ==============================================
 * Complete solution: define a weather tool, handle Claude's tool_use request,
 * execute the tool, send the result back, and return Claude's final response.
 *
 * Usage:
 *     node single_tool.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

// =============================================================================
// MOCK DATA
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

// =============================================================================
// TOOL DEFINITION
// =============================================================================

const WEATHER_TOOL = {
  name: "get_weather",
  description:
    "Get current weather data for a city. Returns temperature (Fahrenheit), " +
    "condition, and humidity. Use this when the user asks about weather.",
  input_schema: {
    type: "object",
    properties: {
      city: {
        type: "string",
        description:
          "The city name to look up weather for, e.g. 'Tokyo' or 'New York'",
      },
    },
    required: ["city"],
  },
};

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
// SOLUTION: runSingleTool
// =============================================================================

async function runSingleTool(userMessage) {
  observe("QUERY", userMessage);

  // Step 1: Call the API with the tool definition
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 1024,
    tools: [WEATHER_TOOL],
    messages: [{ role: "user", content: userMessage }],
  });

  // Step 2: If Claude didn't want to use a tool, return the text directly
  if (response.stop_reason !== "tool_use") {
    let finalText = "";
    for (const block of response.content) {
      if (block.text) {
        finalText += block.text;
      }
    }
    observe("RESPONSE", finalText);
    return finalText;
  }

  // Step 3: Find the tool_use block
  const toolBlock = response.content.find(
    (block) => block.type === "tool_use"
  );
  if (!toolBlock) {
    return "Error: stop_reason was tool_use but no tool_use block found.";
  }

  // Step 4: Execute the tool and log it
  observeToolCall(toolBlock.name, toolBlock.input);
  const result = getWeather(toolBlock.input.city);
  observeToolResult(result);

  // Step 5: Send the tool result back to Claude
  const followupResponse = await client.messages.create({
    model: MODEL,
    max_tokens: 1024,
    tools: [WEATHER_TOOL],
    messages: [
      { role: "user", content: userMessage },
      { role: "assistant", content: response.content },
      {
        role: "user",
        content: [
          {
            type: "tool_result",
            tool_use_id: toolBlock.id,
            content: JSON.stringify(result),
          },
        ],
      },
    ],
  });

  // Step 6: Extract and return Claude's final text
  let finalText = "";
  for (const block of followupResponse.content) {
    if (block.text) {
      finalText += block.text;
    }
  }

  observe("RESPONSE", finalText);
  return finalText;
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M05 Lab - Step 1: Single Tool Call (SOLUTION)");
console.log("=".repeat(60));

// Test 1: Known city
console.log("\n\n>>> Test 1: Known city");
const result1 = await runSingleTool("What's the weather in Tokyo?");
console.log(`\nFINAL ANSWER: ${result1}`);

// Test 2: Unknown city (error case)
console.log("\n\n>>> Test 2: Unknown city (error case)");
const result2 = await runSingleTool("What's the weather in Atlantis?");
console.log(`\nFINAL ANSWER: ${result2}`);

// Test 3: No tool needed
console.log("\n\n>>> Test 3: No tool needed");
const result3 = await runSingleTool("Hello! What can you help me with?");
console.log(`\nFINAL ANSWER: ${result3}`);
