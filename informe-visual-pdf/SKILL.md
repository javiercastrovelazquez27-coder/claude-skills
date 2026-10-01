---
name: informe-visual-pdf
description: |
  Genera PDFs de informe con la marca del cliente: resúmenes ejecutivos, reportes de
  ingresos o cartera, proyecciones, one-pagers y documentos técnicos para juntas. HTML con
  gráficas SVG, impreso con Chrome headless y revisado página por página. Usar SIEMPRE que
  se pida un PDF, un informe, un reporte "para el dueño / para el jefe / para la junta", un
  resumen visual o para presentar, una versión ejecutiva o técnica de algo, o "lo mismo
  pero más técnico / más simple" de un PDF anterior, aunque no digan "PDF".
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, AskUserQuestion, Skill
---

# Informe visual en PDF

Un informe que el dueño de un negocio lee en cinco minutos y le reenvía a alguien más.
Tiene que verse hecho por un diseñador para *esa* marca, sonar a persona y no traer ni
una cifra inventada.

Lo que ya salió mal y esta skill evita: tarjetas KPI con borde de color, barras laterales,
kicker en versalitas encima de cada título, texto redundante, "hora CDMX" en el
encabezado, sin portada. Eso se lee como generado por IA ("vibecoded"). Las gráficas, en
cambio, gustaron: se conservan tal cual en `scripts/charts.py`.

## Flujo

Sigue los pasos en orden. Los marcados ⛔ no se saltan.

`<skill>` es el directorio base que muestra esta skill al cargarse; `<dataviz>`, el de la
skill `dataviz` (cambia con cada versión de Claude Code: tómalo de su encabezado al cargarla).

### 1. Verifica las cifras ⛔

Antes de maquetar, recalcula en Python todo lo que se pueda cruzar: sumas por mes contra
el total, componentes contra su agregado, derivados (promedios, porcentajes, "cada 10
ventas ≈ +22k"). Anota cada discrepancia, aunque sea de centavos, y díselo al usuario al
entregar. No la corrijas en silencio. Si una cifra no está en la fuente, no la pongas.
Aplica también la regla de no inventar causas de `references/redaccion.md`.

Si el informe junta reportes de varias personas o áreas y alguno trae un error (un
porcentaje mal sacado, dos periodos distintos), pregunta antes de maquetar si van **tal
cual** o **corregidas**. Usa lo que elija el usuario y, al entregar, di qué cifras vienen
de terceros y cuáles calculaste tú.

### 2. Encuentra la marca del cliente ⛔

Busca en el proyecto, no la supongas:

```bash
ls <repo>/*logo* <repo>/public/img/                           # logo (PNG si el SVG pesa >100 KB)
grep -n "primary\|accent\|--" <repo>/src/index.css            # colores (a menudo en HSL)
sed -n '/fontFamily/,/}/p' <repo>/tailwind.config.*            # fuentes
grep -rn "fonts.googleapis" <repo>/src <repo>/index.html
```

Del logo, usa la versión más nítida que haya: el PNG incrustado en un Word o PowerPoint
del cliente (`unzip -p archivo.docx 'word/media/*'`) suele verse mejor que un JPEG suelto.

Si hay una wiki o guía de voz de marca, léela. Las fuentes de la marca mandan aunque
sean comunes (Plus Jakarta Sans, DM Sans…): el brief gana. Descárgalas en local, porque
Chrome imprime con Helvetica sin avisar si no las encuentra:

```bash
python3 <skill>/scripts/fetch_fonts.py <trabajo> "Plus Jakarta Sans:500;700;800" "DM Sans:400;500;700"
```

Si la marca usa una fuente de Office que no está en Google Fonts, usa su gemela métrica
instalada en local y decláralas a mano en `fonts/fonts.css` con `@font-face` apuntando al
`.ttf` copiado: Calibri → **Carlito**, Cambria → **Caladea** (`~/Library/Fonts`). Pasa
`charts.FONT` y las familias de `base.css` a esa misma fuente.

Sin marca identificable: pregunta. No inventes una.

### 3. Acuerda la dirección con el usuario ⛔

Una pregunta con `AskUserQuestion`, dos o tres opciones con vista previa ASCII de la
portada y de una página interior. Deja primero la recomendada:

- **Marca + editorial (recomendada):** colores y fuentes del cliente, maquetado de informe
  anual. Cada página abre con una cifra grande y la gráfica ocupa el espacio. Portada con
  un motivo sacado del logo.
- **Editorial neutro:** casi monocromo, un solo acento, tono de documento de consejo.
- Una metáfora del giro del cliente (receta óptica, estado de cuenta…), avisando que puede
  verse juguetona.

Si el usuario ya fijó un estilo, no preguntes: aplícalo.

### 4. Paleta de gráficas validada ⛔

El color codifica un rol y el mismo rol lleva el mismo color en todo el documento:

| Rol | Color |
|---|---|
| Serie principal, escenario base | color principal de la marca |
| Segunda serie categórica | un tono que pase el validador contra el principal (con #0075A2 pasó #E3A33B; el teal #2E9C8A **falló**) |
| Escenarios ordenados (pesimista → optimista) | rampa de un solo tono: claro, medio, profundo |
| Crítico (vencido, caída, mes malo) | rojo de la marca, y en ningún otro uso |
| Parte neutra (cartera, por vencer) | gris azulado |

Carga la skill `dataviz` y corre su validador antes de usar cualquier par:

```bash
node <dataviz>/scripts/validate_palette.js "#0075A2,#E3A33B" --mode light
```

Un WARN de contraste obliga a que cada barra lleve su valor escrito (charts.py ya lo hace).

Si el par es **marca contra neutro** (antes y después, real y meta), no es una paleta
categórica: los FAIL de banda de luminosidad y de croma no aplican. Lo que sí debe
pasar es la separación CVD, el piso de visión normal y, con WARN de contraste, etiquetas
visibles.

### 5. Estructura

A4 horizontal. Cada página es una `.sheet` de 297×210 mm con `overflow:hidden`.

| Página | Tipo | Contenido |
|---|---|---|
| 1 | `.cover` | Logo, motivo con las dos cifras clave, título, destinatario (opcional) y fecha. Ver `references/portada.md`. |
| 2 | `.summary` | Una frase de 25–27 pt con las cifras clave resaltadas (buena en color de marca, mala en rojo). Abajo, dos columnas: "Lo que hay que saber" (3 puntos numerados) y "Qué hacer" (tabla área → acción). |
| 3… | `.spread` | Columna de 72 mm (cifra de 40 pt, frase de 14 pt, una o dos frases de cuerpo, tabla mini opcional) y gráfica grande a la derecha. Una gráfica por página. |
| … | `.toprow` | Cifra y frase en una fila, y debajo contenido a todo lo ancho: tabla de escenarios y dos gráficas, o barra partida y dos columnas. |

Las cuatro cifras clave del resumen **no** van en tarjetas: van dentro de la frase.

Registro técnico (para el equipo, no para dirección): mismas hojas, pero con nombres
reales de servicios, endpoints y tablas en monoespaciada, y diagramas de secuencia en
SVG (`references/diagramas.md`). No le agregues jerga a un documento ejecutivo:
rehaz la estructura.

### 6. Redacta ⛔

Carga la skill `humanizer` y aplica `references/redaccion.md`. Lo mínimo: cifra y frase
que la explica, frases cortas, sin metadatos (hora, zona horaria, nombre de la BD), sin
repetir el titular en el cuerpo, nota de método de dos líneas como máximo.

### 7. Construye

Copia a la carpeta de trabajo (el scratchpad, no el repo del cliente):
`assets/base.css`, `assets/ejemplo.py`, `scripts/charts.py`, el logo y `fonts/`.
Reemplaza en `base.css` los tokens de `:root` y las familias tipográficas; en
`charts.py`, `FONT` si la fuente de texto no es DM Sans; en `ejemplo.py`, datos y textos. Construye todo en un solo generador Python que escriba el
HTML, así cada ajuste es regenerar y no editar a mano. Los `&nbsp;` de cifras ("65 %",
"1 400 h") se ponen solo en el texto, nunca dentro de `<svg>` o `<style>`: ahí rompen
coordenadas sin dar error. `ejemplo.py` ya parte el HTML así; si agregas patrones,
agrégalos en `nbsp()`.

```bash
python3 informe.py && bash <skill>/scripts/build_pdf.sh informe.html informe.pdf
```

`build_pdf.sh` imprime con Chrome headless, lista las fuentes incrustadas y deja un PNG
por página. Si aparece `Helvetica` o `LucidaGrande`, falló una fuente o un glifo (las
flechas → caen en Lucida: escribe "en adelante"). Al empezar borra el PDF y los PNG anteriores, así
que todo PNG que veas es de esa corrida.

Si piden también un **Word sencillo** con el mismo contenido, usa `assets/word_simple.js`
(docx-js): logo, título, un párrafo, una tabla y secciones cortas, en una o dos hojas. Sin
gráficas: lo visual va en el PDF. Valídalo y revísalo renderizado como cualquier docx.

### 8. Revisa lo que salió ⛔

Abre **cada** PNG con Read. Los errores de maquetación no dan error: se ven. Busca:

- Página con media hoja vacía → sube `H` del viewBox de la gráfica (en charts.py cada
  gráfica toma `W`/`H`). Es la palanca principal. Después, el tamaño del texto.
- Cifra partida entre líneas ("$18.5 / mil", "70 / %") → el generador pone `&nbsp;`
  antes de `%` y de `mil`. Revisa que siga ahí.
- Palabras pegadas en títulos con Plus Jakarta Sans a tamaño chico → `word-spacing:.06em`
  y sin `letter-spacing` negativo por debajo de 14 pt (ya está en base.css).
- Cifras grandes con huecos raros ("$128 .7") → `font-variant-numeric:normal` en display.
- Etiquetas de gráfica encimadas con barras o ejes → quita la etiqueta; la leyenda y la
  tabla ya identifican la serie.
- Texto recortado al pie → el `overflow:hidden` lo esconde. Busca la última línea.

Después corre el detector una sola vez:

```bash
~/.claude/skills/impeccable/scripts/impeccable detect --json informe.html
```

Corrige el contraste (texto gris ≥4.5:1: `#687782` sobre blanco pasa, `#8A98A1` no).
Los avisos de `tight-leading` en textos SVG y de `overused-font` en la fuente de marca
no aplican. Dos rondas de revisión como máximo; luego se entrega.

### 9. Entrega

```bash
cp informe.pdf <destino>/<nombre-sugerido>.pdf
pdftotext <destino>/<nombre>.pdf - | grep -ciE "<nombres de clientes>"   # debe dar 0
open <destino>/<nombre>.pdf
```

En la respuesta: qué hay en cada página (tabla corta), las discrepancias de datos del
paso 1, qué calculaste tú y cómo, y cualquier frase que pueda leerse como reclamo a
alguien del equipo, para que el usuario decida si va a la junta.

## Archivos

| Archivo | Qué es |
|---|---|
| `scripts/charts.py` | Barras simples y apiladas, agrupadas, líneas, barra partida, barras horizontales con rango (`range_bars`), pares antes/después (`before_after`), leyenda. |
| `scripts/build_pdf.sh` | Chrome headless → PDF, fuentes incrustadas y PNG por página. |
| `scripts/fetch_fonts.py` | Google Fonts → woff2 local y `fonts/fonts.css`. |
| `assets/base.css` | Tokens, hojas, portada, resumen, spread, toprow, tablas. |
| `assets/ejemplo.py` | Esqueleto de cuatro páginas con datos ficticios. |
| `assets/word_simple.js` | Word acompañante de una o dos hojas (docx-js). |
| `references/portada.md` | Cómo sacar el motivo del logo, con el ejemplo de los lentes. |
| `references/redaccion.md` | Reglas de texto y un antes/después real. |
| `references/diagramas.md` | Diagramas de secuencia en SVG para el registro técnico. |
