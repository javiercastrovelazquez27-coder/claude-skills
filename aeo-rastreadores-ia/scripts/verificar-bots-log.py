#!/usr/bin/env python3
"""Verifica en un log de acceso qué visitas de bots de IA/buscadores son REALES (IP dentro de los
rangos oficiales) y qué código recibieron.

  python3 verificar-bots-log.py access.csv [--excluir-ip 1.2.3.4]

Formato esperado: CSV con columnas status, ipAddress, request, userAgent (export de logs de acceso
de hPanel/Hostinger: status,ipAddress,host,request,userAgent,countryCode,sizeBytes,durationSecs,timestamp).
Otros formatos: adaptar COLS abajo.
--excluir-ip: tu propia IP (tus pruebas con curl se hacen pasar por bots).
"""
import csv, collections, ipaddress, json, sys, urllib.request

COLS = {"status": "status", "ip": "ipAddress", "req": "request", "ua": "userAgent"}
RANGOS = {
    "OpenAI OAI-SearchBot": "https://openai.com/searchbot.json",
    "OpenAI GPTBot": "https://openai.com/gptbot.json",
    "OpenAI ChatGPT-User": "https://openai.com/chatgpt-user.json",
    "Anthropic": "https://claude.com/crawling/bots.json",
    "PerplexityBot": "https://www.perplexity.com/perplexitybot.json",
    "Perplexity-User": "https://www.perplexity.com/perplexity-user.json",
    "Googlebot": "https://developers.google.com/static/search/apis/ipranges/googlebot.json",
    "Bingbot": "https://www.bing.com/toolbox/bingbot.json",
}
BOTS = ["OAI-SearchBot", "GPTBot", "ChatGPT-User", "Claude-SearchBot", "Claude-User", "ClaudeBot",
        "PerplexityBot", "Perplexity-User", "Googlebot", "Google-InspectionTool", "GoogleOther", "bingbot"]


def cargar():
    redes = {}
    for nombre, url in RANGOS.items():
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=20))
            redes[nombre] = [ipaddress.ip_network(p.get("ipv4Prefix") or p.get("ipv6Prefix")) for p in d.get("prefixes", []) if p.get("ipv4Prefix") or p.get("ipv6Prefix")]
        except Exception as e:  # una fuente caída no debe tumbar el resto
            print(f"aviso: no pude leer {nombre} ({url}): {e}", file=sys.stderr)
    return redes


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    archivo = sys.argv[1]
    excluir = set(sys.argv[sys.argv.index("--excluir-ip") + 1:sys.argv.index("--excluir-ip") + 2]) if "--excluir-ip" in sys.argv else set()
    redes = cargar()
    origen = lambda ip: [n for n, rs in redes.items() if any(ipaddress.ip_address(ip) in r for r in rs)]
    filas = list(csv.DictReader(open(archivo, encoding="utf-8")))
    print(f"{len(filas)} peticiones. Códigos: {dict(collections.Counter(f[COLS['status']] for f in filas))}\n")
    print(f"{'bot':22} {'visitas':>7} {'real':>5} {'falso':>5}  códigos (reales)")
    for b in BOTS:
        fs = [f for f in filas if b.lower() in f[COLS["ua"]].lower() and f[COLS["ip"]] not in excluir]
        if not fs:
            continue
        reales = [f for f in fs if origen(f[COLS["ip"]])]
        falsos = [f for f in fs if not origen(f[COLS["ip"]])]
        print(f"{b:22} {len(fs):>7} {len(reales):>5} {len(falsos):>5}  {dict(collections.Counter(f[COLS['status']] for f in reales))}")
        for f in reales:
            if f[COLS["status"]] not in ("200", "304", "301"):
                print(f"   ! {f[COLS['status']]} {f[COLS['ip']]} {f[COLS['req']][:70]}")
    print("\n'falso' = user-agent de bot desde una IP fuera de sus rangos (impostor o prueba propia).")


main()
