"use strict";

const CACHE_NAME = "sales-executive-shell-v1";
const APP_PATHS = new Set(["/sales", "/sales/"]);
const STATIC_ASSET_PREFIX = "/assets/sales_executive_app/";
const PRECACHE_URLS = [
  "/assets/sales_executive_app/icons/sales-pwa.svg",
  "/assets/sales_executive_app/icons/sales-pwa-192.png",
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(names => Promise.all(names
        .filter(name => name.startsWith("sales-executive-shell-") && name !== CACHE_NAME)
        .map(name => caches.delete(name))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== "GET" || url.origin !== self.location.origin) return;

  if (request.mode === "navigate" && APP_PATHS.has(url.pathname)) {
    event.respondWith(fetch(request, { cache: "no-store" }).catch(() => new Response(
      "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta name=\"theme-color\" content=\"#F2F4F9\"><title>Sales Executive · Offline</title><body style=\"margin:0;padding:12vh 8vw;background:#f2f4f9;color:#17213a;font:16px/1.6 system-ui,sans-serif\"><main style=\"max-width:480px;margin:auto\"><h1>You’re offline</h1><p>Reconnect to the internet to securely load the Sales Executive App. Your account data and sales activity are never stored by this offline page.</p><button onclick=\"location.reload()\" style=\"padding:12px 18px;border:0;border-radius:10px;background:#3346d3;color:white;font-weight:700\">Try again</button></main></body></html>",
      { headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" } }
    )));
    return;
  }

  if (!url.pathname.startsWith(STATIC_ASSET_PREFIX)) return;

  event.respondWith(
    caches.open(CACHE_NAME).then(async cache => {
      try {
        const response = await fetch(request);
        if (response.ok && response.type === "basic") {
          await cache.put(request, response.clone());
        }
        return response;
      } catch (error) {
        const cached = await cache.match(request);
        if (cached) return cached;
        throw error;
      }
    })
  );
});
