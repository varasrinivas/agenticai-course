/**
 * M09 Lab — Step 3: Full RAG Pipeline
 * ======================================
 * Retrieve relevant chunks from the vector store, then generate
 * answers with citations using Claude.
 *
 * Run:
 *     node starter/rag_pipeline.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { ChromaClient } from "chromadb";
import dotenv from "dotenv";
import { loadDocuments, chunkByHeaders } from "./chunker_lib.js";

dotenv.config();

// ---------------------------------------------------------------------------
// Setup (COMPLETE — no changes needed)
// ---------------------------------------------------------------------------

/**
 * Load docs, chunk them, and build the vector store.
 */
async function buildVectorStore() {
  const docsDir = new URL("../docs", import.meta.url).pathname.replace(/^\/([A-Z]:)/, "$1");
  const documents = loadDocuments(docsDir);

  let allChunks = [];
  for (const doc of documents) {
    const chunks = chunkByHeaders(doc.content, doc.filename);
    if (chunks) {
      allChunks.push(...chunks);
    }
  }

  if (allChunks.length === 0) {
    throw new Error("No chunks produced. Complete Steps 1 & 2 first!");
  }

  const client = new ChromaClient();
  const collection = await client.getOrCreateCollection({ name: "ucc_documents" });

  // Add chunks to collection
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
// TODO 1: Retrieve Relevant Chunks
// ---------------------------------------------------------------------------

/**
 * Retrieve the most relevant chunks for a query.
 *
 * Steps:
 *   1. Use collection.query() to search for similar chunks.
 *   2. Transform results into an array of objects:
 *      { text, source, header, distance }
 *
 * @param {Collection} collection
 * @param {string} query
 * @param {number} nResults
 * @returns {Promise<Array<{text: string, source: string, header: string, distance: number}>>}
 */
async function retrieve(collection, query, nResults = 3) {
  // TODO: Implement retrieval.
  // Hint:
  //   const results = await collection.query({ queryTexts: [query], nResults });
  //   Then unpack results.documents[0], results.metadatas[0],
  //   and results.distances[0] into an array of objects.
  return null;
}

// ---------------------------------------------------------------------------
// TODO 2: Generate Answer with Citations
// ---------------------------------------------------------------------------

/**
 * Send the query and retrieved context to Claude to generate an answer.
 *
 * Steps:
 *   1. Build a context string from the retrieved chunks.
 *   2. Create the system prompt for RAG.
 *   3. Send the message to Claude.
 *   4. Return Claude's response text.
 *
 * System prompt:
 *   "You are a helpful assistant that answers questions about UCC
 *   (Uniform Commercial Code) filings and secured transactions.
 *   Answer the question based ONLY on the provided context.
 *   Cite your sources using [Source: filename] format.
 *   If the context doesn't contain enough information to answer
 *   the question, say so clearly."
 *
 * @param {string} query
 * @param {Array} contextChunks - from retrieve()
 * @returns {Promise<string>}
 */
async function generate(query, contextChunks) {
  // TODO: Implement the generation step.
  // Hint:
  //   const client = new Anthropic();
  //   const message = await client.messages.create({...});
  //   return message.content[0].text;
  return null;
}

// ---------------------------------------------------------------------------
// TODO 3: End-to-End RAG Query
// ---------------------------------------------------------------------------

/**
 * End-to-end RAG: retrieve relevant chunks, then generate an answer.
 *
 * @param {Collection} collection
 * @param {string} query
 * @returns {Promise<string>}
 */
async function ragQuery(collection, query) {
  // TODO: Implement the end-to-end pipeline.
  // Hint:
  //   const chunks = await retrieve(collection, query);
  //   const answer = await generate(query, chunks);
  //   Log sources, return the answer.
  return null;
}

// ---------------------------------------------------------------------------
// Main — Test Your Implementation
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

    if (answer) {
      console.log(`\nAnswer:\n${answer}`);
    } else {
      console.log("\n  *** ragQuery() returned null — implement TODOs 1-3 ***");
    }
  }

  console.log("\n" + "=".repeat(60));
  console.log("RAG pipeline complete!");
  console.log("=".repeat(60));
}

main().catch(console.error);
