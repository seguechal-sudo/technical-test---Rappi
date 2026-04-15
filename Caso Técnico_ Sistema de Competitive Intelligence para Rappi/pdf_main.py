from src.reporting.pdf_report import generate_pdf_report

if __name__ == "__main__":
    generate_pdf_report(
        input_txt="reporte_ejecutivo_gemini.txt",
        output_pdf="reporte_ejecutivo_final.pdf"
    )