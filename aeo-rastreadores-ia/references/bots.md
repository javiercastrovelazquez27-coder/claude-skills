# Bots de IA: referencia (verificado el 2026-09-29; revisar las fuentes antes de cada auditoría)

## OpenAI — https://developers.openai.com/api/docs/bots

| Bot | Uso | robots.txt | User-agent (oficial) | IPs |
|---|---|---|---|---|
| OAI-SearchBot | "used to surface websites in search results in ChatGPT's search features". Si se bloquea: "will not be shown in ChatGPT search answers" | Sí | `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36; compatible; OAI-SearchBot/1.4; +https://openai.com/searchbot` | https://openai.com/searchbot.json |
| GPTBot | Entrenamiento: "make our generative AI foundation models more useful and safe" | Sí | `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.4; +https://openai.com/gptbot` | https://openai.com/gptbot.json |
| ChatGPT-User | Acciones que pide el usuario en ChatGPT y GPTs | **No** ("robots.txt rules may not apply") | `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot` | https://openai.com/chatgpt-user.json |

Cambios en robots.txt: "~24 hours" en aplicarse.
Otras fuentes (dan 403 a scripts; leer en navegador):
- https://help.openai.com/es-419/articles/12627856-publishers-and-developers-preguntas-frecuentes
- https://help.openai.com/es-419/articles/9237897-searching-the-web-with-chatgpt

## Google (Gemini) — https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers

| Bot / token | Uso | Notas |
|---|---|---|
| Googlebot | Rastreo para Google Search | Token `Googlebot` (variantes Googlebot-Image, -Video, -News) |
| Google-Extended | **Solo token de robots.txt**, sin user-agent propio | Controla si el contenido se usa para entrenar Gemini y para *grounding* en Gemini Apps / Vertex AI. "does not impact a site's inclusion in Google Search nor is it used as a ranking signal" |

Más: https://developers.google.com/crawling/docs/about-crawling ·
https://developers.google.com/search/docs/crawling-indexing/overview

## Anthropic (Claude) — https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler

| Bot | Uso | robots.txt |
|---|---|---|
| ClaudeBot | Entrenamiento: "enhance the utility and safety of our generative AI models" | Sí |
| Claude-User | Cuando un usuario le pide a Claude visitar un sitio | Sí |
| Claude-SearchBot | "improve search result quality for users" | Sí |

Soporta `Crawl-delay` (no estándar). IPs: https://claude.com/crawling/bots.json
UA usados en la auditoría (patrón): `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)` (mismo patrón con Claude-User y Claude-SearchBot).
Herramienta de búsqueda de la API: https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool

## Perplexity — https://docs.perplexity.ai/guides/bots

| Bot | Uso | robots.txt | User-agent | IPs |
|---|---|---|---|---|
| PerplexityBot | "surface and link websites in search results"; **no** entrena modelos | Sí | `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)` | https://www.perplexity.com/perplexitybot.json |
| Perplexity-User | Visitas que pide el usuario; no entrena | **No** ("generally ignores robots.txt") | `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Perplexity-User/1.0; +https://perplexity.ai/perplexity-user)` | https://www.perplexity.com/perplexity-user.json |

## Verificar un bot real en logs

Tomar la IP de la visita con ese user-agent y comprobar que está en el JSON de rangos de su
empresa. Un user-agent sin IP de sus rangos es un impostor (y un CDN puede tratarlo distinto).

## Microsoft (Bing) — https://www.bing.com/webmasters/help/which-crawlers-does-bing-use-8c184ec0

| Bot | Uso | IPs |
|---|---|---|
| bingbot | Rastreo para Bing (y los servicios que usan su índice) | https://www.bing.com/toolbox/bingbot.json |
