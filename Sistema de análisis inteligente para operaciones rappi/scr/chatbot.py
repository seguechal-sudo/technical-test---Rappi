from scr.logic import (
    normalize_text,
    extract_top_n,
    extract_metric,
    extract_country,
    extract_zone,
    top_zones,
    avg_by_country,
    trend,
    compare_wealth,
    multivariable,
    problematic_zones,
    order_growth_inference,
)
from scr.data import anomalies, bad_trends, correlations


def chatbot(query, df_metrics, df_metrics_long, df_orders=None, df_orders_long=None):
    q = normalize_text(query)

    try:
        if q in {"salir", "exit", "quit"}:
            return "EXIT"

        available_metrics = df_metrics["METRIC"].unique().tolist()
        available_zones = df_metrics["ZONE"].dropna().unique().tolist()

        if "problematic" in q or "problemat" in q or "problema" in q:
            n = extract_top_n(q, default=5)
            return problematic_zones(df_metrics, df_metrics_long, n=n)

        if (("top" in q) or ("mayor" in q) or ("highest" in q)) and (("zone" in q) or ("zona" in q)):
            n = extract_top_n(q, default=5)
            metric = extract_metric(q, available_metrics)
            country = extract_country(q)
            return top_zones(df_metrics, metric=metric, n=n, country=country)

        if "wealthy" in q and "non" in q:
            metric = extract_metric(q, available_metrics)
            country = extract_country(q) or "MX"
            return compare_wealth(df_metrics, metric=metric, country=country)

        if "tendencia" in q or "evolucion" in q or "trend" in q:
            metric = extract_metric(q, available_metrics)
            zone = extract_zone(q, available_zones)
            if zone is None:
                return "No pude identificar la zona. Escribe el nombre exacto de la zona, por ejemplo: Chapinero."
            return trend(df_metrics_long, metric=metric, zone=zone)

        if "promedio" in q or "average" in q:
            metric = extract_metric(q, available_metrics)
            return avg_by_country(df_metrics_long, metric=metric)

        if ("alto" in q and "bajo" in q) or ("high" in q and "low" in q):
            return multivariable(df_metrics, "Lead Penetration", "Perfect Orders")

        if "crecen en ordenes" in q or "growth in orders" in q or ("ordenes" in q and "explicar" in q):
            n = extract_top_n(q, default=5)
            return order_growth_inference(df_orders, df_metrics, weeks=5, n=n)

        if "anomal" in q:
            n = extract_top_n(q, default=10)
            return anomalies(df_metrics_long).head(n)

        if "deterioro" in q or "tendencia negativa" in q or "caida" in q:
            n = extract_top_n(q, default=10)
            return bad_trends(df_metrics_long).head(n)

        if "correlacion" in q or "correlation" in q or "relacion entre metricas" in q:
            return correlations(df_metrics_long)

        return (
            "No entendí la pregunta. Prueba con algo como:\n"
            "- ¿Cuáles son las 5 zonas con mayor Lead Penetration esta semana?\n"
            "- Compara Perfect Orders entre zonas Wealthy y Non Wealthy en México\n"
            "- Muestra la evolución de Gross Profit UE en Chapinero\n"
            "- ¿Cuál es el promedio de Lead Penetration por país?\n"
            "- ¿Qué zonas tienen alto Lead Penetration pero bajo Perfect Orders?\n"
            "- ¿Cuáles son las zonas que más crecen en órdenes en las últimas 5 semanas y qué podría explicarlo?"
        )

    except Exception as e:
        return f"Error procesando la consulta: {e}"