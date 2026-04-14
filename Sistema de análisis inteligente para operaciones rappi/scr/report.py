import os
import pandas as pd

from scr.insights import (
    generate_anomalies,
    generate_bad_trends,
    generate_correlations,
    generate_opportunities,
    generate_benchmark,
)

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors


def _head(df, n=5):
    if df is None or df.empty:
        return pd.DataFrame()
    return df.head(n).copy()


def _clean_df_for_pdf(df, max_rows=5, max_cols=6, max_len=18):
    """
    Reduce tamaño para que no se corte en PDF.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df_small = df.copy().head(max_rows)

    if df_small.shape[1] > max_cols:
        df_small = df_small.iloc[:, :max_cols]

    for col in df_small.columns:
        df_small[col] = df_small[col].astype(str).apply(
            lambda x: x if len(x) <= max_len else x[: max_len - 3] + "..."
        )

    return df_small


def _flatten_correlations(corr_df, top_n=8):
    """
    Convierte la matriz de correlación en una tabla angosta:
    METRIC_1 | METRIC_2 | CORRELATION
    para que no se corte en el PDF.
    """
    if corr_df is None or corr_df.empty:
        return pd.DataFrame()

    rows = []
    cols = list(corr_df.columns)

    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            m1 = cols[i]
            m2 = cols[j]
            value = corr_df.loc[m1, m2]

            if pd.notna(value):
                rows.append({
                    "METRIC_1": m1,
                    "METRIC_2": m2,
                    "CORRELATION": float(value),
                    "ABS_CORR": abs(float(value)),
                })

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)
    out = out.sort_values("ABS_CORR", ascending=False).head(top_n)
    out = out.drop(columns=["ABS_CORR"])
    out["CORRELATION"] = out["CORRELATION"].round(3)

    return out


def _build_conclusion(section_name, df):
    if df is None or df.empty:
        return f"No se identificaron hallazgos relevantes en la categoría de {section_name.lower()}."

    if section_name == "Anomalías":
        row = df.iloc[0]
        zone = row.get("ZONE", "N/A")
        metric = row.get("METRIC", "N/A")
        return (
            f"Conclusión: la principal anomalía se concentra en la zona {zone} para la métrica "
            f"{metric}, por lo que conviene revisar si hubo un evento operativo puntual."
        )

    if section_name == "Tendencias Negativas":
        row = df.iloc[0]
        zone = row.get("ZONE", "N/A")
        metric = row.get("METRIC", "N/A")
        return (
            f"Conclusión: la zona {zone} presenta deterioro sostenido en {metric}, lo que sugiere "
            f"un problema persistente más que una fluctuación aislada."
        )

    if section_name == "Oportunidades":
        row = df.iloc[0]
        zone = row.get("ZONE", "N/A")
        return (
            f"Conclusión: {zone} aparece como una oportunidad atractiva para impulsar crecimiento, "
            f"ya que combina señales operativas favorables con espacio para expansión."
        )

    if section_name == "Benchmark":
        row = df.iloc[0]
        country = row.get("COUNTRY", "N/A")
        zone_type = row.get("ZONE_TYPE", "N/A")
        return (
            f"Conclusión: el benchmark sugiere que en {country} el segmento {zone_type} muestra "
            f"el mejor desempeño relativo dentro de la muestra analizada."
        )

    if section_name == "Correlaciones":
        row = df.iloc[0]
        m1 = row.get("METRIC_1", "N/A")
        m2 = row.get("METRIC_2", "N/A")
        corr = row.get("CORRELATION", "N/A")
        return (
            f"Conclusión: la relación más fuerte observada es entre {m1} y {m2} "
            f"(correlación = {corr}), lo que sugiere una posible conexión operativa entre ambas métricas."
        )

    return f"Conclusión: se identificaron hallazgos relevantes en la categoría de {section_name.lower()}."


def generate_executive_report(df_metrics, df_long):
    anomalies = _head(generate_anomalies(df_long), 5)
    trends = _head(generate_bad_trends(df_long), 5)
    opportunities = _head(generate_opportunities(df_metrics), 5)
    benchmark = _head(generate_benchmark(df_metrics), 5)
    correlations_matrix = generate_correlations(df_long)
    correlations = _flatten_correlations(correlations_matrix, top_n=8)

    summary = []

    if not anomalies.empty:
        row = anomalies.iloc[0]
        summary.append(
            f"Se detectó una anomalía relevante en {row.get('ZONE', 'N/A')} para la métrica {row.get('METRIC', 'N/A')}."
        )

    if not trends.empty:
        row = trends.iloc[0]
        summary.append(
            f"Se identificó deterioro consistente en {row.get('ZONE', 'N/A')} para la métrica {row.get('METRIC', 'N/A')}."
        )

    if not opportunities.empty:
        row = opportunities.iloc[0]
        summary.append(
            f"Se detectó una oportunidad en {row.get('ZONE', 'N/A')} por buen desempeño operativo con espacio de crecimiento."
        )

    if not benchmark.empty:
        summary.append(
            "El benchmarking muestra diferencias relevantes entre países y tipos de zona."
        )

    if correlations is not None and not correlations.empty:
        summary.append(
            "Se observan relaciones entre métricas operativas que pueden apoyar decisiones de negocio."
        )

    if not summary:
        summary = ["No se detectaron hallazgos relevantes con la configuración actual."]

    recommendations = [
        "Revisar operativamente las zonas con anomalías negativas para identificar causas raíz.",
        "Monitorear semanalmente las métricas con deterioro consistente.",
        "Priorizar acciones comerciales en zonas con alta calidad operativa y baja penetración.",
        "Usar benchmarking por país y tipo de zona para una priorización más precisa.",
    ]

    conclusions = {
        "anomalies": _build_conclusion("Anomalías", anomalies),
        "trends": _build_conclusion("Tendencias Negativas", trends),
        "opportunities": _build_conclusion("Oportunidades", opportunities),
        "benchmark": _build_conclusion("Benchmark", benchmark),
        "correlations": _build_conclusion("Correlaciones", correlations),
    }

    return {
        "summary": summary[:5],
        "recommendations": recommendations[:5],
        "anomalies": anomalies,
        "trends": trends,
        "opportunities": opportunities,
        "benchmark": benchmark,
        "correlations": correlations,
        "conclusions": conclusions,
    }


def print_report(report):
    print("\n" + "=" * 80)
    print("REPORTE EJECUTIVO")
    print("=" * 80)

    print("\nResumen Ejecutivo:")
    for i, item in enumerate(report["summary"], 1):
        print(f"{i}. {item}")

    print("\nRecomendaciones:")
    for i, item in enumerate(report["recommendations"], 1):
        print(f"{i}. {item}")

    print("\n--- ANOMALÍAS ---")
    if report["anomalies"].empty:
        print("Sin hallazgos")
    else:
        print(report["anomalies"].to_string(index=False))
    print(report["conclusions"]["anomalies"])

    print("\n--- TENDENCIAS NEGATIVAS ---")
    if report["trends"].empty:
        print("Sin hallazgos")
    else:
        print(report["trends"].to_string(index=False))
    print(report["conclusions"]["trends"])

    print("\n--- OPORTUNIDADES ---")
    if report["opportunities"].empty:
        print("Sin hallazgos")
    else:
        print(report["opportunities"].to_string(index=False))
    print(report["conclusions"]["opportunities"])

    print("\n--- BENCHMARK ---")
    if report["benchmark"].empty:
        print("Sin hallazgos")
    else:
        print(report["benchmark"].to_string(index=False))
    print(report["conclusions"]["benchmark"])

    print("\n--- CORRELACIONES ---")
    if report["correlations"] is None or report["correlations"].empty:
        print("Sin hallazgos")
    else:
        print(report["correlations"].to_string(index=False))
    print(report["conclusions"]["correlations"])


def save_report_pdf(report, filename="executive_report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Reporte Ejecutivo de Insights Operacionales", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Resumen Ejecutivo", styles["Heading2"]))
    for item in report["summary"]:
        elements.append(Paragraph(f"- {item}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Recomendaciones", styles["Heading2"]))
    for item in report["recommendations"]:
        elements.append(Paragraph(f"- {item}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    def add_section(title, df, conclusion):
        elements.append(Paragraph(title, styles["Heading3"]))

        if df is None or df.empty:
            elements.append(Paragraph("Sin hallazgos", styles["Normal"]))
        else:
            if title == "Correlaciones":
                df_small = _clean_df_for_pdf(df, max_rows=8, max_cols=3, max_len=22)
            else:
                df_small = _clean_df_for_pdf(df, max_rows=5, max_cols=6, max_len=18)

            data = [df_small.columns.tolist()] + df_small.values.tolist()

            # anchos más cómodos para evitar cortes
            if title == "Correlaciones":
                col_widths = [170, 170, 90]
            else:
                col_widths = None

            table = Table(data, repeatRows=1, colWidths=col_widths)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ]))

            elements.append(table)

        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"<b>{conclusion}</b>", styles["Normal"]))
        elements.append(Spacer(1, 14))

    add_section("Anomalías", report["anomalies"], report["conclusions"]["anomalies"])
    add_section("Tendencias Negativas", report["trends"], report["conclusions"]["trends"])
    add_section("Oportunidades", report["opportunities"], report["conclusions"]["opportunities"])
    add_section("Benchmark", report["benchmark"], report["conclusions"]["benchmark"])
    add_section("Correlaciones", report["correlations"], report["conclusions"]["correlations"])

    doc.build(elements)
    return os.path.abspath(filename)