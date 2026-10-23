from django.contrib.auth.models import User
from django.db import models


class Liga(models.Model):
    nombre = models.CharField(max_length=200)
    region = models.CharField(max_length=120, blank=True)

    class Meta:
        verbose_name = "Liga"
        verbose_name_plural = "Ligas"

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    nombre = models.CharField(max_length=80)
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Define el orden en que aparece la categoría en las listas (menor primero).",
    )
    rango_edad_ref = models.CharField(
        "Rango de edad de referencia", max_length=40, blank=True,
        help_text="Ej: 6-7 años. Solo referencial, la categoría real la define el campeonato.",
    )

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["orden"]

    def __str__(self):
        return self.nombre


class Campeonato(models.Model):
    liga = models.ForeignKey(Liga, on_delete=models.CASCADE, related_name="campeonatos")
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name="campeonatos")
    nombre = models.CharField(max_length=200)
    temporada = models.CharField(max_length=20, help_text="Ej: 2025-2026")

    class Meta:
        verbose_name = "Campeonato"
        verbose_name_plural = "Campeonatos"

    def __str__(self):
        return f"{self.categoria.nombre} — {self.nombre} ({self.temporada})"


class Club(models.Model):
    nombre = models.CharField(max_length=120)
    ciudad = models.CharField(max_length=120, blank=True)

    class Meta:
        verbose_name = "Club"
        verbose_name_plural = "Clubes"

    def __str__(self):
        return self.nombre


class Equipo(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="equipos")
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name="equipos")
    escuadra = models.CharField(
        max_length=10, blank=True,
        help_text="Letra o identificador de la escuadra dentro del club, ej: A, D, D1",
    )

    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"

    def __str__(self):
        nombre = self.club.nombre
        if self.escuadra:
            nombre += f" {self.escuadra}"
        return nombre


class PerfilAdministrador(models.Model):
    ROL_CHOICES = [
        ("admin_club", "Administrador de club"),
        ("admin_liga", "Administrador de liga"),
        ("camarografo", "Camarógrafo / Encargado de video"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_admin")
    club = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name="administradores",
        null=True, blank=True,
        help_text=(
            "Requerido si el rol es Administrador de club. "
            "Para Camarógrafo, déjalo vacío si debe cubrir TODOS los equipos de la liga, "
            "o elige un club si solo debe cubrir ese club."
        ),
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default="admin_club")

    class Meta:
        verbose_name = "Perfil de administrador"
        verbose_name_plural = "Perfiles de administradores"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.rol == "admin_club" and self.club is None:
            raise ValidationError("Un administrador de club necesita un club asignado.")

    def __str__(self):
        alcance = self.club.nombre if self.club else "todos los equipos"
        return f"{self.user.username} — {self.get_rol_display()} ({alcance})"


class Jugador(models.Model):
    POSICION_CHOICES = [
        ("lanzador", "Lanzador"),
        ("receptor", "Receptor"),
        ("1b", "Primera base"),
        ("2b", "Segunda base"),
        ("3b", "Tercera base"),
        ("ss", "Campocorto"),
        ("lf", "Jardinero izquierdo"),
        ("cf", "Jardinero central"),
        ("rf", "Jardinero derecho"),
    ]
    nombre = models.CharField(max_length=150)
    fecha_nacimiento = models.DateField()
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="jugadores")
    posicion_campo = models.CharField(max_length=10, choices=POSICION_CHOICES, blank=True)
    foto = models.ImageField(upload_to="jugadores/fotos/%Y/", blank=True, null=True)

    class Meta:
        verbose_name = "Jugador"
        verbose_name_plural = "Jugadores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def anio_nacimiento(self):
        return self.fecha_nacimiento.year


class Representante(models.Model):
    RELACION_CHOICES = [
        ("padre", "Padre"),
        ("madre", "Madre"),
        ("tutor", "Tutor legal"),
        ("otro", "Otro representante"),
    ]
    jugador = models.OneToOneField(Jugador, on_delete=models.CASCADE, related_name="representante")
    nombre = models.CharField(max_length=150)
    relacion = models.CharField(max_length=10, choices=RELACION_CHOICES)
    contacto = models.CharField(max_length=150, blank=True)
    consentimiento = models.BooleanField(
        "Consentimiento otorgado", default=False,
        help_text="Debe estar marcado antes de publicar cualquier video o foto del jugador.",
    )
    fecha_consentimiento = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Representante"
        verbose_name_plural = "Representantes"

    def __str__(self):
        return f"{self.nombre} ({self.get_relacion_display()} de {self.jugador.nombre})"


class Video(models.Model):
    TIPO_TOMA_CHOICES = [
        ("bateo", "Bateo"),
        ("lanzamiento", "Lanzamiento"),
        ("fildeo_infield", "Fildeo — cuadro"),
        ("fildeo_outfield", "Fildeo — jardines"),
        ("catcher", "Receptor"),
        ("corrido_bases", "Corrido de bases"),
    ]
    VISIBILIDAD_CHOICES = [
        ("equipo", "Solo el equipo"),
        ("representante", "Solo el representante"),
        ("publico", "Público"),
    ]
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name="videos")
    juego = models.ForeignKey(
        "EstadisticaJuego", on_delete=models.SET_NULL, related_name="videos",
        null=True, blank=True,
        help_text="Si esta toma ocurrió en un juego específico, vincúlala aquí para que aparezca en su carta.",
    )
    tipo_toma = models.CharField(max_length=20, choices=TIPO_TOMA_CHOICES)
    fecha = models.DateField()
    archivo = models.FileField(upload_to="videos/%Y/%m/", blank=True, null=True)
    visibilidad = models.CharField(max_length=20, choices=VISIBILIDAD_CHOICES, default="equipo")

    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.jugador.nombre} — {self.get_tipo_toma_display()} ({self.fecha})"


class Partido(models.Model):
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name="partidos")
    equipo_local = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="partidos_local")
    equipo_visitante = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="partidos_visitante")
    fecha = models.DateField()
    hora = models.TimeField(null=True, blank=True)
    estadio = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = "Partido"
        verbose_name_plural = "Partidos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.equipo_local} vs. {self.equipo_visitante} ({self.fecha})"

    def rival_de(self, equipo_id):
        return self.equipo_visitante if equipo_id == self.equipo_local_id else self.equipo_local


class EstadisticaJuego(models.Model):
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name="estadisticas_juego")
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name="estadisticas", null=True, blank=True)
    equipo = models.ForeignKey(
        Equipo, on_delete=models.CASCADE, related_name="estadisticas_juego",
        null=True, blank=True,
        help_text="Equipo con el que jugó este partido (normalmente el equipo actual del jugador).",
    )
    posicion_jugada = models.CharField(max_length=10, choices=Jugador.POSICION_CHOICES, blank=True)

    # --- Bateo ---
    turnos = models.PositiveIntegerField("Turnos al bate", default=0)
    hits = models.PositiveIntegerField(default=0)
    dobles = models.PositiveIntegerField(default=0)
    triples = models.PositiveIntegerField(default=0)
    jonrones = models.PositiveIntegerField(default=0)
    carreras_anotadas = models.PositiveIntegerField(default=0)
    impulsadas = models.PositiveIntegerField(default=0)
    bases_robadas = models.PositiveIntegerField(default=0)
    ponches = models.PositiveIntegerField(default=0)
    base_por_bolas = models.PositiveIntegerField(default=0)

    # --- Defensa ---
    putouts = models.PositiveIntegerField("Outs realizados (PO)", default=0)
    asistencias = models.PositiveIntegerField(default=0)
    errores = models.PositiveIntegerField(default=0)

    # --- Pitcheo (en béisbol menor, casi todo el roster lanza en algún juego) ---
    outs_lanzados = models.PositiveIntegerField(
        "Outs lanzados", default=0,
        help_text="3 outs = 1 entrada. Ej: 4 entradas y 1 out = 13.",
    )
    carreras_permitidas = models.PositiveIntegerField(default=0)
    hits_permitidos = models.PositiveIntegerField(default=0)
    base_por_bolas_permitidas = models.PositiveIntegerField(default=0)
    ponches_pitcheo = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Estadística de juego"
        verbose_name_plural = "Estadísticas de juego"
        ordering = ["-partido__fecha"]

    def __str__(self):
        return f"{self.jugador.nombre} vs {self.rival} ({self.fecha})"

    @property
    def fecha(self):
        return self.partido.fecha if self.partido_id else None

    @property
    def hora(self):
        return self.partido.hora if self.partido_id else None

    @property
    def estadio(self):
        return self.partido.estadio if self.partido_id else ''

    @property
    def rival(self):
        return self.partido.rival_de(self.equipo_id) if self.partido_id else None

    @property
    def lanzo(self):
        return self.outs_lanzados > 0


class Logro(models.Model):
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name="logros")
    temporada = models.CharField(max_length=20)
    descripcion = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Logro"
        verbose_name_plural = "Logros"
        ordering = ["-temporada"]

    def __str__(self):
        return f"{self.descripcion} — {self.jugador.nombre} ({self.temporada})"


class Posicion(models.Model):
    FASE_CHOICES = [
        ("eliminatoria", "Eliminatoria"),
        ("round_robin", "Round Robin"),
        ("final", "Final"),
    ]
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="posiciones")
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name="posiciones")
    fase = models.CharField(max_length=20, choices=FASE_CHOICES, default="round_robin")
    juegos = models.PositiveIntegerField(default=0)
    ganados = models.PositiveIntegerField(default=0)
    perdidos = models.PositiveIntegerField(default=0)
    empatados = models.PositiveIntegerField(default=0)
    carreras_favor = models.PositiveIntegerField(default=0)
    carreras_contra = models.PositiveIntegerField(default=0)
    puntos = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Posición"
        verbose_name_plural = "Tabla de posiciones"

    @property
    def diferencial(self):
        return self.carreras_favor - self.carreras_contra

    @property
    def avg(self):
        if self.juegos == 0:
            return 0.0
        return round(self.ganados / self.juegos, 3)

    def __str__(self):
        return f"{self.equipo} — {self.get_fase_display()}"
