/**
 * M05 Lab - Step 1: Single Tool Call (Starter)
 * =============================================
 * Your first tool-using agent! Define a weather tool and handle
 * Claude's request to use it.
 *
 * KEY CONCEPT: Claude does NOT execute tools. Claude ASKS to use a tool
 * (via stop_reason="tool_use"), YOUR CODE executes it, then you send
 * the result back so Claude can formulate a response.
 *
 * Usage:
 *     node single_tool.js
 */

import Anthropic from "@anthropic-ai/sdk";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

// =============================================================================
// MOCK DATA (complete -- do not modify)
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
// TOOL DEFINITION (complete -- do not modify)
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

function observeToolResult(result) {
  console.log(`\n${"─".repeat(60)}`);
  console.log("[TOOL RESULT]");
  console.log(JSON.stringify(result, null, 2));
  console.log("─".repeat(60));
}

// =============================================================================
// YOUR CODE: Implement runSingleTool
// =============================================================================

async function runSingleTool(userMessage) {
  /**
   * Send a message to Claude with the weather tool available.
   * If Claude wants to use the tool, execute it and send the result back.
   *
   * Returns Claude's final text response.
   */
  observe("QUERY", userMessage);

  // ------------------------------------------------------------------
  // TODO 1: Call client.messages.create with:
  //   model: MODEL
  //   max_tokens: 1024
  //   tools: [WEATHER_TOOL]
  //   messages: [{ role: "user", content: userMessage }]
  // ------------------------------------------------------------------
  let response = null; // Replace with your API call

  // ------------------------------------------------------------------
  // TODO 2: Check if response.stop_reason === "tool_use"
  //   If NOT tool_use, extract and return the text from response.content
  //   (loop through blocks, check if block.text exists)
  // ------------------------------------------------------------------

  // ------------------------------------------------------------------
  // TODO 3: Find the tool_use block in response.content
  //   Use response.content.find(block => block.type === "tool_use")
  //   Save block.name, block.input, and block.id
  // ------------------------------------------------------------------

  // ------------------------------------------------------------------
  // TODO 4: Execute the tool
  //   Call getWeather(toolBlock.input.city) and save the result
  //   Log the call with observeToolCall and observeToolResult
  // ------------------------------------------------------------------

  // ------------------------------------------------------------------
  // TODO 5: Send the tool result back to Claude
  //   Call client.messages.create again with messages: [
  //       { role: "user", content: userMessage },
  //       { role: "assistant", content: response.content },
  //       { role: "user", content: [
  //           {
  //               type: "tool_result",
  //               tool_use_id: toolBlock.id,
  //               content: JSON.stringify(result),
  //           }
  //       ]},
  //   ]
  // ------------------------------------------------------------------

  // ------------------------------------------------------------------
  // TODO 6: Extract and return the final text response
  //   Loop through the new response's content blocks and collect text.
  // ------------------------------------------------------------------
  return "";
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M05 Lab - Step 1: Single Tool Call");
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
