const CACHE = "kattendienst-v2";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icon.svg"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    caches.match(e.request).then(cached => {
      const network = fetch(e.request).then(resp => {
        // ververs cache op de achtergrond
        const copy = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy)).catch(() => {});
        return resp;
      }).catch(() => cached);
      return cached || network;
    })
  );
});

// ===== Web Push: melding tonen ook als de app dicht is =====
self.addEventListener("push", e => {
  let data = {};
  try { data = e.data ? e.data.json() : {}; }
  catch (_) { data = { title: "🐱 Kattendienst", body: e.data ? e.data.text() : "" }; }
  const title = data.title || "🐱 Kattendienst";
  const opts = {
    body: data.body || "",
    tag: data.tag || "kattendienst",
    renotify: true,
    icon: "./icon.svg",
    badge: "./icon.svg",
    data: { url: data.url || "./index.html" }
  };
  e.waitUntil(self.registration.showNotification(title, opts));
});

self.addEventListener("notificationclick", e => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || "./index.html";
  e.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then(list => {
      for (const c of list) {
        if (c.url.includes("kattendienst") && "focus" in c) return c.focus();
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});
