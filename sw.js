// Offline cache. Change VERSION whenever index.html or questions.json changes so phones pick up updates.
const VERSION = "36e0a6c2bb";
const CORE = ["./", "index.html", "questions.json", "manifest.webmanifest", "icon.svg", "icon-180.png", "icon-192.png", "icon-512.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(VERSION).then(c => c.addAll(CORE)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  const save = r => { const c = r.clone(); caches.open(VERSION).then(x => x.put(e.request, c)); return r; };
  // Page and questions: network first so edits arrive, cache when offline. Fonts and icons: cache first.
  // Audio clips stream from the network: Safari plays media with range requests, which a cache-first worker would break.
  if (url.pathname.includes("/audio/") && url.pathname.endsWith(".mp3")) return;
  if (e.request.mode === "navigate" || url.pathname.endsWith("questions.json") || url.pathname.endsWith("audio/index.json")) {
    e.respondWith(fetch(e.request).then(save).catch(() => caches.match(e.request, { ignoreSearch: true }).then(r => r || caches.match("index.html"))));
    return;
  }
  if (url.origin === location.origin || /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) {
    e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(save)));
  }
});
