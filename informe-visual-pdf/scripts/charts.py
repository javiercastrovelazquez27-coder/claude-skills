"""Gráficas SVG para informes en PDF.

Cada función devuelve un <svg> en línea que escala al ancho de su contenedor.
La altura la decide el viewBox: sube H (y ph, la altura del área de trazo) cuando la
gráfica deja la página medio vacía; es la palanca principal de maquetación.

Reglas que ya vienen resueltas aquí (no las rompas al adaptar):
- Barras con esquinas redondeadas solo arriba, ancladas a la base.
- 2 px de separación entre segmentos apilados.
- Etiqueta de valor sobre cada barra; ejes y rejilla en gris claro.
- Textos en tinta (INK/MUT), nunca del color de la serie.
- Un periodo incompleto se marca con rayado (hatch=True), no con otro color.
- Sin eje dual. Una línea puede no empezar en cero, pero se dice en la nota.
"""

INK = "#14242E"
MUT = "#5B6B75"
AXIS = "#687782"   # >= 4.5:1 sobre blanco
GRID = "#E7ECEF"
BASE = "#C5CFD5"
FONT = "'DM Sans', sans-serif"   # cámbiala por la fuente de texto del cliente (charts.FONT = ...)


def money(x):
    return f"${x:,.0f}"


def kilo(x, dec=1):
    return f"{x/1000:.{dec}f}k"


def on_color(hex_):
    """Tinta legible sobre un relleno: blanco en oscuros, INK en claros (ámbar, gris)."""
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    return "#fff" if 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.5 else INK


def txt(x, y, s, size=11, fill=MUT, anchor="middle", weight=400):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def bar_path(x, y, w, h, r=4, top=True):
    if h <= 0:
        return ""
    r = min(r, h, w / 2)
    if not top:
        return f"M{x},{y} h{w} v{h} h{-w} z"
    return (f"M{x},{y+h} v{-(h-r)} q0,{-r} {r},{-r} h{w-2*r} q{r},0 {r},{r} "
            f"v{h-r} z")


def svg_open(w, h, font=FONT):
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
            f'style="width:100%;height:auto;display:block" font-family="{font}" '
            'font-variant-numeric="tabular-nums">'
            '<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="#fff" '
            'stroke-width="2.2" stroke-opacity=".6"/></pattern></defs>')


def ygrid(x0, x1, y0, ph, vmax, step, fmt):
    out, v = [], 0
    while v <= vmax + 1e-9:
        y = y0 + ph - ph * v / vmax
        out.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" '
                   f'stroke="{GRID if v else BASE}" stroke-width="1"/>')
        out.append(txt(x0 - 7, y + 3.5, fmt(v), 10, AXIS, "end"))
        v += step
    return out


def bars(labels, values, vmax, step, color, *, top_labels=None, sub_labels=None,
         highlight=None, hatch_last=False, W=720, H=470, fmt=None):
    """Barras simples. highlight={índice: color} para el dato que hay que ver."""
    x0, x1, y0, ph = 44, W - 5, 24, H - 60
    fmt = fmt or (lambda v: f"{v:.0f}")
    s = [svg_open(W, H)] + ygrid(x0, x1, y0, ph, vmax, step, fmt)
    slot = (x1 - x0) / len(labels)
    bw = slot * 0.5
    for i, v in enumerate(values):
        x = x0 + slot * i + (slot - bw) / 2
        h = ph * v / vmax
        base = y0 + ph
        col = (highlight or {}).get(i, color)
        s.append(f'<path d="{bar_path(x, base-h, bw, h)}" fill="{col}"/>')
        if hatch_last and i == len(values) - 1:
            s.append(f'<path d="{bar_path(x, base-h, bw, h)}" fill="url(#hatch)"/>')
        top = (top_labels or [None] * len(values))[i]
        sub = (sub_labels or [None] * len(values))[i]
        if top is not None:
            s.append(txt(x + bw / 2, base - h - (22 if sub else 9), top, 13, INK, weight=700))
        if sub is not None:
            s.append(txt(x + bw / 2, base - h - 8, sub, 10, MUT))
        s.append(txt(x + bw / 2, base + 17, labels[i], 11.5, MUT))
    s.append("</svg>")
    return "".join(s)


def stacked(labels, series, vmax, step, *, totals=None, hatch_last=False,
            seg_labels=False, W=720, H=470, bw_ratio=0.5, fmt=None):
    """Barras apiladas. series=[(nombre, valores, color), ...] de abajo hacia arriba."""
    x0, x1, y0, ph = 44, W - 5, 24, H - 60
    fmt = fmt or (lambda v: f"{v/1000:.0f}k" if v else "0")
    s = [svg_open(W, H)] + ygrid(x0, x1, y0, ph, vmax, step, fmt)
    slot = (x1 - x0) / len(labels)
    bw = slot * bw_ratio
    for j in range(len(labels)):
        x = x0 + slot * j + (slot - bw) / 2
        yb = y0 + ph
        segs = [c for c in series if c[1][j] > 0]
        for idx, (_, vals, col) in enumerate(segs):
            h = ph * vals[j] / vmax
            path = bar_path(x, yb - h, bw, h, top=idx == len(segs) - 1)
            s.append(f'<path d="{path}" fill="{col}"/>')
            if hatch_last and j == len(labels) - 1:
                s.append(f'<path d="{path}" fill="url(#hatch)"/>')
            if seg_labels and h > 16:
                s.append(txt(x + bw / 2, yb - h / 2 + 4, kilo(vals[j]), 10, on_color(col), weight=700))
            yb -= h + 2
        if totals:
            s.append(txt(x + bw / 2, yb - 7, totals[j], 12.5, INK, weight=700))
        s.append(txt(x + bw / 2, y0 + ph + 17, labels[j], 11.5, MUT))
    s.append("</svg>")
    return "".join(s)


def grouped(labels, series, vmax, step, *, bold=None, W=520, H=330, bw=36, fmt=None):
    """Barras agrupadas (p. ej. escenarios por mes). series=[(nombre, valores, color)]."""
    x0, x1, y0, ph = 40, W - 5, 18, H - 50
    fmt = fmt or (lambda v: f"{v/1000:.0f}k" if v else "0")
    s = [svg_open(W, H)] + ygrid(x0, x1, y0, ph, vmax, step, fmt)
    slot = (x1 - x0) / len(labels)
    gap = 3
    grp = len(series) * bw + (len(series) - 1) * gap
    for j, lab in enumerate(labels):
        gx = x0 + slot * j + (slot - grp) / 2
        for i, (nombre, vals, col) in enumerate(series):
            x = gx + i * (bw + gap)
            h = ph * vals[j] / vmax
            s.append(f'<path d="{bar_path(x, y0+ph-h, bw, h)}" fill="{col}"/>')
            s.append(txt(x + bw / 2, y0 + ph - h - 6, kilo(vals[j], 0), 10.5, INK,
                         weight=700 if nombre == bold else 400))
        s.append(txt(gx + grp / 2, y0 + ph + 17, lab, 11.5, MUT))
    s.append("</svg>")
    return "".join(s)


def lines(labels, series, lo, hi, step, *, unit="&nbsp;%", W=720, H=470):
    """Líneas con marcador. Etiqueta directa solo en el último punto de cada serie.
    series=[(nombre, valores, color, desplazamiento)] con desplazamiento +1 (texto abajo)
    o -1 (texto arriba) para que las etiquetas finales no choquen."""
    x0, x1, y0, ph = 44, W - 80, 20, H - 58
    s = [svg_open(W, H)]
    v = lo
    while v <= hi:
        y = y0 + ph - ph * (v - lo) / (hi - lo)
        s.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        s.append(txt(x0 - 7, y + 3.5, f"{v}{unit}", 10, AXIS, "end"))
        v += step
    stepx = (x1 - x0 - 50) / (len(labels) - 1)
    X = [x0 + 25 + stepx * i for i in range(len(labels))]

    def Y(val):
        return y0 + ph - ph * (val - lo) / (hi - lo)
    for i, lab in enumerate(labels):
        s.append(txt(X[i], y0 + ph + 18, lab, 11.5, MUT))
    for nombre, vals, col, dy in series:
        pts = " ".join(f"{X[i]:.1f},{Y(v):.1f}" for i, v in enumerate(vals))
        s.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.6" '
                 'stroke-linejoin="round" stroke-linecap="round"/>')
        for i, v in enumerate(vals):
            s.append(f'<circle cx="{X[i]:.1f}" cy="{Y(v):.1f}" r="5" fill="{col}" stroke="#fff" stroke-width="2"/>')
        s.append(txt(X[-1] + 12, Y(vals[-1]) + (13 if dy > 0 else -5), f"{vals[-1]}{unit}", 13, INK, "start", 700))
        s.append(txt(X[-1] + 12, Y(vals[-1]) + (27 if dy > 0 else -19), nombre, 11, MUT, "start"))
    s.append("</svg>")
    return "".join(s)


def part_bar(parts, total, W=1000, H=70):
    """Una barra partida que suma el total. parts=[(nombre, valor, color, color_texto)]."""
    s = [svg_open(W, H)]
    x = 0
    for i, (n, v, col, tc) in enumerate(parts):
        w = W * v / total - (3 if i < len(parts) - 1 else 0)
        s.append(f'<rect x="{x:.1f}" y="0" width="{w:.1f}" height="62" rx="6" fill="{col}"/>')
        s.append(txt(x + 12, 25, n, 13, tc, "start", 700))
        s.append(txt(x + 12, 45, f"{money(v)} · {v/total*100:.0f}&nbsp;%", 12.5, tc, "start"))
        x += w + 3
    s.append("</svg>")
    return "".join(s)


def hbar_path(x, y, w, h, r=4):
    """Barra horizontal anclada a la izquierda, esquinas redondeadas solo a la derecha."""
    if w <= 0:
        return ""
    r = min(r, h / 2, w)
    return (f"M{x},{y} h{w-r} q{r},0 {r},{r} v{h-2*r} q0,{r} {-r},{r} "
            f"h{-(w-r)} z")


def range_bars(rows, vmax, step, color, light, *, unit="&nbsp;%", W=760, H=420, lw=230):
    """Barras horizontales con rango: sólido hasta el mínimo, claro hasta el máximo.

    rows=[(nombre, subtítulo, lo, hi)]. Si lo == hi, barra sólida. Para datos que cada
    fuente reporta como intervalo ("60–80 %"): no inventa un punto, muestra el rango.
    """
    x0, x1 = lw, W - 80
    s = [svg_open(W, H)]
    v = 0
    while v <= vmax + 1e-9:
        x = x0 + (x1 - x0) * v / vmax
        s.append(f'<line x1="{x:.1f}" y1="10" x2="{x:.1f}" y2="{H-32}" '
                 f'stroke="{GRID if v else BASE}" stroke-width="1"/>')
        s.append(txt(x, H - 12, f"{v:g}{unit}", 11, AXIS))
        v += step
    fila = (H - 50) / len(rows)
    for i, (nom, sub, lo, hi) in enumerate(rows):
        bh = min(fila * 0.42, 40)
        y = 14 + fila * i + (fila - bh) / 2
        wlo, whi = (x1 - x0) * lo / vmax, (x1 - x0) * hi / vmax
        if hi > lo:
            s.append(f'<path d="{hbar_path(x0, y, whi, bh)}" fill="{light}"/>')
            s.append(f'<rect x="{x0}" y="{y:.1f}" width="{wlo:.1f}" height="{bh:.1f}" fill="{color}"/>')
        else:
            s.append(f'<path d="{hbar_path(x0, y, wlo, bh)}" fill="{color}"/>')
        lab = f"{lo:g}{unit}" if hi == lo else f"{lo:g}–{hi:g}{unit}"
        s.append(txt(x0 + whi + 8, y + bh / 2 + 5, lab, 14, INK, "start", 700))
        s.append(txt(x0 - 12, y + bh / 2 - (2 if sub else -5), nom, 13.5, INK, "end", 700))
        if sub:
            s.append(txt(x0 - 12, y + bh / 2 + 14, sub, 10.5, MUT, "end"))
    s.append("</svg>")
    return "".join(s)


def before_after(rows, vmax, before, after, *, W=1000, H=460, lw=260):
    """Pares horizontales antes / después por tarea, en una sola escala.

    rows=[(tarea, valor_antes, valor_despues, etiqueta_antes, etiqueta_despues)].
    Las etiquetas llevan el dato tal como lo dio la fuente ("2–3 días", "30–45 min");
    la barra usa el punto medio. Dilo en la nota al pie.
    """
    x0, x1 = lw, W - 120
    s = [svg_open(W, H)]
    fila = (H - 10) / len(rows)
    for i, (tarea, a, b, la, lb) in enumerate(rows):
        bh = min(fila * 0.3, 22)
        y = 6 + fila * i
        wa, wb = (x1 - x0) * a / vmax, (x1 - x0) * b / vmax
        s.append(txt(x0 - 12, y + bh + 4, tarea, 13, INK, "end", 700))
        s.append(f'<path d="{hbar_path(x0, y, wa, bh, 3)}" fill="{before}"/>')
        s.append(txt(x0 + wa + 7, y + bh - 4, la, 11.5, MUT, "start"))
        yb = y + bh + 3
        s.append(f'<path d="{hbar_path(x0, yb, max(wb, 2), bh, 3)}" fill="{after}"/>')
        s.append(txt(x0 + max(wb, 2) + 7, yb + bh - 4, lb, 11.5, INK, "start", 700))
    s.append("</svg>")
    return "".join(s)


def legend(*items):
    """Leyenda HTML. items=(texto, color)."""
    return '<p class="legend">' + "".join(
        f'<span><i style="background:{c}"></i>{t}</span>' for t, c in items) + "</p>"
