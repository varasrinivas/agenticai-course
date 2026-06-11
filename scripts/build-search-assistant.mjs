#!/usr/bin/env node
/**
 * build-search-assistant.mjs
 *
 * Builds a search-assistant.html in every course folder under output/courses/ —
 * a fully offline, self-contained search assistant per course. It extracts the
 * plain text of every module section into a JSON index embedded directly in the
 * page, so a learner can instantly check which modules cover a word or topic
 * with no internet connection and no API calls.
 *
 * Usage: node scripts/build-search-assistant.mjs [course-folder ...]
 *        (no args = build all courses)
 * No dependencies — plain Node (regex-based HTML text extraction).
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const COURSES_ROOT = path.join(ROOT, 'output', 'courses');

// ---------------------------------------------------------------- extraction

const ENTITIES = {
  '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'",
  '&apos;': "'", '&nbsp;': ' ', '&mdash;': '—', '&ndash;': '–',
  '&rarr;': '→', '&larr;': '←', '&hellip;': '…', '&times;': '×',
};

function decodeEntities(s) {
  return s
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(Number(d)))
    .replace(/&[a-z]+;/gi, (m) => ENTITIES[m.toLowerCase()] ?? ' ');
}

const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function stripTags(html) {
  return decodeEntities(
    html
      .replace(/<script[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style[\s\S]*?<\/style>/gi, ' ')
      .replace(/<[^>]+>/g, ' ')
  ).replace(/\s+/g, ' ').trim();
}

function firstHeading(html) {
  const m = html.match(/<h[123][^>]*>([\s\S]*?)<\/h[123]>/i);
  return m ? stripTags(m[1]) : '';
}

/** Split a module body into sections keyed by anchor id. */
function extractSections(body) {
  const sections = [];
  const re = /<section[^>]*\bid="([^"]+)"[^>]*>/gi;
  const hits = [];
  let m;
  while ((m = re.exec(body)) !== null) hits.push({ id: m[1], start: m.index });

  if (hits.length >= 2) {
    for (let i = 0; i < hits.length; i++) {
      const chunk = body.slice(hits[i].start, hits[i + 1]?.start ?? body.length);
      const text = stripTags(chunk);
      if (text.length < 40) continue;
      sections.push({ id: hits[i].id, title: firstHeading(chunk) || hits[i].id, text });
    }
    return sections;
  }

  // Fallback for pages without <section id> structure: split on h2/h3 with ids.
  const hre = /<h([23])[^>]*\bid="([^"]+)"[^>]*>([\s\S]*?)<\/h\1>/gi;
  const heads = [];
  while ((m = hre.exec(body)) !== null) {
    heads.push({ id: m[2], title: stripTags(m[3]), start: m.index });
  }
  if (heads.length >= 2) {
    for (let i = 0; i < heads.length; i++) {
      const chunk = body.slice(heads[i].start, heads[i + 1]?.start ?? body.length);
      const text = stripTags(chunk);
      if (text.length < 40) continue;
      sections.push({ id: heads[i].id, title: heads[i].title || heads[i].id, text });
    }
    return sections;
  }

  // Last resort: whole page as one section.
  const text = stripTags(body);
  if (text.length >= 40) sections.push({ id: '', title: '', text });
  return sections;
}

// ------------------------------------------------------------------ indexing

const SKIP = new Set(['index.html', 'search-assistant.html']);

/** Course display name from its index.html <title>, cleaned of suffixes. */
function courseName(courseDir, fallback) {
  const idx = path.join(courseDir, 'index.html');
  if (!fs.existsSync(idx)) return fallback;
  const m = fs.readFileSync(idx, 'utf8').match(/<title>([\s\S]*?)<\/title>/i);
  if (!m) return fallback;
  return stripTags(m[1]).replace(/\s*[—–-]\s*Course Home\s*$/i, '').trim() || fallback;
}

function buildIndex(courseDir) {
  const files = fs.readdirSync(courseDir)
    .filter((f) => f.endsWith('.html') && !SKIP.has(f))
    .filter((f) => fs.statSync(path.join(courseDir, f)).isFile())
    .sort();

  const index = [];
  for (const file of files) {
    const html = fs.readFileSync(path.join(courseDir, file), 'utf8');
    const title = stripTags((html.match(/<title>([\s\S]*?)<\/title>/i) || [, file])[1])
      .replace(/\s*\|[^|]*$/, '');
    const body = html
      .replace(/<head[\s\S]*?<\/head>/i, ' ')
      .replace(/<script[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style[\s\S]*?<\/style>/gi, ' ');
    const sections = extractSections(body);
    if (sections.length === 0) {
      console.warn(`  ! no extractable text: ${file}`);
      continue;
    }
    index.push({ file, title, sections });
  }
  return index;
}

// ----------------------------------------------------------------- page shell

function renderPage(course, index) {
  // JSON inside a <script> tag: escape the only dangerous sequence.
  const indexJson = JSON.stringify(index).replace(/<\//g, '<\\/');
  const builtOn = new Date().toISOString().slice(0, 10);

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Course Search Assistant | ${esc(course)}</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg-primary: #0A1628; --bg-secondary: #111D33; --bg-card: #162033; --bg-surface: #1A2740;
    --text-primary: #E8ECF1; --text-secondary: #94A3B8; --text-muted: #64748B;
    --accent-primary: #D4A843; --accent-muted: rgba(212, 168, 67, 0.15);
    --success: #10B981; --info: #3B82F6; --info-bg: rgba(59, 130, 246, 0.1);
    --code-border: #21262D;
  }
  body { background: var(--bg-primary); color: var(--text-primary); font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; font-size: 1rem; line-height: 1.6; min-height: 100vh; }
  header { background: var(--bg-secondary); border-bottom: 1px solid var(--code-border); padding: 1.25rem 2rem; position: sticky; top: 0; z-index: 50; }
  .header-inner { max-width: 960px; margin: 0 auto; }
  h1 { font-size: 1.4rem; font-weight: 800; }
  h1 .badge { display: inline-block; margin-left: 0.6rem; font-size: 0.7rem; font-weight: 700; vertical-align: middle; background: var(--accent-muted); color: var(--accent-primary); border: 1px solid var(--accent-primary); border-radius: 20px; padding: 0.15rem 0.6rem; }
  .sub { color: var(--text-muted); font-size: 0.85rem; margin-top: 0.2rem; }
  .searchrow { max-width: 960px; margin: 0.9rem auto 0; display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: center; }
  #q { flex: 1; min-width: 260px; background: var(--bg-card); border: 1px solid var(--code-border); border-radius: 10px; color: var(--text-primary); font-size: 1.05rem; padding: 0.65rem 1rem; outline: none; }
  #q:focus { border-color: var(--accent-primary); }
  select, label.opt { background: var(--bg-card); border: 1px solid var(--code-border); border-radius: 10px; color: var(--text-secondary); font-size: 0.85rem; padding: 0.55rem 0.75rem; }
  label.opt { display: inline-flex; align-items: center; gap: 0.4rem; cursor: pointer; user-select: none; }
  main { max-width: 960px; margin: 0 auto; padding: 1.5rem 2rem 4rem; }
  .stats { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1rem; }
  .stats strong { color: var(--accent-primary); }
  table.coverage { border-collapse: collapse; width: 100%; margin: 0.75rem 0 1.5rem; font-size: 0.85rem; }
  table.coverage th, table.coverage td { text-align: left; padding: 0.3rem 0.75rem; border-bottom: 1px solid var(--code-border); }
  table.coverage th { color: var(--text-muted); font-weight: 600; }
  table.coverage td.n { color: var(--accent-primary); font-weight: 700; white-space: nowrap; }
  .doc { background: var(--bg-card); border: 1px solid var(--code-border); border-radius: 12px; margin-bottom: 1rem; overflow: hidden; }
  .doc-head { padding: 0.8rem 1.25rem; background: var(--bg-surface); display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; flex-wrap: wrap; }
  .doc-head a { color: var(--text-primary); font-weight: 700; text-decoration: none; }
  .doc-head a:hover { color: var(--accent-primary); }
  .doc-head .count { color: var(--text-muted); font-size: 0.8rem; white-space: nowrap; }
  .sec { padding: 0.9rem 1.25rem; border-top: 1px solid var(--code-border); }
  .sec a.sec-title { color: var(--info); font-weight: 600; font-size: 0.95rem; text-decoration: none; }
  .sec a.sec-title:hover { text-decoration: underline; }
  .snippet { color: var(--text-secondary); font-size: 0.9rem; margin-top: 0.35rem; }
  mark { background: var(--accent-primary); color: #0A1628; border-radius: 3px; padding: 0 2px; font-weight: 600; }
  .empty { color: var(--text-muted); text-align: center; padding: 3rem 0; }
  .browse h2 { font-size: 1.05rem; margin: 1.5rem 0 0.5rem; color: var(--text-primary); }
  .browse h2 a { color: inherit; text-decoration: none; } .browse h2 a:hover { color: var(--accent-primary); }
  .browse ul { list-style: none; margin: 0; display: flex; flex-wrap: wrap; gap: 0.4rem; }
  .browse li a { display: inline-block; background: var(--bg-card); border: 1px solid var(--code-border); border-radius: 16px; padding: 0.2rem 0.7rem; font-size: 0.78rem; color: var(--text-secondary); text-decoration: none; }
  .browse li a:hover { color: var(--accent-primary); border-color: var(--accent-primary); }
  kbd { background: var(--bg-surface); border: 1px solid var(--code-border); border-radius: 4px; padding: 0 5px; font-size: 0.8em; }
  @media (max-width: 768px) { header, main { padding-left: 1rem; padding-right: 1rem; } }
  @media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <h1>Course Search Assistant <span class="badge">100% OFFLINE</span></h1>
    <div class="sub">${esc(course)} — instantly check which modules cover a word or topic. No internet, no API. Built ${builtOn}.</div>
  </div>
  <div class="searchrow">
    <input id="q" type="search" placeholder="Type a word or topic…  e.g. MCP, embeddings, hooks, HIPAA, rate limit" autofocus aria-label="Search the course">
    <label class="opt"><input type="checkbox" id="whole"> whole word</label>
    <select id="scope" aria-label="Limit search to one file"><option value="">All files</option></select>
  </div>
</header>
<main>
  <div id="out"></div>
</main>
<script id="course-index" type="application/json">${indexJson}</script>
<script>
'use strict';
const INDEX = JSON.parse(document.getElementById('course-index').textContent);
const $q = document.getElementById('q'), $whole = document.getElementById('whole'),
      $scope = document.getElementById('scope'), $out = document.getElementById('out');

for (const d of INDEX) {
  const o = document.createElement('option');
  o.value = d.file; o.textContent = d.title || d.file;
  $scope.appendChild(o);
}

const esc = (s) => s.replace(/[&<>"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const escRe = (s) => s.replace(/[.*+?^\${}()|[\\]\\\\]/g, '\\\\$&');

function buildRegex(query, wholeWord) {
  const terms = query.trim().split(/\\s+/).filter((t) => t.length >= 2);
  if (!terms.length) return null;
  const pats = terms.map((t) => wholeWord ? '\\\\b' + escRe(t) + '\\\\b' : escRe(t));
  return { terms: pats.map((p) => new RegExp(p, 'gi')), any: new RegExp(pats.join('|'), 'gi') };
}

function snippetsFor(text, re, max) {
  const out = []; re.any.lastIndex = 0; let m, guard = 0;
  while (out.length < max && (m = re.any.exec(text)) !== null && guard++ < 500) {
    const lo = Math.max(0, m.index - 90), hi = Math.min(text.length, m.index + m[0].length + 110);
    out.push((lo > 0 ? '…' : '') + text.slice(lo, hi) + (hi < text.length ? '…' : ''));
    re.any.lastIndex = m.index + Math.max(m[0].length, 160); // space snippets apart
  }
  return out;
}

const hl = (s, re) => esc(s).replace(re.any, (m) => '<mark>' + m + '</mark>');

function search() {
  const query = $q.value, scope = $scope.value;
  const re = buildRegex(query, $whole.checked);
  if (!re) { renderBrowse(); return; }

  const docs = [];
  let totalHits = 0, totalSections = 0;
  for (const d of INDEX) {
    if (scope && d.file !== scope) continue;
    const secs = [];
    let docHits = 0;
    for (const s of d.sections) {
      // AND semantics: every term must appear in the section
      let count = 0, all = true;
      for (const t of re.terms) {
        const c = (s.text.match(t) || []).length + (s.title.match(t) || []).length * 4;
        if (c === 0) { all = false; break; }
        count += c;
      }
      if (!all) continue;
      secs.push({ s, count });
      docHits += count;
    }
    if (secs.length) {
      secs.sort((a, b) => b.count - a.count);
      docs.push({ d, secs, docHits });
      totalHits += docHits; totalSections += secs.length;
    }
  }
  docs.sort((a, b) => b.docHits - a.docHits);

  if (!docs.length) {
    $out.innerHTML = '<div class="empty">No matches for <strong>' + esc(query) +
      '</strong>' + ($whole.checked ? ' (whole-word is on — try unchecking it)' : '') + '.</div>';
    return;
  }

  let html = '<div class="stats"><strong>' + totalHits + '</strong> matches in <strong>' +
    totalSections + '</strong> sections across <strong>' + docs.length + '</strong> files</div>';

  // coverage table for quick topic checks
  html += '<table class="coverage"><tr><th>File</th><th>Matches</th><th>Sections</th></tr>';
  for (const { d, secs, docHits } of docs) {
    html += '<tr><td><a class="sec-title" href="' + esc(d.file) + '">' + esc(d.title || d.file) +
      '</a></td><td class="n">' + docHits + '</td><td>' + secs.length + '</td></tr>';
  }
  html += '</table>';

  for (const { d, secs, docHits } of docs) {
    html += '<div class="doc"><div class="doc-head"><a href="' + esc(d.file) + '">' +
      esc(d.title || d.file) + '</a><span class="count">' + docHits + ' matches</span></div>';
    for (const { s, count } of secs.slice(0, 8)) {
      const href = esc(d.file) + (s.id ? '#' + esc(s.id) : '');
      html += '<div class="sec"><a class="sec-title" href="' + href + '">' +
        (s.title ? hl(s.title, re) : '(page)') + '</a> <span class="count" style="color:var(--text-muted);font-size:0.75rem">' + count + '×</span>';
      for (const sn of snippetsFor(s.text, re, 2)) {
        html += '<div class="snippet">' + hl(sn, re) + '</div>';
      }
      html += '</div>';
    }
    if (secs.length > 8) html += '<div class="sec" style="color:var(--text-muted)">… ' + (secs.length - 8) + ' more sections</div>';
    html += '</div>';
  }
  $out.innerHTML = html;
}

function renderBrowse() {
  let html = '<div class="stats">Browse all topics — or type above to search. Press <kbd>/</kbd> to focus the search box.</div><div class="browse">';
  for (const d of INDEX) {
    html += '<h2><a href="' + esc(d.file) + '">' + esc(d.title || d.file) + '</a></h2><ul>';
    for (const s of d.sections) {
      if (!s.title) continue;
      html += '<li><a href="' + esc(d.file) + (s.id ? '#' + esc(s.id) : '') + '">' + esc(s.title) + '</a></li>';
    }
    html += '</ul>';
  }
  $out.innerHTML = html + '</div>';
}

let timer;
const onChange = () => { clearTimeout(timer); timer = setTimeout(search, 120); };
$q.addEventListener('input', onChange);
$whole.addEventListener('change', search);
$scope.addEventListener('change', search);
document.addEventListener('keydown', (e) => {
  if (e.key === '/' && document.activeElement !== $q) { e.preventDefault(); $q.focus(); $q.select(); }
});
renderBrowse();
</script>
</body>
</html>
`;
}

// --------------------------------------------------------------------- main

const requested = process.argv.slice(2);
const courses = (requested.length
  ? requested
  : fs.readdirSync(COURSES_ROOT).filter((d) =>
      fs.statSync(path.join(COURSES_ROOT, d)).isDirectory()))
  .sort();

for (const slug of courses) {
  const courseDir = path.join(COURSES_ROOT, slug);
  if (!fs.existsSync(courseDir)) {
    console.error(`! no such course folder: ${slug}`);
    process.exitCode = 1;
    continue;
  }
  const index = buildIndex(courseDir);
  if (index.length === 0) {
    console.warn(`! ${slug}: no indexable files, skipped`);
    continue;
  }
  const course = courseName(courseDir, slug);
  const outFile = path.join(courseDir, 'search-assistant.html');
  fs.writeFileSync(outFile, renderPage(course, index), 'utf8');
  const sectionCount = index.reduce((n, d) => n + d.sections.length, 0);
  console.log(
    `${slug}: ${index.length} files, ${sectionCount} sections → ` +
    `${path.relative(ROOT, outFile)} (${(fs.statSync(outFile).size / 1024 / 1024).toFixed(1)} MB)`);
}
