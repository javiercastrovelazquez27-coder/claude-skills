"""Client PDF report from a Google Search Console export.

    python build_report.py config.json            # writes the PDF
    python build_report.py config.json --metrics  # prints the computed metrics (JSON) and exits

The export is the folder Search Console downloads from Performance → Export → CSV
(Spanish UI: Gráfico.csv, Consultas.csv, Páginas.csv, Países.csv, Dispositivos.csv;
English UI: Chart.csv, Queries.csv, Pages.csv, Countries.csv, Devices.csv).
Copy is Spanish (es-MX, "usted"). See ../config.example.json for every option.
"""
import csv
import datetime as dt
import json
import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image as RLImage,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import fonts as fontlib  # noqa: E402


def expand(p):
    return pathlib.Path(p).expanduser()


CFG_PATH = expand(sys.argv[1])
CFG = json.loads(CFG_PATH.read_text(encoding="utf-8"))
METRICS_ONLY = "--metrics" in sys.argv
EXPORT = expand(CFG["export_dir"])
OUT = expand(CFG.get("output", f"~/Downloads/Reporte-{CFG['site']}.pdf"))
WORK = pathlib.Path.home() / ".cache" / "reporte-search-console" / "work" / CFG["site"]
WORK.mkdir(parents=True, exist_ok=True)

# ── Export (Spanish or English UI) ──────────────────────────────────────────
FILES = {
    "daily": ("Gráfico.csv", "Chart.csv"),
    "queries": ("Consultas.csv", "Queries.csv"),
    "pages": ("Páginas.csv", "Pages.csv"),
    "countries": ("Países.csv", "Countries.csv"),
    "devices": ("Dispositivos.csv", "Devices.csv"),
}


def num(s):
    s = (s or "").strip().rstrip("%")
    if not s:
        return None
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    return float(s.replace(",", ""))


def read(kind):
    """Rows as (key, clicks, impressions, position) — columns by position, any UI language."""
    for name in FILES[kind]:
        path = EXPORT / name
        if path.exists():
            with open(path, encoding="utf-8-sig") as fh:
                rows = list(csv.reader(fh))[1:]
            out = []
            for r in rows:
                if len(r) < 5 or not r[0].strip():
                    continue
                out.append({"key": r[0].strip(), "c": int(num(r[1]) or 0), "i": int(num(r[2]) or 0), "pos": num(r[4])})
            return out
    return []


daily = read("daily")
if not daily:
    raise SystemExit(f"No Gráfico.csv / Chart.csv in {EXPORT}")
daily.sort(key=lambda r: r["key"])
queries, pages_raw, countries, devices = read("queries"), read("pages"), read("countries"), read("devices")


def wpos(rows):
    i = sum(r["i"] for r in rows if r["pos"] is not None)
    return sum(r["pos"] * r["i"] for r in rows if r["pos"] is not None) / i if i else None


start = dt.date.fromisoformat(daily[0]["key"])
end = dt.date.fromisoformat(daily[-1]["key"])
# Skip leading days before the site first appeared (new sites)
first_seen = next((i for i, r in enumerate(daily) if r["i"] > 0), 0)
active = daily[first_seen:]
clicks = sum(r["c"] for r in daily)
impr = sum(r["i"] for r in daily)
avg_pos = wpos(daily)

half = len(active) // 2
h1, h2 = active[:half], active[half:]
h1_i, h2_i = sum(r["i"] for r in h1), sum(r["i"] for r in h2)
h1_c, h2_c = sum(r["c"] for r in h1), sum(r["c"] for r in h2)
half_months = round(half / 30.4)

MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MON = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def long_date(d):
    return f"{d.day} de {MONTHS[d.month - 1]} de {d.year}"


def days_in_month(y, m):
    return ((dt.date(y + m // 12, m % 12 + 1, 1)) - dt.date(y, m, 1)).days


monthly = {}
for r in daily:
    d = dt.date.fromisoformat(r["key"])
    m = monthly.setdefault((d.year, d.month), {"c": 0, "i": 0, "days": 0})
    m["c"] += r["c"]
    m["i"] += r["i"]
    m["days"] += 1
for (y, m), v in monthly.items():
    v["full"] = v["days"] >= days_in_month(y, m) - 1

brand_terms = [t.lower() for t in CFG.get("brand_queries", [])]
brand_q = [q for q in queries if any(t in q["key"].lower() for t in brand_terms)]
brand_i = sum(q["i"] for q in brand_q)
brand_pos = wpos(brand_q)

topics = {}
for label, kws in CFG.get("topic_keywords", {}).items():
    rows = [q for q in queries if any(k.lower() in q["key"].lower() for k in kws) and q not in brand_q]
    if rows:
        topics[label] = {"rows": rows, "i": sum(r["i"] for r in rows), "c": sum(r["c"] for r in rows), "pos": wpos(rows)}
topic_rows = sorted({id(r): r for t in topics.values() for r in t["rows"]}.values(), key=lambda r: -r["i"])
top_topic = max(topics.items(), key=lambda kv: kv[1]["i"]) if topics else None
visible_query_clicks = sum(q["c"] for q in queries)

site_host = CFG["site"].removeprefix("www.")


def norm_path(url):
    p = url.split("://", 1)[-1]
    p = p[p.find("/"):] if "/" in p else "/"
    p = p.split("?")[0].split("#")[0]
    p = p.rstrip("/") or "/"
    for home in CFG.get("locale_homes", []):  # e.g. "/en/"
        if p == home.rstrip("/"):
            return home
    return p


pages = {}
for r in pages_raw:
    p = pages.setdefault(norm_path(r["key"]), {"c": 0, "i": 0, "pw": 0.0})
    p["c"] += r["c"]
    p["i"] += r["i"]
    p["pw"] += (r["pos"] or 0) * r["i"]
blog_prefixes = tuple(CFG.get("blog_prefixes", ["/blog"]))
blog_i = sum(v["i"] for k, v in pages.items() if k.startswith(blog_prefixes) and k.rstrip("/") not in {b.rstrip("/") for b in blog_prefixes})
blog_i_all = sum(v["i"] for k, v in pages.items() if k.startswith(blog_prefixes))
page_names = CFG.get("page_names", {})

DEVICE_ES = {"Mobile": "Celular", "Móviles": "Celular", "Desktop": "Computadora", "Ordenador": "Computadora", "Tablet": "Tablet"}
dev = {DEVICE_ES.get(d["key"], d["key"]): d for d in devices}
mobile = dev.get("Celular")
desktop = dev.get("Computadora")
COUNTRY_ES = {"Mexico": "México", "United States": "Estados Unidos", "Spain": "España", "Canada": "Canadá"}
countries_sorted = sorted(countries, key=lambda c: -c["c"])
home_country = countries_sorted[0] if countries_sorted else None
abroad = [c for c in countries_sorted[1:] if c["c"] > 0]

metrics = {
    "period": [start.isoformat(), end.isoformat()],
    "first_impression": active[0]["key"],
    "clicks": clicks,
    "impressions": impr,
    "ctr": clicks / impr if impr else 0,
    "avg_position": avg_pos,
    "halves": {"days_each": half, "first": [h1_i, h1_c], "last": [h2_i, h2_c]},
    "monthly": {f"{y}-{m:02d}": v for (y, m), v in monthly.items()},
    "brand": {"impressions": brand_i, "clicks": sum(q["c"] for q in brand_q), "position": brand_pos, "rows": [q["key"] for q in brand_q]},
    "topics": {k: {"impressions": v["i"], "clicks": v["c"], "position": v["pos"]} for k, v in topics.items()},
    "visible_query_clicks": visible_query_clicks,
    "pages": dict(sorted(pages.items(), key=lambda kv: -kv[1]["i"])),
    "blog_article_impressions": blog_i,
    "blog_impressions_incl_index": blog_i_all,
    "devices": {k: {"clicks": v["c"], "impressions": v["i"], "position": v["pos"]} for k, v in dev.items()},
    "countries": [{"country": c["key"], "clicks": c["c"], "impressions": c["i"]} for c in countries_sorted[:6]],
}
if METRICS_ONLY:
    print(json.dumps(metrics, indent=2, ensure_ascii=False, default=str))
    sys.exit()

# ── Brand, fonts ────────────────────────────────────────────────────────────
B = CFG.get("brand", {})
NAVY = B.get("primary", "#0F1F4D")
NAVY_DEEP = B.get("primary_deep", NAVY)
ACCENT = B.get("accent", "#6A9BCD")
ICE = B.get("surface", "#F3F5FD")
INK = B.get("ink", "#1F2A44")
MUTED = B.get("muted", "#5B6680")
LINE = B.get("line", "#DCE2F0")
COVER_SUB = B.get("cover_subtle", "#C9D5EE")

F = CFG.get("fonts", {})


def register(role, family, fallback):
    try:
        files = fontlib.ensure(family)
    except (SystemExit, Exception) as e:  # offline or unknown family → built-in fonts
        print(f"font {family}: {e} → {fallback}")
        return {w: fallback for w in (300, 400, 600, 700)}
    names = {}
    for w in (300, 400, 600, 700):
        path = files.get(w) or files.get(400 if w < 600 else max(files))
        name = f"{role}-{w}"
        pdfmetrics.registerFont(TTFont(name, str(path)))
        names[w] = name
        if role == "body":
            font_manager.fontManager.addfont(str(path))
    return names


DISPLAY = register("display", F.get("display", "Inter"), "Helvetica-Bold")
BODY = register("body", F.get("body", "Inter"), "Helvetica")
if BODY[400] != "Helvetica":
    pdfmetrics.registerFontFamily(BODY[400], normal=BODY[400], bold=BODY[600], italic=BODY[400], boldItalic=BODY[600])
    plt.rcParams["font.family"] = F.get("body", "Inter")
plt.rcParams.update({"font.size": 9, "axes.edgecolor": LINE, "text.color": INK})

# Logo (raster with transparency; SVG must be converted first — see SKILL.md)
LOGO = CFG.get("logo")
LOGO_WHITE = None
if LOGO:
    im = Image.open(expand(LOGO)).convert("RGBA")
    im = im.crop(im.getbbox()) if im.getbbox() else im
    im.thumbnail((800, 800), Image.LANCZOS)
    im.save(WORK / "logo.png")
    LOGO = WORK / "logo.png"
    if CFG.get("cover_logo", "white") == "white":
        white = Image.new("RGBA", im.size, (255, 255, 255, 0))
        white.putalpha(im.getchannel("A"))
        white.save(WORK / "logo-white.png")
        LOGO_WHITE = WORK / "logo-white.png"

# ── Charts ──────────────────────────────────────────────────────────────────
def chart_monthly():
    keys = list(monthly)
    labels = [MON[m - 1] + ("" if monthly[(y, m)]["full"] else "*") for y, m in keys]
    series = (("Apariciones en Google", [monthly[k]["i"] for k in keys], ACCENT), ("Visitas desde Google", [monthly[k]["c"] for k in keys], NAVY))
    fig, axes = plt.subplots(2, 1, figsize=(6.9, 3.6), dpi=220, sharex=True, gridspec_kw={"hspace": 0.35})
    for ax, (title, vals, color) in zip(axes, series):
        bars = ax.bar(labels, vals, color=color, width=0.62)
        top = max(vals) or 1
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, v + top * 0.03, str(v), ha="center", va="bottom", fontsize=8, color=INK, fontweight="semibold")
        ax.set_ylim(0, top * 1.28)
        ax.set_yticks([])
        ax.set_title(title, fontsize=9, color=INK, loc="left", fontweight="semibold")
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(LINE)
        ax.tick_params(colors=MUTED, length=0)
    fig.tight_layout()
    fig.savefig(WORK / "monthly.png", transparent=True)
    plt.close(fig)


def chart_halves():
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 1.9), dpi=220)
    lab_last, lab_first = f"Últimos {half_months} meses", f"Primeros {half_months} meses"
    for ax, (title, a, b) in zip(axes, (("Apariciones en Google", h1_i, h2_i), ("Visitas desde Google", h1_c, h2_c))):
        bars = ax.barh([lab_last, lab_first], [b, a], color=[NAVY, "#B9C9E3"], height=0.55)
        top = max(a, b) or 1
        for bar, v in zip(bars, (b, a)):
            ax.text(v + top * 0.02, bar.get_y() + bar.get_height() / 2, str(v), va="center", fontsize=9, color=INK, fontweight="semibold")
        ax.set_xlim(0, top * 1.25)
        ax.set_title(title, fontsize=9, color=INK, loc="left", fontweight="semibold")
        for s in ("top", "right", "bottom"):
            ax.spines[s].set_visible(False)
        ax.spines["left"].set_color(LINE)
        ax.tick_params(colors=MUTED, length=0)
        ax.set_xticks([])
    fig.tight_layout()
    fig.savefig(WORK / "halves.png", transparent=True)
    plt.close(fig)


def donut(ax, parts, title, center_idx=0):
    vals = [v for _, v in parts]
    ax.pie(vals, colors=[NAVY, ACCENT, "#B9C9E3"][: len(vals)], startangle=90, counterclock=False, wedgeprops={"width": 0.38, "edgecolor": "white"})
    share = vals[center_idx] / sum(vals)
    ax.text(0, 0, f"{share:.0%}", ha="center", va="center", fontsize=15, color=[NAVY, ACCENT, MUTED][center_idx], fontweight="semibold")
    ax.set_title(title, fontsize=9, loc="left", fontweight="semibold")
    ax.legend([f"{k} ({v})" for k, v in parts], loc="center left", bbox_to_anchor=(0.95, 0.5), frameon=False, fontsize=8)


def chart_audience():
    panels = []
    dev_parts = [(k, v["c"]) for k, v in sorted(dev.items(), key=lambda kv: -kv[1]["c"]) if v["c"] > 0]
    if len(dev_parts) >= 2:
        panels.append((dev_parts[:3], "Visitas por dispositivo", 0))
    if home_country and abroad:
        c_parts = [(COUNTRY_ES.get(home_country["key"], home_country["key"]), home_country["c"])]
        c_parts.append((COUNTRY_ES.get(abroad[0]["key"], abroad[0]["key"]), abroad[0]["c"]))
        rest = sum(c["c"] for c in abroad[1:])
        if rest:
            c_parts.append(("Otros países", rest))
        panels.append((c_parts, "Visitas por país", 1))
    if not panels:
        return False
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.2), dpi=220)
    for ax, (parts, title, idx) in zip(axes, panels):
        donut(ax, parts, title, idx)
    for ax in axes[len(panels):]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(WORK / "audience.png", transparent=True)
    plt.close(fig)
    return True


chart_monthly()
has_halves = len(active) >= 56
if has_halves:
    chart_halves()
has_audience = chart_audience()

# ── Document helpers ────────────────────────────────────────────────────────
W, H = A4
M = 20 * mm
CW = W - 2 * M
ss = {
    "h1": ParagraphStyle("h1", fontName=DISPLAY[700], fontSize=22, leading=26, textColor=NAVY, spaceAfter=4),
    "kicker": ParagraphStyle("kicker", fontName=BODY[600], fontSize=8, leading=10, textColor=ACCENT, spaceAfter=4),
    "lead": ParagraphStyle("lead", fontName=BODY[300], fontSize=11.5, leading=17, textColor=INK, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName=DISPLAY[600], fontSize=13.5, leading=17, textColor=NAVY, spaceBefore=10, spaceAfter=5),
    "body": ParagraphStyle("body", fontName=BODY[400], fontSize=10, leading=15, textColor=INK, spaceAfter=6),
    "small": ParagraphStyle("small", fontName=BODY[400], fontSize=8, leading=11, textColor=MUTED),
    "cell": ParagraphStyle("cell", fontName=BODY[400], fontSize=9, leading=12, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName=BODY[600], fontSize=9, leading=12, textColor=INK),
    "th": ParagraphStyle("th", fontName=BODY[600], fontSize=8, leading=10, textColor=MUTED),
    "kpi": ParagraphStyle("kpi", fontName=DISPLAY[700], fontSize=27, leading=30, textColor=NAVY),
    "kpil": ParagraphStyle("kpil", fontName=BODY[400], fontSize=9, leading=12.5, textColor=INK),
    "bullet": ParagraphStyle("bullet", fontName=BODY[400], fontSize=10, leading=15, textColor=INK, leftIndent=14, bulletIndent=0, spaceAfter=5),
}


def P(text, style="body"):
    return Paragraph(text, ss[style])


def pct(x, digits=0):
    return f"{x * 100:.{digits}f}%"


def fpos(x):
    return "—" if x is None else f"{x:.1f}"


def kb(n):
    return f"{n / 1_000_000:.1f} MB" if n >= 1_000_000 else f"{round(n / 1000)} KB"


def img(path, width):
    im = Image.open(path)
    return RLImage(str(path), width=width, height=width * im.height / im.width)


def table(rows, widths, header=True, right_from=1):
    t = Table(rows, colWidths=widths, hAlign="LEFT")
    st = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor(LINE)),
    ]
    if header:
        st.append(("LINEBELOW", (0, 0), (-1, 0), 0.9, colors.HexColor(NAVY)))
    for i in range(1 if header else 0, len(rows)):
        if (i % 2 == 0) == header:
            st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(ICE)))
    t.setStyle(TableStyle(st))
    return t


def kpi_grid(items):
    cells = [[P(v, "kpi"), Spacer(1, 3), P(l, "kpil")] for v, l in items]
    rows = [cells[i : i + 2] for i in range(0, len(cells), 2)]
    t = Table(rows, colWidths=[CW / 2 - 4] * 2, hAlign="LEFT", spaceBefore=4, spaceAfter=8)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(ICE)),
                ("LINEAFTER", (0, 0), (0, -1), 8, colors.white),
                ("LINEBELOW", (0, 0), (-1, -2), 8, colors.white),
                ("TOPPADDING", (0, 0), (-1, -1), 13),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 13),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


def callout(text):
    t = Table([[P(text)]], colWidths=[CW], hAlign="LEFT", spaceBefore=6, spaceAfter=6)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(ICE)),
                ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor(NAVY)),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return t


def bullets(items):
    return [Paragraph(t, ss["bullet"], bulletText="•") for t in items]


def growth(a, b):
    return f"+{(b / a - 1) * 100:.0f}%" if a and b > a else None


PERIOD = f"{start.day} de {MONTHS[start.month - 1]} al {long_date(end)}" if start.year == end.year else f"{long_date(start)} al {long_date(end)}"
REPORT_DATE = long_date(dt.date.fromisoformat(CFG.get("report_date", dt.date.today().isoformat())))
AGENCY = CFG.get("agency", "Médico Creativo")
CLIENT = CFG.get("client", {})
BRAND_LABEL = CFG.get("brand_label", "su nombre")


def on_cover(c, doc):
    c.saveState()
    c.setFillColor(colors.HexColor(NAVY_DEEP))
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(colors.HexColor(NAVY))
    c.circle(W * 0.92, H * 0.18, 230, fill=1, stroke=0)
    logo = LOGO_WHITE or LOGO
    if logo:
        lw, (iw, ih) = CFG.get("cover_logo_width", 62), Image.open(logo).size
        c.drawImage(str(logo), M, H - M - lw * ih / iw, width=lw, height=lw * ih / iw, mask="auto")
    c.setFillColor(colors.HexColor(ACCENT))
    c.setFont(BODY[600], 9)
    c.drawString(M, H * 0.56, f"REPORTE DE DESEMPEÑO · {site_host.upper()}")
    c.setFillColor(colors.white)
    c.setFont(DISPLAY[700], 40)
    for i, line in enumerate(CFG.get("cover_title", ["Su sitio web", "en Google"])):
        c.drawString(M, H * 0.56 - 50 - i * 44, line)
    c.setFont(BODY[300], 12.5)
    c.setFillColor(colors.HexColor(COVER_SUB))
    c.drawString(M, H * 0.56 - 128, f"Periodo analizado: {PERIOD}")
    c.setFont(BODY[400], 10)
    c.setFillColor(colors.white)
    if CLIENT.get("prepared_for"):
        c.drawString(M, M + 34, f"Preparado para {CLIENT['prepared_for']}")
    c.setFillColor(colors.HexColor(COVER_SUB))
    c.drawString(M, M + 18, f"{AGENCY} · {REPORT_DATE}")
    c.restoreState()


def on_page(c, doc):
    c.saveState()
    c.setStrokeColor(colors.HexColor(LINE))
    c.setLineWidth(0.6)
    c.line(M, H - 14 * mm, W - M, H - 14 * mm)
    c.setFont(BODY[400], 7.5)
    c.setFillColor(colors.HexColor(MUTED))
    c.drawString(M, H - 11 * mm, f"Reporte de desempeño en Google · {site_host}")
    c.drawRightString(W - M, H - 11 * mm, PERIOD)
    c.drawString(M, 10 * mm, f"Fuente: Google Search Console (búsqueda web). Preparado por {AGENCY}.")
    c.drawRightString(W - M, 10 * mm, str(doc.page))
    c.restoreState()


OUT.parent.mkdir(parents=True, exist_ok=True)
doc = BaseDocTemplate(str(OUT), pagesize=A4, title=f"Reporte de desempeño en Google — {site_host}", author=AGENCY, subject=f"Google Search Console, {PERIOD}")
doc.addPageTemplates(
    [
        PageTemplate(id="cover", frames=[Frame(0, 0, W, H)], onPage=on_cover),
        PageTemplate(id="page", frames=[Frame(M, 18 * mm, CW, H - 38 * mm, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=on_page),
    ]
)
story = [NextPageTemplate("page"), PageBreak()]

# ── 1. Resumen ──────────────────────────────────────────────────────────────
auto_highlights = []
g_i, g_c = growth(h1_i, h2_i), growth(h1_c, h2_c)
if has_halves and g_i:
    verb = "se duplicó con creces" if h2_i > 2 * h1_i else "se duplicó" if h2_i >= 1.9 * h1_i else "creció"
    visits = f" Las visitas subieron de {h1_c} a {h2_c} ({g_c})." if g_c else ""
    auto_highlights.append(f"<b>Su visibilidad {verb}.</b> En los últimos {half_months} meses Google mostró su sitio {h2_i} veces, contra {h1_i} en los {half_months} primeros ({g_i}).{visits}")
if brand_q and brand_pos is not None and brand_pos <= 10:
    auto_highlights.append(f"<b>Quien lo busca, lo encuentra.</b> Las búsquedas por {BRAND_LABEL} lo muestran, en promedio, en la posición {fpos(brand_pos)} de la primera página.")
if mobile and clicks and mobile["c"] / clicks >= 0.5:
    share = mobile["c"] / clicks
    frac = "Tres de cada cuatro" if 0.7 <= share < 0.8 else "Cuatro de cada cinco" if 0.78 <= share < 0.85 else pct(share)
    auto_highlights.append(f"<b>{frac} visitas llegan desde el celular</b> ({mobile['c']} de {clicks}).")
if abroad and clicks and abroad[0]["c"] / clicks >= 0.05:
    name = COUNTRY_ES.get(abroad[0]["key"], abroad[0]["key"])
    auto_highlights.append(f"<b>{pct(abroad[0]['c'] / clicks)} de las visitas viene de {name}</b> ({abroad[0]['c']} visitas).")
if blog_i and impr and blog_i / impr >= 0.15:
    auto_highlights.append(f"<b>Los artículos del blog generan el {pct(blog_i / impr)} de las apariciones en Google</b> ({blog_i} de {impr}).")

kpis = [
    (f"{impr:,}", "veces apareció su sitio en los resultados de Google"),
    (f"{clicks:,}", "visitas llegaron a su sitio desde Google"),
    (pct(clicks / impr, 1) if impr else "—", "de las personas que vieron su sitio en Google hicieron clic"),
    (fpos(brand_pos), f"posición promedio al buscar {BRAND_LABEL}") if brand_q else (fpos(avg_pos), "posición promedio de su sitio en Google"),
]
story += [
    P("RESUMEN", "kicker"),
    P("Lo más importante", "h1"),
    P(CFG.get("summary_lead") or f"Del {PERIOD}, su sitio apareció {impr:,} veces en Google y recibió {clicks} visitas de personas que lo buscaron.", "lead"),
    kpi_grid(kpis),
    P("Hallazgos principales", "h2"),
    *bullets(CFG.get("highlights") or auto_highlights),
    PageBreak(),
]

# ── 2. Crecimiento ──────────────────────────────────────────────────────────
partial = [MONTHS[m - 1] for (y, m), v in monthly.items() if not v["full"]]
full_months = [(k, v) for k, v in monthly.items() if v["full"]]
story += [
    P("CRECIMIENTO", "kicker"),
    P(CFG.get("growth_title", "Mes a mes, cuántas personas lo ven"), "h1"),
    P("Las <b>apariciones</b> son las veces que su sitio se mostró en los resultados de Google; las <b>visitas</b> son las personas que hicieron clic para entrar.", "lead"),
    img(WORK / "monthly.png", CW),
]
if partial:
    names = partial[0] if len(partial) == 1 else ", ".join(partial[:-1]) + " y " + partial[-1]
    story.append(P(f"* Datos parciales: {names} no incluye{'n' if len(partial) > 1 else ''} el mes completo.", "small"))
if has_halves:
    story += [Spacer(1, 8), img(WORK / "halves.png", CW), Spacer(1, 6)]
if len(full_months) >= 2:
    best = sorted(full_months, key=lambda kv: -kv[1]["i"])[:2]
    first_full = full_months[0]
    names = " y ".join(MONTHS[m - 1] for (y, m), _ in sorted(best))
    bi, bc = sum(v["i"] for _, v in best), sum(v["c"] for _, v in best)
    ratio = (best[0][1]["i"] / first_full[1]["i"]) if first_full[1]["i"] else 0
    extra = f", {ratio:.1f} veces las apariciones de {MONTHS[first_full[0][1] - 1]}, el primer mes completo" if ratio >= 1.5 and first_full[0] not in dict(best) else ""
    story.append(callout(CFG.get("growth_callout") or f"Los meses más fuertes fueron {names}: {bi} apariciones y {bc} visitas en conjunto{extra}."))
story.append(PageBreak())

# ── 3. Búsquedas ────────────────────────────────────────────────────────────
def q_table(rows):
    data = [[P("Búsqueda en Google", "th"), P("Apariciones", "th"), P("Visitas", "th"), P("Posición", "th")]]
    data += [[P(r["key"], "cell"), P(str(r["i"]), "cell"), P(str(r["c"]), "cell"), P(fpos(r["pos"]), "cell")] for r in rows]
    return table(data, [CW * 0.46, CW * 0.18, CW * 0.18, CW * 0.18])


story += [
    P("BÚSQUEDAS", "kicker"),
    P("Cómo lo encuentran", "h1"),
    P("La <b>posición</b> indica en qué lugar aparece su sitio dentro de los resultados: del 1 al 10 es la primera página de Google, del 11 al 20 la segunda.", "lead"),
]
if brand_q:
    story += [
        P(f"Búsquedas por {BRAND_LABEL}", "h2"),
        P(CFG.get("brand_text") or ("Cuando alguien escribe su nombre en Google, su sitio aparece en los primeros lugares." if brand_pos and brand_pos <= 5 else "Estas son las búsquedas con su nombre que llevaron a su sitio.")),
        q_table(sorted(brand_q, key=lambda r: -r["i"])[:8]),
        Spacer(1, 6),
    ]
if topic_rows:
    t_label, t = top_topic
    page_word = "primera" if t["pos"] <= 10 else "segunda" if t["pos"] <= 20 else "segunda o tercera"
    story += [
        P(CFG.get("topics_title", "Búsquedas de servicios"), "h2"),
        P(CFG.get("topics_text") or f"Su sitio ya aparece cuando las personas buscan sus servicios, sobre todo {t_label} ({t['i']} apariciones), en la {page_word} página de Google (posición promedio {t['pos']:.0f})."
          + (" Ahí está la mayor oportunidad de crecimiento: estas búsquedas las hacen personas que aún no eligen a quién acudir." if t["pos"] > 10 else "")),
        q_table(topic_rows[:9]),
        Spacer(1, 4),
    ]
if visible_query_clicks < clicks:
    story.append(P(f"Google oculta por privacidad la mayoría de las búsquedas individuales: de las {clicks} visitas del periodo, solo {visible_query_clicks} muestran la búsqueda exacta que las originó.", "small"))
story.append(PageBreak())

# ── 4. Páginas y audiencia ──────────────────────────────────────────────────
top_pages = sorted(pages.items(), key=lambda kv: -kv[1]["i"])[:10]
if top_pages:
    rows = [[P("Página", "th"), P("Apariciones", "th"), P("Visitas", "th"), P("Posición", "th")]]
    rows += [[P(page_names.get(p, p), "cell"), P(str(v["i"]), "cell"), P(str(v["c"]), "cell"), P(fpos(v["pw"] / v["i"] if v["i"] else None), "cell")] for p, v in top_pages]
    lead_page, lead_v = max(pages.items(), key=lambda kv: kv[1]["c"])
    story += [
        P("PÁGINAS Y AUDIENCIA", "kicker"),
        P("Qué páginas atraen y quién llega", "h1"),
        P(CFG.get("pages_lead") or f"La página que más visitas recibe es «{page_names.get(lead_page, lead_page)}» ({lead_v['c']} de {clicks}).", "lead"),
        table(rows, [CW * 0.52, CW * 0.16, CW * 0.16, CW * 0.16]),
        Spacer(1, 12),
    ]
    if has_audience:
        story.append(img(WORK / "audience.png", CW))
    if mobile and desktop and mobile["pos"] and desktop["pos"] and clicks:
        better = "mejor" if mobile["pos"] < desktop["pos"] else "peor"
        story.append(callout(f"{pct(mobile['c'] / clicks)} de las visitas llegan desde un celular, y en el celular su sitio aparece en {better} posición (promedio {fpos(mobile['pos'])} contra {fpos(desktop['pos'])} en computadora)."))
    story.append(PageBreak())

# ── 5. Mejoras (optional) ───────────────────────────────────────────────────
imp = CFG.get("improvements")
if imp:
    story += [P(imp.get("kicker", "MEJORAS REALIZADAS"), "kicker"), P(imp.get("title", "Mejoras realizadas"), "h1")]
    if imp.get("intro"):
        story.append(P(imp["intro"], "lead"))
    if imp.get("weight_table"):
        story += [P("Velocidad", "h2")]
        if imp.get("speed_text"):
            story.append(P(imp["speed_text"]))
        rows = [[P("Qué se descarga", "th"), P("Antes", "th"), P("Ahora", "th"), P("Reducción", "th")]]
        for label, before, after in imp["weight_table"]:
            rows.append([P(label, "cell"), P(kb(before), "cell"), P(kb(after), "cellb"), P(f"−{(1 - after / before) * 100:.0f}%", "cell")])
        story += [table(rows, [CW * 0.46, CW * 0.18, CW * 0.18, CW * 0.18]), Spacer(1, 4)]
        if imp.get("weight_note"):
            story.append(P(imp["weight_note"], "small"))
    if imp.get("bullets"):
        story += [P(imp.get("bullets_title", "Visibilidad en buscadores"), "h2"), *bullets(imp["bullets"])]
    story.append(PageBreak())

# ── 6. Próximos pasos + glosario ────────────────────────────────────────────
story += [P("PRÓXIMOS PASOS", "kicker"), P("Hacia dónde seguir", "h1")]
if CFG.get("next_steps_lead"):
    story.append(P(CFG["next_steps_lead"], "lead"))
story += bullets(CFG.get("next_steps", []))
story += [
    Spacer(1, 10),
    P("Glosario", "h2"),
    table(
        [
            [P("<b>Apariciones</b>", "cell"), P("Veces que su sitio se mostró en los resultados de Google (en inglés, <i>impressions</i>).", "cell")],
            [P("<b>Visitas</b>", "cell"), P("Clics desde los resultados de Google hacia su sitio.", "cell")],
            [P("<b>% de clic</b>", "cell"), P("Visitas divididas entre apariciones: qué tan atractivo es su resultado frente a los demás.", "cell")],
            [P("<b>Posición</b>", "cell"), P("Lugar promedio de su sitio en los resultados. Del 1 al 10 es la primera página.", "cell")],
        ],
        [CW * 0.2, CW * 0.8],
        header=False,
    ),
]

doc.build(story)
print("wrote", OUT)
