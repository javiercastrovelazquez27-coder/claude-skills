#!/usr/bin/env bash
# Prueba las URLs de un sitio con los user-agents oficiales de los bots de IA y buscadores.
#   bash auditar-bots.sh https://dominio.com [/ruta ...] [--lento]
# --lento: 1 petición cada 6 s (distingue un límite por ráfaga de una regla por user-agent).
# Ojo: sale desde TU IP, no desde la del bot real; un CDN puede tratar distinto al bot verificado.
set -u
BASE="${1:?uso: auditar-bots.sh https://dominio.com [/ruta ...] [--lento]}"; shift
PAUSA=1; RUTAS=()
for a in "$@"; do if [ "$a" = "--lento" ]; then PAUSA=6; else RUTAS+=("$a"); fi; done
[ ${#RUTAS[@]} -eq 0 ] && RUTAS=(/ /robots.txt /sitemap.xml /llms.txt)
BOTS=(
"Googlebot|Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
"Bingbot|Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
"OAI-SearchBot|Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36; compatible; OAI-SearchBot/1.4; +https://openai.com/searchbot"
"ChatGPT-User|Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot"
"GPTBot|Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.4; +https://openai.com/gptbot"
"Claude-SearchBot|Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude-SearchBot/1.0; +Claude-SearchBot@anthropic.com)"
"Claude-User|Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude-User/1.0; +Claude-User@anthropic.com)"
"ClaudeBot|Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)"
"PerplexityBot|Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)"
"Perplexity-User|Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Perplexity-User/1.0; +https://perplexity.ai/perplexity-user)"
)
printf "%-17s" "bot"; for r in "${RUTAS[@]}"; do printf " %-8s" "${r:0:8}"; done; echo
TMP=$(mktemp)
for e in "${BOTS[@]}"; do
  n="${e%%|*}"; ua="${e#*|}"; printf "%-17s" "$n"
  for r in "${RUTAS[@]}"; do
    c=$(curl -s -o "$TMP" -A "$ua" -w "%{http_code}" "$BASE$r")
    h1=""; case "$r" in *.xml|*.txt) ;; *) grep -q "<h1" "$TMP" && h1="+h1" ;; esac
    printf " %-8s" "$c$h1"; sleep "$PAUSA"
  done; echo
done
rm -f "$TMP"
echo "(+h1 = el HTML trae contenido sin ejecutar JavaScript)"
echo "Cabeceras de CDN/robots de la home:"; curl -sI "$BASE/" | grep -iE "^(server|x-robots-tag|cf-ray|x-hcdn|x-cache|platform)" || true
