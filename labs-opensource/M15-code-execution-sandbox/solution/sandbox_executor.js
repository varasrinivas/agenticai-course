/**
 * M15 Lab - Step 1: SubprocessExecutor — SOLUTION (Node.js)
 * ==========================================================
 * Run: node sandbox_executor.js
 */

import { execFile } from "node:child_process";
import { writeFile, unlink } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

import { pathToFileURL } from "node:url";
import assert from "node:assert/strict";
const execFileAsync = promisify(execFile);
const PYTHON = process.platform === "win32" ? "python" : "python3";

export function toToolContent(r) {
  const parts = [`exit_code: ${r.exitCode}`];
  if (r.stdout) parts.push(`stdout:\n${r.stdout.trim()}`);
  if (r.stderr) parts.push(`stderr:\n${r.stderr.trim()}`);
  return parts.join("\n");
}

export class SubprocessExecutor {
  constructor(timeoutSeconds = 10) {
    this.timeoutSeconds = timeoutSeconds;
  }

  async run(code, timeoutSeconds) {
    const seconds = timeoutSeconds ?? this.timeoutSeconds;
    const timeout = seconds * 1000;
    const tmpFile = join(tmpdir(), `sandbox_${Date.now()}_${Math.random().toString(36).slice(2)}.py`);
    await writeFile(tmpFile, code, "utf-8");
    try {
      // execFile = no shell = no shell injection
      const { stdout, stderr } = await execFileAsync(PYTHON, [tmpFile], {
        timeout,
        encoding: "utf8",
      });
      return { stdout, stderr, exitCode: 0 };
    } catch (err) {
      if (err.killed || err.signal === "SIGTERM") {
        return {
          stdout: "",
          stderr: `Execution timed out after ${seconds} seconds.`,
          exitCode: 124, // bash timeout(1) convention
        };
      }
      return {
        stdout: err.stdout ?? "",
        stderr: err.stderr ?? String(err),
        exitCode: typeof err.code === "number" ? err.code : 1,
      };
    } finally {
      await unlink(tmpFile).catch(() => {}); // cleanup even on crash
    }
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const ex = new SubprocessExecutor(3);

  console.log("TEST 1: happy path");
  let r = await ex.run("print(sum(range(101)))");
  console.log(`  ${toToolContent(r)}`);
  assert.ok(r.exitCode === 0 && r.stdout.includes("5050"));

  console.log("\nTEST 2: deliberate NameError (must return, not throw)");
  r = await ex.run("print(undefined_variable)");
  console.log(`  exitCode=${r.exitCode}, stderr contains NameError: ${r.stderr.includes("NameError")}`);
  assert.ok(r.exitCode !== 0 && r.stderr.includes("NameError"));

  console.log("\nTEST 3: infinite loop (must time out at exit code 124, not hang)");
  r = await ex.run("while True: pass");
  console.log(`  exitCode=${r.exitCode}, stderr=${r.stderr.slice(0, 50)}`);
  assert.ok(r.exitCode === 124);

  console.log("\nAll executor checks passed.");
}
