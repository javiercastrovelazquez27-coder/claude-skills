#!/usr/bin/env python3
"""Esqueleto de informe: portada, resumen, spread y toprow.

DATOS FICTICIOS. Cópialo a la carpeta de trabajo, reemplaza datos, textos, colores y
logo, y genera con:
    python3 ejemplo.py && bash <skill>/scripts/build_pdf.sh informe.html informe.pdf

Espera junto a él: fonts/fonts.css (scripts/fetch_fonts.py), base.css (assets/),
charts.py (scripts/) y el logo del cliente.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from charts import bars, stacked, lines, legend, part_bar, money  # noqa: E402

# Paleta: roles, no decoración. Revisa los pares con scripts/contraste.py.
BRAND = "#0075A2"
BRAND_D = "#0B3446"
SECOND = "#E3A33B"   # segunda serie categórica (pasa CVD contra BRAND)
CRIT = "#DE3E41"
GRAY = "#A9B6BE"

meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun*"]
a = [12000, 15000, 18000, 21000, 19000, 9000]
b = [8000, 9000, 14000, 16000, 12000, 6000]
tot = [x + y for x, y in zip(a, b)]


def foot(n):
    return (f'<footer><span>Cliente · Nombre del informe · Mes año</span>'
            f'<span class="pn">{n}</span></footer>')


css = (open(os.path.join(HERE, "fonts", "fonts.css")).read()
       + open(os.path.join(HERE, "base.css")).read())

html = f"""<!doctype html><html lang="es-MX"><head><meta charset="utf-8">
<title>Cliente · Informe</title><style>{css}</style></head><body>

<section class="sheet cover">
  <img class="logo" src="logo.png" alt="Cliente">
  <!-- Motivo de portada: sácalo del logo del cliente (ver references/portada.md).
       Aquí, a falta de logo, las dos cifras clave a escala de cartel. -->
  <div class="motif" style="display:grid;grid-template-columns:1fr 1fr;gap:20mm;margin-top:40mm">
    <div><p class="num" style="font-size:54pt">$94 mil</p><p class="lead">cobrados en el semestre</p></div>
    <div><p class="num r" style="font-size:54pt">$18 mil</p><p class="lead">vencidos</p></div>
  </div>
  <div class="cover-foot">
    <div><h1>Nombre del<br>informe</h1><p class="cover-sub">Una línea que dice qué contiene.</p></div>
    <p class="cover-meta">Para Nombre Apellido<br>1 de julio de 2026</p>
  </div>
</section>

<section class="sheet summary">
  <p class="statement">En el semestre se cobraron <b>$94 mil</b>. Hay <b class="r">$18 mil</b> vencidos.
  Para el siguiente trimestre esperamos <b>$60 mil</b>.</p>
  <div class="cols2">
    <div><h2>Lo que hay que saber</h2>
      <ol class="points">
        <li><b>Hallazgo en una frase.</b> La consecuencia, con su número.</li>
        <li><b>Segundo hallazgo.</b> Qué implica, con su número.</li>
      </ol></div>
    <div><h2>Qué hacer</h2>
      <table class="todo">
        <tr><th>Área</th><td>Acción concreta, con verbo y objeto.</td></tr>
        <tr><th>Área</th><td>Otra acción.</td></tr>
      </table></div>
  </div>
  {foot(2)}
</section>

<section class="sheet spread">
  <aside>
    <p class="num">$37 mil</p>
    <p class="lead">se cobraron en abril, el mejor mes.</p>
    <p>Una o dos frases que dicen lo que la gráfica no dice sola.</p>
  </aside>
  <main>
    <h2>Cobrado por mes</h2>
    {legend(("Serie A", BRAND), ("Serie B", SECOND))}
    {stacked(meses, [("A", a, BRAND), ("B", b, SECOND)], 40000, 10000,
             totals=[f"{t/1000:.1f}k" for t in tot], hatch_last=True)}
    <p class="note">* Junio, al día 15.</p>
  </main>
  {foot(3)}
</section>

<section class="sheet">
  <div class="toprow">
    <p class="num">$112 mil</p>
    <p class="lead">falta por cobrar. $18 mil ya vencieron.</p>
  </div>
  {part_bar([("Cobrado", 94000, BRAND, "#fff"), ("Vencido", 18000, CRIT, "#fff"),
             ("Por vencer", 30000, "#D5DEE3", "#14242E")], 142000)}
  <div class="cols2" style="margin-top:8mm">
    <div><h2>Tasa de cobro</h2>
      {legend(("A", BRAND), ("B", SECOND))}
      {lines(meses[:-1], [("A", [96, 94, 90, 85, 80], BRAND, 1), ("B", [99, 92, 93, 88, 84], SECOND, -1)],
             70, 100, 10, W=520, H=300)}</div>
    <div><h2>Ventas por mes</h2>
      {bars(meses, [10, 12, 15, 14, 3, 8], 20, 5, BRAND, top_labels=[10, 12, 15, 14, 3, 8],
            highlight=dict([(4, CRIT)]), hatch_last=True, W=520, H=300)}</div>
  </div>
  {foot(4)}
</section>
</body></html>"""

# Espacios que no deben partir línea: "70 %", "$18.5 mil", "1 400 h".
# Solo sobre el texto: dentro de <svg> y <style> los espacios entre números son
# coordenadas y valores CSS, y un &nbsp; ahí rompe la gráfica sin dar error.
def nbsp(chunk):
    chunk = re.sub(r"(\d) (%|mil|h\b|horas)", r"\1&nbsp;\2", chunk)
    return re.sub(r"(\d) (\d{3})\b", r"\1&nbsp;\2", chunk)


partes = re.split(r"(<style>.*?</style>|<svg.*?</svg>)", html, flags=re.S)
html = "".join(p if p.startswith(("<style>", "<svg")) else nbsp(p) for p in partes)
open(os.path.join(HERE, "informe.html"), "w").write(html)
print(os.path.join(HERE, "informe.html"))
