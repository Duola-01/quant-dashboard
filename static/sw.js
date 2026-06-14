// 量化监控台 — Service Worker (离线缓存)
const CACHE = "quant-monitor-v1";

self.addEventListener("install", (e) => {
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
});

self.addEventListener("fetch", (e) => {
  // 对于 Streamlit 的 WebSocket 连接，直接放行（不缓存）
  if (e.request.url.includes("_stcore/stream")) {
    return;
  }
  e.respondWith(
    caches.match(e.request).then(
      (cached) => cached || fetch(e.request).then((resp) => {
        if (resp.ok && e.request.method === "GET") {
          const clone = resp.clone();
          caches.open(CACHE).then((cache) =>
            cache.put(e.request, clone)
          );
        }
        return resp;
      })
    )
  );
});
