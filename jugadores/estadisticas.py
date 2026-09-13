"""
Fórmulas de estadísticas de béisbol usadas en la ficha del jugador.

Simplificaciones deliberadas para esta versión beta:
- OBP no incluye golpeado por lanzamiento (HBP) ni elevado de sacrificio (SF)
  porque todavía no los registramos juego a juego.
- ERA se calcula sobre 9 entradas (fórmula estándar), aunque los juegos de
  béisbol menor suelen ser más cortos (6-7 entradas) — es una referencia,
  no una comparación 1:1 con ligas profesionales.
- OPS+ se calcula contra el promedio de la propia categoría y temporada en
  esta base de datos. Con pocos jugadores cargados, el número no es muy
  significativo todavía; se vuelve más útil mientras más jugadores reales
  se registren en la misma categoría.
"""


def _safe_div(a, b):
    return a / b if b else 0.0


def calcular_bateo(agregado):
    """agregado: dict con turnos, hits, dobles, triples, jonrones, base_por_bolas, etc."""
    ab = agregado.get('turnos') or 0
    h = agregado.get('hits') or 0
    dobles = agregado.get('dobles') or 0
    triples = agregado.get('triples') or 0
    hr = agregado.get('jonrones') or 0
    bb = agregado.get('base_por_bolas') or 0

    sencillos = max(h - dobles - triples - hr, 0)
    bases_totales = sencillos + 2 * dobles + 3 * triples + 4 * hr

    avg = round(_safe_div(h, ab), 3)
    obp = round(_safe_div(h + bb, ab + bb), 3)
    slg = round(_safe_div(bases_totales, ab), 3)
    ops = round(obp + slg, 3)

    return {
        'turnos': ab, 'hits': h, 'dobles': dobles, 'triples': triples, 'jonrones': hr,
        'carreras': agregado.get('carreras_anotadas') or 0,
        'impulsadas': agregado.get('impulsadas') or 0,
        'robadas': agregado.get('bases_robadas') or 0,
        'ponches': agregado.get('ponches') or 0,
        'base_por_bolas': bb,
        'avg': avg, 'obp': obp, 'slg': slg, 'ops': ops,
        'bases_totales': bases_totales,
    }


def calcular_ops_plus(bateo_jugador, obp_liga, slg_liga):
    if not obp_liga or not slg_liga:
        return None
    return round(100 * (_safe_div(bateo_jugador['obp'], obp_liga) + _safe_div(bateo_jugador['slg'], slg_liga) - 1))


def calcular_defensa(agregado):
    po = agregado.get('putouts') or 0
    a = agregado.get('asistencias') or 0
    e = agregado.get('errores') or 0
    fld_pct = round(_safe_div(po + a, po + a + e), 3) if (po + a + e) else None
    return {'putouts': po, 'asistencias': a, 'errores': e, 'fld_pct': fld_pct}


def calcular_pitcheo(agregado):
    outs = agregado.get('outs_lanzados') or 0
    if outs == 0:
        return None
    carreras = agregado.get('carreras_permitidas') or 0
    hits = agregado.get('hits_permitidos') or 0
    bb = agregado.get('base_por_bolas_permitidas') or 0
    k = agregado.get('ponches_pitcheo') or 0

    entradas = outs / 3
    era = round(carreras * 27 / outs, 2)
    whip = round((hits + bb) / entradas, 2) if entradas else 0.0

    return {
        'outs': outs,
        'entradas_display': f"{outs // 3}.{outs % 3}",
        'carreras': carreras, 'hits': hits, 'base_por_bolas': bb, 'ponches': k,
        'era': era, 'whip': whip,
    }
