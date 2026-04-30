/**
 * RAG Agent — Capstone 2, Domain C (UCC) — SOLUTION (Node.js)
 *
 * A Retrieval-Augmented Generation agent that answers UCC regulatory
 * and filing procedure questions using ChromaDB for vector search and
 * Claude for answer generation with citations.
 *
 * Prerequisites:
 *   npm install @anthropic-ai/sdk chromadb
 */

import Anthropic from "@anthropic-ai/sdk";
import { ChromaClient } from "chromadb";
import { readFileSync, readdirSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createInterface } from "readline";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const CHROMA_COLLECTION = "ucc_reference";
const MODEL = "claude-sonnet-4-6";
const TOP_K = 5;

const SYSTEM_PROMPT = `You are a UCC (Uniform Commercial Code) regulatory reference assistant.
Your job is to answer questions about UCC Article 9 secured transactions,
filing procedures, collateral classification, and related regulatory topics
using ONLY the provided context.

Rules:
1. Base your answer strictly on the provided context passages. Do not use outside knowledge.
2. Cite every factual claim using the format [Source: <filename>, Chunk <N>].
3. If the context does not contain enough information to answer the question,
   say: "I don't have enough information in the loaded reference documents to answer that question."
4. When citing legal rules or procedures, quote them accurately from the source documents.
5. Use clear, professional language appropriate for legal, compliance, and data engineering staff.`;

// ---------------------------------------------------------------------------
// Document Loading
// ---------------------------------------------------------------------------
function loadDocuments(docsDir) {
  if (!existsSync(docsDir)) {
    throw new Error(`Documents directory not found: ${docsDir}`);
  }

  const files = readdirSync(docsDir).filter((f) => f.endsWith(".md")).sort();
  const documents = [];

  for (const fname of files) {
    const content = readFileSync(join(docsDir, fname), "utf-8");
    if (content.trim()) {
      documents.push({ filename: fname, content });
    }
  }

  return documents;
}

// ---------------------------------------------------------------------------
// Chunking
// ---------------------------------------------------------------------------
function chunkDocument(document, chunkSize = 1000, overlap = 200) {
  const { content, filename } = document;
  if (!content.trim()) return [];

  const chunks = [];
  const step = Math.max(chunkSize - overlap, 1);
  let start = 0;
  let chunkIndex = 0;

  while (start < content.length) {
    const text = content.slice(start, start + chunkSize);
    if (text.trim()) {
      chunks.push({ text, source: filename, chunk_index: chunkIndex });
      chunkIndex++;
    }
    start += step;
  }

  return chunks;
}

function chunkAll(documents, chunkSize = 1000, overlap = 200) {
  return documents.flatMap((doc) => chunkDocument(doc, chunkSize, overlap));
}

// ---------------------------------------------------------------------------
// ChromaDB Indexing
// ---------------------------------------------------------------------------
async function indexDocuments(chunks, collection) {
  const ids = chunks.map((c) => `${c.source}_${c.chunk_index}`);
  const documents = chunks.map((c) => c.text);
  const metadatas = chunks.map((c) => ({
    source: c.source,
    chunk_index: c.chunk_index,
  }));

  await collection.add({ ids, documents, metadatas });
  return ids.length;
}

// ---------------------------------------------------------------------------
// Retrieval
// ---------------------------------------------------------------------------
async function retrieve(query, collection, topK = TOP_K) {
  const results = await collection.query({ queryTexts: [query], nResults: topK });

  const parsed = [];
  for (let i = 0; i < results.ids[0].length; i++) {
    parsed.push({
      text: results.documents[0][i],
      source: results.metadatas[0][i].source,
      chunk_index: results.metadatas[0][i].chunk_index,
    });
  }

  return parsed;
}

function buildContext(results) {
  return results
    .map((r) => `[Source: ${r.source}, Chunk ${r.chunk_index}]\n${r.text}`)
    .join("\n\n---\n\n");
}

// ---------------------------------------------------------------------------
// Ask Claude
// ---------------------------------------------------------------------------
async function ask(question, context, client, conversationHistory) {
  const userMessage = `Context (retrieved from UCC reference documents):\n\n${context}\n\n---\n\nQuestion: ${question}`;

  const messages = [
    ...conversationHistory,
    { role: "user", content: userMessage },
  ];

  try {
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 2048,
      system: SYSTEM_PROMPT,
      messages,
    });
    return response.content[0].text;
  } catch (error) {
    return `API error: ${error.message}`;
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = dirname(__filename);
  const docsPath = join(__dirname, "..", "docs");

  console.log("Loading documents...");
  const documents = loadDocuments(docsPath);
  if (documents.length === 0) {
    console.error("No documents found.");
    process.exit(1);
  }
  console.log(`  Loaded ${documents.length} documents.`);

  console.log("Chunking documents...");
  const chunks = chunkAll(documents, 1000, 200);
  console.log(`  Created ${chunks.length} chunks.`);

  console.log("Indexing into ChromaDB...");
  const chromaClient = new ChromaClient();
  const collection = await chromaClient.getOrCreateCollection({
    name: CHROMA_COLLECTION,
  });

  const existingCount = await collection.count();
  if (existingCount === 0) {
    const count = await indexDocuments(chunks, collection);
    console.log(`  Indexed ${count} chunks.`);
  } else {
    console.log(`  Collection already has ${existingCount} items.`);
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    console.error("Error: ANTHROPIC_API_KEY environment variable is not set.");
    process.exit(1);
  }
  const client = new Anthropic();

  const conversationHistory = [];

  console.log("\n" + "=".repeat(60));
  console.log("UCC Regulatory Reference Agent");
  console.log("=".repeat(60));
  console.log("Ask questions about UCC Article 9, filing procedures,");
  console.log("collateral classification, and secured transactions.");
  console.log("Commands: 'sources' = list documents, 'quit' = exit");
  console.log("=".repeat(60) + "\n");

  const rl = createInterface({ input: process.stdin, output: process.stdout });

  const prompt = () => {
    rl.question("You: ", async (userInput) => {
      userInput = userInput.trim();

      if (!userInput) { prompt(); return; }

      if (userInput.toLowerCase() === "quit") {
        console.log("Goodbye!");
        rl.close();
        return;
      }

      if (userInput.toLowerCase() === "sources") {
        console.log("\nLoaded reference documents:");
        documents.forEach((doc) => console.log(`  - ${doc.filename}`));
        console.log();
        prompt();
        return;
      }

      const results = await retrieve(userInput, collection, TOP_K);
      const context = buildContext(results);
      const answer = await ask(userInput, context, client, conversationHistory);

      conversationHistory.push({ role: "user", content: userInput });
      conversationHistory.push({ role: "assistant", content: answer });

      if (conversationHistory.length > 20) {
        conversationHistory.splice(0, conversationHistory.length - 20);
      }

      console.log(`\nAgent: ${answer}\n`);
      prompt();
    });
  };

  prompt();
}

main().catch(console.error);
