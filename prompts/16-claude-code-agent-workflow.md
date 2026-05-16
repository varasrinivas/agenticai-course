# Building Agents with Claude Code + Agent SDK

## Add to M25: Use Claude Code to Build an Agent Project
Step 1: Create CLAUDE.md via Claude Code (project brain)
Step 2: Create 4 slash commands (/run-agent, /test-agent, /add-tool, /eval-agent)
Step 3: Build and iterate using commands + natural language
Step 4: Create entity-resolution skill in .claude/skills/

Key insight: Claude Code is an agent development environment, not just a code editor.

## Add to M26: Agent SDK Inside Claude Code Project
Step 5: Convert raw agent to Agent SDK via Claude Code
Step 6: Add hooks via Claude Code (logging, PII redaction)
Step 7: Add session support + /chat-agent slash command
Step 8: Create pytest test suite via Claude Code
Step 9: Deploy with Dockerfile + docker-compose via Claude Code

Complete workflow: claude -> "Create CLAUDE.md" -> "Create commands" -> /run-agent -> "Convert to SDK" -> "Add hooks" -> "Add sessions" -> /test-agent -> /eval-agent -> "Deploy"
