# Capstone 2: Knowledge Agent -- RAG-Powered Domain Expert

Build a Retrieval-Augmented Generation (RAG) agent that ingests domain documents,
stores them in a vector database, retrieves relevant passages at query time, and
answers questions with inline citations.

## What You'll Build

A conversational knowledge agent that:

1. Loads and parses domain-specific reference documents
2. Chunks documents into overlapping segments for retrieval
3. Embeds chunks and stores them in ChromaDB (a local vector database)
4. Accepts natural-language questions
5. Retrieves the most relevant chunks via vector similarity search
6. Sends the retrieved context to Claude for answer generation
7. Returns answers with inline citations pointing back to source documents

**Difficulty:** 2 out of 5 stars -- Intermediate

**Skills practiced:**
- Document ingestion and text chunking (M09-M10)
- Vector embeddings and similarity search (M10)
- RAG pipeline architecture (M10)
- Prompt engineering with retrieved context (M03-M04)
- Conversation management (M08)

### Choose Your Domain

| Domain | Directory | Description |
|--------|-----------|-------------|
| **A -- Healthcare** | `domain-a-healthcare/` | Clinical policy Q&A -- ingest payer policy docs, answer coverage questions with cited policy references |
| **B -- Ecommerce** | `domain-b-ecommerce/` | Product catalog and contract Q&A -- answer pricing, availability, and contract-term questions |
| **C -- UCC / Public Records** | `domain-c-ucc/` | UCC regulatory reference agent -- answer filing procedure and collateral classification questions |

Pick **one** domain to complete the capstone. All three share the same architecture;
only the documents and sample queries differ.

## Prerequisites

- Modules M01 through M10 completed
- Python 3.10+ installed
- An Anthropic API key (set as `ANTHROPIC_API_KEY` environment variable)
- `chromadb` and `anthropic` Python packages installed

## Setup

```bash
# Navigate into your chosen domain
cd labs/capstone-2-knowledge-agent/domain-a-healthcare  # or domain-b / domain-c

# Install dependencies (from the starter/ directory)
pip install -r starter/requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Lab Instructions (Generic Steps)

Work through these six steps in order. Each step corresponds to code you will
write (or complete) in the `starter/` directory. Reference the `solution/`
directory only if you get stuck.

### Step 1: Load Documents

Open `starter/loader.py`. Your job:

- Read every `.md` file from the `docs/` directory
- Return a list of dictionaries, each containing:
  - `filename` -- the name of the source file
  - `content` -- the full text of the file
- Handle missing directories and empty files gracefully

**Checkpoint:** Run `python loader.py` and verify it prints the filename and
character count for every document.

### Step 2: Chunk Documents with Overlap

Open `starter/chunker.py`. Your job:

- Accept a document dict (from Step 1) and split its content into chunks
- Each chunk should be approximately `chunk_size` characters (default 1000)
- Consecutive chunks must overlap by `overlap` characters (default 200)
- Attach metadata to each chunk: `source` (filename) and `chunk_index`

**Checkpoint:** Run `python chunker.py` and verify it prints chunk counts per
document and the first chunk of the first document.

### Step 3: Create Embeddings and Store in ChromaDB

This step happens inside `starter/rag_agent.py`. Your job:

- Initialize a ChromaDB client (persistent or in-memory)
- Create (or get) a collection
- For every chunk, add it to the collection with its text, metadata, and a
  unique ID (e.g., `{filename}_{chunk_index}`)
- ChromaDB's default embedding function handles vectorization automatically

**Checkpoint:** After indexing, print the total number of items in the
collection. It should match your total chunk count from Step 2.

### Step 4: Build the RAG Query Pipeline

Still in `starter/rag_agent.py`:

- Accept a user question as input
- Query the ChromaDB collection for the top-k most similar chunks (k=5)
- Assemble a context block from the retrieved chunks
- Send the context + question to Claude using the Messages API
- Return the raw response text

**Checkpoint:** Ask a simple factual question and verify you get a relevant
answer.

### Step 5: Add Citation Formatting

Enhance the pipeline so every answer includes inline citations:

- In the system prompt, instruct Claude to cite sources using the format
  `[Source: filename, Section: ...]`
- Pass the source metadata alongside each chunk in the context block
- Verify that the response includes at least one citation

**Checkpoint:** Ask a question and confirm the response contains bracketed
source references.

### Step 6: Build the Conversational Agent Loop

Wrap everything in an interactive loop:

- Print a welcome message explaining the agent's domain
- Accept user input in a loop
- Maintain conversation history so follow-up questions work
- Support special commands: `quit` to exit, `sources` to list loaded documents
- Handle errors gracefully (API failures, empty queries)

**Checkpoint:** Have a multi-turn conversation. Ask a question, then ask a
follow-up that references the previous answer. Verify the agent maintains
context.

---

## Running Tests

Each domain includes a `tests/` directory with unit tests for the loader and
chunker components. Tests do not require an API key -- they exercise only the
local pipeline code.

```bash
# From the domain directory (e.g., domain-a-healthcare/)
pip install pytest
pytest tests/test_rag.py -v
```

The tests validate:
- All expected documents are loaded from `docs/`
- Document dicts have the correct keys (`filename`, `content`)
- Chunk counts are correct for known input sizes
- Chunk metadata (`source`, `chunk_index`) is set properly
- Empty and whitespace-only documents produce no chunks
- Overlap between consecutive chunks is exact
- All content characters are covered by at least one chunk

---

## Lab Instructions -- Domain A: Clinical Policy Q&A

### Step 1: Understand the Healthcare Documents

**What:** Open the `docs/` directory and browse the five clinical policy documents:

| File | Content |
|------|---------|
| `policy_cardiac_cath.md` | Cardiac catheterization coverage criteria |
| `policy_knee_replacement.md` | Total knee replacement pre-authorization requirements |
| `policy_mri_brain.md` | Brain MRI medical necessity criteria |
| `policy_physical_therapy.md` | Physical therapy visit limits and authorization tiers |
| `policy_specialty_drugs.md` | Specialty drug prior authorization and step therapy rules |

These documents simulate real payer policies. Each one defines when a procedure or treatment is considered medically necessary, what documentation is required, and what the exclusion criteria are.

**Run:**

```bash
cd domain-a-healthcare
python solution/loader.py
```

**Expected output:** 5 documents loaded, each showing a filename and character count (typically 3,000-8,000 chars per policy).

**Checkpoint:** Can you describe the general structure of a policy document? (Hint: look for sections like "Medical Necessity Criteria", "Required Documentation", "Exclusions".)

---

### Step 2: Chunk the Clinical Policies

**Why this matters for healthcare:** Policy documents have dense, nested criteria (e.g., "at least 3 of 5 conservative treatments over a minimum of 3 months"). If your chunks are too small, you will split a criterion across two chunks and lose context. If chunks are too large, retrieval becomes noisy. The default 1000-char chunks with 200-char overlap are a good starting point for these documents.

**Run:**

```bash
python solution/chunker.py
```

**Checkpoint:** Verify that each document produces multiple chunks. A typical policy document at ~5000 characters should produce roughly 6-7 chunks with chunk_size=1000 and overlap=200.

---

### Step 3-5: Build and Test the RAG Pipeline

**Sample queries to test with (from `expected_output/sample_queries.txt`):**

1. `"What are the medical necessity criteria for a brain MRI without contrast?"`
   - Should cite `policy_mri_brain.md` and list multiple indication categories (headache, seizures, cognitive decline, stroke, trauma).

2. `"What conservative treatments are required before a total knee replacement can be authorized?"`
   - Should cite `policy_knee_replacement.md` and list 5 conservative treatments (pharmacotherapy, PT, injections, activity modification, assistive devices).

3. `"Does the specialty drug policy require step therapy for adalimumab?"`
   - Should cite `policy_specialty_drugs.md` and mention biosimilar step therapy (Hadlima, Hyrimoz, Cyltezo).

4. `"How many physical therapy visits are covered after ACL reconstruction?"`
   - Should cite `policy_physical_therapy.md` and mention 36 visits over 6 months with phased protocol.

**Expected output format:**

```
According to the clinical policy, MRI of the brain without contrast
(CPT 70551) is considered medically necessary for the following
indications:

1. Headache -- new-onset severe headache with neurological deficits...
   [Source: policy_mri_brain.md, Chunk 2]

2. Seizures -- new-onset seizure in adults...
   [Source: policy_mri_brain.md, Chunk 3]
```

---

### Step 6: Conversational Healthcare Agent

**Domain-specific guidance:**

- The welcome message should identify the agent as a clinical policy reference assistant.
- Warn users that the agent provides policy reference information only, not medical advice.
- When a user asks about a procedure not covered in the documents, the agent should say so explicitly rather than guessing.

**Multi-turn test sequence:**

1. Ask: `"What are the criteria for a brain MRI?"`
2. Follow up: `"What about for seizures specifically?"`
3. Follow up: `"Is that different for pediatric patients?"`

The agent should use conversation history to understand that questions 2 and 3 still refer to the brain MRI policy.

---

### Domain A Checkpoint Criteria

- [ ] Loader finds all 5 policy documents
- [ ] Chunker produces 20+ total chunks across all documents
- [ ] RAG retrieves relevant policy chunks for clinical questions
- [ ] Answers include citations like `[Source: policy_mri_brain.md, Chunk 2]`
- [ ] Agent correctly refuses questions outside the policy scope
- [ ] Follow-up questions maintain context about the procedure being discussed
- [ ] All `pytest tests/test_rag.py` tests pass

### Domain A Edge Cases to Test

- Ask about a procedure not in any policy (e.g., `"Is LASIK eye surgery covered?"`) -- agent should say it has no policy information for that procedure.
- Ask a vague question (e.g., `"Tell me about drugs"`) -- agent should ask for clarification or provide a broad answer citing `policy_specialty_drugs.md`.
- Ask a question that spans two policies (e.g., `"After a knee replacement, how many PT visits are covered?"`) -- agent should pull from both `policy_knee_replacement.md` and `policy_physical_therapy.md`.

---

## Lab Instructions -- Domain B: Product Catalog & Contract Q&A

### Step 1: Understand the Ecommerce Documents

**What:** Open the `docs/` directory and browse the five ecommerce documents:

| File | Content |
|------|---------|
| `contract_acme_corp.md` | Platinum-tier contract: 22% fastener discount, Net 60, consignment terms |
| `contract_globex_industries.md` | Gold-tier contract: discount tiers, Net 45, early payment terms |
| `contract_initech_solutions.md` | Silver-tier contract: volume-based discounts, Net 30, credit limit |
| `product_catalog.md` | Full product catalog with SKUs, list prices, case quantities |
| `shipping_policies.md` | Shipping methods, return policies, hazmat rules, restocking fees |

These documents simulate a B2B industrial supply company. The contracts define customer-specific pricing, payment terms, and special arrangements (like consignment inventory). The product catalog and shipping policies apply to all customers.

**Run:**

```bash
cd domain-b-ecommerce
python solution/loader.py
```

**Expected output:** 5 documents loaded with their character counts.

**Checkpoint:** Can you identify which customers have which contract tiers (Platinum, Gold, Silver)?

---

### Step 2: Chunk the Ecommerce Documents

**Why this matters for ecommerce:** Contract documents mix general terms with customer-specific pricing tables. A chunk that splits a pricing table in half will produce poor retrieval results. The 200-character overlap helps ensure table rows stay connected to their column headers.

**Run:**

```bash
python solution/chunker.py
```

**Checkpoint:** The product catalog is typically the largest document. Verify it produces more chunks than the individual contracts.

---

### Step 3-5: Build and Test the RAG Pipeline

**Sample queries to test with (from `expected_output/sample_queries.txt`):**

1. `"What is the price for 1/2 inch Grade 5 hex bolts, and what discount does Acme Corporation get?"`
   - Should cite both `product_catalog.md` (list price $0.58/unit) and `contract_acme_corp.md` (22% discount).

2. `"What are the payment terms for Initech Solutions, and do they get an early payment discount?"`
   - Should cite `contract_initech_solutions.md` (Net 30, no early payment discount) and optionally compare with other tiers.

3. `"What items does Acme keep on consignment, and how does the replenishment work?"`
   - Should cite `contract_acme_corp.md` and list the consignment items with reorder triggers.

4. `"Can I return opened safety glasses? What is the return policy?"`
   - Should cite `shipping_policies.md` (no returns on opened safety equipment due to hygiene policy).

**Expected output format:**

```
The list price for 1/2"-13 x 2" Grade 5 Hex Bolts (SKU: FB-HX5-0500)
is $0.58 per unit, or $24.65 per case of 50 units.
[Source: product_catalog.md, Chunk 1]

Acme Corporation receives a 22% discount on Industrial Fasteners per
their Platinum contract...
[Source: contract_acme_corp.md, Chunk 2]
```

---

### Step 6: Conversational Ecommerce Agent

**Domain-specific guidance:**

- The welcome message should identify the agent as a B2B product and contract reference assistant.
- Clarify that pricing shown is list pricing unless a specific customer contract is referenced.
- When a customer name is mentioned, the agent should look up their contract terms.

**Multi-turn test sequence:**

1. Ask: `"What does Acme Corporation pay for hex bolts?"`
2. Follow up: `"What about their payment terms?"`
3. Follow up: `"How does that compare to Globex?"`

The agent should maintain that the conversation is about Acme, then compare with Globex when asked.

---

### Domain B Checkpoint Criteria

- [ ] Loader finds all 5 ecommerce documents
- [ ] Chunker produces 20+ total chunks across all documents
- [ ] RAG retrieves relevant chunks for pricing and contract questions
- [ ] Answers include citations like `[Source: contract_acme_corp.md, Chunk 2]`
- [ ] Agent correctly cross-references catalog prices with contract discounts
- [ ] Follow-up questions maintain context about the customer being discussed
- [ ] All `pytest tests/test_rag.py` tests pass

### Domain B Edge Cases to Test

- Ask about a product not in the catalog (e.g., `"Do you sell welding equipment?"`) -- agent should say it has no catalog information for that product.
- Ask about a customer with no contract (e.g., `"What discount does Vandelay Industries get?"`) -- agent should say no contract was found.
- Ask a question requiring cross-document reasoning (e.g., `"Which customer gets the best deal on safety glasses?"`) -- agent should compare across all three contracts.

---

## Lab Instructions -- Domain C: UCC Regulatory Reference

### Step 1: Understand the UCC Documents

**What:** Open the `docs/` directory and browse the five UCC reference documents:

| File | Content |
|------|---------|
| `collateral_classification.md` | How goods are classified under Article 9 (consumer goods, equipment, inventory, farm products) |
| `filing_procedures_faq.md` | Common questions about UCC-1 filings, amendments, continuations, and terminations |
| `state_filing_handbook.md` | State-by-state filing offices, fees, and expedited service options |
| `ucc_article9_guide.md` | Overview of Article 9: attachment, perfection, priority, default |
| `ucc_data_dictionary.md` | Field definitions for UCC filing data (debtor name, collateral description, etc.) |

These documents simulate a reference library for UCC (Uniform Commercial Code) filing professionals. The content covers secured transactions -- how lenders protect their interest in collateral by filing public records.

**Run:**

```bash
cd domain-c-ucc
python solution/loader.py
```

**Expected output:** 5 documents loaded with their character counts.

**Checkpoint:** Can you explain in one sentence what a UCC-1 filing is? (Hint: read the opening section of `ucc_article9_guide.md`.)

---

### Step 2: Chunk the UCC Documents

**Why this matters for UCC:** Legal reference documents use precise terminology where a single word change alters the meaning (e.g., "attachment" vs. "perfection" are distinct legal concepts). The overlap ensures that a definition introduced at the end of one chunk is still present at the start of the next.

**Run:**

```bash
python solution/chunker.py
```

**Checkpoint:** The FAQ and Article 9 guide are typically the longest documents. Verify they produce the most chunks.

---

### Step 3-5: Build and Test the RAG Pipeline

**Sample queries to test with (from `expected_output/sample_queries.txt`):**

1. `"What are the three requirements for a security interest to attach?"`
   - Should cite `ucc_article9_guide.md` and list: value given, debtor has rights, security agreement exists.

2. `"Where do I file a UCC-1 for an LLC formed in Delaware that operates in California?"`
   - Should cite `state_filing_handbook.md` and `filing_procedures_faq.md` -- file in Delaware (state of formation), $50 fee.

3. `"How is a tractor classified as collateral under Article 9? Does it depend on who owns it?"`
   - Should cite `collateral_classification.md` and explain that classification depends on debtor's use (farm products, equipment, inventory, consumer goods).

4. `"I missed the continuation window and my filing lapsed. What happens now?"`
   - Should cite `filing_procedures_faq.md` and `ucc_article9_guide.md` -- filing is unperfected, must file new UCC-1, lose priority.

**Expected output format:**

```
A security interest "attaches" to collateral when three conditions
are met:

1. Value has been given...
2. The debtor has rights in the collateral...
3. A security agreement exists...
   [Source: ucc_article9_guide.md, Chunk 3]
```

---

### Step 6: Conversational UCC Agent

**Domain-specific guidance:**

- The welcome message should identify the agent as a UCC filing reference assistant.
- Include a disclaimer that the agent provides general reference information, not legal advice.
- UCC terminology is highly specific -- the agent should use and define terms precisely (e.g., "perfection" means making a security interest enforceable against third parties, not just the debtor).

**Multi-turn test sequence:**

1. Ask: `"What is perfection?"`
2. Follow up: `"How do I perfect a security interest in equipment?"`
3. Follow up: `"What if the debtor moves to another state?"`

The agent should use conversation history to understand the progression from general concept to specific scenario.

---

### Domain C Checkpoint Criteria

- [ ] Loader finds all 5 UCC reference documents
- [ ] Chunker produces 20+ total chunks across all documents
- [ ] RAG retrieves relevant chunks for filing and classification questions
- [ ] Answers include citations like `[Source: ucc_article9_guide.md, Chunk 3]`
- [ ] Agent correctly distinguishes between related legal concepts (attachment vs. perfection)
- [ ] Follow-up questions maintain context about the filing scenario being discussed
- [ ] All `pytest tests/test_rag.py` tests pass

### Domain C Edge Cases to Test

- Ask about a non-UCC topic (e.g., `"What is the statute of limitations for breach of contract?"`) -- agent should say this is outside its UCC reference scope.
- Ask about an ambiguous collateral type (e.g., `"How do I classify a fleet of delivery trucks?"`) -- agent should explain the equipment vs. inventory distinction based on debtor's use.
- Ask a question requiring cross-document reasoning (e.g., `"I want to file a UCC-1 in Texas for equipment. What form do I need, where do I file, and what are the fees?"`) -- agent should pull from the filing handbook, Article 9 guide, and collateral classification docs.

---

## Final Verification

Run the complete solution and try the sample queries from
`expected_output/sample_queries.txt`. Compare your agent's responses to the
expected output. Your answers should:

1. Be factually consistent with the source documents
2. Include at least one inline citation per answer
3. Handle follow-up questions using conversation history
4. Gracefully refuse questions outside the document scope

## What You Built

By completing this capstone you have:

- **Document ingestion pipeline** -- loading and parsing domain documents
- **Text chunking with overlap** -- splitting documents for optimal retrieval
- **Vector storage** -- embedding and indexing chunks in ChromaDB
- **Semantic search** -- retrieving relevant context via similarity queries
- **RAG answer generation** -- combining retrieved context with Claude
- **Citation tracking** -- attributing answers to source documents
- **Conversational interface** -- multi-turn Q&A with history

These are the foundational building blocks of every production RAG system.

## Next Steps

Continue to **Capstone 3: Workflow Agent** to build a multi-step agent that
plans, executes, and verifies complex tasks using tool orchestration.
