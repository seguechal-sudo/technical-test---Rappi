import json
import os

from google import genai

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


# =========================
# CONFIG GEMINI
# =========================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


SYSTEM_PROMPT = """
You are an analytics query parser for a Rappi operations assistant.
Your job is to convert the user's natural language question into a JSON action.

Return ONLY valid JSON.
Do not add markdown.
Do not explain anything.

Supported actions:
1. top_zones
2. avg_by_country
3. trend
4. compare_wealth
5. multivariable
6. problematic_zones
7. order_growth_inference
8. anomalies
9. bad_trends
10. correlations

JSON examples:
{"action":"top_zones","metric":"Lead Penetration","n":5,"country":null}
{"action":"compare_wealth","metric":"Perfect Orders","country":"MX"}
{"action":"trend","metric":"Gross Profit UE","zone":"Chapinero"}
{"action":"multivariable","metric1":"Lead Penetration","metric2":"Perfect Orders"}
{"action":"problematic_zones","n":3}
{"action":"order_growth_inference","weeks":5,"n":5}
{"action":"anomalies","n":10}
{"action":"bad_trends","n":10}
{"action":"correlations"}

Use only these metric names when relevant:
- Lead Penetration
- Perfect Orders
- Gross Profit UE
- Pro Adoption
- Turbo Adoption
- MLTV Top Verticals Adoption
- Orders

Use ISO country codes when possible:
MX, CO, EC, PE, CL, AR, BR, CR, UY

If unsure, choose the closest valid action.
"""


def _extract_json(text: str) -> dict:
    text = text.strip()

    # Caso ideal: viene puro JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Caso común: viene texto + bloque JSON
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        return json.loads(candidate)

    raise ValueError(f"No pude extraer JSON válido desde: {text}")


def parse_query_with_gemini(query: str) -> dict:
    if client is None:
        raise RuntimeError("GEMINI_API_KEY no configurada")

    prompt = f"""{SYSTEM_PROMPT}

User question:
{query}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    text = getattr(response, "text", None)
    if not text:
        raise ValueError("Gemini no devolvió texto utilizable")

    return _extract_json(text)


def summarize_result_with_gemini(query: str, action_payload: dict, result_text: str) -> str:
    if client is None:
        raise RuntimeError("GEMINI_API_KEY no configurada")

    prompt = f"""
Eres un asistente analítico para operaciones de Rappi.

Pregunta del usuario:
{query}

Acción interpretada:
{json.dumps(action_payload, ensure_ascii=False)}

Resultado crudo:
{result_text}

Redacta una respuesta corta, clara y ejecutiva en español.
No inventes datos.
Si el resultado es una tabla, resume el hallazgo principal y luego deja ver el resultado estructurado.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    text = getattr(response, "text", None)
    if not text:
        return "No pude generar un resumen ejecutivo, pero sí tengo el resultado estructurado."

    return text.strip()


# =========================
# FALLBACK RULE-BASED
# =========================

def fallback_rule_based(query, df_metrics, df_metrics_long, df_orders=None, df_orders_long=None):
    q = normalize_text(query)

    available_metrics = df_metrics["METRIC"].unique().tolist()
    available_zones = df_metrics["ZONE"].dropna().unique().tolist()

    if q in {"salir", "exit", "quit"}:
        return "EXIT"

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


# =========================
# EJECUCIÓN DE ACCIONES
# =========================

def execute_action(payload, df_metrics, df_metrics_long, df_orders=None):
    action = payload.get("action", "unknown")

    if action == "top_zones":
        metric = payload.get("metric", "Lead Penetration")
        n = int(payload.get("n", 5))
        country = payload.get("country")
        return top_zones(df_metrics, metric=metric, n=n, country=country)

    elif action == "avg_by_country":
        metric = payload.get("metric", "Lead Penetration")
        return avg_by_country(df_metrics_long, metric=metric)

    elif action == "trend":
        metric = payload.get("metric", "Gross Profit UE")
        zone = payload.get("zone", "Chapinero")
        return trend(df_metrics_long, metric=metric, zone=zone)

    elif action == "compare_wealth":
        metric = payload.get("metric", "Perfect Orders")
        country = payload.get("country", "MX")
        return compare_wealth(df_metrics, metric=metric, country=country)

    elif action == "multivariable":
        metric1 = payload.get("metric1", "Lead Penetration")
        metric2 = payload.get("metric2", "Perfect Orders")
        return multivariable(df_metrics, metric1=metric1, metric2=metric2)

    elif action == "problematic_zones":
        n = int(payload.get("n", 5))
        return problematic_zones(df_metrics, df_metrics_long, n=n)

    elif action == "order_growth_inference":
        weeks = int(payload.get("weeks", 5))
        n = int(payload.get("n", 5))
        return order_growth_inference(df_orders, df_metrics, weeks=weeks, n=n)

    elif action == "anomalies":
        n = int(payload.get("n", 10))
        return anomalies(df_metrics_long).head(n)

    elif action == "bad_trends":
        n = int(payload.get("n", 10))
        return bad_trends(df_metrics_long).head(n)

    elif action == "correlations":
        return correlations(df_metrics_long)

    else:
        return "No pude interpretar la consulta con suficiente claridad."


# =========================
# CHATBOT PRINCIPAL
# =========================

def chatbot(query, df_metrics, df_metrics_long, df_orders=None, df_orders_long=None):
    q = normalize_text(query)

    if q in {"salir", "exit", "quit"}:
        return "EXIT"

    # 1. Intentar Gemini
    try:
        payload = parse_query_with_gemini(query)
        result = execute_action(payload, df_metrics, df_metrics_long, df_orders=df_orders)

        if hasattr(result, "empty") and result.empty:
            return "No se encontraron resultados para esa consulta."

        raw_result_text = result.to_string(index=False) if hasattr(result, "to_string") else str(result)

        try:
            summary = summarize_result_with_gemini(query, payload, raw_result_text)
            return f"{summary}\n\nResultado estructurado:\n{raw_result_text}"
        except Exception:
            return f"Resultado estructurado:\n{raw_result_text}"

    # 2. Fallback estable
    except Exception:
        return fallback_rule_based(
            query=query,
            df_metrics=df_metrics,
            df_metrics_long=df_metrics_long,
            df_orders=df_orders,
            df_orders_long=df_orders_long,
        )