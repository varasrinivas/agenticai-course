/**
 * M01 Bonus Lab — Model Zoo: Generative vs. Multimodal
 * =====================================================
 * You've already used the GENERATIVE mode in the temperature lab.
 * This script shows the MULTIMODAL mode: pass an image URL alongside
 * a text question and Claude returns a description.
 *
 * No extra API key needed — both modes use the same Anthropic client.
 *
 * HOW TO RUN
 * ----------
 *   node model_zoo_lab.mjs
 *
 * (Rename to .mjs or ensure package.json has "type": "module")
 *
 * LOOKING AHEAD
 * -------------
 * Embedding and reranker models require a separate API key (Voyage, Cohere,
 * or OpenAI).  You'll call them in the RAG labs:
 *   - M09: embedding model to index documents, cosine-similarity search
 *   - M10: reranker to score retrieved chunks before sending to Claude
 */
import Anthropic from '@anthropic-ai/sdk';
import 'dotenv/config';

const client = new Anthropic();
const MODEL = 'claude-haiku-4-5-20251001'; // cheapest Claude; handles both modes

// ---------------------------------------------------------------------------
// Part 1: GENERATIVE (text only)
// ---------------------------------------------------------------------------

/**
 * Standard text-in / text-out call.
 * @param {string} question
 * @returns {Promise<string>}
 */
async function generativeCall(question) {
  // TODO: Call client.messages.create() with:
  //   model: MODEL, max_tokens: 128
  //   messages: [{ role: 'user', content: question }]
  // Return the first content block's text
  throw new Error('Not implemented');
}

// ---------------------------------------------------------------------------
// Part 2: MULTIMODAL (image URL + text → text)
// ---------------------------------------------------------------------------

/**
 * Pass a public image URL alongside a text question.
 * @param {string} imageUrl
 * @param {string} question
 * @returns {Promise<string>}
 */
async function multimodalCall(imageUrl, question) {
  // TODO: Call client.messages.create() with:
  //   model: MODEL, max_tokens: 128
  //   messages: [{
  //     role: 'user',
  //     content: [
  //       { type: 'image', source: { type: 'url', url: imageUrl } },
  //       { type: 'text', text: question }
  //     ]
  //   }]
  // Return the first content block's text
  throw new Error('Not implemented');
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

const IMAGE_URL =
  'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Bikesgray.jpg/320px-Bikesgray.jpg';

try {
  console.log('='.repeat(60));
  console.log('PART 1: GENERATIVE MODEL (text → text)');
  console.log('='.repeat(60));
  const answer = await generativeCall('What is the Eiffel Tower? One sentence.');
  console.log(`Claude: ${answer}\n`);

  console.log('='.repeat(60));
  console.log('PART 2: MULTIMODAL MODEL (image + text → text)');
  console.log('='.repeat(60));
  const description = await multimodalCall(IMAGE_URL, 'Describe this image in one sentence.');
  console.log(`Claude sees: ${description}\n`);

  console.log('='.repeat(60));
  console.log('CONCEPTUAL: EMBEDDING & RERANKER MODELS');
  console.log('='.repeat(60));
  console.log(`An EMBEDDING model (e.g., Voyage-3) would NOT describe the image.
Instead it would output ~1024 numbers — a dense vector capturing
meaning — so you could search a million images by comparing vectors.

A RERANKER model (e.g., Cohere Rerank) takes a query + a list of
candidate passages and outputs a relevance score for each one.
It is too slow to scan millions of items but very accurate at the
final scoring step (typically top-20 → top-5).

You will call both in the RAG track:
  → M09: embed documents, build a vector index, run semantic search
  → M10: add a reranker stage to improve precision`);
} catch (err) {
  console.error(`[ERROR] ${err.message}`);
  process.exit(1);
}
