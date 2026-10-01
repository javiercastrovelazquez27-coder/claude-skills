#!/usr/bin/env bash
# Imprime un HTML a PDF con Chrome headless y deja un PNG por página para revisarlo.
# Uso: build_pdf.sh entrada.html salida.pdf [dpi]
set -euo pipefail
IN="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="$2"
DPI="${3:-80}"
BASE="${OUT%.pdf}"
# Limpia antes de imprimir: si el script se corta (p. ej. con `| head`), no deben
# quedar PNG de una corrida anterior que parezcan de esta.
rm -f "$OUT" "${BASE}"-p-*.png

CHROME=""
for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
         "$(command -v google-chrome || true)" "$(command -v chromium || true)"; do
  [ -n "$c" ] && [ -x "$c" ] && CHROME="$c" && break
done
[ -z "$CHROME" ] && { echo "No encontré Chrome/Chromium"; exit 1; }

"$CHROME" --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$OUT" "file://$IN" 2>/dev/null
[ -s "$OUT" ] || { echo "Chrome no generó $OUT"; exit 1; }
pdftoppm -r "$DPI" -png "$OUT" "${BASE}-p"
echo "PDF: $OUT"
pdfinfo "$OUT" | grep -E "Pages|Page size"

# Fuentes realmente incrustadas: si aparece Helvetica/LucidaGrande donde no debería,
# faltó cargar una fuente o un glifo (flechas, símbolos) cayó en la de respaldo.
echo "Fuentes:"; pdffonts "$OUT" | tail -n +3 | awk '{print "  " $1}' | sed 's/^  [A-Z]*+/  /' | sort -u
ls "${BASE}"-p-*.png
