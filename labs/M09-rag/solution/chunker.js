/**
 * M09 Lab — Step 1: Document Loader & Chunker (SOLUTION)
 * ========================================================
 * Load markdown documents and split them into chunks for RAG.
 *
 * Run:
 *     node solution/chunker.js
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ---------------------------------------------------------------------------
// Document Loading
// ---------------------------------------------------------------------------

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
// Fixed-Size Chunking
// ---------------------------------------------------------------------------

function chunkDocument(text, chunkSize = 500, overlap = 50) {
  if (!text) return [];

  const chunks = [];
  let start = 0;
  const step = chunkSize - overlap;

  while (start < text.length) {
    const chunk = text.slice(start, start + chunkSize);
    chunks.push(chunk);
    start += step;
  }

  return chunks;
}

// ---------------------------------------------------------------------------
// Header-Based Semantic Chunking
// ---------------------------------------------------------------------------

function chunkByHeaders(text, filename = "unknown") {
  const lines = text.split("\n");
  const chunks = [];
  let currentLines = [];
  let currentHeader = "Introduction";
  let chunkIndex = 0;

  for (const line of lines) {
    if (line.startsWith("## ")) {
      // Save previous chunk
      if (currentLines.length > 0) {
        const chunkText = currentLines.join("\n").trim();
        if (chunkText.length > 0) {
          chunks.push({
            text: chunkText,
            metadata: {
              source: filename,
              header: currentHeader,
              chunk_index: chunkIndex,
            },
          });
          chunkIndex++;
        }
      }
      currentHeader = line.replace(/^##\s+/, "");
      currentLines = [line];
    } else {
      currentLines.push(line);
    }
  }

  // Save the last chunk
  if (currentLines.length > 0) {
    const chunkText = currentLines.join("\n").trim();
    if (chunkText.length > 0) {
      chunks.push({
        text: chunkText,
        metadata: {
          source: filename,
          header: currentHeader,
          chunk_index: chunkIndex,
        },
      });
    }
  }

  return chunks;
}

// ---------------------------------------------------------------------------
// Fixed-Size Chunks with Metadata
// ---------------------------------------------------------------------------

function chunkWithMetadata(text, filename = "unknown", chunkSize = 500, overlap = 50) {
  const rawChunks = chunkDocument(text, chunkSize, overlap);
  return rawChunks.map((chunk, i) => ({
    text: chunk,
    metadata: {
      source: filename,
      chunk_index: i,
      chunk_method: "fixed_size",
      chunk_size: chunkSize,
      overlap,
    },
  }));
}

// ---------------------------------------------------------------------------
// Main
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
    allFixedChunks.push(...chunks);
    console.log(`  ${doc.filename}: ${chunks.length} chunks`);
  }

  const avgFixed = allFixedChunks.reduce((s, c) => s + c.length, 0) / allFixedChunks.length;
  console.log(`\n  Total fixed-size chunks : ${allFixedChunks.length}`);
  console.log(`  Average chunk size      : ${Math.round(avgFixed)} chars`);
  console.log(`  Smallest chunk          : ${Math.min(...allFixedChunks.map((c) => c.length))} chars`);
  console.log(`  Largest chunk           : ${Math.max(...allFixedChunks.map((c) => c.length))} chars`);

  // --- Header-based chunking ---
  console.log("\n" + "=".repeat(60));
  console.log("STEP 3: Header-Based Semantic Chunking");
  console.log("=".repeat(60));
  let allHeaderChunks = [];
  for (const doc of documents) {
    const chunks = chunkByHeaders(doc.content, doc.filename);
    allHeaderChunks.push(...chunks);
    console.log(`  ${doc.filename}: ${chunks.length} chunks`);
    for (const chunk of chunks) {
      console.log(`    - '${chunk.metadata.header}' (${chunk.text.length} chars)`);
    }
  }

  const avgHeader = allHeaderChunks.reduce((s, c) => s + c.text.length, 0) / allHeaderChunks.length;
  console.log(`\n  Total header chunks : ${allHeaderChunks.length}`);
  console.log(`  Average chunk size  : ${Math.round(avgHeader)} chars`);

  // --- Comparison ---
  console.log("\n" + "=".repeat(60));
  console.log("COMPARISON");
  console.log("=".repeat(60));
  console.log(`  Fixed-size chunks : ${allFixedChunks.length}`);
  console.log(`  Header chunks     : ${allHeaderChunks.length}`);
  console.log("  Header chunking produces fewer, more meaningful chunks.");
}

main();
