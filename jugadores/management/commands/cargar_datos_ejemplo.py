import datetime

from django.core.management.base import BaseCommand

from jugadores.models import (
    Campeonato, Categoria, Club, Equipo, EstadisticaJuego, Jugador, Liga, Logro, Partido, Video,
)

CATEGORIAS = ["Preparatorio", "Pre Infantil", "Infantil", "Pre Junior", "Junior"]

JUGADORES = [
    ("Adrián Rodríguez", "San Luis", "A", "Preparatorio", 2019, "ss"),
    ("Emmanuel Torres", "Mariscal", "A", "Preparatorio", 2019, "lanzador"),
    ("Josué Fernández", "Bravos", "A", "Preparatorio", 2020, "cf"),
    ("Ángel Ramírez", "Santa Fe", "A", "Preparatorio", 2019, "receptor"),
    ("Kevin Pérez", "San Luis", "D", "Pre Infantil", 2017, "2b"),
    ("Santiago Díaz", "Azulejos", "A", "Pre Infantil", 2017, "1b"),
    ("Luis Martínez", "Angeles", "B", "Pre Infantil", 2018, "lanzador"),
    ("Gabriel Herrera", "Yoguis", "B", "Pre Infantil", 2017, "rf"),
    ("Diego Sánchez", "San Luis", "A", "Infantil", 2015, "3b"),
    ("Miguel Ángel Castro", "Bravos", "A", "Infantil", 2015, "lanzador"),
    ("Andrés Gómez", "Angeles", "A", "Infantil", 2016, "ss"),
    ("Ronaldo Suárez", "Texas", "", "Infantil", 2015, "receptor"),
    ("Jesús Alberto León", "Mariscal", "A", "Pre Junior", 2013, "lf"),
    ("Franklin Ortega", "Santa Fe", "A", "Pre Junior", 2013, "1b"),
    ("Eduardo Vargas", "San Luis", "D", "Pre Junior", 2014, "lanzador"),
    ("Carlos Julio Mendoza", "Bravos", "A", "Pre Junior", 2013, "2b"),
    ("Reinaldo Blanco", "San Luis", "A", "Junior", 2011, "ss"),
    ("Yorman Delgado", "Angeles", "A", "Junior", 2012, "cf"),
    ("Wilker Salazar", "Spartans", "", "Junior", 2011, "lanzador"),
    ("Anthony Rivas", "San Luis", "D1", "Junior", 2012, "receptor"),
]

CLUBES_CONOCIDOS = sorted({c for _, c, _, _, _, _ in JUGADORES}, key=len, reverse=True)

# fecha, rival, posicion, AB, H, 2B, 3B, HR, C, RBI, BR, K, BB, PO, A, E, outs_lanzados, CP, HP, BBP, KP
JUEGOS_ADRIAN = [
    (datetime.date(2026, 3, 1), "Mariscal A", "ss", 3, 2, 1, 0, 0, 1, 1, 0, 0, 1, 2, 3, 0, 0, 0, 0, 0, 0),
    (datetime.date(2026, 3, 8), "Bravos A", "ss", 4, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 2, 1, 0, 0, 0, 0, 0),
    (datetime.date(2026, 3, 15), "Santa Fe A", "ss", 3, 3, 1, 0, 1, 2, 2, 0, 0, 0, 3, 4, 0, 0, 0, 0, 0, 0),
    (datetime.date(2026, 3, 22), "Angeles B", "2b", 4, 2, 0, 0, 0, 1, 0, 0, 1, 1, 2, 3, 1, 0, 0, 0, 0, 0),
    (datetime.date(2026, 3, 29), "Yoguis B", "ss", 3, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0),
    (datetime.date(2026, 4, 5), "Azulejos A", "ss", 4, 2, 1, 0, 0, 1, 0, 1, 1, 0, 2, 3, 0, 0, 0, 0, 0, 0),
    (datetime.date(2026, 4, 12), "Texas", "ss", 3, 0, 0, 0, 0, 0, 0, 0, 2, 0, 1, 1, 1, 8, 2, 3, 1, 2),
    (datetime.date(2026, 4, 19), "Santa Fe A", "3b", 3, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0),
]

JUEGOS_DIEGO = [
    (datetime.date(2026, 2, 20), "Bravos A", "3b", 3, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0),
    (datetime.date(2026, 2, 27), "Angeles A", "3b", 4, 0, 0, 0, 0, 0, 0, 0, 2, 0, 2, 0, 0, 0, 0, 0, 0, 0),
    (datetime.date(2026, 3, 6), "Texas", "3b", 3, 2, 1, 0, 0, 1, 1, 1, 0, 1, 1, 2, 0, 0, 0, 0, 0, 0),
]


class Command(BaseCommand):
    help = "Carga datos de ejemplo (ficticios) para probar el buscador, la ficha y las estadísticas."

    def handle(self, *args, **options):
        liga, _ = Liga.objects.get_or_create(
            nombre="Liga Jesús Chucho Ramos - Criollitos de Venezuela",
            defaults={"region": "Baruta, Miranda"},
        )

        categorias = {
            n: Categoria.objects.get_or_create(nombre=n, defaults={"orden": i})[0]
            for i, n in enumerate(CATEGORIAS)
        }
        for i, n in enumerate(CATEGORIAS):
            Categoria.objects.filter(nombre=n).update(orden=i)
        campeonatos = {
            n: Campeonato.objects.get_or_create(
                liga=liga, categoria=categorias[n], temporada="2025-2026",
                defaults={"nombre": f"Copa {n} 2025-2026"},
            )[0]
            for n in CATEGORIAS
        }

        clubes, equipos = {}, {}
        creados = 0
        for nombre, club_nombre, escuadra, categoria_nombre, anio, posicion in JUGADORES:
            clubes.setdefault(club_nombre, Club.objects.get_or_create(nombre=club_nombre)[0])
            equipo_key = (club_nombre, escuadra, categoria_nombre)
            if equipo_key not in equipos:
                equipos[equipo_key], _ = Equipo.objects.get_or_create(
                    club=clubes[club_nombre], campeonato=campeonatos[categoria_nombre], escuadra=escuadra,
                )
            _, was_created = Jugador.objects.get_or_create(
                nombre=nombre, equipo=equipos[equipo_key],
                defaults={"fecha_nacimiento": datetime.date(anio, 4, 15), "posicion_campo": posicion},
            )
            if was_created:
                creados += 1

        self.stdout.write(self.style.SUCCESS(f"Listo. {creados} jugadores nuevos cargados."))

        def resolver_rival(rival_str, campeonato):
            """Encuentra (o crea) el Equipo rival dentro del MISMO campeonato,
            a partir de un texto como 'Mariscal A' o 'Texas'."""
            club_nombre, escuadra = rival_str, ""
            for candidato in CLUBES_CONOCIDOS:
                if rival_str == candidato or rival_str.startswith(candidato + " "):
                    club_nombre = candidato
                    escuadra = rival_str[len(candidato):].strip()
                    break
            clubes.setdefault(club_nombre, Club.objects.get_or_create(nombre=club_nombre)[0])
            key = (club_nombre, escuadra, campeonato.categoria.nombre)
            if key not in equipos:
                equipos[key], _ = Equipo.objects.get_or_create(
                    club=clubes[club_nombre], campeonato=campeonato, escuadra=escuadra,
                )
            return equipos[key]

        def cargar_juegos(nombre_jugador, filas):
            jugador = Jugador.objects.filter(nombre=nombre_jugador).first()
            if not jugador:
                return None
            equipo_local = jugador.equipo
            campeonato = equipo_local.campeonato

            for (fecha, rival_str, pos, ab, h, dobles, triples, hr, c, rbi, br, k, bb,
                 po, a, e, outs, cp, hp, bbp, kp) in filas:
                equipo_visitante = resolver_rival(rival_str, campeonato)
                partido, _ = Partido.objects.get_or_create(
                    campeonato=campeonato, equipo_local=equipo_local,
                    equipo_visitante=equipo_visitante, fecha=fecha,
                    defaults={"hora": datetime.time(9, 0), "estadio": "Complejo Criollitos de Venezuela"},
                )
                juego, _ = EstadisticaJuego.objects.get_or_create(
                    jugador=jugador, partido=partido,
                    defaults={
                        "equipo": equipo_local, "posicion_jugada": pos,
                        "turnos": ab, "hits": h, "dobles": dobles, "triples": triples, "jonrones": hr,
                        "carreras_anotadas": c, "impulsadas": rbi, "bases_robadas": br,
                        "ponches": k, "base_por_bolas": bb,
                        "putouts": po, "asistencias": a, "errores": e,
                        "outs_lanzados": outs, "carreras_permitidas": cp,
                        "hits_permitidos": hp, "base_por_bolas_permitidas": bbp, "ponches_pitcheo": kp,
                    },
                )
                if h > 0:
                    Video.objects.get_or_create(
                        jugador=jugador, juego=juego, tipo_toma="bateo", fecha=fecha,
                        defaults={"visibilidad": "equipo"},
                    )
                if outs > 0:
                    Video.objects.get_or_create(
                        jugador=jugador, juego=juego, tipo_toma="lanzamiento", fecha=fecha,
                        defaults={"visibilidad": "equipo"},
                    )
            return jugador

        adrian = cargar_juegos("Adrián Rodríguez", JUEGOS_ADRIAN)
        if adrian:
            Logro.objects.get_or_create(
                jugador=adrian, temporada="2025-2026", descripcion="Líder de bateo — Preparatorio",
            )

        diego = cargar_juegos("Diego Sánchez", JUEGOS_DIEGO)
        if diego:
            Logro.objects.get_or_create(
                jugador=diego, temporada="2025-2026", descripcion="Campeón — Infantil",
            )
