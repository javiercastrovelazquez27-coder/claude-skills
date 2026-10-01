#!/usr/bin/env python3
"""Contraste WCAG de cada color contra el fondo y entre pares vecinos.

Uso: python3 contraste.py "#0075A2,#E3A33B" [--fondo "#FFFFFF"]
- Color de serie contra fondo: >= 3:1 o cada barra lleva su valor escrito.
- Texto contra fondo: >= 4.5:1.
- Entre series vecinas: la diferencia de luminancia ayuda a distinguirlas sin color;
  por debajo de 1.5:1 pon etiquetas directas o textura.
"""
import sys


def lum(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


if len(sys.argv) < 2:
    sys.exit(__doc__)
cols = [c.strip() for c in sys.argv[1].split(",")]
fondo = sys.argv[sys.argv.index("--fondo") + 1] if "--fondo" in sys.argv else "#FFFFFF"
for c in cols:
    r = ratio(c, fondo)
    print(f"{c} vs fondo {fondo}: {r:4.2f}:1  "
          f"{'texto OK' if r >= 4.5 else 'serie OK' if r >= 3 else 'BAJO: escribe el valor en cada barra'}")
for a, b in zip(cols, cols[1:]):
    r = ratio(a, b)
    print(f"{a} vs {b}: {r:4.2f}:1  {'distinguibles sin color' if r >= 1.5 else 'parecidos: etiquetas directas o textura'}")
