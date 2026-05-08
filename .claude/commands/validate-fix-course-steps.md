---
description: Walks through the hands-on steps inside the course HTML like a learner following instructions. Validates every command, code block, config, and expected output in the PHASES content. Fixes wrong steps directly in the HTML.
argument-hint: COURSE_SLUG e.g. ai-sdlc-data-engineering
---

Open output/$ARGUMENTS.html and walk through every phase like a learner following the steps.


For EACH phase in the PHASES JSON, walk through every section in order:

CHECK 1 STEP SEQUENCE: When an explain section says "first do X then do Y" followed by a code section, does the code actually do X then Y in that order? If the text says "start by reading Bronze data" but the code starts with a write operation, fix the text or the code so they match.

CHECK 2 CODE RUNS AFTER PREVIOUS STEP: Does each code section assume something created by a previous code section? Trace the data flow: if Phase 02 code reads from bronze_filings table, was that table created in Phase 01 code? If Phase 04 code imports a function defined in Phase 03 code, is that import correct? Fix any broken references.

CHECK 3 COMMANDS ARE CORRECT: For every bash or shell command shown in the course (pip install, docker run, mvn compile, npm run, curl commands) verify: the package names are real, the flags are valid, the URLs are correct, the file paths match files created in earlier steps. Fix wrong commands.

CHECK 4 CONFIG IS COMPLETE: For every config section (YAML, JSON, properties files) verify: all required fields are present, values are consistent with the code that uses them, no placeholder values like YOUR_VALUE_HERE unless explicitly noted. Fix incomplete configs.

CHECK 5 EXPECTED OUTPUT IS ACCURATE: When the course shows expected output after a code section, verify: the record counts match (50 bronze, 41 silver, 12 gold entities), the entity names match the 5 canonical entities, the risk scores match the formula, the error messages are realistic. Fix wrong output.

CHECK 6 INSTRUCTIONS ARE FOLLOWABLE: Read each explain section as a first-time learner. Can you follow every instruction without ambiguity? Flag and fix: instructions that say "configure the X" without showing how. References to "the file we created earlier" without naming which file. Steps that skip from A to C without B. Assumptions about tools being installed without mentioning prerequisites.

CHECK 7 CODE ANNOTATIONS MATCH CODE: When an explain section says "notice line 4 does X" verify that line 4 of the following code section actually does X. Fix wrong line references or wrong descriptions.

Fix every issue using str_replace directly in the PHASES JSON content fields of output/$ARGUMENTS.html. Do NOT touch the CSS or JS engine.

After all fixes verify the PHASES JSON still parses.

Report per phase:
| Phase | Steps Checked | Issues Found | Issues Fixed |
