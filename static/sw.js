const CACHE_NAME = 'eduvault-v3';
const ASSETS = [
    '/static/css/style.css',
    '/static/js/responsive.js',
    'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap'
];

// Install Event
self.addEventListener('install', (e) => {
    self.skipWaiting();
    e.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS);
        })
    );
});

// Activate Event
self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch Event - Network First for HTML, Cache First for Assets
self.addEventListener('fetch', (e) => {
    // HTML / Navigation requests -> Network First
    if (e.request.mode === 'navigate') {
        e.respondWith(
            fetch(e.request).catch(() => {
                return caches.match(e.request);
            })
        );
        return;
    }

    // Static Assets -> Cache First
    e.respondWith(
        caches.match(e.request).then((response) => {
            return response || fetch(e.request);
        })
    );
});
