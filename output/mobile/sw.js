/* Service worker for the Agent Course mobile companion.
 *
 * Strategy:
 *   - Pre-cache the app shell (index + every module HTML + manifest + icon)
 *     during install so the whole course is available offline after first visit.
 *   - Same-origin GETs: cache-first, fall through to network on miss.
 *   - Google Fonts (cross-origin): stale-while-revalidate so installed PWAs
 *     get fresh CSS when online but render with last-good copy when offline.
 *   - Bump CACHE_VERSION to force a refresh of the precache list.
 */

const CACHE_VERSION = "agent-course-v1";
const RUNTIME_CACHE = "agent-course-runtime-v1";
const FONTS_CACHE = "agent-course-fonts-v1";

/* List explicit files so we can verify install completes only when each is fetched.
 * Keep this list in sync with output/mobile/ — regenerate via `ls output/mobile/`. */
const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icon.svg",
  "./M00-course-overview-agent-lifecycle-mobile.html",
  "./M01-llm-mental-model-mobile.html",
  "./M02-tokens-mobile.html",
  "./M03-prompts-mobile.html",
  "./M04-structured-output-mobile.html",
  "./M05-function-calling-mobile.html",
  "./M06-multi-tool-orchestration-mobile.html",
  "./M07-mcp-model-context-protocol-mobile.html",
  "./M08-conversation-management-mobile.html",
  "./M09-rag-retrieval-augmented-generation-mobile.html",
  "./M10-advanced-rag-patterns-mobile.html",
  "./M11-multi-layer-memory-mobile.html",
  "./M12-react-agent-loop-mobile.html",
  "./M13-planning-task-decomposition-mobile.html",
  "./M14-multi-agent-systems-mobile.html",
  "./M15-code-interpreter-sandbox-mobile.html",
  "./M15B-build-agent-subagent-system-mobile.html",
  "./M16-input-guardrails-mobile.html",
  "./M17-output-guardrails-hitl-mobile.html",
  "./M18-evaluation-testing-mobile.html",
  "./M19-tracing-logging-mobile.html",
  "./M20-monitoring-continuous-improvement-mobile.html",
  "./M21-api-design-deployment-mobile.html",
  "./M22-cost-optimization-mobile.html",
  "./M22B-deploy-local-cloud-mobile.html",
  "./M23-capstone-project-series-mobile.html",
  "./M24-whats-next-agent-frontier-mobile.html",
  "./M25-claude-code-mastery-mobile.html",
  "./M26-hooks-sessions-agent-sdk-mobile.html",
  "./M27-cert-exam-prep-mobile.html",
];

const FONT_HOSTS = ["fonts.googleapis.com", "fonts.gstatic.com"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_VERSION)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => ![CACHE_VERSION, RUNTIME_CACHE, FONTS_CACHE].includes(k))
            .map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);

  if (FONT_HOSTS.includes(url.hostname)) {
    event.respondWith(staleWhileRevalidate(req, FONTS_CACHE));
    return;
  }

  if (url.origin === self.location.origin) {
    event.respondWith(cacheFirst(req, RUNTIME_CACHE));
    return;
  }
});

async function cacheFirst(request, runtimeCacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(runtimeCacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    /* Offline and not in any cache. Try the index as a fallback for navigation requests. */
    if (request.mode === "navigate") {
      const fallback = await caches.match("./index.html");
      if (fallback) return fallback;
    }
    throw err;
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const networkPromise = fetch(request)
    .then((response) => {
      if (response && (response.ok || response.type === "opaque")) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => null);
  return cached || (await networkPromise) || new Response("", { status: 504 });
}
