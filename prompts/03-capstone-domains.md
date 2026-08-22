TRACK 8: CAPSTONE PROJECTS — "Build Real Things"
--------------------------------------------------

MODULE 23: [M23] Capstone Project Series

All capstone projects are anchored in THREE real-world industry domains. Each project builds the SAME agent capability but applies it to all three domains, so learners see how patterns transfer across industries. The three domains are:

DOMAIN A — HEALTHCARE PRE-AUTHORIZATION
  Context: Health insurance prior authorization (pre-auth) is a process where providers must get
  approval from payers (insurance companies) before delivering certain services (surgeries, imaging,
  specialty drugs). It involves clinical criteria matching, CPT/ICD-10 code validation, medical
  necessity determination, and multi-party communication between providers, payers, and patients.
  Key data: CPT codes, ICD-10 diagnosis codes, payer policy documents, clinical guidelines (MCG,
  InterQual), formulary lists, provider network status, patient benefit summaries.
  Why it's great for agents: Multi-step decision logic, document retrieval (RAG on policy docs),
  structured output (auth request forms), human-in-the-loop (clinical reviewer approval), strict
  guardrails (HIPAA, PHI handling), and real cost/time pressure.

DOMAIN B — B2B ECOMMERCE ORDER TRACKING
  Context: B2B ecommerce involves complex order lifecycles — RFQ (Request for Quote), PO (Purchase
  Order) creation, multi-warehouse fulfillment, partial shipments, carrier tracking, invoicing,
  returns/RMAs, and contract pricing. Unlike B2C, B2B orders have approval workflows, net payment
  terms, volume discounts, and multi-stakeholder communication.
  Key data: SKUs, PO numbers, carrier tracking APIs (FedEx/UPS/DHL), warehouse management system
  (WMS) data, ERP order status, invoice/payment records, customer contract terms, SLA commitments.
  Why it's great for agents: Multi-tool orchestration (ERP + WMS + carrier APIs), real-time status
  aggregation, proactive alerting (delayed shipments), multi-agent handoffs (sales → fulfillment →
  support), and production-grade observability needs.

DOMAIN C — PUBLIC RECORDS / UCC DATA ENGINEERING
  Context: UCC (Uniform Commercial Code) filings are public records filed with US Secretaries of
  State documenting secured commercial transactions (liens on business assets). They are used in
  commercial credit risk profiling, due diligence, and lien risk assessment. The data pipeline
  involves ingesting bulk filing data from 50+ state SOS offices, normalizing inconsistent formats,
  entity resolution (matching debtor/secured party names across filings), and building risk profiles.
  Key data: UCC-1 financing statements, UCC-3 amendments/continuations/terminations, debtor and
  secured party names/addresses, collateral descriptions, filing dates, lapse dates, SOS bulk
  download files (CSV, fixed-width, XML varying by state).
  Why it's great for agents: Data engineering pipeline orchestration (PySpark, BigQuery, Medallion
  Architecture), RAG on legal/regulatory reference docs, entity resolution as a multi-step reasoning
  task, planning agents for complex ETL workflows, and evaluation/testing on data quality metrics.


DOMAIN A-BH — BEHAVIORAL HEALTH UTILIZATION MANAGEMENT  [VARIANT OF DOMAIN A]
  Status: NOT one of the three primary domains. A variant of Domain A used by CAPSTONE-9, and
  available to any future module that wants a healthcare domain the clinical material does not
  already cover. The A/B/C triad above is unchanged.

  Context: Behavioral health prior authorization. For thirty years payers CARVED OUT behavioral
  health to a separate vendor with its own provider network, its own clinical criteria, its own
  claims platform, and — crucially — its own member identifiers. Plans are now in-sourcing it, which
  is why the domain shows up as a migration problem rather than a greenfield one.

  Key data: ASAM levels 0.5–4.0 scored across six dimensions; LOCUS/CALOCUS for psychiatric
  placement; CPT 90791/90792/90832/90834/90837/90853; ABA 97151–97158; HCPCS H0015/H0018/H0019/
  H0035/H2036/S9480; ICD-10 chapter F (F10–F19 substance use, F20–F49 psychiatric); PHQ-9, GAD-7,
  C-SSRS instrument scores; 42 CFR Part 2 consents; X12 278 review requests.

  FOUR THINGS THAT MAKE IT DIFFERENT FROM DOMAIN A, and every one of them breaks an assumption a
  clinical prior-auth system is built on:

  1. THE CRITERIA ARE A LADDER, NOT A YES/NO. Medical asks "is this procedure necessary for this
     diagnosis?" Behavioral health asks "at what INTENSITY should this person be treated right
     now?" — a rung chosen from six independently scored dimensions. An engine that can only
     approve or deny the level that was REQUESTED is missing the domain.
     Watch dimension 4: readiness to change INVERTS. A low score argues AGAINST residential
     placement, because placement without engagement produces an AMA discharge inside 72 hours.
     Treat all six as severity indicators and you get it backwards, plausibly.

  2. AUTHORIZATION IS A SERIES, NOT AN EVENT. Concurrent review: an initial determination plus
     recurring continued-stay reviews on a cadence set by level of care — 3 days at ASAM 4.0,
     7 at 3.5, 14 at PHP. The cadence follows the LEVEL, not the units approved. A next-review
     date is a REGULATORY DEADLINE, not a reminder. Approval is not terminal.

  3. TWO PRIVACY REGIMES. HIPAA plus 42 CFR Part 2 for records from federally assisted SUD
     treatment programs. Part 2 requires a consent that NAMES the recipient, states a purpose and
     scope, expires, and carries a redisclosure notice — plus an accounting of disclosures. A
     system can be fully HIPAA-compliant and violate Part 2 on every request, and the failure is
     almost always plumbing rather than policy.

  4. PARITY IS A DESIGN CONSTRAINT. MHPAEA: a limitation applied to BH may be no more restrictive
     than the comparable med/surg limitation. The hard ones are non-quantitative — review
     frequency, step therapy, criteria strictness, network standards. These appear in legacy code
     as rules that look reasonable in isolation. Neither port them silently nor drop them silently.

  THE REVIEWER-LICENSURE RULE (load-bearing, and easy to lose in a port):
    A nurse may approve. A nurse may NEVER deny. Only a physician may issue an adverse
    determination — and for SUD or psychiatric level of care, a SAME-SPECIALTY peer reviewer.
    This is why a PENDED status exists at all: it is the state a case waits in for someone
    licensed to deny it.

  Why it's great for agents: every one of the four differences above is a place where a
  well-built general system has no answer, so the agent's job becomes DETECTING INSUFFICIENCY
  rather than translating. Plus a hard "no PHI in prompts, ever" constraint that forces the
  question of how you point an agent at a regulated codebase without feeding it regulated data.

  Generator note: all fixtures for this domain MUST be synthetic, generated from a documented
  seed, and clearly fictional. Codes are real and correctly formatted; the people are not. Any
  Part 2 or parity behaviour is an EDUCATIONAL MODEL and must carry a "not legal advice" note.


CAPSTONE PROJECT 1: [CAPSTONE-1] "First Agent" — Single-Tool Conversational Assistant
  Difficulty: ★☆☆☆☆
  Skills practiced: Tool use basics (M05), conversation management (M08), structured output (M04)
  
  Domain A — Pre-Auth Status Checker:
    Build an agent that takes a pre-auth reference number, calls a mock payer API tool to retrieve
    status (approved/pending/denied/info-requested), and responds in natural language with next steps.
    Tool: get_preauth_status(reference_id) → returns status, clinical reviewer notes, timeline
    Stretch: Add a second tool to look up CPT code descriptions
  
  Domain B — Order Status Bot:
    Build an agent that takes a PO number, calls a mock ERP tool to retrieve order status (confirmed/
    in-production/shipped/delivered/invoiced), and provides a natural language summary with ETAs.
    Tool: get_order_status(po_number) → returns line items, shipment status, tracking numbers
    Stretch: Add a carrier tracking tool for shipment-level detail
  
  Domain C — UCC Filing Lookup Agent:
    Build an agent that takes a business name, calls a mock SOS search tool to retrieve active UCC
    filings, and summarizes the lien exposure in plain English.
    Tool: search_ucc_filings(business_name, state) → returns filing list with secured parties,
    collateral descriptions, filing/lapse dates
    Stretch: Add a tool to check filing amendment history


CAPSTONE PROJECT 2: [CAPSTONE-2] "Knowledge Agent" — RAG-Powered Domain Expert
  Difficulty: ★★☆☆☆
  Skills practiced: RAG pipeline (M09-M10), embeddings, chunking, vector search, citations
  
  Domain A — Clinical Policy Q&A System:
    Build a RAG agent that ingests payer clinical policy documents (medical necessity criteria for
    common procedures like MRI, knee replacement, specialty drugs) and answers provider questions
    like "Is prior auth required for CPT 27447 under Aetna?" with cited policy references.
    Data: 10-15 mock payer policy PDFs with clinical criteria, covered codes, exclusions
    Stretch: Add hybrid search (keyword + semantic) for CPT/ICD code lookups
  
  Domain B — Product Catalog & Contract Q&A:
    Build a RAG agent that ingests B2B product catalogs and customer contract documents, then answers
    questions like "What's the contract price for SKU-4892 for Acme Corp?" or "What's the lead time
    for bulk orders of industrial bearings?"
    Data: Mock product catalog with specs/pricing, 5 customer contracts with volume tiers and terms
    Stretch: Add re-ranking to prioritize contract-specific answers over general catalog info
  
  Domain C — UCC Regulatory Reference Agent:
    Build a RAG agent that ingests UCC Article 9 reference materials, state-specific filing guides,
    and a UCC data dictionary, then answers questions like "What happens when a UCC-1 lapses?" or
    "How does a UCC-3 termination affect the secured party's priority?"
    Data: UCC Article 9 plain-English guide, state filing handbooks, collateral classification guide
    Stretch: Add query transformation (HyDE) for legal terminology normalization


CAPSTONE PROJECT 3: [CAPSTONE-3] "Reasoning Agent" — ReAct Multi-Step Problem Solver
  Difficulty: ★★★☆☆
  Skills practiced: ReAct loop (M12), multi-tool orchestration (M06), planning (M13)
  
  Domain A — Pre-Auth Decision Support Agent:
    Build a ReAct agent that takes a pre-auth request (procedure, diagnosis, patient info) and
    reasons through the decision: (1) look up clinical criteria for the procedure, (2) match patient
    diagnosis against criteria, (3) check provider network status, (4) verify patient benefit
    coverage, (5) generate a structured recommendation (approve/deny/request-more-info) with
    clinical justification. Agent must "think out loud" at each step.
    Tools: lookup_clinical_criteria, verify_diagnosis_match, check_network_status,
    get_benefit_summary, generate_auth_recommendation
    Stretch: Add a "peer-to-peer review" escalation path for edge cases
  
  Domain B — Order Exception Resolution Agent:
    Build a ReAct agent that investigates order exceptions: (1) identify the exception type (delayed
    shipment, partial delivery, pricing discrepancy, quality hold), (2) gather data from relevant
    systems (ERP, WMS, carrier), (3) determine root cause, (4) propose resolution with customer
    communication draft. Agent reasons through each diagnostic step.
    Tools: get_order_details, query_warehouse_inventory, track_shipment, get_contract_pricing,
    check_quality_hold_status, draft_customer_notification
    Stretch: Add a cost-impact calculator tool for exception resolution options
  
  Domain C — Entity Resolution Agent:
    Build a ReAct agent that takes a business entity name and resolves it across UCC filings:
    (1) search filings across multiple states, (2) identify name variations (abbreviations, DBAs,
    misspellings), (3) score match confidence using fuzzy matching, (4) merge results into a
    unified entity profile with total lien exposure. Agent reasons about which matches are true
    positives vs. false positives.
    Tools: search_filings_by_name, fuzzy_match_score, get_filing_details, get_business_registry_data,
    merge_entity_profile
    Stretch: Add a tool that checks SOS business entity registration to validate entity existence


CAPSTONE PROJECT 4: [CAPSTONE-4] "Agent Team" — Multi-Agent Pipeline with Human-in-the-Loop
  Difficulty: ★★★★☆
  Skills practiced: Multi-agent (M14), HITL (M17), guardrails (M16-M17), evaluation (M18)
  
  Domain A — End-to-End Pre-Auth Processing Pipeline:
    Build a multi-agent system:
    Agent 1 — Intake Agent: Parses incoming pre-auth request (structured or freetext), extracts
    CPT codes, ICD-10 codes, provider NPI, patient ID. Input guardrails: PII detection, schema
    validation.
    Agent 2 — Clinical Criteria Agent: RAG-powered lookup of payer policies, matches clinical
    criteria, generates preliminary determination with confidence score.
    Agent 3 — Decision Agent: Reviews Agent 2's determination. If confidence > 90%, auto-approves.
    If 70-90%, routes to HITL clinical reviewer with summary. If < 70%, auto-denies with appeal
    instructions.
    Agent 4 — Communication Agent: Generates provider notification (approval letter / denial with
    clinical rationale / info-request letter). Output guardrails: HIPAA compliance check, tone
    validation, format verification.
    Human-in-the-Loop: Clinical reviewer dashboard for medium-confidence cases — approve, deny,
    modify, or escalate.
    Circuit Breaker: If > 3 consecutive processing failures, halt pipeline and alert ops team.
  
  Domain B — B2B Order Lifecycle Management Pipeline:
    Build a multi-agent system:
    Agent 1 — Order Intake Agent: Parses incoming POs (EDI 850, email, portal submission), extracts
    line items, validates against product catalog and contract pricing. Input guardrails: schema
    validation, duplicate PO detection.
    Agent 2 — Fulfillment Planning Agent: Checks inventory across warehouses, determines optimal
    fulfillment strategy (single vs. split shipment), calculates ETAs.
    Agent 3 — Exception Monitor Agent: Continuously monitors order status, detects anomalies
    (delayed carrier pickup, inventory shortfall, quality hold), triggers resolution workflows.
    Agent 4 — Customer Communication Agent: Generates proactive status updates, exception
    notifications, and delivery confirmations. Output guardrails: SLA compliance check, contract
    terms verification, tone matching per customer tier.
    Human-in-the-Loop: Operations manager approval for split shipments over $50K or exception
    resolutions involving credit issuance.
    Circuit Breaker: If carrier API fails > 5 times in 10 minutes, switch to fallback polling mode.
  
  Domain C — UCC Data Pipeline Orchestration System:
    Build a multi-agent system:
    Agent 1 — Ingestion Agent: Monitors state SOS data drops, detects new files, validates format
    (CSV, fixed-width, XML), triggers appropriate parser. Input guardrails: file integrity checks,
    schema validation per state format.
    Agent 2 — Transformation Agent: Normalizes data across state formats into Medallion Architecture
    layers (Bronze → Silver → Gold), handles entity resolution, deduplication, collateral
    classification.
    Agent 3 — Quality Agent: Runs data quality checks (completeness, consistency, freshness),
    generates quality scorecards, flags anomalies (e.g., a state's filing count drops 80% — is it
    a real trend or a data feed issue?).
    Agent 4 — Reporting Agent: Generates risk profiles, lien summaries, and portfolio exposure
    reports. Output guardrails: PII redaction for public-facing reports, data accuracy verification.
    Human-in-the-Loop: Data steward review for entity resolution conflicts with confidence < 80%
    and quality anomalies flagged by Agent 3.
    Circuit Breaker: If a state data feed produces > 10% parse errors, quarantine the batch and
    alert the data engineering team.


CAPSTONE PROJECT 5: [CAPSTONE-5] "Production Agent" — Autonomous System with Full Observability
  Difficulty: ★★★★★
  Skills practiced: ALL modules — this is the comprehensive integration project
  
  This capstone combines everything: planning (M13), multi-layer memory (M11), multi-agent (M14),
  RAG (M09-M10), guardrails (M16-M17), HITL (M17), evaluation (M18), tracing (M19), monitoring
  (M20), deployment (M21), and cost optimization (M22).
  
  Pick ONE domain (A, B, or C) and build the PRODUCTION VERSION:
  
  Domain A — Autonomous Pre-Auth Processing System:
    Everything from CAPSTONE-4 Domain A, PLUS:
    - Multi-layer memory: Working memory for current case, episodic memory for similar past cases
      (retrieve past approvals/denials for similar procedure+diagnosis combos), procedural memory
      for learned payer-specific quirks
    - Advanced RAG: Hybrid search on clinical policies with re-ranking and contextual compression
    - Full observability: Trace every LLM call, tool call, and decision point; dashboard showing
      approval rates, average processing time, escalation rates, cost per auth
    - Cost optimization: Route simple lookups to Haiku, complex clinical reasoning to Opus,
      cache frequently accessed policy sections
    - Deployment: Containerized API with streaming responses, queue-based processing for batch
      submissions, webhook notifications for status changes
    - Evaluation harness: 100-case test suite covering approvals, denials, edge cases, adversarial
      inputs (prompt injection via freetext clinical notes)
  
  Domain B — Autonomous B2B Order Management System:
    Everything from CAPSTONE-4 Domain B, PLUS:
    - Multi-layer memory: Working memory for active orders, episodic memory for customer interaction
      history (retrieve past exception resolutions for same customer), procedural memory for learned
      carrier-specific handling procedures
    - Advanced RAG: Hybrid search on product catalogs + contract terms with customer-specific re-ranking
    - Full observability: Trace every order lifecycle event; dashboard showing fulfillment rates,
      exception frequency by type, average resolution time, SLA compliance, cost per order processed
    - Cost optimization: Route status checks to Haiku, exception analysis to Sonnet, complex
      multi-party resolutions to Opus; cache product catalog lookups
    - Deployment: Containerized API with WebSocket for real-time order status, event-driven
      architecture with Pub/Sub for order state changes, ERP integration via webhooks
    - Evaluation harness: 100-order test suite covering normal flow, split shipments, exceptions,
      pricing disputes, and adversarial inputs (SQL injection via PO notes fields)
  
  Domain C — Autonomous UCC Data Engineering Platform:
    Everything from CAPSTONE-4 Domain C, PLUS:
    - Multi-layer memory: Working memory for current pipeline run state, episodic memory for past
      pipeline runs (retrieve how similar data quality issues were resolved), procedural memory for
      state-specific parsing quirks learned over time
    - Advanced RAG: Hybrid search on UCC regulatory docs + state filing guides with jurisdiction-
      specific re-ranking
    - Full observability: Trace every pipeline stage; dashboard showing records processed per state,
      entity resolution confidence distribution, data quality trends, pipeline latency, cost per
      record
    - Cost optimization: Route simple format validation to Haiku, entity resolution reasoning to
      Sonnet, complex collateral classification to Opus; cache state format schemas
    - Deployment: Containerized pipeline on GCP (Cloud Run + Cloud Composer/Airflow), event-driven
      triggers on GCS file drops, BigQuery integration for Gold layer analytics
    - Evaluation harness: 100-filing test suite covering clean filings, edge cases (missing fields,
      ambiguous collateral descriptions, name variations), multi-state entity resolution, and
      adversarial inputs (malformed CSV injections)
