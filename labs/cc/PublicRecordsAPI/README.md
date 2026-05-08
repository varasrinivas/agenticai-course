# PublicRecords API — Claude Code Course Lab Project

A small Spring Boot REST API serving US **UCC (Uniform Commercial Code) lien filings**. Used as the running example across the 8-module Claude Code track (CC0 → CC7). Each module's hands-on lab extends, secures, automates, or ships this same project.

## Stack

- Java 21, Spring Boot 3.3
- Spring Web + Spring Data JPA + Bean Validation
- H2 in-memory database, seeded from `src/main/resources/data.sql`

## Run

```bash
mvn spring-boot:run
```

Then in another terminal:

```bash
curl http://localhost:8080/filings
curl http://localhost:8080/filings/1
curl "http://localhost:8080/filings?state=TX"
```

H2 console: http://localhost:8080/h2 — JDBC URL `jdbc:h2:mem:ucc`, user `sa`, no password.

## Test

```bash
mvn test
```

## Lab Index

| Module | What you'll add |
| --- | --- |
| CC0 | Run this project, ask Claude to map the codebase |
| CC1 | `CLAUDE.md` with UCC glossary + security rules |
| CC2 | `.claude/settings.json` with permission tiers |
| CC3 | `/new-resource` slash command for scaffolding |
| CC4 | `pii-auditor` subagent (Read + Grep only) |
| CC5 | `PostToolUse` hook running `mvn spotless:check` |
| CC6 | Postgres MCP server connected to UCC schema |
| CC7 | GitHub Action running Claude Code in headless mode |

## Project Layout

```
src/main/java/com/publicrecords/api/
  PublicRecordsApiApplication.java   # @SpringBootApplication entry point
  filing/
    Filing.java                      # JPA entity for a UCC-1 filing
    FilingRepository.java            # Spring Data JPA repository
    FilingController.java            # GET /filings, GET /filings/{id}
  common/
    Pii.java                         # mask() helper for SSN / EIN / DOB
src/main/resources/
  application.yml                    # H2 + JPA config
  data.sql                           # seed data: 8 filings across 6 states
src/test/java/com/publicrecords/api/filing/
  FilingControllerTest.java          # MockMvc smoke tests
```

## Domain Glossary

- **UCC-1 filing** — a public lien notice filed at a state secretary-of-state to perfect a security interest in collateral.
- **Debtor** — the party whose assets are encumbered (e.g., a borrowing business).
- **Secured Party** — the lender holding the lien (e.g., a bank or equipment finance company).
- **Collateral** — the assets covered by the filing. Can be specific (a VIN, a piece of equipment) or blanket (all inventory and receivables).
- **Filed at / expires at** — UCC-1 filings lapse after 5 years unless continued.

## Security Rules (enforced by CC1's CLAUDE.md and CC4's pii-auditor)

- Never log raw SSN, EIN, or DOB. Use `Pii.mask()` instead.
- Never commit `application-prod.yml` or any file containing real PII.
- All `@RestController` endpoints that accept user input must use `@Valid`.

## Prerequisites

- JDK 21 (`java -version` should show 21.x). On Windows: `winget install Microsoft.OpenJDK.21`.
- Maven 3.9+ (`mvn -v`). On Windows: `winget install Apache.Maven`.
- Claude Code CLI: `npm install -g @anthropic-ai/claude-code`, then `claude login`.
