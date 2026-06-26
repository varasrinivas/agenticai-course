// M21C Lab - Headless Log-Triage Agent (SOLUTION, Node.js mirror)
// ===============================================================
// Reads raw log lines on stdin, asks Mistral to flag anomalies, emits ONE
// JSON envelope on stdout, logs to stderr only, exits with a meaningful code.
//
// Run:
//   cat sample.log | node triage_agent.js
//   cat sample.log | node triage_agent.js 2>/dev/null | jq .
// Requires: npm install openai   (+ Ollama running with `ollama pull mistral`)
import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });
const MODEL = "mistral";

// ── Exit-code contract ──────────────────────────────────────────────────────
const EXIT_OK = 0;            // success
const EXIT_TRANSIENT = 1;     // operational failure (Ollama down, timeout) -> retry
const EXIT_BAD_OUTPUT = 2;    // bad/non-JSON output -> escalate, no retry
const EXIT_NEEDS_REVIEW = 3;  // critical anomaly -> needs a human

class BadOutput extends Error { code = EXIT_BAD_OUTPUT; }
class NeedsReview extends Error { code = EXIT_NEEDS_REVIEW; }
class GuardTripped extends Error { code = EXIT_TRANSIENT; }

const log = (msg) => console.error(`[triage] ${msg}`); // -> stderr

const SYSTEM_PROMPT =
  "You are a log-analysis agent. You are given raw log lines. " +
  "Return ONLY a JSON object, no prose, in exactly this shape:\n" +
  '{"anomalies": [{"line": <str>, "reason": <str>, ' +
  '"severity": "low|medium|high|critical"}], "clean": <bool>}\n' +
  "List only genuinely suspicious lines (errors, security events, resource " +
  "exhaustion). If nothing is wrong, return an empty anomalies list and " +
  "clean=true. Use severity=critical only for outages or security breaches.";

async function analyze(logs, { maxSeconds, maxTokens }) {
  // GUARD 1: wall-clock timeout via AbortController.
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), maxSeconds * 1000);
  let resp;
  try {
    log(`analyzing ${logs.split("\n").length} log line(s)`);
    resp = await client.chat.completions.create(
      {
        model: MODEL,
        temperature: 0,
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          { role: "user", content: logs },
        ],
      },
      { signal: ac.signal }
    );
  } catch (e) {
    if (ac.signal.aborted) throw new GuardTripped("wall-clock timeout exceeded");
    throw e; // connection refused etc. -> transient at the top level
  } finally {
    clearTimeout(timer); // always disarm
  }

  // GUARD 3: token budget.
  if (resp.usage.total_tokens > maxTokens)
    throw new GuardTripped(`token budget ${maxTokens} exceeded (${resp.usage.total_tokens})`);

  let raw = resp.choices[0].message.content.trim();
  raw = raw.replace(/^```json/, "").replace(/^```/, "").replace(/```$/, "").trim();

  let report;
  try {
    report = JSON.parse(raw);
  } catch (e) {
    throw new BadOutput(`model did not return valid JSON: ${e.message}`);
  }
  if (typeof report !== "object" || !("anomalies" in report) || !("clean" in report))
    throw new BadOutput("JSON missing required keys 'anomalies'/'clean'");
  if (!Array.isArray(report.anomalies))
    throw new BadOutput("'anomalies' must be a list");

  report.tokens = { prompt: resp.usage.prompt_tokens, completion: resp.usage.completion_tokens };

  // Business rule: critical anomalies are never auto-actioned.
  if (report.anomalies.some((a) => a.severity === "critical")) {
    const err = new NeedsReview("critical anomaly detected");
    err.report = report;
    throw err;
  }
  return report;
}

async function readLogs() {
  const fileIdx = process.argv.indexOf("--file");
  if (fileIdx !== -1 && process.argv[fileIdx + 1]) {
    const { readFile } = await import("node:fs/promises");
    return (await readFile(process.argv[fileIdx + 1], "utf8")).trim();
  }
  if (!process.stdin.isTTY) {
    const chunks = [];
    for await (const c of process.stdin) chunks.push(c);
    return Buffer.concat(chunks).toString("utf8").trim();
  }
  throw new Error("no input: pipe logs on stdin or pass --file PATH");
}

function argNum(flag, dflt) {
  const i = process.argv.indexOf(flag);
  return i !== -1 && process.argv[i + 1] ? Number(process.argv[i + 1]) : dflt;
}

async function main() {
  const started = Date.now();
  const envelope = { ok: false, data: null, error: null, meta: {} };
  let code = EXIT_OK;
  try {
    const logs = await readLogs();
    envelope.data = await analyze(logs, {
      maxSeconds: argNum("--max-seconds", 30),
      maxTokens: argNum("--max-tokens", 4000),
    });
    envelope.ok = true;
  } catch (e) {
    code = e.code ?? EXIT_TRANSIENT;
    const type =
      e instanceof NeedsReview ? "needs_review" :
      e instanceof BadOutput ? "bad_output" :
      e instanceof GuardTripped ? "guard_tripped" : e.name;
    if (e instanceof NeedsReview && e.report) envelope.data = e.report;
    envelope.error = { type, message: e.message };
  }
  envelope.meta = { exit_code: code, latency_ms: Date.now() - started };
  process.stdout.write(JSON.stringify(envelope) + "\n"); // THE result
  log(`done in ${envelope.meta.latency_ms}ms, exit=${code}`);
  return code;
}

main().then((code) => process.exit(code)); // exit code IS the status API
