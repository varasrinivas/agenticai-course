/**
 * M09 Lab: The Full RAG Pipeline (Node.js)
 * =========================================
 * Load → chunk → store → retrieve → generate-with-citations.
 *
 * NOTE: the chromadb JS client needs a Chroma SERVER running:
 *   pip install chromadb && chroma run --path ./chroma_data
 * The Python version runs fully in-process — prefer it if you only do one.
 *
 * Run: node rag_pipeline.js   (from this folder; reads ../docs)
 */

import { readFileSync, readdirSync } from "node:fs";
import { join, basename, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import OpenAI from "openai";
import { ChromaClient } from "chromadb";

const DOCS_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "docs");

// ── Document Loading (COMPLETE) ──────────────────────────────
function loadDocuments(docsDir) {
  const files = readdirSync(docsDir).filter((f) => f.endsWith(".md") || f.endsWith(".txt"));
  if (files.length === 0) throw new Error(`No documents found in ${docsDir}`);
  return files
    .map((f) => {
      try {
        return { content: readFileSync(join(docsDir, f), "utf-8"), source: basename(f) };
      } catch (e) {
        console.warn(`  Skipping ${f}: ${e.message}`);
        return null;
      }
    })
    .filter(Boolean);
}

// ── Part 1: Chunking (YOUR JOB) ──────────────────────────────
/**
 * Split text into overlapping chunks, cutting at natural boundaries.
 *
 * TODO:
 * 1. If text.length <= chunkSize: return [text]
 * 2. Walk the text with a start pointer:
 *    a. let end = start + chunkSize; let chunk = text.slice(start, end);
 *    b. If end < text.length: try separators ["\n\n", "\n", ". "] in order —
 *       find the LAST occurrence (lastIndexOf) inside chunk; if it sits past
 *       the halfway point (lastSep > chunkSize * 0.5), cut there instead:
 *       end = start + lastSep + sep.length, re-slice chunk, stop trying
 *    c. Push chunk.trim()
 *    d. start = end - overlap     ← overlap for continuity
 * 3. Return chunks, dropping empty strings
 */
function chunkText(text, chunkSize = 500, overlap = 50) {
  // TODO: implement
}

// ── Part 2: Ingestion (COMPLETE) ─────────────────────────────
async function ingest(docsDir = DOCS_DIR) {
  console.log("-- Ingestion Pipeline --");
  const docs = loadDocuments(docsDir);
  console.log(`  Loaded ${docs.length} documents`);

  const allChunks = [];
  for (const doc of docs) {
    chunkText(doc.content, 500, 50).forEach((chunk, i) => {
      allChunks.push({ text: chunk, source: doc.source, index: i });
    });
  }
  console.log(`  Created ${allChunks.length} chunks`);

  const chroma = new ChromaClient(); // expects chroma server on :8000
  const collection = await chroma.getOrCreateCollection({
    name: "rag_lab",
    metadata: { "hnsw:space": "cosine" },
  });
  await collection.add({
    ids: allChunks.map((_, i) => `chunk_${i}`),
    documents: allChunks.map((c) => c.text),
    metadatas: allChunks.map((c) => ({ source: c.source, index: c.index })),
  });
  console.log(`  Stored ${await collection.count()} chunks in ChromaDB`);
  return collection;
}

// ── Part 3: Query (YOUR JOB) ─────────────────────────────────
const GROUNDING_SYSTEM =
  "You are a helpful assistant that answers questions based ONLY on the " +
  "provided context. If the context doesn't contain the answer, say " +
  '"I don\'t have enough information to answer that." Always cite your ' +
  "sources using [Source N] format.";

/**
 * Retrieve relevant chunks and generate a grounded, cited answer.
 *
 * TODO:
 * 1. results = await collection.query({ queryTexts: [question], nResults: topK })
 *    (try/catch → return `Retrieval error: ${e.message}`)
 * 2. If (!results.documents?.[0]?.length):
 *      return "No relevant documents found. I don't have enough information.";
 * 3. const chunks = results.documents[0]; const sources = results.metadatas[0];
 * 4. Build the context block:
 *      `[Source ${i + 1}: ${sources[i].source}]\n${chunk}` joined by "\n\n---\n\n"
 * 5. Call Mistral with GROUNDING_SYSTEM as system message and the
 *    Context/Question user message (try/catch → `Generation error: ...`)
 * 6. Return the answer text
 */
async function queryRag(collection, question, topK = 3) {
  // TODO: implement
}

// ── Test harness (COMPLETE) ──────────────────────────────────
const collection = await ingest();

const questions = [
  "What happens if a continuation statement is filed late?",
  "What are the high-risk indicators in a lien risk assessment?",
  "What is the capital of France?", // NOT in the docs — must refuse!
];
for (const q of questions) {
  console.log(`\n${"=".repeat(60)}\nQ: ${q}`);
  console.log(`A: ${await queryRag(collection, q)}`);
}
