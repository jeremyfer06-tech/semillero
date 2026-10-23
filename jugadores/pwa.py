"""
Soporte de PWA (app web instalable) para Semillero.

- /manifest.webmanifest : describe la app (nombre, colores, íconos).
- /sw.js                : service worker (debe servirse desde la raíz para
                          controlar todo el sitio).
- /offline/             : página que se muestra cuando no hay conexión.
"""
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static

# Súbele el número cuando cambies el service worker, para que los
# teléfonos descarten la caché anterior.
CACHE_VERSION = "semillero-v1"

SERVICE_WORKER_JS = """
const VERSION = '__VERSION__';
const STATIC_CACHE = VERSION + '-static';
const OFFLINE_URL = '/offline/';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.add(new Request(OFFLINE_URL, { cache: 'reload' })))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== STATIC_CACHE).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;

  // Solo lecturas del mismo sitio; nunca formularios, videos (Range) ni otros dominios.
  if (req.method !== 'GET') return;
  if (req.headers.has('range')) return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // El panel y el admin siempre van directo a la red (login, CSRF, datos al día).
  if (url.pathname.startsWith('/panel/') || url.pathname.startsWith('/admin/')) return;
  if (url.pathname === '/sw.js') return;

  // Páginas: red primero; si no hay conexión, mostrar la página offline.
  if (req.mode === 'navigate') {
    event.respondWith(fetch(req).catch(() => caches.match(OFFLINE_URL)));
    return;
  }

  // Archivos estáticos (CSS, íconos): caché con actualización en segundo plano.
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.open(STATIC_CACHE).then((cache) =>
        cache.match(req).then((cached) => {
          const network = fetch(req)
            .then((res) => {
              if (res && res.ok) cache.put(req, res.clone());
              return res;
            })
            .catch(() => cached);
          return cached || network;
        })
      )
    );
  }
});
"""


def _static(path):
    """URL de un estático; si no está en el manifest de collectstatic, usa la ruta directa."""
    try:
        return static(path)
    except ValueError:
        return settings.STATIC_URL.rstrip("/") + "/" + path


def pwa_manifest(request):
    icono_192 = _static("jugadores/icons/icon-192.png")
    data = {
        "id": "/",
        "name": "Semillero",
        "short_name": "Semillero",
        "description": "Seguimiento del desarrollo de cada pelotero del béisbol menor venezolano.",
        "lang": "es",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#FAFAF7",
        "theme_color": "#1B7A43",
        "categories": ["sports"],
        "icons": [
            {"src": icono_192, "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": _static("jugadores/icons/icon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": _static("jugadores/icons/icon-maskable-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
        "shortcuts": [
            {
                "name": "Buscar jugadores",
                "url": "/buscador/",
                "icons": [{"src": icono_192, "sizes": "192x192", "type": "image/png"}],
            },
            {
                "name": "Categorías",
                "url": "/categorias/",
                "icons": [{"src": icono_192, "sizes": "192x192", "type": "image/png"}],
            },
        ],
    }
    return JsonResponse(data, content_type="application/manifest+json")


def pwa_service_worker(request):
    respuesta = HttpResponse(
        SERVICE_WORKER_JS.replace("__VERSION__", CACHE_VERSION),
        content_type="application/javascript",
    )
    # Que el navegador siempre revise si hay una versión nueva del service worker.
    respuesta["Cache-Control"] = "no-cache"
    return respuesta


def pwa_offline(request):
    return render(request, "jugadores/offline.html")
