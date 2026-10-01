---
name: reporte-search-console
description: |
  Genera un reporte PDF para un cliente (médico o negocio) con el desempeño de su sitio en
  Google, a partir del export CSV de Google Search Console y del código del sitio. Activar
  cuando se pida "reporte de Search Console", "reporte para el cliente", "PDF con las
  métricas de su web", "que vea el valor de su sitio", o al recibir una carpeta
  `<dominio>-Performance-on-Search-<fecha>`. Incluye portada con su marca, KPIs, crecimiento
  mes a mes, búsquedas, páginas, audiencia, mejoras realizadas y próximos pasos.
compatibility: Requiere Python 3 (setup.sh crea un venv con reportlab y matplotlib) y acceso a internet para bajar fuentes de Google Fonts.
---

# Reporte de Search Console → PDF para el cliente

El generador vive en `scripts/` de esta skill. Se configura con un JSON por cliente
(`config.example.json` documenta cada campo). El texto sale en español de México, trato de
usted, pensado para un cliente no técnico.

## Flujo

1. **Entorno**, una vez por máquina. Devuelve el `python` del venv (`~/.cache/reporte-search-console/venv`):
   ```bash
   PY=$(bash <skill>/scripts/setup.sh)   # <skill> = carpeta de esta skill
   ```
2. **Datos.** La carpeta del export trae `Gráfico.csv`, `Consultas.csv`, `Páginas.csv`,
   `Países.csv` y `Dispositivos.csv`, o sus equivalentes en inglés (`Chart.csv`…).
   Revisa `Filtros.csv`: el reporte asume búsqueda web y el rango completo.
3. **Marca del sitio**, leída del repo del cliente:
   - Colores: tokens CSS o la config de Tailwind (`primary`, `accent`, `surface`, en hex).
   - Fuentes: el nombre exacto de Google Fonts. Se descargan de github.com/google/fonts.
   - Logo: PNG con transparencia. Si es SVG, rasterízalo antes (en Mac: `sips -s format png logo.svg --out logo.png`). Si el SVG solo envuelve PNGs en base64, extráelos.
   - Consultas de marca: nombre, apellido y sus variantes mal escritas.
   - Palabras clave por servicio.
   - Nombres legibles para cada página (`page_names`).
4. **Métricas primero:** `"$PY" scripts/build_report.py config.json --metrics`. Con esos números
   decides el texto opcional: `summary_lead`, `highlights`, `growth_callout`, `pages_lead`,
   `improvements` y `next_steps`. Si los dejas en `null`, se generan solos a partir de los datos.
5. **Generar:** `"$PY" scripts/build_report.py config.json`.
6. **Revisar cada página:** `"$PY" scripts/render_pages.py reporte.pdf` y lee los PNG.
   Busca textos encimados, páginas desbordadas y frases sin artículo. La salida lista las
   fuentes embebidas: debe haber un nombre por peso (`Inter-Regular`, `Inter-SemiBold`…).
7. **Entrega:** guarda el PDF en `~/Downloads/Reporte-<dominio>-<AAAA-MM>.pdf`. Si lo pide, prepara también
   un mensaje corto de WhatsApp con 4–5 cifras con emoji; el PDF lleva el detalle.

## Reglas de contenido

- **Honestidad por encima del brillo.** Con números chicos, preséntalos como crecimiento de un
  sitio nuevo, sin inflarlos. Si hubo caída, dilo en tono neutral. Visitas no son pacientes
  ni citas: nunca los mezcles.
- **Cada afirmación sobre el sitio se verifica en el código** antes de escribirla. Ejemplo
  real: se escribió que el JSON-LD incluía las cédulas y no era así.
- Los datos de Search Console tienen unos 2 días de retraso. Si hubo cambios técnicos recientes, aclara
  que el efecto se verá en 2–4 semanas.
- Google oculta la mayoría de las consultas por privacidad. El generador lo aclara solo
  cuando hay más visitas que consultas visibles.
- Formato mexicano: punto decimal y `%` pegado (`8.8%`). Fechas: "11 de septiembre de 2026".
- Cliente médico: nada de promesas de resultados ni precios. En "mejoras realizadas" solo lo
  que se hizo y es verificable. Si hay política editorial (blog sin autoría médica), respétala.
- Los compromisos a futuro ("el siguiente reporte incluirá…") son decisión del usuario:
  márcalos para que los revise antes de enviar.

## Trampas ya resueltas en el código (no reintroducir)

- **Pesos de fuente colapsados.** `varLib.instancer` deja el mismo nombre PostScript en cada
  instancia y reportlab las incrusta por ese nombre: todo sale en un solo peso. `fonts.py`
  renombra el nameID 6 por peso.
- **Familia para matplotlib.** matplotlib agrupa por nameID 1: debe quedar la familia pelona
  ("Inter"), con el peso en `usWeightClass`. Si cambia, las gráficas caen a DejaVu.
- **Etiquetas encimadas.** Barras y línea en ejes dobles enciman etiquetas. Por eso la gráfica mensual son
  dos paneles de barras.
- **Nada de Chrome.** El PDF se arma con reportlab y se revisa renderizándolo con PyMuPDF.
