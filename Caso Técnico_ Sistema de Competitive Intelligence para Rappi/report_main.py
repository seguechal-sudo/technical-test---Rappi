from src.reporting.executive_report import generate_executive_report


if __name__ == "__main__":
    input_file = "competitive_data.csv"
    output_file = "reporte_ejecutivo_gemini.txt"

    path = generate_executive_report(
        input_file=input_file,
        output_file=output_file,
        model="gemini-2.5-flash",
    )

    print(f"Reporte generado correctamente en: {path}")