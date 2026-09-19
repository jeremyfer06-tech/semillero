import unicodedata

from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, render

from .estadisticas import calcular_bateo, calcular_defensa, calcular_ops_plus, calcular_pitcheo
from .models import Categoria, Club, Equipo, EstadisticaJuego, Jugador, Liga, Posicion


def normalizar(texto):
    """Quita tildes/acentos y pasa a minúsculas, para comparar sin importar cómo se haya escrito."""
    texto = texto or ''
    sin_acentos = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return sin_acentos.lower()

UMBRAL_POSICION_REGULAR = 20  # % mínimo de juegos en una posición para considerarla "regular"

CAMPOS_BATEO = ['turnos', 'hits', 'dobles', 'triples', 'jonrones', 'carreras_anotadas',
                'impulsadas', 'bases_robadas', 'ponches', 'base_por_bolas']
CAMPOS_DEFENSA = ['putouts', 'asistencias', 'errores']
CAMPOS_PITCHEO = ['outs_lanzados', 'carreras_permitidas', 'hits_permitidos',
                   'base_por_bolas_permitidas', 'ponches_pitcheo']


def _agregar(queryset, campos):
    return queryset.aggregate(**{c: Sum(c) for c in campos})


def inicio(request):
    context = {
        'total_jugadores': Jugador.objects.count(),
        'total_equipos': Equipo.objects.count(),
        'total_clubes': Club.objects.count(),
        'total_categorias': Categoria.objects.count(),
    }
    return render(request, 'jugadores/inicio.html', context)


def categorias_lista(request):
    categorias = Categoria.objects.annotate(
        total_equipos=Count('campeonatos__equipos', distinct=True),
        total_jugadores=Count('campeonatos__equipos__jugadores', distinct=True),
    ).order_by('orden')
    return render(request, 'jugadores/categorias.html', {'categorias': categorias})


def categoria_detalle(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    equipos = (
        Equipo.objects
        .filter(campeonato__categoria=categoria)
        .select_related('club', 'campeonato', 'campeonato__liga')
        .annotate(total_jugadores=Count('jugadores'))
        .order_by('club__nombre', 'escuadra')
    )
    posiciones = (
        Posicion.objects
        .filter(equipo__campeonato__categoria=categoria)
        .select_related('equipo', 'equipo__club')
        .order_by('fase', '-puntos', '-carreras_favor')
    )
    return render(request, 'jugadores/categoria_detalle.html', {
        'categoria': categoria, 'equipos': equipos, 'posiciones': posiciones,
    })


def equipo_detalle(request, equipo_id):
    equipo = get_object_or_404(
        Equipo.objects.select_related('club', 'campeonato', 'campeonato__categoria', 'campeonato__liga'),
        pk=equipo_id,
    )
    jugadores = equipo.jugadores.all().order_by('nombre')
    return render(request, 'jugadores/equipo_detalle.html', {
        'equipo': equipo, 'jugadores': jugadores,
    })


def buscador_jugadores(request):
    q = request.GET.get('q', '').strip()
    liga_id = request.GET.get('liga', '')
    categoria_id = request.GET.get('categoria', '')
    club_id = request.GET.get('club', '')
    anio_min = request.GET.get('anio_min', '')
    anio_max = request.GET.get('anio_max', '')

    hay_busqueda = bool(q or liga_id or categoria_id or club_id or anio_min or anio_max)

    jugadores = None
    categorias_browse = None

    if hay_busqueda:
        jugadores_qs = (
            Jugador.objects
            .select_related(
                'equipo', 'equipo__club', 'equipo__campeonato',
                'equipo__campeonato__categoria', 'equipo__campeonato__liga',
            )
        )
        if liga_id:
            jugadores_qs = jugadores_qs.filter(equipo__campeonato__liga_id=liga_id)
        if categoria_id:
            jugadores_qs = jugadores_qs.filter(equipo__campeonato__categoria_id=categoria_id)
        if club_id:
            jugadores_qs = jugadores_qs.filter(equipo__club_id=club_id)
        if anio_min:
            jugadores_qs = jugadores_qs.filter(fecha_nacimiento__year__gte=anio_min)
        if anio_max:
            jugadores_qs = jugadores_qs.filter(fecha_nacimiento__year__lte=anio_max)

        if q:
            q_normalizado = normalizar(q)
            jugadores = [j for j in jugadores_qs if q_normalizado in normalizar(j.nombre)]
        else:
            jugadores = list(jugadores_qs)
    else:
        categorias_browse = Categoria.objects.annotate(
            total_equipos=Count('campeonatos__equipos', distinct=True),
            total_jugadores=Count('campeonatos__equipos__jugadores', distinct=True),
        ).order_by('orden')

    context = {
        'hay_busqueda': hay_busqueda,
        'jugadores': jugadores,
        'total_resultados': len(jugadores) if jugadores is not None else 0,
        'categorias_browse': categorias_browse,
        'ligas': Liga.objects.all(),
        'categorias': Categoria.objects.all(),
        'clubes': Club.objects.all(),
        'filtros': {
            'q': q, 'liga': liga_id, 'categoria': categoria_id,
            'club': club_id, 'anio_min': anio_min, 'anio_max': anio_max,
        },
    }
    return render(request, 'jugadores/buscador.html', context)


def ficha_jugador(request, jugador_id):
    jugador = get_object_or_404(
        Jugador.objects.select_related(
            'equipo', 'equipo__club', 'equipo__campeonato',
            'equipo__campeonato__categoria', 'equipo__campeonato__liga',
        ),
        pk=jugador_id,
    )

    todos_los_juegos = jugador.estadisticas_juego.select_related('equipo', 'partido', 'partido__equipo_local', 'partido__equipo_visitante').order_by('partido__fecha')
    juegos_temporada = todos_los_juegos.filter(equipo__campeonato_id=jugador.equipo.campeonato_id)

    # --- Bateo: temporada actual vs. de por vida ---
    bateo_temporada = calcular_bateo(_agregar(juegos_temporada, CAMPOS_BATEO))
    bateo_vida = calcular_bateo(_agregar(todos_los_juegos, CAMPOS_BATEO))

    # OPS+ relativo al promedio de la misma categoría y temporada en esta base de datos
    liga_qs = EstadisticaJuego.objects.filter(
        equipo__campeonato__categoria=jugador.equipo.campeonato.categoria,
        equipo__campeonato__temporada=jugador.equipo.campeonato.temporada,
    )
    bateo_liga = calcular_bateo(_agregar(liga_qs, CAMPOS_BATEO))
    ops_plus_temporada = calcular_ops_plus(bateo_temporada, bateo_liga['obp'], bateo_liga['slg'])

    # --- Defensa ---
    defensa_temporada = calcular_defensa(_agregar(juegos_temporada, CAMPOS_DEFENSA))
    defensa_vida = calcular_defensa(_agregar(todos_los_juegos, CAMPOS_DEFENSA))

    # --- Pitcheo (solo si alguna vez lanzó) ---
    pitcheo_temporada = calcular_pitcheo(_agregar(juegos_temporada, CAMPOS_PITCHEO))
    pitcheo_vida = calcular_pitcheo(_agregar(todos_los_juegos, CAMPOS_PITCHEO))

    # --- Posiciones regulares vs. ocasionales (de por vida) ---
    posiciones_conteo = (
        todos_los_juegos.exclude(posicion_jugada='')
        .values('posicion_jugada')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    total_con_posicion = sum(p['total'] for p in posiciones_conteo)
    nombres_posicion = dict(Jugador.POSICION_CHOICES)

    posiciones_regulares, posiciones_ocasionales = [], []
    for p in posiciones_conteo:
        pct = round(p['total'] / total_con_posicion * 100) if total_con_posicion else 0
        entry = {'nombre': nombres_posicion.get(p['posicion_jugada'], p['posicion_jugada']), 'pct': pct}
        (posiciones_regulares if pct >= UMBRAL_POSICION_REGULAR else posiciones_ocasionales).append(entry)

    if not posiciones_conteo and jugador.posicion_campo:
        posiciones_regulares = [{'nombre': jugador.get_posicion_campo_display(), 'pct': None}]

    logros_por_temporada = {}
    for logro in jugador.logros.all():
        logros_por_temporada.setdefault(logro.temporada, []).append(logro)

    context = {
        'jugador': jugador,
        'bateo_temporada': bateo_temporada,
        'bateo_vida': bateo_vida,
        'ops_plus_temporada': ops_plus_temporada,
        'defensa_temporada': defensa_temporada,
        'defensa_vida': defensa_vida,
        'pitcheo_temporada': pitcheo_temporada,
        'pitcheo_vida': pitcheo_vida,
        'posiciones_regulares': posiciones_regulares,
        'posiciones_ocasionales': posiciones_ocasionales,
        'logros_por_temporada': logros_por_temporada,
        'juegos_lista': juegos_temporada.order_by('-partido__fecha')[:20],
        'total_juegos_temporada': juegos_temporada.count(),
    }
    return render(request, 'jugadores/ficha.html', context)


def detalle_juego(request, jugador_id, juego_id):
    jugador = get_object_or_404(
        Jugador.objects.select_related('equipo', 'equipo__club', 'equipo__campeonato'),
        pk=jugador_id,
    )
    juego = get_object_or_404(
        EstadisticaJuego.objects.select_related('partido', 'partido__equipo_local', 'partido__equipo_visitante', 'equipo'),
        pk=juego_id, jugador=jugador,
    )

    # Acumulado de temporada tal como quedó justo después de este juego específico
    # (no necesariamente el más reciente — puede ser cualquier juego del historial).
    juegos_hasta_este = (
        jugador.estadisticas_juego
        .filter(equipo__campeonato_id=jugador.equipo.campeonato_id)
        .order_by('partido__fecha', 'id')
    )
    acumulado = {c: 0 for c in CAMPOS_BATEO}
    for g in juegos_hasta_este:
        for c in CAMPOS_BATEO:
            acumulado[c] += getattr(g, c)
        if g.id == juego.id:
            break
    acumulado_stats = calcular_bateo(acumulado)

    pitcheo_juego = calcular_pitcheo({c: getattr(juego, c) for c in CAMPOS_PITCHEO}) if juego.lanzo else None
    defensa_juego = calcular_defensa({c: getattr(juego, c) for c in CAMPOS_DEFENSA})

    context = {
        'jugador': jugador,
        'juego': juego,
        'acumulado': acumulado_stats,
        'pitcheo_juego': pitcheo_juego,
        'defensa_juego': defensa_juego,
        'videos': juego.videos.all(),
    }
    return render(request, 'jugadores/detalle_juego.html', context)


# ============================================================
# Panel del administrador de equipo
# ============================================================

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect

from .forms import EquipoForm, JugadorForm, VideoForm
from .models import PerfilAdministrador, Video


def _perfil_por_rol(user, roles_permitidos=None):
    """Devuelve el PerfilAdministrador del usuario si su rol está entre los
    permitidos (o cualquiera si no se especifica). None si no aplica."""
    try:
        perfil = user.perfil_admin
    except PerfilAdministrador.DoesNotExist:
        return None
    if roles_permitidos and perfil.rol not in roles_permitidos:
        return None
    return perfil


def _perfil_club_admin(user):
    """Admin de club: requiere club asignado (siempre está acotado a uno solo)."""
    perfil = _perfil_por_rol(user, roles_permitidos=['admin_club'])
    if perfil is None or perfil.club is None:
        return None
    return perfil


def _perfil_camarografo(user):
    """Camarógrafo: el club puede venir vacío, y eso significa 'todos los equipos'."""
    return _perfil_por_rol(user, roles_permitidos=['camarografo'])


def _perfil_valido_para_panel(user):
    """Para decidir a dónde redirigir tras el login. admin_club exige club; camarógrafo no."""
    perfil = _perfil_por_rol(user)
    if perfil is None:
        return None
    if perfil.rol == 'admin_club' and perfil.club is None:
        return None
    return perfil


def _perfil_admin_liga(user):
    """Admin de liga: acceso a toda la liga, no depende de ningún club."""
    return _perfil_por_rol(user, roles_permitidos=['admin_liga'])


def _redirigir_segun_rol(perfil):
    if perfil.rol == 'camarografo':
        return redirect('panel_videos')
    if perfil.rol == 'admin_liga':
        return redirect('panel_liga_dashboard')
    return redirect('panel_dashboard')


def panel_login(request):
    if request.user.is_authenticated:
        perfil = _perfil_valido_para_panel(request.user)
        if perfil is not None:
            return _redirigir_segun_rol(perfil)
        # Sesión iniciada pero con una cuenta sin perfil válido asignado
        # (por ejemplo, tu superusuario). La cerramos para evitar un ciclo
        # de redirección y dejamos que inicie sesión con la cuenta correcta.
        logout(request)

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        perfil = _perfil_valido_para_panel(user) if user is not None else None
        if perfil is not None:
            login(request, user)
            return _redirigir_segun_rol(perfil)
        error = 'Usuario o contraseña incorrectos, o esta cuenta no tiene un rol asignado.'

    return render(request, 'jugadores/panel_login.html', {'error': error})


def panel_logout(request):
    logout(request)
    return redirect('panel_login')


@login_required(login_url='panel_login')
def panel_dashboard(request):
    perfil = _perfil_club_admin(request.user)
    if perfil is None:
        messages.error(request, 'Tu usuario no tiene un perfil de administrador de club asignado.')
        return redirect('panel_login')

    equipos = (
        Equipo.objects
        .filter(club=perfil.club)
        .select_related('campeonato', 'campeonato__categoria')
        .prefetch_related('jugadores')
        .annotate(total_jugadores=Count('jugadores'))
        .order_by('campeonato__categoria__orden', 'escuadra')
    )
    return render(request, 'jugadores/panel_dashboard.html', {
        'club': perfil.club, 'equipos': equipos,
    })


@login_required(login_url='panel_login')
def panel_equipo_form(request, equipo_id=None):
    perfil = _perfil_club_admin(request.user)
    if perfil is None:
        messages.error(request, 'Tu usuario no tiene un perfil de administrador de club asignado.')
        return redirect('panel_login')

    instancia = None
    if equipo_id:
        instancia = get_object_or_404(Equipo, pk=equipo_id, club=perfil.club)

    if request.method == 'POST':
        form = EquipoForm(request.POST, instance=instancia, club=perfil.club)
        if form.is_valid():
            form.save()
            messages.success(request, 'Equipo guardado correctamente.')
            return redirect('panel_dashboard')
    else:
        form = EquipoForm(instance=instancia, club=perfil.club)

    return render(request, 'jugadores/panel_equipo_form.html', {
        'form': form, 'club': perfil.club, 'editando': instancia is not None,
    })


@login_required(login_url='panel_login')
def panel_jugador_form(request, jugador_id=None):
    perfil = _perfil_club_admin(request.user)
    if perfil is None:
        messages.error(request, 'Tu usuario no tiene un perfil de administrador de club asignado.')
        return redirect('panel_login')

    instancia = None
    if jugador_id:
        instancia = get_object_or_404(Jugador, pk=jugador_id, equipo__club=perfil.club)

    if request.method == 'POST':
        form = JugadorForm(request.POST, instance=instancia, club=perfil.club)
        if form.is_valid():
            form.save()
            messages.success(request, 'Jugador guardado correctamente.')
            return redirect('panel_dashboard')
    else:
        form = JugadorForm(instance=instancia, club=perfil.club)

    return render(request, 'jugadores/panel_jugador_form.html', {
        'form': form, 'club': perfil.club, 'editando': instancia is not None,
    })


@login_required(login_url='panel_login')
def panel_videos(request):
    perfil = _perfil_camarografo(request.user)
    if perfil is None:
        messages.error(request, 'Tu usuario no tiene permiso de camarógrafo.')
        return redirect('panel_login')

    juegos_qs = (
        EstadisticaJuego.objects
        .select_related('jugador', 'equipo', 'equipo__club', 'partido', 'partido__equipo_local', 'partido__equipo_visitante')
        .prefetch_related('videos')
        .order_by('-partido__fecha')
    )
    if perfil.club is not None:
        juegos_qs = juegos_qs.filter(jugador__equipo__club=perfil.club)

    return render(request, 'jugadores/panel_videos.html', {
        'club': perfil.club, 'juegos': juegos_qs[:50],
    })


@login_required(login_url='panel_login')
def panel_video_form(request, juego_id):
    perfil = _perfil_camarografo(request.user)
    if perfil is None:
        messages.error(request, 'Tu usuario no tiene permiso de camarógrafo.')
        return redirect('panel_login')

    juego_qs = EstadisticaJuego.objects.select_related('jugador', 'equipo', 'equipo__club', 'partido', 'partido__equipo_local', 'partido__equipo_visitante')
    if perfil.club is not None:
        juego_qs = juego_qs.filter(jugador__equipo__club=perfil.club)
    juego = get_object_or_404(juego_qs, pk=juego_id)

    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES, juego=juego)
        if form.is_valid():
            form.save()
            messages.success(request, 'Video cargado correctamente.')
            return redirect('panel_video_nuevo', juego_id=juego.id)
    else:
        form = VideoForm(juego=juego)

    return render(request, 'jugadores/panel_video_form.html', {
        'form': form, 'club': perfil.club, 'juego': juego,
        'videos_cargados': juego.videos.all().order_by('-id'),
    })


@login_required(login_url='panel_login')
def panel_video_eliminar(request, video_id):
    perfil = _perfil_camarografo(request.user)
    if perfil is None:
        messages.error(request, 'Tu usuario no tiene permiso de camarógrafo.')
        return redirect('panel_login')

    video_qs = Video.objects.select_related('jugador__equipo__club', 'juego')
    if perfil.club is not None:
        video_qs = video_qs.filter(jugador__equipo__club=perfil.club)
    video = get_object_or_404(video_qs, pk=video_id)
    juego_id = video.juego_id

    if request.method == 'POST':
        # Borra también el archivo físico del storage, no solo el registro.
        if video.archivo:
            video.archivo.delete(save=False)
        video.delete()
        messages.success(request, 'Video eliminado.')

    if juego_id:
        return redirect('panel_video_nuevo', juego_id=juego_id)
    return redirect('panel_videos')


# ============================================================
# Vista temporal de diagnóstico — quitar cuando ya no se necesite
# ============================================================
from django.conf import settings as _settings
from django.contrib.auth.models import User as _User
from django.http import HttpResponse as _HttpResponse


def debug_conexion(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return _HttpResponse(
            "No autorizado. Inicia sesión en /admin/ con un superusuario primero, "
            "y vuelve a esta misma URL en la misma pestaña.",
            status=403,
        )

    db = _settings.DATABASES['default']
    lineas = [
        "=== Conexión real que está usando la aplicación ahora mismo ===",
        f"ENGINE: {db.get('ENGINE')}",
        f"HOST: {db.get('HOST')}",
        f"PORT: {db.get('PORT')}",
        f"NAME (base de datos): {db.get('NAME')}",
        f"USER: {db.get('USER')}",
        "",
        "=== Lo que hay realmente en esa base ahora mismo ===",
        f"Jugadores: {Jugador.objects.count()}",
        f"Usuarios (auth_user): {_User.objects.count()}",
        f"Equipos: {Equipo.objects.count()}",
    ]
    return _HttpResponse("<pre>" + "\n".join(lineas) + "</pre>")


# ============================================================
# Panel del administrador de liga
# ============================================================
from .forms import EstadisticaJuegoForm, PartidoForm, PosicionForm
from .models import Partido, Posicion


@login_required(login_url='panel_login')
def panel_liga_dashboard(request):
    perfil = _perfil_admin_liga(request.user)
    if perfil is None:
        messages.error(request, 'Tu usuario no tiene permiso de administrador de liga.')
        return redirect('panel_login')

    context = {
        'total_partidos': Partido.objects.count(),
        'total_jugadores': Jugador.objects.count(),
        'total_equipos': Equipo.objects.count(),
        'proximos_partidos': Partido.objects.select_related(
            'equipo_local', 'equipo_visitante', 'equipo_local__club', 'equipo_visitante__club',
        ).order_by('-fecha')[:5],
    }
    return render(request, 'jugadores/panel_liga_dashboard.html', context)


@login_required(login_url='panel_login')
def panel_liga_calendario(request):
    perfil = _perfil_admin_liga(request.user)
    if perfil is None:
        messages.error(request, 'Tu usuario no tiene permiso de administrador de liga.')
        return redirect('panel_login')

    if request.method == 'POST':
        form = PartidoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Partido agregado al calendario.')
            return redirect('panel_liga_calendario')
    else:
        form = PartidoForm()

    partidos = Partido.objects.select_related(
        'equipo_local', 'equipo_visitante', 'equipo_local__club', 'equipo_visitante__club',
        'campeonato', 'campeonato__categoria',
    ).order_by('-fecha')[:50]

    return render(request, 'jugadores/panel_liga_calendario.html', {'form': form, 'partidos': partidos})


@login_required(login_url='panel_login')
def panel_liga_partido_detalle(request, partido_id):
    perfil = _perfil_admin_liga(request.user)
    if perfil is None:
        messages.error(request, 'Tu usuario no tiene permiso de administrador de liga.')
        return redirect('panel_login')

    partido = get_object_or_404(
        Partido.objects.select_related('equipo_local', 'equipo_visitante', 'campeonato'),
        pk=partido_id,
    )
    jugadores_local = partido.equipo_local.jugadores.all().order_by('nombre')
    jugadores_visitante = partido.equipo_visitante.jugadores.all().order_by('nombre')

    con_stats_ids = set(
        EstadisticaJuego.objects.filter(partido=partido).values_list('jugador_id', flat=True)
    )

    return render(request, 'jugadores/panel_liga_partido_detalle.html', {
        'partido': partido,
        'jugadores_local': jugadores_local,
        'jugadores_visitante': jugadores_visitante,
        'con_stats_ids': con_stats_ids,
    })


@login_required(login_url='panel_login')
def panel_liga_stats_form(request, partido_id, jugador_id):
    perfil = _perfil_admin_liga(request.user)
    if perfil is None:
        messages.error(request, 'Tu usuario no tiene permiso de administrador de liga.')
        return redirect('panel_login')

    partido = get_object_or_404(Partido, pk=partido_id)
    jugador = get_object_or_404(Jugador, pk=jugador_id)
    instancia = EstadisticaJuego.objects.filter(partido=partido, jugador=jugador).first()

    if request.method == 'POST':
        form = EstadisticaJuegoForm(request.POST, instance=instancia, jugador=jugador, partido=partido)
        if form.is_valid():
            form.save()
            messages.success(request, f'Estadísticas de {jugador.nombre} guardadas.')
            return redirect('panel_liga_partido_detalle', partido_id=partido.id)
    else:
        form = EstadisticaJuegoForm(instance=instancia, jugador=jugador, partido=partido)

    return render(request, 'jugadores/panel_liga_stats_form.html', {
        'form': form, 'partido': partido, 'jugador': jugador,
    })


@login_required(login_url='panel_login')
def panel_liga_posicion_eliminar(request, posicion_id):
    perfil = _perfil_admin_liga(request.user)
    if perfil is None:
        messages.error(request, 'Tu usuario no tiene permiso de administrador de liga.')
        return redirect('panel_login')

    posicion = get_object_or_404(Posicion, pk=posicion_id)
    if request.method == 'POST':
        posicion.delete()
        messages.success(request, 'Registro eliminado.')
    return redirect('panel_liga_equipos')


@login_required(login_url='panel_login')
def panel_liga_equipos(request):
    perfil = _perfil_admin_liga(request.user)
    if perfil is None:
        messages.error(request, 'Tu usuario no tiene permiso de administrador de liga.')
        return redirect('panel_login')

    if request.method == 'POST':
        form = PosicionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estadísticas de equipo guardadas.')
            return redirect('panel_liga_equipos')
    else:
        form = PosicionForm()

    posiciones = Posicion.objects.select_related(
        'equipo', 'equipo__club', 'campeonato', 'campeonato__categoria',
    ).order_by('campeonato__categoria__orden', '-puntos')[:100]

    return render(request, 'jugadores/panel_liga_equipos.html', {'form': form, 'posiciones': posiciones})
