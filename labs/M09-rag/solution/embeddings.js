/**
 * M09 Lab — Step 2: Embeddings & Vector Store (SOLUTION)
 * ========================================================
 * Embed document chunks and store them in ChromaDB for similarity search.
 *
 * Run:
 *     node solution/embeddings.js
 */

import { ChromaClient } from "chromadb";
import { loadDocuments, chunkByHeaders } from "./chunker_lib.js";

// ---------------------------------------------------------------------------
// ChromaDB Setup
// ---------------------------------------------------------------------------

function getChromaClient() {
  return new ChromaClient();
}

// ---------------------------------------------------------------------------
// Create Collection and Add Chunks
// ---------------------------------------------------------------------------

async function createCollection(client, chunks, collectionName = "ucc_documents") {
  const collection = await client.getOrCreateCollection({ name: collectionName });

  await collection.add({
    documents: chunks.map((c) => c.text),
    metadatas: chunks.map((c) => c.metadata),
    ids: chunks.map((_, i) => `chunk_${i}`),
  });

  return collection;
}

// ---------------------------------------------------------------------------
// Search the Collection
// ---------------------------------------------------------------------------

async function search(collection, query, nResults = 3) {
  const results = await collection.query({
    queryTexts: [query],
    nResults,
  });
  return results;
}

// ---------------------------------------------------------------------------
// Display Helper
// ---------------------------------------------------------------------------

function printResults(query, results) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`Query: "${query}"`);
  console.log(`${"─".repeat(60)}`);

  const documents = results.documents[0];
  const metadatas = results.metadatas[0];
  const distances = results.distances[0];

  for (let i = 0; i < documents.length; i++) {
    console.log(`\n  Result ${i + 1} (distance: ${distances[i].toFixed(4)}):`);
    console.log(`  Source : ${metadatas[i].source || "unknown"}`);
    console.log(`  Header : ${metadatas[i].header || "N/A"}`);
    console.log(`  Preview: ${documents[i].slice(0, 150).trim()}...`);
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const docsDir = new URL("../docs", import.meta.url).pathname.replace(/^\/([A-Z]:)/, "$1");

  console.log("=".repeat(60));
  console.log("Loading and chunking documents...");
  console.log("=".repeat(60));
  const documents = loadDocuments(docsDir);
  let allChunks = [];
  for (const doc of documents) {
    const chunks = chunkByHeaders(doc.content, doc.filename);
    allChunks.push(...chunks);
  }
  console.log(`\nTotal chunks: ${allChunks.length}`);

  console.log("\n" + "=".repeat(60));
  console.log("Creating ChromaDB collection...");
  console.log("=".repeat(60));
  const client = getChromaClient();
  const collection = await createCollection(client, allChunks);
  const count = await collection.count();
  console.log(`  Collection 'ucc_documents' created with ${count} chunks.`);

  console.log("\n" + "=".repeat(60));
  console.log("Running similarity searches...");
  console.log("=".repeat(60));

  const testQueries = [
    "What is perfection in UCC Article 9?",
    "How do I search for liens on a business?",
    "What types of collateral can be secured?",
    "When does a UCC filing expire?",
  ];

  for (const query of testQueries) {
    const results = await search(collection, query, 3);
    printResults(query, results);
  }

  console.log("\n" + "=".repeat(60));
  console.log("Done! Your vector store is working.");
  console.log("=".repeat(60));
}

main().catch(console.error);
