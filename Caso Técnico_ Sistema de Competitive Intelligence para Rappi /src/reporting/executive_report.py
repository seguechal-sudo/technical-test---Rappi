from __future__ import annotations
from pathlib import Path

from src.reporting.data_loader import load_competitive_data
from src.reporting.metrics import build_metrics_summary
from src.reporting.gemini_client import generate_executive_report_with_gemini


def generate_executive_report(
    input_file: str,
    output_file: str = "reporte_ejecutivo.txt",
    model: str = "gemini-2.5-flash",
) -> str:
    """
    Lee CSV/Excel, resume métricas y genera un reporte ejecutivo con Gemini.
    """
    df = load_competitive_data(input_file)
    summary = build_metrics_summary(df)
    report = generate_executive_report_with_gemini(summary, model=model)

    output_path = Path(output_file)
    output_path.write_text(report, encoding="utf-8")

    return str(output_path)