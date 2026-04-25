---
description: Validate a capstone project for accuracy, executability, and completeness
argument-hint: [CAPSTONE_ID DOMAIN e.g. CAPSTONE-3 DOMAIN-A, or CAPSTONE-3 to check all domains]
---

Validate the capstone project $ARGUMENTS for technical accuracy and student executability.

Read `prompts/03-capstone-domains.md` for the domain specifications.
Read `prompts/04-quality-standards.md` for content quality rules.
Read `prompts/07-depth-rules.md` for explanation quality rules.

Find the capstone HTML file in `output/` (glob match on the capstone ID and domain).

Run ALL of the following validation passes:

## PASS 1: Prerequisites Check
- List every module referenced as a prerequisite
- For each prerequisite module, verify it exists in `output/`
- Check: does the capstone use any concept NOT covered in a prerequisite module? If yes, flag it.
- Report: prerequisites satisfied / missing

## PASS 2: Environment Setup Validation
Check that the capstone provides COMPLETE setup instructions:
- [ ] Python version specified (e.g., "Python 3.10+")
- [ ] Node.js version specified (if applicable)
- [ ] ALL pip/npm packages listed with version numbers
- [ ] A single copy-pasteable install command (e.g., `pip install anthropic chromadb pydantic`)
- [ ] Environment variable setup instructions (ANTHROPIC_API_KEY at minimum)
- [ ] Any external services needed (databases, APIs) are either mocked or have free tier setup instructions
- [ ] Operating system assumptions stated (Windows/Mac/Linux, any WSL requirements)
- [ ] No package that requires paid subscription without stating it
- Flag: any dependency mentioned in code but NOT in the setup instructions

## PASS 3: Code Completeness — Can a Student Copy-Paste and Run?
For EVERY code block in the capstone:
- [ ] Complete imports at the top (no missing imports)
- [ ] No placeholder comments like "# ... implement here" or "// TODO" or "# rest of implementation"
- [ ] No undefined variables or functions referenced
- [ ] No hardcoded file paths that only work on the author's machine
- [ ] All API keys read from environment variables, never hardcoded
- [ ] Error handling present (try/except or try/catch)
- [ ] Expected output shown after the code block
- [ ] If code depends on a previous step's output, that dependency is explicit ("This uses the `chunks` variable from Step 1")
- Flag: any code block where a student pressing Ctrl+C → paste → Enter would get an error

## PASS 4: Mock Data Validation
- [ ] Mock data is provided (not "connect to your real database")
- [ ] Mock data files are included inline or with creation scripts
- [ ] Mock data is realistic enough to demonstrate the concept (not just `{"test": "data"}`)
- [ ] Mock data matches the schema referenced in code (field names, types, nesting)
- [ ] For UCC domain: uses realistic filing_number, debtor_name, secured_party_name, state_code, collateral_description fields
- [ ] For Healthcare domain: uses realistic CPT codes, ICD-10 codes, payer names
- [ ] For B2B domain: uses realistic PO numbers, SKUs, carrier tracking formats
- Flag: any mismatch between mock data schema and code that accesses it

## PASS 5: Step Sequence — Does the Order Work?
Walk through the capstone as a student would, step by step:
- [ ] Steps are numbered sequentially
- [ ] Each step's OUTPUT is the next step's INPUT (no gaps)
- [ ] No step requires running something that hasn't been created yet
- [ ] File creation order is correct (don't import a module before creating it)
- [ ] If there are multiple files, the creation order and directory structure are specified
- [ ] Each step has a "checkpoint" — how the student knows the step succeeded
- [ ] Expected terminal output or response shown for verification
- Flag: any step where a student following instructions exactly would get stuck

## PASS 6: Tool/Function Definitions — API Accuracy
- [ ] All Claude API calls use current Anthropic SDK format (anthropic.Anthropic(), client.messages.create())
- [ ] Tool definitions use correct JSON Schema format (type, properties, required)
- [ ] tool_use response handling matches current API format (stop_reason check, tool_use content block)
- [ ] tool_result message format is correct (role: "user", content with type: "tool_result")
- [ ] MCP server code uses current @modelcontextprotocol/sdk API (if applicable)
- [ ] No deprecated API patterns (old tool_use XML format, legacy completion endpoint)
- Flag: any API call that would return an error with the current Anthropic SDK

## PASS 7: Conceptual Accuracy
- [ ] Technical explanations are factually correct
- [ ] Architecture diagrams match the actual code implementation
- [ ] Claimed performance numbers are realistic (not "reduces hallucinations by 99%")
- [ ] Best practices match Anthropic's official documentation
- [ ] Anti-patterns are correctly identified (matches cert exam anti-patterns where applicable)
- [ ] Token counts and cost estimates are in the right ballpark
- Flag: any claim that contradicts Anthropic's documentation or established best practices

## PASS 8: Quiz/Assessment Accuracy
- [ ] Every quiz question has exactly ONE correct answer
- [ ] The correct answer is actually correct (verify against the module content)
- [ ] Wrong answers are plausible but clearly wrong (not trick questions)
- [ ] Wrong answer explanations accurately explain WHY they're wrong
- [ ] Questions test understanding, not memorization of arbitrary details
- [ ] At least 1 question requires applying knowledge to a new scenario (not just recall)
- Flag: any question where the "correct" answer is debatable or where a wrong answer could be argued as correct

## PASS 9: Student Experience Flow
Read through the entire capstone imagining you are a student with ONLY the knowledge from prerequisite modules:
- [ ] Is the difficulty progression smooth? (doesn't jump from easy to impossible)
- [ ] Are there enough "small wins" early to build confidence?
- [ ] If a student gets stuck, is there enough troubleshooting guidance?
- [ ] Common error messages are anticipated with solutions ("If you see 'ModuleNotFoundError: No module named chromadb', run: pip install chromadb")
- [ ] Stretch goals are clearly marked as OPTIONAL (student doesn't feel like they failed by skipping them)
- [ ] The final "What You Built" section makes the student feel accomplished
- [ ] Time estimate is realistic (not "30 minutes" for something that takes 3 hours)
- Flag: any point where a student would likely get frustrated or lost

## PASS 10: Domain-Specific Validation
For Healthcare Pre-Auth (Domain A):
- [ ] CPT and ICD-10 codes used are real and correctly formatted
- [ ] Clinical workflow makes medical sense (pre-auth → review → determination)
- [ ] HIPAA/PHI callouts present where patient data is handled
- [ ] No actual patient data — all mock data is clearly fictional

For B2B Ecommerce (Domain B):
- [ ] PO lifecycle stages are realistic (confirmed → in-production → shipped → delivered)
- [ ] Carrier tracking formats are plausible
- [ ] Pricing/contract logic makes business sense
- [ ] SLA calculations are correct

For UCC Data Engineering (Domain C):
- [ ] UCC filing types are correct (UCC-1, UCC-3 amendment/continuation/termination)
- [ ] State SOS data format descriptions are plausible
- [ ] Entity resolution logic makes sense
- [ ] Medallion Architecture layers (Bronze/Silver/Gold) are used correctly
- [ ] Lien risk scoring logic is reasonable

## FINAL REPORT

Generate a report with:
1. **Overall Status**: PASS / PASS WITH WARNINGS / NEEDS FIXES
2. **Pass Summary**: X of 10 passes clean, Y with warnings, Z with failures
3. **Critical Issues** (must fix before publishing):
   - Code that won't run
   - Missing dependencies
   - Wrong API format
   - Incorrect quiz answers
4. **Warnings** (should fix):
   - Missing checkpoints
   - Thin explanations
   - Missing error handling
5. **Suggestions** (nice to have):
   - Better mock data
   - Additional troubleshooting tips
   - Extra stretch goals
6. **Estimated Fix Time**: how long to address all critical issues

Ask: "Should I auto-fix the critical issues?"
