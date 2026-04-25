/**
 * M09 Lab — Step 2: Embeddings & Vector Store
 * =============================================
 * Embed document chunks and store them in ChromaDB for similarity search.
 *
 * Uses ChromaDB's default embedding function so no external API key
 * is needed for embeddings.
 *
 * Run:
 *     node starter/embeddings.js
 */

import { ChromaClient } from "chromadb";
import { loadDocuments, chunkByHeaders } from "./chunker_lib.js";

// ---------------------------------------------------------------------------
// ChromaDB Setup (COMPLETE — no changes needed)
// ---------------------------------------------------------------------------

/**
 * Create a ChromaDB client connecting to the default local server.
 * Start ChromaDB first: chroma run --path ./chroma_data
 */
function getChromaClient() {
  return new ChromaClient();
}

// ---------------------------------------------------------------------------
// TODO 1: Create Collection and Add Chunks
// ---------------------------------------------------------------------------

/**
 * Create a ChromaDB collection and add all chunks to it.
 *
 * Each chunk object looks like:
 *   { text: "chunk text...", metadata: { source: "file.md", header: "Section", chunk_index: 0 } }
 *
 * Steps:
 *   1. Create (or get) a collection with the given name.
 *   2. Prepare three parallel arrays:
 *      - documents: the chunk text strings
 *      - metadatas: the chunk metadata objects
 *      - ids: unique string IDs (e.g., "chunk_0", "chunk_1", ...)
 *   3. Add them to the collection using collection.add().
 *   4. Return the collection.
 *
 * @param {ChromaClient} client
 * @param {Array} chunks - array of chunk objects
 * @param {string} collectionName
 * @returns {Promise<Collection>}
 */
async function createCollection(client, chunks, collectionName = "ucc_documents") {
  // TODO: Implement collection creation and chunk insertion.
  // Hint:
  //   const collection = await client.getOrCreateCollection({ name: collectionName });
  //   await collection.add({
  //     documents: [...],
  //     metadatas: [...],
  //     ids: [...],
  //   });
  return null;
}

// ---------------------------------------------------------------------------
// TODO 2: Search the Collection
// ---------------------------------------------------------------------------

/**
 * Search the collection for chunks most similar to the query.
 *
 * Steps:
 *   1. Use collection.query() with queryTexts and nResults.
 *   2. Return the raw results object.
 *
 * Results object contains:
 *   - results.documents[0]  -> array of matching document texts
 *   - results.metadatas[0]  -> array of metadata objects
 *   - results.distances[0]  -> array of distance scores (lower = more similar)
 *   - results.ids[0]        -> array of chunk IDs
 *
 * @param {Collection} collection
 * @param {string} query
 * @param {number} nResults
 * @returns {Promise<object>}
 */
async function search(collection, query, nResults = 3) {
  // TODO: Implement similarity search.
  // Hint: const results = await collection.query({ queryTexts: [query], nResults });
  return null;
}

// ---------------------------------------------------------------------------
// Display Helper (COMPLETE — no changes needed)
// ---------------------------------------------------------------------------

function printResults(query, results) {
  console.log(`\n${"─".repeat(60)}`);
  console.log(`Query: "${query}"`);
  console.log(`${"─".repeat(60)}`);

  if (!results) {
    console.log("  *** search() returned null — implement TODO 2 ***");
    return;
  }

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
// Main — Test Your Implementation
// ---------------------------------------------------------------------------

async function main() {
  const docsDir = new URL("../docs", import.meta.url).pathname.replace(/^\/([A-Z]:)/, "$1");

  // --- Load and chunk documents ---
  console.log("=".repeat(60));
  console.log("Loading and chunking documents...");
  console.log("=".repeat(60));
  const documents = loadDocuments(docsDir);
  let allChunks = [];
  for (const doc of documents) {
    const chunks = chunkByHeaders(doc.content, doc.filename);
    if (chunks) {
      allChunks.push(...chunks);
    }
  }
  console.log(`\nTotal chunks: ${allChunks.length}`);

  if (allChunks.length === 0) {
    console.log("\nERROR: No chunks produced. Complete Step 1 (chunker.js) first!");
    return;
  }

  // --- Create collection ---
  console.log("\n" + "=".repeat(60));
  console.log("Creating ChromaDB collection...");
  console.log("=".repeat(60));
  const client = getChromaClient();
  const collection = await createCollection(client, allChunks);

  if (!collection) {
    console.log("\n  *** createCollection() returned null — implement TODO 1 ***");
    return;
  }

  const count = await collection.count();
  console.log(`  Collection '${collection.name}' created with ${count} chunks.`);

  // --- Run test queries ---
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
