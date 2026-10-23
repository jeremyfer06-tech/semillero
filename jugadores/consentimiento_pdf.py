"""
Genera la planilla de consentimiento de uso de imagen, video y datos
deportivos de un jugador menor de edad, ya con los datos del jugador
(y su representante, si está registrado) rellenados.

Plantilla estándar de partida: se recomienda que un abogado la revise
antes de usarla de forma oficial con las familias.
"""
import io

from django.core.exceptions import ObjectDoesNotExist
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer,
)

MAROON = "#7A1F2B"


def _linea_datos(label, valor):
    valor = valor or "_" * 40
    return f"<b>{label}:</b> {valor}"


def generar_pdf_consentimiento(jugador):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=2.2 * cm, bottomMargin=2 * cm,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
    )

    styles = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "TituloConsentimiento", parent=styles["Title"],
        fontSize=14, leading=18, textColor=MAROON, spaceAfter=4,
    )
    subtitulo = ParagraphStyle(
        "Subtitulo", parent=styles["Normal"],
        fontSize=10, textColor="#555555", spaceAfter=16,
    )
    cuerpo = ParagraphStyle("Cuerpo", parent=styles["Normal"], fontSize=10.5, leading=15, spaceAfter=8)
    dato = ParagraphStyle("Dato", parent=styles["Normal"], fontSize=10.5, leading=16)
    item = ParagraphStyle("Item", parent=styles["Normal"], fontSize=10.5, leading=15)
    firma_label = ParagraphStyle("FirmaLabel", parent=styles["Normal"], fontSize=9, textColor="#555555")

    club = jugador.equipo.club if jugador.equipo_id else None
    liga = jugador.equipo.campeonato.liga if jugador.equipo_id else None
    try:
        representante = jugador.representante
    except ObjectDoesNotExist:
        representante = None

    story = []

    story.append(Paragraph("CONSENTIMIENTO DE USO DE IMAGEN, VIDEO Y DATOS DEPORTIVOS DE MENOR DE EDAD", titulo))
    encabezado = " · ".join(filter(None, [
        club.nombre if club else None,
        liga.nombre if liga else None,
    ])) or "Semillero"
    story.append(Paragraph(encabezado, subtitulo))
    story.append(HRFlowable(width="100%", color=MAROON, thickness=1, spaceAfter=14))

    # --- Datos del jugador ---
    story.append(Paragraph(_linea_datos("Jugador", jugador.nombre), dato))
    if getattr(jugador, "fecha_nacimiento", None):
        story.append(Paragraph(_linea_datos("Fecha de nacimiento", jugador.fecha_nacimiento.strftime("%d/%m/%Y")), dato))
    if club:
        story.append(Paragraph(_linea_datos("Club", club.nombre), dato))
    if jugador.equipo_id:
        story.append(Paragraph(_linea_datos("Equipo / Categoría", f"{jugador.equipo} — {jugador.equipo.campeonato.categoria}"), dato))
    story.append(Spacer(1, 10))

    # --- Datos del representante ---
    story.append(Paragraph(_linea_datos("Nombre del representante", representante.nombre if representante else None), dato))
    story.append(Paragraph(_linea_datos("Relación con el menor", representante.get_relacion_display() if representante else None), dato))
    story.append(Paragraph(_linea_datos("Cédula de identidad", None), dato))
    story.append(Paragraph(_linea_datos("Teléfono / contacto", representante.contacto if representante else None), dato))
    story.append(Spacer(1, 16))

    # --- Cuerpo del consentimiento ---
    story.append(Paragraph(
        "Quien suscribe, en la condición de representante legal del menor identificado en esta planilla, "
        "de manera libre, voluntaria e informada, autoriza al club y a la liga arriba identificados a:",
        cuerpo,
    ))
    story.append(ListFlowable([
        ListItem(Paragraph(
            "Captar, grabar y almacenar fotografías y videos del menor durante entrenamientos, partidos y "
            "actividades del club, con fines exclusivamente deportivos, formativos y de seguimiento de su desarrollo.",
            item,
        )),
        ListItem(Paragraph(
            "Registrar y conservar estadísticas de desempeño deportivo del menor en la plataforma de seguimiento "
            "del club (\"Semillero\").",
            item,
        )),
        ListItem(Paragraph(
            "Mostrar dicha información y videos en el buscador público de jugadores de la plataforma, con el fin "
            "de dar visibilidad al desarrollo deportivo del menor.",
            item,
        )),
    ], bulletType="bullet", leftIndent=14, spaceAfter=10))

    story.append(Paragraph("El representante declara entender que:", cuerpo))
    story.append(ListFlowable([
        ListItem(Paragraph("Este consentimiento puede ser revocado en cualquier momento mediante solicitud escrita dirigida al club.", item)),
        ListItem(Paragraph("El material autorizado no será utilizado con fines comerciales sin una autorización adicional y específica.", item)),
        ListItem(Paragraph("Puede solicitar la eliminación de videos, fotografías o datos puntuales del menor en cualquier momento.", item)),
    ], bulletType="bullet", leftIndent=14, spaceAfter=18))

    # --- Firmas ---
    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="45%", color="#333333", thickness=0.8))
    story.append(Paragraph("Firma del representante", firma_label))
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="45%", color="#333333", thickness=0.8))
    story.append(Paragraph("Fecha (dd/mm/aaaa)", firma_label))

    story.append(Spacer(1, 26))
    story.append(Paragraph(
        "<i>Planilla generada automáticamente por Semillero. Plantilla estándar de partida — se recomienda "
        "revisión legal antes de su uso oficial.</i>",
        ParagraphStyle("Nota", parent=styles["Normal"], fontSize=7.5, textColor="#888888"),
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
