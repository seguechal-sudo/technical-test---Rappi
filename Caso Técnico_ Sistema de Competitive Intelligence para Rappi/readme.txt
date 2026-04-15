Sistema de Competitive Intelligence para Rappi y Uber Eats

Descripción
Este proyecto implementa un sistema automatizado de recolección y análisis de datos para plataformas de delivery, enfocado en Rappi y Uber Eats. El objetivo es capturar información competitiva desde distintas direcciones, buscar tiendas específicas, localizar productos dentro del menú y extraer variables relevantes como precio, ETA y descuentos activos.

El sistema también incluye un módulo de reporting para generar reportes ejecutivos a partir de los datos recolectados.

Funcionalidades principales
- Automatización de navegación con Playwright
- Selección automática de dirección
- Búsqueda de tienda en Rappi y Uber Eats
- Selección de la primera tienda sugerida en Uber Eats
- Búsqueda de producto dentro de la página del restaurante
- Extracción de datos desde JSON estructurado y desde el DOM
- Manejo de popups y ventanas emergentes bloqueantes
- Almacenamiento de resultados en CSV
- Generación de reporte ejecutivo en texto y PDF
- Integración con Gemini para redactar reportes ejecutivos automáticamente

Estructura del proyecto
project/
│
├── main.py
├── report_main.py
├── pdf_main.py
├── requirements.txt
├── addresses.csv
├── products.json
├── competitive_data.csv
├── reporte_ejecutivo_gemini.txt
│
└── src/
    ├── __init__.py
    ├── config.py
    │
    ├── core/
    │   ├── __init__.py
    │   ├── utils.py
    │   ├── io.py
    │   ├── parsers.py
    │   └── selectors.py
    │
    ├── scrapers/
    │   ├── __init__.py
    │   ├── rappi.py
    │   └── uber.py
    │
    ├── services/
    │   ├── __init__.py
    │   └── runner.py
    │
    └── reporting/
        ├── __init__.py
        ├── data_loader.py
        ├── metrics.py
        ├── gemini_client.py
        ├── executive_report.py
        └── pdf_report.py

Requisitos
- Python 3.9 o superior
- pip
- Playwright
- pandas
- openpyxl
- reportlab
- google-genai

Instalación
1. Crear y activar entorno virtual

En macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate

En Windows:
python -m venv .venv
.venv\Scripts\activate

2. Instalar dependencias
pip install -r requirements.txt

3. Instalar navegadores de Playwright
playwright install

Configuración de archivos de entrada

1. addresses.csv
Debe contener las direcciones que se van a evaluar.

Ejemplo:
address_id,zone_type,address
1,premium,"González 8, Guadalupe Mainero, 87100 Cdad. Victoria, Tamps., México"
2,premium,"Cdad. Mante 117, Enrique Cárdenas González, 87010 Cdad. Victoria, Tamps., México"

2. products.json
Debe contener la lista de tiendas y productos a consultar.

Ejemplo:
[
  {
    "product_id": "P1",
    "store_name": "La Estación",
    "product_name": "Promo 1"
  },
  {
    "product_id": "P2",
    "store_name": "Domino's",
    "product_name": "Alitas"
  }
]

Cómo ejecutar el scraping
Para correr todo el flujo de extracción:

python main.py

Resultado esperado:
- Se abrirá el navegador
- El sistema recorrerá plataformas, direcciones y productos
- Se generará el archivo competitive_data.csv con los resultados

Columnas esperadas en el CSV
- timestamp
- platform
- address
- store
- product
- matched_product_name
- matched_section_name
- price
- price_text
- eta
- active_discount
- status
- error

Cómo generar el reporte ejecutivo con Gemini
1. Configurar la API key de Gemini

En macOS / Linux:
export GEMINI_API_KEY="TU_API_KEY"

En Windows CMD:
set GEMINI_API_KEY=TU_API_KEY

En Windows PowerShell:
$env:GEMINI_API_KEY="TU_API_KEY"

2. Ejecutar generación del reporte
python report_main.py

Resultado esperado:
- Se lee el archivo competitive_data.csv o el archivo definido
- Se calculan métricas agregadas
- Gemini redacta el reporte ejecutivo
- Se genera el archivo reporte_ejecutivo_gemini.txt

Cómo generar el PDF
Una vez tengas el archivo de texto del reporte:

python pdf_main.py

Resultado esperado:
- Se genera el archivo reporte_ejecutivo_final.pdf

Lógica general del sistema

Rappi
- Ingresa la dirección
- Selecciona sugerencia
- Confirma y guarda dirección
- Busca tienda
- Entra a la tienda
- Busca producto en JSON estructurado del restaurante
- Si no lo encuentra, usa fallback en DOM
- Extrae precio, ETA y descuentos

Uber Eats
- Ingresa dirección
- Selecciona sugerencia
- Busca tienda
- Abre la primera tienda sugerida
- Busca el producto dentro del JSON-LD del restaurante
- Luego lo localiza directamente en la página, sin usar la barra de búsqueda
- Si aparece un popup bloqueante, lo cierra
- Extrae precio, ETA y descuentos

Comandos principales
Instalación:
pip install -r requirements.txt
playwright install

Scraping:
python main.py
