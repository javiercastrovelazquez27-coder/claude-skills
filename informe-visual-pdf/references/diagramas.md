# Diagramas dentro del PDF

Chrome renderiza SVG en línea sin problema. No hace falta generar imágenes
aparte ni depender de librerías de graficación: escribe el SVG a mano y tendrás
control exacto sobre el resultado.

## Regla de altura

El SVG escala con el ancho del contenedor. La altura resultante es:

```
altura_mm = ancho_disponible_mm × (viewBox_alto / viewBox_ancho)
```

En A4 horizontal con márgenes de 13mm el ancho disponible es ~271mm. Un
`viewBox="0 0 1010 476"` a ancho completo ocupa 271 × 0.471 ≈ **128mm** de los
~190mm útiles, y solo quedan 62mm para lo demás.

Por eso conviene controlar el alto con el ancho:

```html
<svg viewBox="0 0 1010 476" xmlns="http://www.w3.org/2000/svg"
     style="width:83%;height:auto;display:block;margin:0 auto">
```

Bajar de 100% a 83% recorta ~22mm de alto. Es la palanca más rápida cuando una
página se desborda por poco: **ajusta el ancho del SVG antes de recortar texto.**

## Diagrama de secuencia (lanes verticales)

Es el formato que mejor comunica un flujo entre sistemas: cada actor es una
columna, el tiempo baja, cada flecha es una llamada. Plantilla:

```html
<svg viewBox="0 0 1010 476" xmlns="http://www.w3.org/2000/svg"
     style="width:83%;height:auto;display:block;margin:0 auto">
  <defs>
    <marker id="ar" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 z" fill="#0B4F9E"/>
    </marker>
    <!-- un marker por color de flecha: los markers NO heredan el stroke -->
  </defs>

  <g font-family="Carlito, sans-serif">
    <!-- cabecera de cada lane -->
    <rect x="10" y="0" width="215" height="30" rx="4" fill="#0B2545"/>
    <text x="117" y="19" fill="#fff" font-size="11.5" font-weight="700"
          text-anchor="middle">Sistema A</text>

    <!-- línea de vida -->
    <line x1="117" y1="34" x2="117" y2="468"
          stroke="#C9D3DC" stroke-width="1.2" stroke-dasharray="4 4"/>

    <!-- mensaje: título, subtítulo y flecha -->
    <text x="122" y="60" font-size="10.5" font-weight="700" fill="#0B2545">1 · Nombre del paso</text>
    <text x="122" y="72" font-size="9" fill="#5A6875">detalle técnico del paso</text>
    <line x1="117" y1="80" x2="347" y2="80"
          stroke="#0B4F9E" stroke-width="1.6" marker-end="url(#ar)"/>
  </g>
</svg>
```

Convenciones que hacen que se lea bien:

- **Ritmo constante.** Deja ~44px entre flechas consecutivas: título en `y-20`,
  subtítulo en `y-8`, flecha en `y`. Si un paso necesita una tercera línea, dale
  ~54px y recorre el resto.
- **Numera los pasos.** `1 ·`, `2 ·` … El lector sigue la secuencia sin rastrear
  posiciones verticales.
- **El texto arranca 5px a la derecha del origen de la flecha**, no centrado:
  centrar hace que los textos largos invadan lanes vecinos.
- **Flechas de regreso** (derecha a izquierda) invierten `x1`/`x2` y usan un
  marker del color correspondiente. Colorearlas distinto del flujo de ida ayuda
  a distinguir petición de respuesta.
- **Mensaje a sí mismo:** `<path d="M352,210 h22 v14 h-22" fill="none" .../>`.
- **Deja que las flechas crucen lanes intermedios** cuando el salto es real
  (por ejemplo, middleware → OMS pasando sobre otro sistema). Es más honesto
  que inventar un rebote que no ocurre.

## Pipeline horizontal (registro ejecutivo)

Para el documento de alto nivel funciona mejor una fila de tarjetas con
chevrones entre ellas, usando `.pipe` / `.step` / `.arrow` del CSS base. Cinco
pasos es el máximo cómodo en A4 horizontal; con seis el texto se vuelve ilegible.

Cada `.step` lleva una barra de color superior (`.bar` con `background` propio).
Un degradado de tono a lo largo del pipeline —del azul profundo al verde—
comunica progreso sin necesidad de explicarlo.
