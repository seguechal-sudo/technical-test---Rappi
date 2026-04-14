from scr.data import load_data
from scr.chatbot import chatbot
from scr.report import generate_executive_report, print_report, save_report_pdf


def main():
    file_path = "data_base.xlsx"

    print("Cargando datos...")
    df_metrics, df_metrics_long, df_orders, df_orders_long = load_data(file_path)

    print("\n" + "=" * 80)
    print("SISTEMA DE ANÁLISIS INTELIGENTE PARA OPERACIONES RAPPI")
    print("=" * 80)
    print("\nComandos:")
    print("- Haz preguntas en lenguaje natural")
    print("- Escribe 'reporte' para ver el reporte ejecutivo")
    print("- Escribe 'guardar pdf' para generar el PDF")
    print("- Escribe 'salir' para cerrar\n")

    while True:
        query = input("Pregunta: ").strip()

        if query.lower() in {"salir", "exit", "quit"}:
            print("Cerrando sistema.")
            break

        if query.lower() == "reporte":
            report = generate_executive_report(df_metrics, df_metrics_long)
            print_report(report)
            continue

        if query.lower() == "guardar pdf":
            report = generate_executive_report(df_metrics, df_metrics_long)
            filename = save_report_pdf(report)
            print(f"\nPDF guardado en:\n{filename}\n")
            continue

        result = chatbot(
            query=query,
            df_metrics=df_metrics,
            df_metrics_long=df_metrics_long,
            df_orders=df_orders,
            df_orders_long=df_orders_long,
        )

        if isinstance(result, str) and result == "EXIT":
            print("Cerrando sistema.")
            break

        print("\nRespuesta:")
        print(result)
        print("\n" + "-" * 100 + "\n")


if __name__ == "__main__":
    main()