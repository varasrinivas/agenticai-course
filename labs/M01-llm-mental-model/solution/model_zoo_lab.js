/**
 * M01 Bonus Lab — Model Zoo: Generative vs. Multimodal (SOLUTION)
 */
import Anthropic from '@anthropic-ai/sdk';
import 'dotenv/config';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const client = new Anthropic();
const MODEL = 'claude-haiku-4-5-20251001';

async function generativeCall(question) {
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 128,
    messages: [{ role: 'user', content: question }],
  });
  return response.content[0].text;
}

async function multimodalCall(imagePath, question) {
  // Send the image as base64 from disk rather than pointing the API at a URL.
  // The API fetches a URL itself, so that form depends on a third party still
  // serving that exact path to Anthropic's fetcher: the Wikimedia URL this lab
  // used now fails with "Unable to download the file", and a Google-hosted
  // replacement returns "This URL is disallowed". Reading bytes has neither
  // failure mode, and the Python twin does the same.
  const data = readFileSync(imagePath).toString('base64');
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 128,
    messages: [
      {
        role: 'user',
        content: [
          { type: 'image', source: { type: 'base64', media_type: 'image/png', data } },
          { type: 'text', text: question },
        ],
      },
    ],
  });
  return response.content[0].text;
}

// Shipped with the lab so it cannot rot: a red circle, a blue square and a
// green triangle, chosen so the description is checkable by eye.
const IMAGE_PATH = join(dirname(fileURLToPath(import.meta.url)), '..', 'assets', 'shapes.png');

try {
  console.log('='.repeat(60));
  console.log('PART 1: GENERATIVE MODEL (text → text)');
  console.log('='.repeat(60));
  const answer = await generativeCall('What is the Eiffel Tower? One sentence.');
  console.log(`Claude: ${answer}\n`);

  console.log('='.repeat(60));
  console.log('PART 2: MULTIMODAL MODEL (image + text → text)');
  console.log('='.repeat(60));
  const description = await multimodalCall(IMAGE_PATH, 'Describe this image in one sentence.');
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
