#!/usr/bin/env python3
"""Descarga fuentes de Google Fonts (subset latin, woff2) y escribe fonts/fonts.css.

Uso:
    python3 fetch_fonts.py <dir_salida> "Plus Jakarta Sans:500;700;800" "DM Sans:400;500;700"

Chrome imprime con lo que tenga cargado: si la fuente no está en local o en la red al
momento de imprimir, cae en Helvetica sin avisar. Confírmalo después con `pdffonts`.
"""
import os
import re
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")


def main():
    out = sys.argv[1]
    specs = sys.argv[2:]
    os.makedirs(os.path.join(out, "fonts"), exist_ok=True)
    fams = []
    for spec in specs:
        fam, weights = spec.split(":")
        fams.append(f"family={urllib.parse.quote_plus(fam)}:wght@{weights}")
    url = "https://fonts.googleapis.com/css2?" + "&".join(fams) + "&display=swap"
    css = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA})).read().decode()
    faces = []
    for sub, body in re.findall(r"/\* (\S+) \*/\s*@font-face \{(.*?)\}", css, re.S):
        if sub != "latin":
            continue
        fam = re.search(r"font-family: '([^']+)'", body).group(1)
        w = re.search(r"font-weight: ([\d ]+);", body).group(1).strip()
        src = re.search(r"url\((\S+?)\)", body).group(1)
        fn = f"fonts/{fam.replace(' ', '')}-{w.replace(' ', '_')}.woff2"
        urllib.request.urlretrieve(src, os.path.join(out, fn))
        faces.append(f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;"
                     f"src:url('{fn}') format('woff2')}}")
    with open(os.path.join(out, "fonts", "fonts.css"), "w") as f:
        f.write("\n".join(faces) + "\n")
    print("\n".join(faces))


if __name__ == "__main__":
    main()
