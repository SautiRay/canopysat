const CACHE_NAME = 'canopysat-v21';
const STATIC_ASSETS = [
    '/',
    '/static/manifest.json',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
    'https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css',
    'https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js',
    'https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css',
    'https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js'
];

self.addEventListener('install', function(e) {
    e.waitUntil(
        caches.open(CACHE_NAME).then(function(cache) {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', function(e) {
    e.waitUntil(
        caches.keys().then(function(keys) {
            return Promise.all(
                keys.filter(function(k) { return k !== CACHE_NAME; })
                    .map(function(k) { return caches.delete(k); })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', function(e) {
    // Network first for API calls
    if (e.request.url.includes('/analyze') || 
        e.request.url.includes('/report')) {
        return;
    }
    e.respondWith(
        fetch(e.request).catch(function() {
            return caches.match(e.request);
        })
    );
});
