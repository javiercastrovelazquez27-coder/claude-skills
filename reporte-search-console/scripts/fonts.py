"""Download Google Fonts families (github.com/google/fonts) and make static weights.

    python fonts.py "Inter" "Funnel Display"

Writes <cache>/fonts/<Family>-<weight>.ttf for 300/400/600/700 when the family has
those weights. Two traps handled here:
- `fonttools varLib.instancer` keeps the variable font's PostScript name in every
  instance ("Inter-Regular"), and reportlab embeds fonts by that name: all weights
  collapse into one. Each instance gets a unique PostScript name (nameID 6).
- matplotlib groups faces by family name (nameID 1): it must stay the plain family
  ("Inter"), with the weight read from OS/2.usWeightClass.
"""
import io
import json
import pathlib
import sys
import urllib.request

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

CACHE = pathlib.Path.home() / ".cache" / "reporte-search-console" / "fonts"
WEIGHTS = {300: "Light", 400: "Regular", 600: "SemiBold", 700: "Bold"}
UA = {"User-Agent": "reporte-search-console"}


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def _source_ttf(family):
    """The family's upright TTF from google/fonts: (path, is_variable, static file entries)."""
    slug = family.lower().replace(" ", "")
    for lic in ("ofl", "apache", "ufl"):
        try:
            listing = json.loads(_get(f"https://api.github.com/repos/google/fonts/contents/{lic}/{slug}"))
        except Exception:
            continue
        ttfs = [f for f in listing if f["name"].endswith(".ttf") and "Italic" not in f["name"]]
        variable = [f for f in ttfs if "[" in f["name"]]
        pick = variable[0] if variable else next((f for f in ttfs if f["name"].endswith("-Regular.ttf")), None)
        if pick:
            dest = CACHE / "src" / pick["name"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                dest.write_bytes(_get(pick["download_url"]))
            return dest, bool(variable), [f for f in ttfs if "[" not in f["name"]]
    raise SystemExit(f"{family}: not found in google/fonts (ofl/apache/ufl)")


def _rename(font, family, weight):
    ps_family = family.replace(" ", "")
    style = WEIGHTS[weight]
    name = font["name"]
    for i in (1, 2, 3, 4, 6, 16, 17):
        name.removeNames(nameID=i)
    for i, value in (
        (1, family),
        (2, "Bold" if weight == 700 else "Regular"),
        (3, f"{ps_family}-{style};static"),
        (4, f"{family} {style}"),
        (6, f"{ps_family}-{style}"),
        (16, family),
        (17, style),
    ):
        name.setName(value, i, 3, 1, 0x409)
    font["OS/2"].usWeightClass = weight


def ensure(family):
    """Static TTFs for `family`: {weight: path}. Cached across runs."""
    ps_family = family.replace(" ", "")
    out = {w: CACHE / f"{ps_family}-{w}.ttf" for w in WEIGHTS}
    if all(p.exists() for p in out.values()):
        return out
    src, is_variable, statics = _source_ttf(family)
    result = {}
    if is_variable:
        base = TTFont(src)
        axes = {a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in base["fvar"].axes}
        lo, _, hi = axes["wght"]
        for w in WEIGHTS:
            if not lo <= w <= hi:
                continue
            # Other axes at their default; optical size at text size (14)
            loc = {tag: default for tag, (_, default, _) in axes.items()}
            loc["wght"] = w
            if "opsz" in axes:
                loc["opsz"] = max(axes["opsz"][0], min(14, axes["opsz"][2]))
            inst = instancer.instantiateVariableFont(TTFont(src), loc)
            _rename(inst, family, w)
            inst.save(out[w])
            result[w] = out[w]
    else:
        by_style = {f["name"].rsplit("-", 1)[-1].removesuffix(".ttf"): f for f in statics}
        for w, style in WEIGHTS.items():
            f = by_style.get(style)
            if not f:
                continue
            font = TTFont(io.BytesIO(_get(f["download_url"])))
            _rename(font, family, w)
            font.save(out[w])
            result[w] = out[w]
    if 400 not in result:
        raise SystemExit(f"{family}: no regular weight available")
    return result


if __name__ == "__main__":
    for fam in sys.argv[1:]:
        print(fam, {w: str(p) for w, p in ensure(fam).items()})
