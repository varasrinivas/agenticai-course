/**
 * M00 Lab - Step 1: Environment Check (COMPLETE — just run it)
 * =============================================================
 * Verifies: openai SDK installed, Ollama server reachable, mistral model pulled.
 * Run: node check_setup.js
 */

const OLLAMA_URL = "http://localhost:11434";
const REQUIRED_MODEL = "mistral";

function check(label, ok, fix) {
  console.log(`[${ok ? "OK " : "FAIL"}] ${label}`);
  if (!ok) console.log(`       Fix: ${fix}`);
  return ok;
}

let allOk = true;

// 1. openai SDK importable?
try {
  await import("openai");
  allOk = check("openai SDK installed", true, "") && allOk;
} catch {
  allOk = check("openai SDK installed", false, "npm install openai") && allOk;
}

// 2. Ollama server reachable? 3. mistral pulled?
let models = [];
try {
  const resp = await fetch(`${OLLAMA_URL}/api/tags`, { signal: AbortSignal.timeout(5000) });
  const data = await resp.json();
  models = (data.models ?? []).map((m) => m.name);
  allOk = check(`Ollama server reachable at ${OLLAMA_URL}`, true, "") && allOk;
} catch {
  allOk =
    check(
      `Ollama server reachable at ${OLLAMA_URL}`,
      false,
      "Start it with: ollama serve  (or launch the Ollama app)"
    ) && allOk;
}

const hasModel = models.some((m) => m.startsWith(REQUIRED_MODEL));
allOk =
  check(
    `model '${REQUIRED_MODEL}' is pulled (${models.join(", ") || "none found"})`,
    hasModel,
    `ollama pull ${REQUIRED_MODEL}`
  ) && allOk;

console.log();
if (allOk) {
  console.log("Environment ready — continue to Step 2 (hello_mistral).");
} else {
  console.log("Fix the FAIL items above, then re-run this script.");
  process.exit(1);
}
