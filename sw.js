/* Constellation Tracker service worker
 * - app shell: network-first (so updates arrive), cache fallback for offline
 * - versioned CDN libraries (Cesium, satellite.js): cache-first
 * - map imagery tiles: stale-while-revalidate, capped
 * - tle/ mirror: network-first
 * - CelesTrak: not intercepted (the page caches TLEs itself in Cache Storage)
 * Bump VERSION when you change index.html so installed apps pick up the new build. */
const VERSION = 'uct-v3';
const SHELL = VERSION + '-shell', CDN = VERSION + '-cdn', MIRROR = VERSION + '-mirror', TILES = 'uct-tiles';
const TILE_MAX = 1500;
const SHELL_FILES = ['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/apple-touch-icon.png'];
const CDN_FILES = [
  'https://cdn.jsdelivr.net/npm/cesium@1.121.0/Build/Cesium/Cesium.js',
  'https://cdn.jsdelivr.net/npm/cesium@1.121.0/Build/Cesium/Widgets/widgets.css',
  'https://cdnjs.cloudflare.com/ajax/libs/satellite.js/4.1.4/satellite.min.js'
];
const TILE_HOSTS = ['services.arcgisonline.com', 'server.arcgisonline.com', 'basemaps.cartocdn.com', 'gibs.earthdata.nasa.gov'];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    await (await caches.open(SHELL)).addAll(SHELL_FILES);
    const c = await caches.open(CDN);
    await Promise.all(CDN_FILES.map(u => c.add(u).catch(() => {})));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keep = new Set([SHELL, CDN, MIRROR, TILES, 'uct-tle-v1']);
    for (const k of await caches.keys()) if (!keep.has(k)) await caches.delete(k);
    await self.clients.claim();
  })());
});

async function networkFirst(req, cacheName) {
  const c = await caches.open(cacheName);
  try {
    const r = await fetch(req);
    if (r.ok) c.put(req, r.clone());
    return r;
  } catch (err) {
    const hit = await c.match(req, { ignoreSearch: req.mode === 'navigate' });
    if (hit) return hit;
    if (req.mode === 'navigate') { const idx = await c.match('index.html'); if (idx) return idx; }
    throw err;
  }
}
async function cacheFirst(req, cacheName) {
  const c = await caches.open(cacheName);
  const hit = await c.match(req);
  if (hit) return hit;
  const r = await fetch(req);
  if (r.ok) c.put(req, r.clone());
  return r;
}
let putCount = 0;
async function staleWhileRevalidate(req, cacheName) {
  const c = await caches.open(cacheName);
  const hit = await c.match(req);
  const net = fetch(req).then(r => {
    if (r.ok) {
      c.put(req, r.clone());
      if (++putCount % 50 === 0) c.keys().then(k => { for (let i = 0; i < k.length - TILE_MAX; i++) c.delete(k[i]); });
    }
    return r;
  }).catch(() => hit);
  return hit || net;
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === self.location.origin) {
    if (url.pathname.includes('/__local_tle/')) return;
    if (url.pathname.includes('/tle/')) return e.respondWith(networkFirst(req, MIRROR));
    return e.respondWith(networkFirst(req, SHELL));
  }
  if (url.hostname === 'cdn.jsdelivr.net' || url.hostname === 'cdnjs.cloudflare.com') return e.respondWith(cacheFirst(req, CDN));
  if (TILE_HOSTS.some(h => url.hostname.endsWith(h))) return e.respondWith(staleWhileRevalidate(req, TILES));
  // everything else (CelesTrak, …) goes straight to the network
});
