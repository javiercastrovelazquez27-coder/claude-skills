# Portada

La portada es la primera impresión del documento y la parte que más se ve cuando se
reenvía. Tiene tres piezas y nada más:

1. **Logo del cliente**, arriba a la izquierda, a unos 17 mm de alto.
2. **Un motivo sacado del logo** con las dos cifras que resumen el informe dentro.
3. **Pie**: título en dos líneas, una frase de qué contiene, y a la derecha
   la fecha y, si el usuario lo quiere, "Para <nombre>". Si el documento no debe decir a
   quién va dirigido, pon el área o la empresa que lo firma. La fecha va aquí y en
   ningún otro lado.

## Cómo encontrar el motivo

Mira el logo y busca su forma dominante, no su color. Esa forma, en grande y como
contenedor de datos, es la portada. No inventes una ilustración ni pongas degradados.

| Logo | Motivo |
|---|---|
| Óptica con dos lentes | Dos círculos del grosor del logo, unidos por el puente, con las patillas rojas del logo a los lados. Una cifra en cada lente. |
| Marca con un círculo o sello | Un solo sello grande con la cifra principal. |
| Logotipo solo tipográfico | Sin motivo: las dos cifras a escala de cartel (54 pt o más) en dos columnas. |

Si el logo es un SVG pesado (más de 100 KB suele traer un raster incrustado), usa el PNG.

## Referencia: el logo de dos lentes de una óptica

```python
def cover_glasses(pet="#0075A2", red="#DE3E41", deep="#0B3446", mut="#5B6B75"):
    W, H, r = 1000, 430, 196
    cxl, cxr, cy = 250, 750, 215
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
         'style="width:100%;height:auto;display:block" font-family="DM Sans">']
    s.append(f'<rect x="{cxl-r-30}" y="{cy-34}" width="9" height="68" rx="4.5" fill="{red}"/>')
    s.append(f'<rect x="{cxr+r+21}" y="{cy-34}" width="9" height="68" rx="4.5" fill="{red}"/>')
    s.append(f'<path d="M{cxl+r},{cy-6} Q500,{cy-40} {cxr-r},{cy-6}" fill="none" '
             f'stroke="{pet}" stroke-width="9" stroke-linecap="round"/>')
    for cx in (cxl, cxr):
        s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{pet}" stroke-width="11"/>')
    for cx, big, small, col in ((cxl, "$94&nbsp;mil", "cobrados en el semestre", deep),
                                (cxr, "$18&nbsp;mil", "vencidos sin cobrar", red)):
        s.append(f'<text x="{cx}" y="{cy+8}" text-anchor="middle" font-family="Plus Jakarta Sans" '
                 f'font-weight="800" font-size="74" letter-spacing="-2" fill="{col}">{big}</text>')
        s.append(f'<text x="{cx}" y="{cy+52}" text-anchor="middle" font-size="22" '
                 f'font-weight="500" fill="{mut}">{small}</text>')
    s.append("</svg>")
    return "".join(s)
```

La cifra buena va en el color profundo de la marca; la mala, en el rojo de crítico.
