"""Render every page of a PDF to PNG for visual review.

    python render_pages.py report.pdf [out_dir] [dpi]
"""
import pathlib
import sys

import pymupdf

pdf = pathlib.Path(sys.argv[1]).expanduser()
out = pathlib.Path(sys.argv[2]).expanduser() if len(sys.argv) > 2 else pdf.with_suffix("")
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 85
out.mkdir(parents=True, exist_ok=True)
doc = pymupdf.open(pdf)
for i, page in enumerate(doc, 1):
    page.get_pixmap(dpi=dpi).save(out / f"page-{i}.png")
print(f"{doc.page_count} pages → {out}")
print("fonts:", sorted({f[3] for p in doc for f in p.get_fonts()}))
