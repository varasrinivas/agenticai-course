/**
 * M09 Lab — Step 1: Document Loader & Chunker
 * =============================================
 * Load markdown documents and split them into chunks for RAG.
 *
 * Two chunking strategies:
 *   1. Fixed-size with overlap (character-based)
 *   2. Header-based semantic chunking (split on ## headings)
 *
 * Run:
 *     node starter/chunker.js
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ---------------------------------------------------------------------------
// Document Loading (COMPLETE — no changes needed)
// ---------------------------------------------------------------------------

/**
 * Load all .md files from the docs directory.
 * @param {string} docsDir - Path to the docs folder
 * @returns {Array<{filename: string, content: string}>}
 */
function loadDocuments(docsDir) {
  const files = fs.readdirSync(docsDir)
    .filter((f) => f.endsWith(".md"))
    .sort();

  if (files.length === 0) {
    throw new Error(`No .md files found in ${docsDir}`);
  }

  const documents = files.map((file) => {
    const content = fs.readFileSync(path.join(docsDir, file), "utf-8");
    console.log(`  Loaded: ${file} (${content.length} chars)`);
    return { filename: file, content };
  });

  return documents;
}

// ---------------------------------------------------------------------------
// TODO 1: Fixed-Size Chunking
// ---------------------------------------------------------------------------

/**
 * Split text into chunks of approximately chunkSize characters
 * with overlap characters of overlap between consecutive chunks.
 *
 * Rules:
 *   - Each chunk should be at most chunkSize characters.
 *   - Consecutive chunks overlap by overlap characters.
 *   - The last chunk may be smaller than chunkSize.
 *   - If the text is shorter than chunkSize, return it as a single chunk.
 *
 * Example (chunkSize=10, overlap=3):
 *   text = "abcdefghijklmnopqrst"  (20 chars)
 *   chunks = ["abcdefghij", "hijklmnopq", "opqrst"]
 *
 * @param {string} text
 * @param {number} chunkSize
 * @param {number} overlap
 * @returns {string[]}
 */
function chunkDocument(text, chunkSize = 500, overlap = 50) {
  // TODO: Implement fixed-size chunking with overlap.
  // Hint: use a while loop with a `start` pointer.
  //   - Each iteration, take text.slice(start, start + chunkSize)
  //   - Advance start by (chunkSize - overlap)
  //   - Stop when start >= text.length
  return null;
}

// ---------------------------------------------------------------------------
// TODO 2: Header-Based Semantic Chunking
// ---------------------------------------------------------------------------

/**
 * Split text on markdown ## headers to create semantic chunks.
 *
 * Each chunk should contain the text under one ## heading (including the
 * heading line itself). Text before the first ## heading is captured as
 * an "Introduction" chunk.
 *
 * @param {string} text
 * @param {string} filename
 * @returns {Array<{text: string, metadata: {source: string, header: string, chunk_index: number}}>}
 */
function chunkByHeaders(text, filename = "unknown") {
  // TODO: Implement header-based semantic chunking.
  // Step 1: Split the text into lines.
  // Step 2: Walk through lines, starting a new chunk each time you see "## ".
  // Step 3: Collect text before the first heading as "Introduction".
  // Step 4: Build the array of chunk objects with metadata.
  return null;
}

// ---------------------------------------------------------------------------
// TODO 3: Add Metadata to Fixed-Size Chunks
// ---------------------------------------------------------------------------

/**
 * Combine fixed-size chunking with metadata.
 *
 * @param {string} text
 * @param {string} filename
 * @param {number} chunkSize
 * @param {number} overlap
 * @returns {Array<{text: string, metadata: {source: string, chunk_index: number, chunk_method: string, chunk_size: number, overlap: number}}>}
 */
function chunkWithMetadata(text, filename = "unknown", chunkSize = 500, overlap = 50) {
  // TODO: Call chunkDocument() and wrap each result with metadata.
  return null;
}

// ---------------------------------------------------------------------------
// Main — Test Your Implementation
// ---------------------------------------------------------------------------

function main() {
  const docsDir = path.join(__dirname, "..", "docs");

  console.log("=".repeat(60));
  console.log("STEP 1: Loading Documents");
  console.log("=".repeat(60));
  const documents = loadDocuments(docsDir);
  console.log(`\nLoaded ${documents.length} documents.\n`);

  // --- Fixed-size chunking ---
  console.log("=".repeat(60));
  console.log("STEP 2: Fixed-Size Chunking (chunkSize=500, overlap=50)");
  console.log("=".repeat(60));
  let allFixedChunks = [];
  for (const doc of documents) {
    const chunks = chunkDocument(doc.content, 500, 50);
    if (chunks) {
      allFixedChunks.push(...chunks);
      console.log(`  ${doc.filename}: ${chunks.length} chunks`);
    }
  }

  if (allFixedChunks.length > 0) {
    const avgSize = allFixedChunks.reduce((s, c) => s + c.length, 0) / allFixedChunks.length;
    const smallest = Math.min(...allFixedChunks.map((c) => c.length));
    const largest = Math.max(...allFixedChunks.map((c) => c.length));
    console.log(`\n  Total fixed-size chunks : ${allFixedChunks.length}`);
    console.log(`  Average chunk size      : ${Math.round(avgSize)} chars`);
    console.log(`  Smallest chunk          : ${smallest} chars`);
    console.log(`  Largest chunk           : ${largest} chars`);
  } else {
    console.log("\n  *** chunkDocument() returned null — implement TODO 1 ***");
  }

  // --- Header-based chunking ---
  console.log("\n" + "=".repeat(60));
  console.log("STEP 3: Header-Based Semantic Chunking");
  console.log("=".repeat(60));
  let allHeaderChunks = [];
  for (const doc of documents) {
    const chunks = chunkByHeaders(doc.content, doc.filename);
    if (chunks) {
      allHeaderChunks.push(...chunks);
      console.log(`  ${doc.filename}: ${chunks.length} chunks`);
      for (const chunk of chunks) {
        console.log(`    - '${chunk.metadata.header}' (${chunk.text.length} chars)`);
      }
    }
  }

  if (allHeaderChunks.length > 0) {
    const avgSize = allHeaderChunks.reduce((s, c) => s + c.text.length, 0) / allHeaderChunks.length;
    console.log(`\n  Total header chunks : ${allHeaderChunks.length}`);
    console.log(`  Average chunk size  : ${Math.round(avgSize)} chars`);
  } else {
    console.log("\n  *** chunkByHeaders() returned null — implement TODO 2 ***");
  }

  // --- Comparison ---
  console.log("\n" + "=".repeat(60));
  console.log("COMPARISON");
  console.log("=".repeat(60));
  if (allFixedChunks.length > 0 && allHeaderChunks.length > 0) {
    console.log(`  Fixed-size chunks : ${allFixedChunks.length}`);
    console.log(`  Header chunks     : ${allHeaderChunks.length}`);
    console.log("  Header chunking produces fewer, more meaningful chunks.");
  } else {
    console.log("  Complete TODOs 1 and 2 to see the comparison.");
  }
}

main();
