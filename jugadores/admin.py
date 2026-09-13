from django.contrib import admin

from .models import (
    Campeonato, Categoria, Club, Equipo, EstadisticaJuego, Jugador, Liga,
    Logro, Partido, PerfilAdministrador, Posicion, Representante, Video,
)


class ClubScopedAdmin(admin.ModelAdmin):
    """
    Restringe lo que ve un administrador de club: solo puede ver y editar
    registros que pertenezcan a su propio club. Los superusuarios (staff
    de la plataforma) siguen viendo todo.
    """
    club_lookup = "club"  # override en subclases cuando el path al club sea distinto

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            perfil = request.user.perfil_admin
        except PerfilAdministrador.DoesNotExist:
            return qs.none()
        if perfil.rol == "admin_liga":
            return qs
        filtro = {self.club_lookup: perfil.club}
        return qs.filter(**filtro)


@admin.register(Liga)
class LigaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "region")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rango_edad_ref")


@admin.register(Campeonato)
class CampeonatoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "liga", "categoria", "temporada")
    list_filter = ("liga", "categoria", "temporada")


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ciudad")


@admin.register(Equipo)
class EquipoAdmin(ClubScopedAdmin):
    club_lookup = "club"
    list_display = ("__str__", "campeonato")
    list_filter = ("campeonato",)


class RepresentanteInline(admin.StackedInline):
    model = Representante
    extra = 0


class VideoInline(admin.TabularInline):
    model = Video
    extra = 0


class EstadisticaJuegoInline(admin.TabularInline):
    model = EstadisticaJuego
    extra = 0
    fields = ("partido", "equipo", "posicion_jugada", "turnos", "hits", "impulsadas")
    show_change_link = True


class LogroInline(admin.TabularInline):
    model = Logro
    extra = 0


@admin.register(Jugador)
class JugadorAdmin(ClubScopedAdmin):
    club_lookup = "equipo__club"
    list_display = ("nombre", "equipo", "posicion_campo", "fecha_nacimiento")
    list_filter = ("equipo__campeonato__categoria", "posicion_campo")
    search_fields = ("nombre",)
    inlines = [RepresentanteInline, VideoInline, EstadisticaJuegoInline, LogroInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "equipo" and not request.user.is_superuser:
            try:
                perfil = request.user.perfil_admin
                if perfil.rol == "admin_club":
                    kwargs["queryset"] = Equipo.objects.filter(club=perfil.club)
            except PerfilAdministrador.DoesNotExist:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(EstadisticaJuego)
class EstadisticaJuegoAdmin(ClubScopedAdmin):
    club_lookup = "jugador__equipo__club"
    list_display = ("jugador", "fecha", "rival", "turnos", "hits", "impulsadas", "lanzo")
    list_filter = ("posicion_jugada",)
    fieldsets = (
        ("General", {"fields": ("jugador", "partido", "equipo", "posicion_jugada")}),
        ("Bateo", {"fields": (
            ("turnos", "hits"), ("dobles", "triples", "jonrones"),
            ("carreras_anotadas", "impulsadas", "bases_robadas"),
            ("ponches", "base_por_bolas"),
        )}),
        ("Defensa", {"fields": (("putouts", "asistencias", "errores"),)}),
        ("Pitcheo", {
            "fields": (("outs_lanzados", "carreras_permitidas"), ("hits_permitidos", "base_por_bolas_permitidas", "ponches_pitcheo")),
            "description": "Déjalo en cero si el jugador no lanzó en este partido.",
        }),
    )


@admin.register(Logro)
class LogroAdmin(ClubScopedAdmin):
    club_lookup = "jugador__equipo__club"
    list_display = ("jugador", "temporada", "descripcion")
    list_filter = ("temporada",)


@admin.register(Video)
class VideoAdmin(ClubScopedAdmin):
    club_lookup = "jugador__equipo__club"
    list_display = ("jugador", "juego", "tipo_toma", "fecha", "visibilidad")
    list_filter = ("tipo_toma", "visibilidad")


@admin.register(Posicion)
class PosicionAdmin(ClubScopedAdmin):
    club_lookup = "equipo__club"
    list_display = ("equipo", "campeonato", "fase", "juegos", "ganados", "perdidos", "puntos")
    list_filter = ("campeonato", "fase")


@admin.register(PerfilAdministrador)
class PerfilAdministradorAdmin(admin.ModelAdmin):
    list_display = ("user", "rol", "club")
    list_filter = ("rol",)


@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    list_display = ("equipo_local", "equipo_visitante", "fecha", "campeonato")
    list_filter = ("campeonato",)
