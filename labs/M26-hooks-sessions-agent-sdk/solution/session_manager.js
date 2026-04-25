/**
 * M26 Lab — Step 3: Session Management with Fork (Node.js)
 *
 * Sessions allow an agent to persist conversation state across interactions
 * and branch into parallel explorations without polluting the main context.
 *
 * Usage:
 *     node session_manager.js
 */

class Session {
  constructor(name, systemPrompt = "", parentName = null) {
    this.name = name;
    this.systemPrompt = systemPrompt;
    this.parentName = parentName;
    this.messages = [];
    this.createdAt = new Date();
    this.lastActive = new Date();
    this.tokenCount = 0;
    this.maxTokens = 100000;
    this.metadata = {};
  }
}

class SessionManager {
  constructor() {
    this.sessions = new Map();
    this.activeSession = null;
  }

  createSession(name, systemPrompt = "") {
    if (this.sessions.has(name)) {
      console.log(`  [!] Session '${name}' already exists. Use resumeSession() instead.`);
      return this.sessions.get(name);
    }

    const session = new Session(name, systemPrompt);
    this.sessions.set(name, session);
    this.activeSession = session;

    console.log(`  [+] Created session: '${name}'`);
    console.log(`      System prompt: ${systemPrompt.slice(0, 60)}...`);
    return session;
  }

  resumeSession(name) {
    if (!this.sessions.has(name)) {
      console.log(`  [!] Session '${name}' not found.`);
      return null;
    }

    const session = this.sessions.get(name);
    session.lastActive = new Date();
    this.activeSession = session;

    console.log(`  [>] Resumed session: '${name}' (${session.messages.length} messages)`);
    return session;
  }

  addMessage(role, content, sessionName = null) {
    const session = this._getSession(sessionName);
    if (!session) return;

    const message = {
      role,
      content,
      timestamp: new Date().toISOString(),
    };
    session.messages.push(message);

    const estimatedTokens = Math.floor(content.length / 4);
    session.tokenCount += estimatedTokens;
    session.lastActive = new Date();

    console.log(`  [${role}] ${content.slice(0, 60)}...`);
    console.log(`      Tokens: ~${session.tokenCount}/${session.maxTokens}`);

    const usagePct = session.tokenCount / session.maxTokens;
    if (usagePct > 0.8) {
      console.log(`      [!] Context window ${(usagePct * 100).toFixed(0)}% full — consider compaction`);
    }

    return message;
  }

  forkSession(sourceName, forkName) {
    if (!this.sessions.has(sourceName)) {
      console.log(`  [!] Source session '${sourceName}' not found.`);
      return null;
    }
    if (this.sessions.has(forkName)) {
      console.log(`  [!] Fork name '${forkName}' already exists.`);
      return null;
    }

    const source = this.sessions.get(sourceName);

    const forked = new Session(forkName, source.systemPrompt, sourceName);
    forked.messages = structuredClone(source.messages);
    forked.tokenCount = source.tokenCount;
    forked.metadata = structuredClone(source.metadata);

    this.sessions.set(forkName, forked);

    console.log(`  [Fork] '${sourceName}' -> '${forkName}'`);
    console.log(`      Copied ${forked.messages.length} messages, ~${forked.tokenCount} tokens`);
    return forked;
  }

  isContextStale(sessionName = null, maxAgeMinutes = 30, maxTokenPct = 0.7) {
    const session = this._getSession(sessionName);
    if (!session) return false;

    const reasons = [];

    const ageMs = Date.now() - session.lastActive.getTime();
    const ageMinutes = ageMs / 60000;
    if (ageMinutes > maxAgeMinutes) {
      reasons.push(`Inactive for ${ageMinutes.toFixed(0)} min (limit: ${maxAgeMinutes} min)`);
    }

    const usagePct = session.tokenCount / session.maxTokens;
    if (usagePct > maxTokenPct) {
      reasons.push(`Token usage ${(usagePct * 100).toFixed(0)}% (limit: ${(maxTokenPct * 100).toFixed(0)}%)`);
    }

    const isStale = reasons.length > 0;

    if (isStale) {
      console.log(`  [!] Session '${session.name}' is STALE:`);
      for (const reason of reasons) {
        console.log(`      - ${reason}`);
      }
    } else {
      console.log(`  [OK] Session '${session.name}' is fresh`);
    }

    return isStale;
  }

  compactSession(sessionName = null, keepRecent = 3) {
    const session = this._getSession(sessionName);
    if (!session) return;

    if (session.messages.length <= keepRecent) {
      console.log(`  [OK] Session '${session.name}' has ${session.messages.length} messages — no compaction needed`);
      return;
    }

    const oldCount = session.messages.length;
    const oldTokens = session.tokenCount;

    const toSummarize = session.messages.slice(0, -keepRecent);
    const recent = session.messages.slice(-keepRecent);

    const summaryParts = toSummarize.map(
      (msg) => `[${msg.role}] ${msg.content.slice(0, 40)}...`
    );

    const summary = {
      role: "system",
      content: `[Compacted summary of ${toSummarize.length} earlier messages]\n${summaryParts.join("\n")}`,
      timestamp: new Date().toISOString(),
      isSummary: true,
    };

    session.messages = [summary, ...recent];
    session.tokenCount = session.messages.reduce(
      (sum, m) => sum + Math.floor(m.content.length / 4),
      0
    );

    console.log(`  [Compact] Session '${session.name}':`);
    console.log(`      Messages: ${oldCount} -> ${session.messages.length}`);
    console.log(`      Tokens: ~${oldTokens} -> ~${session.tokenCount} (saved ~${oldTokens - session.tokenCount})`);
  }

  listSessions() {
    console.log(`\n  Active sessions: ${this.sessions.size}`);
    for (const [name, session] of this.sessions) {
      const activeMarker = session === this.activeSession ? " (ACTIVE)" : "";
      const forkMarker = session.parentName ? ` [forked from ${session.parentName}]` : "";
      console.log(`    - ${name}${activeMarker}${forkMarker}: ${session.messages.length} msgs, ~${session.tokenCount} tokens`);
    }
  }

  _getSession(sessionName = null) {
    if (sessionName) {
      const session = this.sessions.get(sessionName);
      if (!session) {
        console.log(`  [!] Session '${sessionName}' not found.`);
      }
      return session;
    }
    return this.activeSession;
  }
}

// --- Main ---

function main() {
  console.log("=".repeat(60));
  console.log("M26 Lab — Session Management with Fork");
  console.log("=".repeat(60));

  const mgr = new SessionManager();

  console.log("\n--- Step 1: Create a named session ---");
  mgr.createSession(
    "ucc-support-main",
    "You are a UCC filing support agent. Help customers with filing lookups, risk checks, and refund requests."
  );

  console.log("\n--- Step 2: Simulate a conversation ---");
  mgr.addMessage("user", "I need to look up filing UCC-2024-NY-0012847 for Greenfield Logistics.");
  mgr.addMessage("assistant", "I'll look that up for you. Let me search our filing database.");
  mgr.addMessage("assistant", "Found it. Filing UCC-2024-NY-0012847 is Active. Debtor: Greenfield Logistics LLC. Secured Party: Atlantic Capital Partners. Expires 2029-03-15.");
  mgr.addMessage("user", "What's their risk profile?");
  mgr.addMessage("assistant", "Greenfield Logistics LLC has a LOW risk score of 0.35. No prior defaults, active 5+ years, single active lien.");
  mgr.addMessage("user", "Now I want to explore what happens if we add a second lien.");

  console.log("\n--- Step 3: Fork session for what-if analysis ---");
  mgr.forkSession("ucc-support-main", "ucc-support-what-if-second-lien");

  mgr.addMessage("user", "Hypothetically, if Greenfield takes on a second lien from Pacific Trust, what happens to risk?", "ucc-support-what-if-second-lien");
  mgr.addMessage("assistant", "Adding a second lien would increase the risk score from 0.35 to approximately 0.58 (MEDIUM). Two concurrent liens raise subordination concerns.", "ucc-support-what-if-second-lien");

  console.log("\n--- Step 4: Verify isolation ---");
  const mainSession = mgr.sessions.get("ucc-support-main");
  const forkSession = mgr.sessions.get("ucc-support-what-if-second-lien");
  console.log(`  Main session messages: ${mainSession.messages.length}`);
  console.log(`  Fork session messages: ${forkSession.messages.length}`);
  console.log(`  Isolation verified: ${forkSession.messages.length > mainSession.messages.length}`);

  console.log("\n--- Step 5: Stale context detection ---");
  mgr.isContextStale("ucc-support-main", 30, 0.001);
  mgr.isContextStale("ucc-support-main", 30, 0.9);

  console.log("\n--- Step 6: Context compaction ---");
  for (let i = 0; i < 5; i++) {
    mgr.addMessage("user", `Follow-up question #${i + 1} about UCC filings and compliance requirements for multi-state entities.`, "ucc-support-main");
    mgr.addMessage("assistant", `Here is detailed answer #${i + 1} covering jurisdictional rules, continuation statements, and amendment procedures.`, "ucc-support-main");
  }

  console.log(`\n  Before compaction: ${mgr.sessions.get("ucc-support-main").messages.length} messages`);
  mgr.compactSession("ucc-support-main", 4);

  console.log("\n--- Step 7: List all sessions ---");
  mgr.listSessions();

  console.log(`\n${"=".repeat(60)}`);
  console.log("Key Takeaways");
  console.log("=".repeat(60));
  console.log(`
    1. Named sessions: Create, resume, and manage by name
    2. forkSession: Branch for what-if analysis without polluting main context
    3. Stale detection: Warn when context is old or overfull
    4. Compaction: Summarize old messages to reclaim context budget
    5. Isolation: Fork changes never affect the parent session
  `);

  console.log("[OK] Lab Step 3 complete — Session management with fork\n");
}

main();
