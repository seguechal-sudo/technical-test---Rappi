from __future__ import annotations
import os
import json
from google import genai


DEFAULT_MODEL = "gemini-2.5-flash"


def build_report_prompt(summary: dict) -> str:
    """
    Construye un prompt robusto para pedirle a Gemini un reporte ejecutivo.
    """
    return f"""
Eres un analista senior de negocio y pricing.

Necesito un REPORTE EJECUTIVO en español, profesional, claro y accionable.
El reporte debe estar orientado a un proyecto de análisis competitivo de plataformas de delivery.

Usa EXCLUSIVAMENTE esta información resumida del dataset:
{json.dumps(summary, ensure_ascii=False, indent=2)}

Instrucciones:
1. Escribe un reporte ejecutivo con estas secciones:
   - Resumen ejecutivo
   - Objetivo del análisis
   - Cobertura del análisis
   - Hallazgos clave
   - Comparación por plataforma
   - Riesgos / limitaciones
   - Recomendaciones
   - Conclusión
2. No inventes cifras.
3. Si algo no está disponible, dilo explícitamente.
4. Redacta en tono ejecutivo, no académico.
5. Usa párrafos cortos y claros.
6. Resalta diferencias entre plataformas, productos, tiendas y direcciones cuando existan.
7. Incluye observaciones sobre calidad del dato si hay errores o fallos.

Devuélvelo en texto plano bien estructurado.
""".strip()


def generate_executive_report_with_gemini(summary: dict, model: str = DEFAULT_MODEL) -> str:
    """
    Genera un reporte ejecutivo usando Gemini.
    Requiere GEMINI_API_KEY en variables de entorno.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "No se encontró GEMINI_API_KEY en las variables de entorno."
        )

    client = genai.Client(api_key=api_key)
    prompt = build_report_prompt(summary)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Gemini no devolvió texto en la respuesta.")

    return text.strip()