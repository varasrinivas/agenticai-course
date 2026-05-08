# fix-add-approach-references.ps1
# Adds forward/backward references connecting raw → SDK → spec across modules
# Run: .\fix-add-approach-references.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Adding Approach References Across Modules ===" -ForegroundColor Cyan
Write-Host "5 modules will be updated. Estimated: 15 minutes." -ForegroundColor Yellow
Write-Host ""

# 1. M05 — First tool call, forward reference to the journey ahead
Write-Host "[1/5] M05 - Adding forward reference..." -ForegroundColor Green

$cmd1 = @"
Open the M05 HTML file in output/. Find the end of the hands-on lab section or the quiz section. Add a callout box BEFORE the quiz with this content:

Title: Where This Leads — Three Ways to Build Agents
Style: Use the gold accent callout box style (border-color D4A843)

Content: You just wrote your first tool call using client.messages.create(). This is the RAW approach — you control every line. As the course progresses you will see this same pattern evolve:

In M12 you will wrap this tool call in a ReAct loop — the agent decides WHAT to call and WHEN to stop.
In M15B you will build a complete multi-agent system with this same raw loop — coordinator plus subagents plus guardrails.
In M26 you will rebuild that same agent using the Agent SDK where agent.tool decorators replace JSON Schema and hooks replace inline guardrails. Same output in 15 lines instead of 60.
In M25 you will write a specification document and Claude Code generates the entire agent from it.
In CAPSTONE-7 you will build the SAME agent all three ways and compare.

Every approach uses the tool pattern you just learned. The loop changes. The tools stay the same.

Use str_replace to insert. About 100 words.
"@

claude --dangerously-skip-permissions -p $cmd1
Write-Host ""

# 2. M12 — ReAct loop, reference back to M05 and forward to M15B/M26
Write-Host "[2/5] M12 - Adding approach reference..." -ForegroundColor Green

$cmd2 = @"
Open the M12 HTML file in output/. Find the end of the ReAct loop implementation section (after the code walkthrough but before design patterns or quiz). Add a callout box:

Title: The Evolution of This Loop
Style: Gold accent callout (D4A843)

Content: In M05 you made a single tool call. Now you have wrapped it in a while loop that checks stop_reason and lets Claude decide what to do next. This is the RAW ReAct loop and you see every line.

What comes next:
M15B — You will add a coordinator that delegates to subagent functions. Each subagent runs its own loop with its own tools. Same pattern but orchestrated.
M26 — The Agent SDK replaces this entire while loop. You define tools with agent.tool decorators and the SDK runs the loop for you. Hooks let you intercept each tool call for logging and guardrails without touching the loop code.
M25 — You write a spec document describing the agent and Claude Code generates the loop and tools and hooks and tests from the spec.

You are learning the engine before using the car. Understanding this raw loop is what lets you debug the SDK when something goes wrong.

Use str_replace to insert. About 120 words.
"@

claude --dangerously-skip-permissions -p $cmd2
Write-Host ""

# 3. M15B — Complete agent built raw, forward to M26 SDK rebuild
Write-Host "[3/5] M15B - Adding forward reference to SDK..." -ForegroundColor Green

$cmd3 = @"
Open the M15B HTML file in output/. Find the very end of the module content (after the final verification or reflection section but before the quiz). Add a prominent callout box:

Title: What You Just Built — And What Comes Next
Style: Gold accent callout (D4A843) with a slightly larger font

Content: You just built a complete multi-agent system from scratch. Coordinator plus two specialist subagents plus three tools plus conversation memory plus error handling. About 250 lines of code where you control every decision.

Now here is the question: what if you could get the SAME output in 15 lines?

In M26 you will rebuild this exact agent using the Anthropic Agent SDK. The agent.tool decorator replaces your JSON Schema definitions. Hooks replace your inline guardrails. Sessions replace your manual conversation history. The SDK runs the while loop for you.

Same tools. Same mock data. Same question. Same output. One fifth the code.

But you needed to build it raw first. When the SDK does something unexpected you will know exactly what it is abstracting because you wrote that code yourself in this module. That is why M15B exists before M26.

And in CAPSTONE-7 you will build this same agent a third time — by writing a specification document and letting Claude Code generate everything. Three approaches. Same agent. You will compare code size and development time and flexibility and decide which fits your workflow.

Use str_replace to insert. About 150 words.
"@

claude --dangerously-skip-permissions -p $cmd3
Write-Host ""

# 4. M26 — SDK module, reference back to M15B raw and forward to spec
Write-Host "[4/5] M26 - Adding backward and forward references..." -ForegroundColor Green

$cmd4 = @"
Open the M26 HTML file in output/. Find the beginning of the module content (after the title and intro but before the first technical section). Add a callout box:

Title: Remember M15B? You Are About to Rebuild It.
Style: Gold accent callout (D4A843)

Content: In M15B you built a UCC filing research agent from scratch. Coordinator plus subagents plus tools plus guardrails plus conversation history. About 250 lines where you wrote every line of the while loop.

This module rebuilds that SAME agent using the Anthropic Agent SDK. You will see your 250 lines shrink to about 40 lines. The output is identical. The difference is WHERE the logic lives — in your code (M15B) versus in the SDK (M26).

Keep M15B open in another tab as you work through this module. At each step compare what the SDK does versus what you coded manually. That comparison IS the lesson.

After M26 there is one more level. In M25 you learned spec-driven development where you write a specification and Claude Code generates everything. CAPSTONE-7 ties all three together — raw versus SDK versus spec for the same agent.

Use str_replace to insert at the top of the module content. About 120 words.
"@

claude --dangerously-skip-permissions -p $cmd4
Write-Host ""

# 5. M25 — Claude Code module, reference the full journey
Write-Host "[5/5] M25 - Adding journey reference..." -ForegroundColor Green

$cmd5 = @"
Open the M25 HTML file in output/. Find the spec-driven development section (or the end of the main content if spec-driven has not been added yet). Add a callout box:

Title: The Three Approaches — Your Complete Toolkit
Style: Gold accent callout (D4A843)

Content: You now have three ways to build agents:

Approach 1 Raw API Loop (M15B): You write the while loop and check stop_reason and execute tools and manage messages. Full control. Full understanding. 250 lines.

Approach 2 Agent SDK (M26): You define tools with decorators and add hooks for guardrails and use sessions for persistence. The SDK handles the loop. 40 lines.

Approach 3 Spec-Driven (this module): You write a specification document describing what the agent does. Claude Code generates the implementation. You review and iterate. 100 lines of spec.

Each approach builds on the one before it. You cannot debug Approach 3 without understanding Approach 1. You cannot appreciate Approach 2 without having suffered through Approach 1.

CAPSTONE-7 is where you prove this. You build the SAME agent all three ways in three sessions and compare everything: code size and development time and flexibility and debugging and maintenance. That comparison is the graduation exercise of this course.

Use str_replace to insert. About 150 words.
"@

claude --dangerously-skip-permissions -p $cmd5
Write-Host ""

Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "5 modules updated with approach references:" -ForegroundColor Cyan
Write-Host "  M05  + Forward reference: this tool pattern evolves into agents"
Write-Host "  M12  + Forward reference: this raw loop gets replaced by SDK"
Write-Host "  M15B + Forward reference: same agent in 15 lines next (M26)"
Write-Host "  M26  + Backward reference: remember M15B? Rebuild it now"
Write-Host "  M25  + Journey summary: three approaches, your complete toolkit"
