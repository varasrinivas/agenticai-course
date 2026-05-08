// Generate pre-rendered narration MP3s for a course module via OpenAI TTS.
//
// Prerequisites:
//   1. Open output/M{XX}-*.html in a browser with ?listen-dev=1 appended to the URL.
//      Click the "Listen" button, then "Export sections JSON" in the dev row at the
//      bottom of the panel. Save the downloaded file to:
//         output/audio/M{XX}/sections.json
//   2. Set OPENAI_API_KEY in your environment.
//
// Usage:
//   node scripts/generate-audio.mjs M00            # default voice=alloy, model=tts-1
//   node scripts/generate-audio.mjs M00 nova tts-1-hd
//
// Output:
//   output/audio/M{XX}/{section-id}-1.mp3, -2.mp3, ...
//   output/audio/M{XX}/manifest.json    <- consumed by the in-page Listen player
//
// Re-runs are incremental: sections whose text+voice+model hash is unchanged are skipped.

import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

const MODULE = process.argv[2] || 'M00';
const VOICE = process.argv[3] || 'alloy';   // alloy | echo | fable | onyx | nova | shimmer
const MODEL = process.argv[4] || 'tts-1';   // tts-1 (faster, $15/1M chars) | tts-1-hd ($30/1M)
const API_KEY = process.env.OPENAI_API_KEY;
const MAX_CHARS = 3800;                     // OpenAI TTS hard limit is 4096; leave headroom

if (!API_KEY) {
  console.error('ERROR: OPENAI_API_KEY is not set in the environment.');
  process.exit(1);
}

const OUT_DIR = path.join('output', 'audio', MODULE);
const SECTIONS_PATH = path.join(OUT_DIR, 'sections.json');
const MANIFEST_PATH = path.join(OUT_DIR, 'manifest.json');

await fs.mkdir(OUT_DIR, { recursive: true });

let sections;
try {
  sections = JSON.parse(await fs.readFile(SECTIONS_PATH, 'utf8'));
} catch (err) {
  console.error(`ERROR: Could not read ${SECTIONS_PATH}.`);
  console.error('Export it first from the module page using ?listen-dev=1.');
  process.exit(1);
}

let prev = { sections: [] };
try { prev = JSON.parse(await fs.readFile(MANIFEST_PATH, 'utf8')); } catch {}
const prevById = new Map(prev.sections.map(s => [s.id, s]));

function hashText(text) {
  return crypto.createHash('sha1').update(text + '|' + MODEL + '|' + VOICE).digest('hex').slice(0, 12);
}

function chunkText(text) {
  if (text.length <= MAX_CHARS) return [text];
  const sentences = text.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [text];
  const chunks = [];
  let cur = '';
  for (const s of sentences) {
    const trimmed = s.trim();
    if (!trimmed) continue;
    if ((cur + ' ' + trimmed).length > MAX_CHARS && cur) {
      chunks.push(cur.trim());
      cur = trimmed;
    } else {
      cur = cur ? cur + ' ' + trimmed : trimmed;
    }
  }
  if (cur.trim()) chunks.push(cur.trim());
  return chunks;
}

async function fileExists(p) {
  try { await fs.access(p); return true; } catch { return false; }
}

async function tts(text) {
  const res = await fetch('https://api.openai.com/v1/audio/speech', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: MODEL, voice: VOICE, input: text, response_format: 'mp3' }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`OpenAI ${res.status}: ${body.slice(0, 300)}`);
  }
  return Buffer.from(await res.arrayBuffer());
}

console.log(`Module: ${MODULE}   Voice: ${VOICE}   Model: ${MODEL}`);
console.log(`Sections to consider: ${sections.length}\n`);

const out = {
  module: MODULE,
  model: MODEL,
  voice: VOICE,
  generatedAt: new Date().toISOString(),
  sections: [],
};

let totalChars = 0;
let renderedChunks = 0;
let skipped = 0;

for (const s of sections) {
  const h = hashText(s.text);
  const cached = prevById.get(s.id);
  const chunks = chunkText(s.text);
  const expectedFiles = chunks.map((_, i) => `${s.id}-${i + 1}.mp3`);

  const allCached = cached
    && cached.hash === h
    && Array.isArray(cached.files)
    && cached.files.length === expectedFiles.length
    && (await Promise.all(expectedFiles.map(f => fileExists(path.join(OUT_DIR, f))))).every(Boolean);

  if (allCached) {
    console.log(`  cached  ${s.id} (${chunks.length} file${chunks.length > 1 ? 's' : ''})`);
    out.sections.push({ id: s.id, title: s.title, files: expectedFiles, hash: h });
    skipped += chunks.length;
    continue;
  }

  for (let i = 0; i < chunks.length; i++) {
    const fname = expectedFiles[i];
    const fpath = path.join(OUT_DIR, fname);
    process.stdout.write(`  rendering  ${s.id} chunk ${i + 1}/${chunks.length} (${chunks[i].length} chars)... `);
    const mp3 = await tts(chunks[i]);
    await fs.writeFile(fpath, mp3);
    process.stdout.write(`${(mp3.length / 1024).toFixed(0)} KB\n`);
    totalChars += chunks[i].length;
    renderedChunks++;
  }
  out.sections.push({ id: s.id, title: s.title, files: expectedFiles, hash: h });
}

await fs.writeFile(MANIFEST_PATH, JSON.stringify(out, null, 2));

const costPerMillion = MODEL === 'tts-1-hd' ? 30 : 15;
const estCost = (totalChars / 1_000_000) * costPerMillion;

console.log('\nDone.');
console.log(`  Sections:        ${out.sections.length}`);
console.log(`  Chunks rendered: ${renderedChunks}  (skipped from cache: ${skipped})`);
console.log(`  Chars rendered:  ${totalChars.toLocaleString()}`);
console.log(`  Est. cost:       $${estCost.toFixed(3)}  (${MODEL} @ $${costPerMillion}/1M chars)`);
console.log(`  Manifest:        ${MANIFEST_PATH}`);
