// Klondike Service Worker for Offline Support
const CACHE_NAME = "klondike-cache-v1";
const STATIC_CACHE_NAME = "klondike-static-v1";
const API_CACHE_NAME = "klondike-api-v1";

// Static assets to cache on install
const STATIC_ASSETS = ["/", "/index.html"];

// API routes that should be cached with network-first strategy
const API_ROUTES = ["/api/status", "/api/features", "/api/progress"];

// Install event - cache static assets
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME).then((cache) => {
            console.log("[SW] Caching static assets");
            return cache.addAll(STATIC_ASSETS);
        })
    );
    // Activate immediately without waiting
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => !name.startsWith("klondike-"))
                    .map((name) => {
                        console.log("[SW] Deleting old cache:", name);
                        return caches.delete(name);
                    })
            );
        })
    );
    // Claim all clients immediately
    self.clients.claim();
});

// Network first strategy for API calls
async function networkFirstStrategy(request) {
    const cache = await caches.open(API_CACHE_NAME);

    try {
        const networkResponse = await fetch(request);

        // Clone and cache the response
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        // Network failed, try cache
        const cachedResponse = await cache.match(request);

        if (cachedResponse) {
            console.log("[SW] Serving from cache:", request.url);
            return cachedResponse;
        }

        // Return offline response if no cache
        return new Response(
            JSON.stringify({ error: "Offline", message: "You are offline and no cached data is available" }),
            {
                status: 503,
                headers: { "Content-Type": "application/json" },
            }
        );
    }
}

// Cache first strategy for static assets
async function cacheFirstStrategy(request) {
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        // Return cached, but update in background
        updateCache(request);
        return cachedResponse;
    }

    // Not in cache, fetch from network
    try {
        const networkResponse = await fetch(request);

        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        // Return offline page if available
        const offlinePage = await caches.match("/");
        if (offlinePage) {
            return offlinePage;
        }

        return new Response("Offline", { status: 503 });
    }
}

// Update cache in background
async function updateCache(request) {
    try {
        const cache = await caches.open(STATIC_CACHE_NAME);
        const response = await fetch(request);
        if (response.ok) {
            await cache.put(request, response);
        }
    } catch (error) {
        // Silently fail background updates
    }
}

// Fetch event - network first for API, cache first for static
self.addEventListener("fetch", (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== "GET") {
        return;
    }

    // Skip WebSocket connections
    if (url.protocol === "ws:" || url.protocol === "wss:") {
        return;
    }

    // API routes - network first with cache fallback
    if (API_ROUTES.some((route) => url.pathname.startsWith(route))) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }

    // Static assets - cache first with network fallback
    if (url.origin === self.location.origin) {
        event.respondWith(cacheFirstStrategy(request));
        return;
    }
});

// Handle messages from the main thread
self.addEventListener("message", (event) => {
    if (event.data?.type === "SKIP_WAITING") {
        self.skipWaiting();
    }

    if (event.data?.type === "CLEAR_CACHE") {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(cacheNames.map((name) => caches.delete(name)));
            })
        );
    }
});
