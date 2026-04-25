/**
 * Shared chunker library for JS labs.
 * This file exports the chunker functions so they can be imported
 * by embeddings.js and rag_pipeline.js.
 *
 * NOTE: This file contains the SOLUTION for the chunker functions
 * so that Steps 2 and 3 can work independently. Students should
 * still implement chunker.js themselves first.
 */

import fs from "fs";
import path from "path";

/**
 * Load all .md files from the docs directory.
 */
export function loadDocuments(docsDir) {
  const files = fs.readdirSync(docsDir)
    .filter((f) => f.endsWith(".md"))
    .sort();

  if (files.length === 0) {
    throw new Error(`No .md files found in ${docsDir}`);
  }

  return files.map((file) => {
    const content = fs.readFileSync(path.join(docsDir, file), "utf-8");
    console.log(`  Loaded: ${file} (${content.length} chars)`);
    return { filename: file, content };
  });
}

/**
 * Split text on markdown ## headers for semantic chunking.
 */
export function chunkByHeaders(text, filename = "unknown") {
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
