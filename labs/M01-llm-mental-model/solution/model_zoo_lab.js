/**
 * M01 Bonus Lab — Model Zoo: Generative vs. Multimodal (SOLUTION)
 */
import Anthropic from '@anthropic-ai/sdk';
import 'dotenv/config';

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

async function multimodalCall(imageUrl, question) {
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 128,
    messages: [
      {
        role: 'user',
        content: [
          { type: 'image', source: { type: 'url', url: imageUrl } },
          { type: 'text', text: question },
        ],
      },
    ],
  });
  return response.content[0].text;
}

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
