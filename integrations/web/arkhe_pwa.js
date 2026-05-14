// PWA service worker and manifest generator for Arkhe Web
const cacheName = 'arkhe-v790-pwa-cache';
const assets = [
    '/',
    '/index.html',
    '/arkhe_wasm_bridge.js',
    '/arkhe_worker.js',
    '/manifest.json'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(cacheName).then(cache => {
            return cache.addAll(assets);
        })
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});
