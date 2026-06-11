/**
 * M21B Lab: Connection Verifier (COMPLETE — Node.js)
 * ===================================================
 * Run: node verify_connection.js
 *      OLLAMA_BASE_URL=http://localhost:11434/v1 node verify_connection.js
 */

import OpenAI from "openai";

async function verifyConnection(baseUrl) {
  const url = baseUrl ?? process.env.OLLAMA_BASE_URL ?? "http://localhost:11434/v1";
  const client = new OpenAI({ baseURL: url, apiKey: process.env.API_KEY ?? "ollama" });

  try {
    const response = await client.chat.completions.create({
      model: process.env.MODEL ?? "mistral",
      messages: [{ role: "user", content: "Reply with the single word: connected" }],
      max_tokens: 10,
    });
    const reply = response.choices[0].message.content?.trim();
    console.log(`[OK] Endpoint ${url} responded: ${JSON.stringify(reply)}`);
    console.log(`     Model: ${response.model}`);
    console.log(`     Tokens used: ${response.usage?.total_tokens}`);
  } catch (err) {
    console.error(`[FAIL] Cannot reach endpoint at ${url}: ${err.message}`);
    console.error("       Local:  is Ollama running? (ollama serve)");
    console.error("       Cloud:  is the SSH tunnel up?");
    console.error("       Command: gcloud compute ssh ollama-server -- -L 11434:localhost:11434 -N -f");
    process.exit(1);
  }
}

await verifyConnection();
