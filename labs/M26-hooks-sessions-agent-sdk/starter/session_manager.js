/**
 * M26 Lab — Step 3: Session Management with Fork (Node.js)
 *
 * Sessions allow an agent to persist conversation state across interactions
 * and branch into parallel explorations without polluting the main context.
 *
 * YOUR TASK: Fill in the TODO sections to implement session management.
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
    // TODO: Implement session creation
    //
    // 1. Check if a session with this name already exists (this.sessions.has(name))
    //    - If yes, console.log a warning and return the existing session
    // 2. Create a new Session(name, systemPrompt)
    // 3. Store it: this.sessions.set(name, session)
    // 4. Set this.activeSession = session
    // 5. console.log the session name and system prompt (first 60 chars)
    // 6. Return the session

    // Replace the line below with your implementation
    return null;
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

    // TODO: Implement message addition with token tracking
    //
    // 1. Create a message object with role, content, and timestamp (new Date().toISOString())
    // 2. Push it to session.messages
    // 3. Estimate tokens: Math.floor(content.length / 4)
    // 4. Add estimated tokens to session.tokenCount
    // 5. Update session.lastActive = new Date()
    // 6. console.log the role and first 60 chars of content
    // 7. console.log current token usage
    // 8. If token usage > 80%, console.log a warning
    // 9. Return the message

    // Replace the line below with your implementation
    return null;
  }

  forkSession(sourceName, forkName) {
    // TODO: Implement session forking
    //
    // 1. Check that sourceName exists in this.sessions (console.log error if not)
    // 2. Check that forkName doesn't already exist (console.log error if it does)
    // 3. Get the source session
    // 4. Create a new Session(forkName, source.systemPrompt, sourceName)
    // 5. Deep copy messages: forked.messages = structuredClone(source.messages)
    // 6. Copy tokenCount: forked.tokenCount = source.tokenCount
    // 7. Deep copy metadata: forked.metadata = structuredClone(source.metadata)
    // 8. Store: this.sessions.set(forkName, forked)
    // 9. console.log the fork details
    // 10. Return the forked session

    // Replace the line below with your implementation
    return null;
  }

  isContextStale(sessionName = null, maxAgeMinutes = 30, maxTokenPct = 0.7) {
    const session = this._getSession(sessionName);
    if (!session) return false;

    // TODO: Implement stale context detection
    //
    // 1. Create a reasons array (empty)
    // 2. Check age: const ageMs = Date.now() - session.lastActive.getTime()
    //    - const ageMinutes = ageMs / 60000
    //    - If ageMinutes > maxAgeMinutes, push a reason string
    // 3. Check token usage: const usagePct = session.tokenCount / session.maxTokens
    //    - If usagePct > maxTokenPct, push a reason string
    // 4. isStale = reasons.length > 0
    // 5. If stale, console.log session name and each reason
    // 6. If not stale, console.log "[OK] Session '${name}' is fresh"
    // 7. Return isStale

    // Replace the line below with your implementation
    return false;
  }

  compactSession(sessionName = null, keepRecent = 3) {
    const session = this._getSession(sessionName);
    if (!session) return;

    if (session.messages.length <= keepRecent) {
      console.log(`  [OK] Session '${session.name}' has ${session.messages.length} messages — no compaction needed`);
      return;
    }

    // TODO: Implement context compaction
    //
    // 1. Save oldCount and oldTokens
    // 2. Split: toSummarize = session.messages.slice(0, -keepRecent), recent = session.messages.slice(-keepRecent)
    // 3. Build summaryParts: map each msg to `[${msg.role}] ${msg.content.slice(0, 40)}...`
    // 4. Create summary object with role "system", content, timestamp, isSummary: true
    // 5. Replace session.messages = [summary, ...recent]
    // 6. Recalculate tokenCount
    // 7. console.log before/after counts

    // Replace the line below with your implementation
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
  if (mainSession && forkSession) {
    console.log(`  Main session messages: ${mainSession.messages.length}`);
    console.log(`  Fork session messages: ${forkSession.messages.length}`);
    console.log(`  Isolation verified: ${forkSession.messages.length > mainSession.messages.length}`);
  } else {
    console.log("  [!] Sessions not found — check your createSession and forkSession implementations");
  }

  console.log("\n--- Step 5: Stale context detection ---");
  mgr.isContextStale("ucc-support-main", 30, 0.001);
  mgr.isContextStale("ucc-support-main", 30, 0.9);

  console.log("\n--- Step 6: Context compaction ---");
  for (let i = 0; i < 5; i++) {
    mgr.addMessage("user", `Follow-up question #${i + 1} about UCC filings and compliance requirements for multi-state entities.`, "ucc-support-main");
    mgr.addMessage("assistant", `Here is detailed answer #${i + 1} covering jurisdictional rules, continuation statements, and amendment procedures.`, "ucc-support-main");
  }

  const mainSess = mgr.sessions.get("ucc-support-main");
  if (mainSess) {
    console.log(`\n  Before compaction: ${mainSess.messages.length} messages`);
  }
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
