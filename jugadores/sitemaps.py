from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Categoria, Jugador


class PaginasEstaticasSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return ["inicio", "buscador_jugadores", "categorias_lista"]

    def location(self, item):
        return reverse(item)


class CategoriaSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Categoria.objects.all()

    def location(self, obj):
        return reverse("categoria_detalle", args=[obj.id])


class JugadorSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Jugador.objects.select_related("equipo").all()

    def location(self, obj):
        return reverse("ficha_jugador", args=[obj.id])

    def lastmod(self, obj):
        return None


sitemaps = {
    "estaticas": PaginasEstaticasSitemap,
    "categorias": CategoriaSitemap,
    "jugadores": JugadorSitemap,
}
