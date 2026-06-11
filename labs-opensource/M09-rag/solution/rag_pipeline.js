/**
 * M09 Lab: The Full RAG Pipeline — SOLUTION (Node.js)
 * ====================================================
 * Requires a Chroma server: pip install chromadb && chroma run --path ./chroma_data
 * Run: node rag_pipeline.js
 */

import { readFileSync, readdirSync } from "node:fs";
import { join, basename, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import OpenAI from "openai";
import { ChromaClient } from "chromadb";

const DOCS_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "docs");

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

function chunkText(text, chunkSize = 500, overlap = 50) {
  if (text.length <= chunkSize) return [text];

  const chunks = [];
  let start = 0;
  while (start < text.length) {
    let end = start + chunkSize;
    let chunk = text.slice(start, end);

    if (end < text.length) {
      // Prefer to cut at a natural boundary in the second half of the window
      for (const sep of ["\n\n", "\n", ". "]) {
        const lastSep = chunk.lastIndexOf(sep);
        if (lastSep > chunkSize * 0.5) {
          end = start + lastSep + sep.length;
          chunk = text.slice(start, end);
          break;
        }
      }
    }

    chunks.push(chunk.trim());
    start = end - overlap; // overlap for continuity
  }
  return chunks.filter(Boolean);
}

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

  const chroma = new ChromaClient();
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

const GROUNDING_SYSTEM =
  "You are a helpful assistant that answers questions based ONLY on the " +
  "provided context. If the context doesn't contain the answer, say " +
  '"I don\'t have enough information to answer that." Always cite your ' +
  "sources using [Source N] format.";

async function queryRag(collection, question, topK = 3) {
  const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

  let results;
  try {
    results = await collection.query({ queryTexts: [question], nResults: topK });
  } catch (e) {
    return `Retrieval error: ${e.message}`;
  }

  if (!results.documents?.[0]?.length) {
    return "No relevant documents found. I don't have enough information.";
  }

  const chunks = results.documents[0];
  const sources = results.metadatas[0];

  const context = chunks
    .map((chunk, i) => `[Source ${i + 1}: ${sources[i].source}]\n${chunk}`)
    .join("\n\n---\n\n");

  try {
    const response = await client.chat.completions.create({
      model: "mistral",
      messages: [
        { role: "system", content: GROUNDING_SYSTEM },
        { role: "user", content:
            `Context:\n${context}\n\nQuestion: ${question}\n\n` +
            "Answer based on the context above, citing sources:" },
      ],
    });
    return response.choices[0].message.content;
  } catch (e) {
    return `Generation error: ${e.message}`;
  }
}

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
