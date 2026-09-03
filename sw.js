const CACHE_NAME = 'aquele-abraco-v3.5.0';

// Apenas os arquivos fixos do seu repositório
const STATIC_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './cbtData.js',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      )
    )
  );
  self.clients.claim();
});

// O CÉREBRO ATUALIZADO: CACHE DINÂMICO
self.addEventListener('fetch', (event) => {
  // Ignora requisições que não sejam GET (ex: envios de POST pra API)
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      // 1. Se já tem no cache (seja estático ou dinâmico), retorna instantaneamente
      if (cachedResponse) {
        return cachedResponse;
      }
      
      // 2. Se não tem no cache, busca na internet
      return fetch(event.request).then((networkResponse) => {
        // Verifica se é uma resposta válida da internet para não salvar lixo no cache
        if (!networkResponse || networkResponse.status !== 200 || (networkResponse.type !== 'basic' && networkResponse.type !== 'cors')) {
          return networkResponse;
        }

        // 3. Clona a resposta da internet (como o script do WebLLM)
        const responseToCache = networkResponse.clone();

        // 4. Guarda o clone no cache dinâmico para a próxima vez que faltar internet
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });

        return networkResponse;
      }).catch(() => {
        // Se a internet cair e o arquivo não estiver em nenhum cache, mostra o index estático
        if (event.request.mode === 'navigate') {
          return caches.match('./index.html');
        }
      });
    })
  );
});

// Listener para receber ordem de atualização silenciosa (skipWaiting)
self.addEventListener('message', (event) => {
  if (event.data && event.data.action === 'skipWaiting') {
    self.skipWaiting();
  }
});
