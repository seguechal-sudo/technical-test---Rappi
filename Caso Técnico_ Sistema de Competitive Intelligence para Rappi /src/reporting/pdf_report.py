from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors


def _clean_text(text: str) -> str:
    """
    Limpia markdown básico y deja solo el contenido útil.
    """
    lines = []

    for line in text.splitlines():
        line = line.strip()
        line = line.replace("**", "")

        if not line:
            continue

        if line == "---":
            continue

        if line.upper().startswith("REPORTE EJECUTIVO"):
            continue

        if line.lower().startswith("fecha:"):
            continue

        if line.lower().startswith("analista:"):
            continue

        lines.append(line)

    return "\n".join(lines)


def _extract_conclusion_section(text: str) -> str:
    """
    Intenta quedarse solo con la sección de conclusión y recomendaciones.
    Si no la encuentra, devuelve todo el texto limpio.
    """
    clean_text = _clean_text(text)

    lower_text = clean_text.lower()

    start_idx = None
    possible_titles = [
        "8. conclusión",
        "conclusión",
        "7. recomendaciones",
        "recomendaciones"
    ]

    for title in possible_titles:
        idx = lower_text.find(title)
        if idx != -1:
            start_idx = idx
            break

    if start_idx is not None:
        return clean_text[start_idx:].strip()

    return clean_text


def generate_pdf_report(input_txt: str, output_pdf: str = "reporte_ejecutivo_final.pdf"):
    input_path = Path(input_txt)

    if not input_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {input_path}")

    raw_text = input_path.read_text(encoding="utf-8")
    final_text = _clean_text(raw_text)

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=LETTER,
        rightMargin=55,
        leftMargin=55,
        topMargin=55,
        bottomMargin=55
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="SimpleTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.black,
        alignment=TA_LEFT,
        spaceAfter=14
    )

    body_style = ParagraphStyle(
        name="SimpleBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=colors.black,
        alignment=TA_LEFT,
        spaceAfter=8
    )

    story = []

    story.append(Paragraph("Conclusiones del reporte ejecutivo", title_style))
    story.append(Spacer(1, 8))

    for line in final_text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Si viene enumerado, lo deja como párrafo normal
        story.append(Paragraph(line, body_style))

    doc.build(story)
    return output_pdf