/**
 * RAG Agent — Capstone 2, Domain A (Healthcare) — SOLUTION (Node.js)
 *
 * A Retrieval-Augmented Generation agent that answers clinical policy
 * questions using ChromaDB for vector search and Claude for answer
 * generation with citations.
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
const CHROMA_COLLECTION = "healthcare_policies";
const MODEL = "claude-sonnet-4-6";
const TOP_K = 5;

const SYSTEM_PROMPT = `You are a clinical policy reference assistant. Your job is to answer questions
about healthcare payer clinical policies using ONLY the provided context.

Rules:
1. Base your answer strictly on the provided context passages. Do not use outside knowledge.
2. Cite every factual claim using the format [Source: <filename>, Chunk <N>].
3. If the context does not contain enough information to answer the question,
   say: "I don't have enough information in the loaded policies to answer that question."
4. When listing criteria, quote them accurately from the source documents.
5. Use clear, professional language appropriate for healthcare administrators and clinical staff.`;

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
    .map(
      (r) => `[Source: ${r.source}, Chunk ${r.chunk_index}]\n${r.text}`
    )
    .join("\n\n---\n\n");
}

// ---------------------------------------------------------------------------
// Ask Claude
// ---------------------------------------------------------------------------
async function ask(question, context, client, conversationHistory) {
  const userMessage = `Context (retrieved from policy documents):\n\n${context}\n\n---\n\nQuestion: ${question}`;

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

  // Load documents
  console.log("Loading documents...");
  const documents = loadDocuments(docsPath);
  if (documents.length === 0) {
    console.error("No documents found. Check the docs/ directory.");
    process.exit(1);
  }
  console.log(`  Loaded ${documents.length} documents.`);

  // Chunk documents
  console.log("Chunking documents...");
  const chunks = chunkAll(documents, 1000, 200);
  console.log(`  Created ${chunks.length} chunks.`);

  // Index into ChromaDB
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

  // Initialize Anthropic client
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error("Error: ANTHROPIC_API_KEY environment variable is not set.");
    process.exit(1);
  }
  const client = new Anthropic();

  // Conversation loop
  const conversationHistory = [];

  console.log("\n" + "=".repeat(60));
  console.log("Clinical Policy Q&A Agent");
  console.log("=".repeat(60));
  console.log("Ask questions about clinical policies.");
  console.log("Commands: 'sources' = list documents, 'quit' = exit");
  console.log("=".repeat(60) + "\n");

  const rl = createInterface({ input: process.stdin, output: process.stdout });

  const prompt = () => {
    rl.question("You: ", async (userInput) => {
      userInput = userInput.trim();

      if (!userInput) {
        prompt();
        return;
      }

      if (userInput.toLowerCase() === "quit") {
        console.log("Goodbye!");
        rl.close();
        return;
      }

      if (userInput.toLowerCase() === "sources") {
        console.log("\nLoaded policy documents:");
        documents.forEach((doc) => console.log(`  - ${doc.filename}`));
        console.log();
        prompt();
        return;
      }

      // Retrieve relevant chunks
      const results = await retrieve(userInput, collection, TOP_K);
      const context = buildContext(results);

      // Ask Claude
      const answer = await ask(userInput, context, client, conversationHistory);

      // Update conversation history
      conversationHistory.push({ role: "user", content: userInput });
      conversationHistory.push({ role: "assistant", content: answer });

      // Keep history manageable
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
