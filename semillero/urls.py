"""
URL configuration for semillero project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path

from jugadores.sitemaps import sitemaps
from jugadores.views import (
    buscador_jugadores, categoria_detalle, categorias_lista,
    debug_conexion, detalle_juego, equipo_detalle, ficha_jugador, inicio,
    panel_dashboard, panel_equipo_form, panel_jugador_consentimiento_pdf, panel_jugador_form, panel_login, panel_logout,
    panel_liga_calendario, panel_liga_dashboard, panel_liga_equipos,
    panel_liga_partido_detalle, panel_liga_posicion_eliminar, panel_liga_stats_form,
    panel_video_eliminar, panel_video_form, panel_videos, robots_txt,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('debug-conexion/', debug_conexion, name='debug_conexion'),
    path('', inicio, name='inicio'),
    path('buscador/', buscador_jugadores, name='buscador_jugadores'),
    path('categorias/', categorias_lista, name='categorias_lista'),
    path('categoria/<int:categoria_id>/', categoria_detalle, name='categoria_detalle'),
    path('equipo/<int:equipo_id>/', equipo_detalle, name='equipo_detalle'),
    path('jugador/<int:jugador_id>/', ficha_jugador, name='ficha_jugador'),
    path('jugador/<int:jugador_id>/juego/<int:juego_id>/', detalle_juego, name='detalle_juego'),

    # Panel del administrador de equipo
    path('panel/login/', panel_login, name='panel_login'),
    path('panel/logout/', panel_logout, name='panel_logout'),
    path('panel/', panel_dashboard, name='panel_dashboard'),
    path('panel/equipo/nuevo/', panel_equipo_form, name='panel_equipo_nuevo'),
    path('panel/equipo/<int:equipo_id>/editar/', panel_equipo_form, name='panel_equipo_editar'),
    path('panel/jugador/nuevo/', panel_jugador_form, name='panel_jugador_nuevo'),
    path('panel/jugador/<int:jugador_id>/editar/', panel_jugador_form, name='panel_jugador_editar'),
    path('panel/jugador/<int:jugador_id>/consentimiento/', panel_jugador_consentimiento_pdf, name='panel_jugador_consentimiento_pdf'),

    # Panel del camarógrafo / encargado de video
    path('panel/videos/', panel_videos, name='panel_videos'),
    path('panel/videos/juego/<int:juego_id>/nuevo/', panel_video_form, name='panel_video_nuevo'),
    path('panel/videos/<int:video_id>/eliminar/', panel_video_eliminar, name='panel_video_eliminar'),

    # Panel del administrador de liga
    path('panel/liga/', panel_liga_dashboard, name='panel_liga_dashboard'),
    path('panel/liga/calendario/', panel_liga_calendario, name='panel_liga_calendario'),
    path('panel/liga/partido/<int:partido_id>/', panel_liga_partido_detalle, name='panel_liga_partido_detalle'),
    path('panel/liga/partido/<int:partido_id>/jugador/<int:jugador_id>/', panel_liga_stats_form, name='panel_liga_stats_form'),
    path('panel/liga/equipos/', panel_liga_equipos, name='panel_liga_equipos'),
    path('panel/liga/equipos/<int:posicion_id>/eliminar/', panel_liga_posicion_eliminar, name='panel_liga_posicion_eliminar'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
