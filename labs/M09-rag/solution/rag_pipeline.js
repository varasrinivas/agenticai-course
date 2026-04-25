/**
 * M09 Lab — Step 3: Full RAG Pipeline (SOLUTION)
 * =================================================
 * Retrieve relevant chunks from the vector store, then generate
 * answers with citations using Claude.
 *
 * Run:
 *     node solution/rag_pipeline.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { ChromaClient } from "chromadb";
import dotenv from "dotenv";
import { loadDocuments, chunkByHeaders } from "./chunker_lib.js";

dotenv.config();

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

async function buildVectorStore() {
  const docsDir = new URL("../docs", import.meta.url).pathname.replace(/^\/([A-Z]:)/, "$1");
  const documents = loadDocuments(docsDir);

  let allChunks = [];
  for (const doc of documents) {
    const chunks = chunkByHeaders(doc.content, doc.filename);
    allChunks.push(...chunks);
  }

  const client = new ChromaClient();
  const collection = await client.getOrCreateCollection({ name: "ucc_documents_rag" });

  await collection.add({
    documents: allChunks.map((c) => c.text),
    metadatas: allChunks.map((c) => c.metadata),
    ids: allChunks.map((_, i) => `chunk_${i}`),
  });

  const count = await collection.count();
  console.log(`Vector store ready: ${count} chunks indexed.\n`);
  return collection;
}

// ---------------------------------------------------------------------------
// Retrieve Relevant Chunks
// ---------------------------------------------------------------------------

async function retrieve(collection, query, nResults = 3) {
  const results = await collection.query({
    queryTexts: [query],
    nResults,
  });

  const chunks = [];
  const documents = results.documents[0];
  const metadatas = results.metadatas[0];
  const distances = results.distances[0];

  for (let i = 0; i < documents.length; i++) {
    chunks.push({
      text: documents[i],
      source: metadatas[i].source || "unknown",
      header: metadatas[i].header || "N/A",
      distance: distances[i],
    });
  }

  return chunks;
}

// ---------------------------------------------------------------------------
// Generate Answer with Citations
// ---------------------------------------------------------------------------

const RAG_SYSTEM_PROMPT = `You are a helpful assistant that answers questions about UCC \
(Uniform Commercial Code) filings and secured transactions.

Answer the question based ONLY on the provided context. \
Cite your sources using [Source: filename] format. \
If the context doesn't contain enough information to answer the question, say so clearly.`;

async function generate(query, contextChunks) {
  // Build context string
  const contextParts = contextChunks.map(
    (chunk) =>
      `[Source: ${chunk.source} | Section: ${chunk.header}]\n${chunk.text}`
  );
  const contextStr = contextParts.join("\n\n");

  const userMessage = `Context:
---
${contextStr}
---

Question: ${query}`;

  const client = new Anthropic();
  const message = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 1024,
    system: RAG_SYSTEM_PROMPT,
    messages: [{ role: "user", content: userMessage }],
  });

  return message.content[0].text;
}

// ---------------------------------------------------------------------------
// End-to-End RAG Query
// ---------------------------------------------------------------------------

async function ragQuery(collection, query) {
  // Retrieve
  const chunks = await retrieve(collection, query);

  // Show sources
  console.log("\n  Sources retrieved:");
  chunks.forEach((chunk, i) => {
    console.log(
      `    ${i + 1}. ${chunk.source} — ${chunk.header} (distance: ${chunk.distance.toFixed(4)})`
    );
  });

  // Generate
  const answer = await generate(query, chunks);
  return answer;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  console.log("=".repeat(60));
  console.log("M09 Lab — Full RAG Pipeline");
  console.log("=".repeat(60));

  console.log("\nBuilding vector store...");
  const collection = await buildVectorStore();

  const testQueries = [
    "What is the difference between a UCC-1 and UCC-3 filing?",
    "What are the priority rules for secured transactions?",
    "How should I interpret multiple liens on the same debtor?",
    "What is a blanket lien and why is it a red flag?",
  ];

  for (const query of testQueries) {
    console.log("\n" + "=".repeat(60));
    console.log(`Question: ${query}`);
    console.log("=".repeat(60));

    const answer = await ragQuery(collection, query);
    console.log(`\nAnswer:\n${answer}`);
  }

  console.log("\n" + "=".repeat(60));
  console.log("RAG pipeline complete!");
  console.log("=".repeat(60));
}

main().catch(console.error);
