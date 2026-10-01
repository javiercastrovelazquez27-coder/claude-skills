---
name: aeo-rastreadores-ia
description: Auditar y configurar un sitio para que ChatGPT, Gemini, Claude y Perplexity puedan rastrearlo, citarlo y usarlo en respuestas (AEO técnico). Bots de búsqueda vs de usuario vs de entrenamiento, robots.txt por bot, bloqueos de CDN/WAF (429/403), rangos de IP oficiales, Google-Extended, llms.txt, y script de auditoría con los user-agents oficiales. Usar al auditar "si ChatGPT/Gemini/Claude/Perplexity pueden ver mi sitio", al tocar robots.txt por bots de IA, al ver 429/403 a bots, o al decidir si permitir el entrenamiento.
---

# AEO técnico: rastreadores de IA

Cómo dejar un sitio legible para los asistentes de IA **sin confundir** tres cosas distintas:

| Tipo | Para qué | Bots | ¿Respeta robots.txt? |
|---|---|---|---|
| **Búsqueda** | Que el sitio salga y se cite en las respuestas con búsqueda | OAI-SearchBot, Googlebot, Bingbot, Claude-SearchBot, PerplexityBot | Sí |
| **Usuario** | Leer una página cuando un usuario lo pide en el chat | ChatGPT-User, Claude-User, Perplexity-User | ChatGPT-User y Perplexity-User **no**; Claude-User **sí** |
| **Entrenamiento** | Contenido para entrenar/fundamentar modelos | GPTBot, ClaudeBot, Google-Extended (solo token) | Sí |

Detalle de cada bot (user-agent, rangos de IP, fuente): [references/bots.md](references/bots.md).

## Reglas que no se rompen

1. **Bloquear entrenamiento no quita de la búsqueda.** GPTBot ≠ ChatGPT Search (OAI-SearchBot).
   Google-Extended "no afecta la inclusión ni el ranking en Google Search" (Google).
2. **Google-Extended no es un user-agent**: no hace peticiones; solo es un token de robots.txt.
   Nunca buscarlo en logs ni "probarlo" con curl.
3. **Un grupo propio anula a `User-agent: *`.** Si un bot tiene su bloque, solo lee ese bloque:
   cada grupo debe llevar su `Allow`/`Disallow` completo.
4. **Rastrear ≠ indexar ≠ aparecer en respuestas.** Nunca afirmar que una plataforma indexó el
   sitio sin evidencia (Search Console, logs con IP verificada). Nunca garantizar apariciones.
5. **No hay DNS para bots de IA.** Ninguna documentación oficial pide registros DNS; no proponerlos.
6. **llms.txt es sugerencia técnica, no requisito**: ninguna de las 4 plataformas lo exige.
7. **Probar desde tu IP ≠ el bot real.** Los CDN pueden validar bots por IP (rangos oficiales).
   Un 200 con el user-agent es buena señal, no prueba; un 429/403 sí es un problema a investigar.

## Decidir: ¿permitir entrenamiento?

- **Opción A (todo permitido)**: negocio que vende algo distinto a su contenido (lote de autos,
  consultorio, comercio local). Que la IA "sepa" del negocio es ganancia; el contenido ya es público.
- **Opción B (búsqueda sí, entrenamiento no)**: el contenido ES el producto (medios, cursos,
  investigación de pago) o hay política/legal que lo exige.
- Es decisión de negocio: presentarla, recomendar, no imponer. Plantillas:
  [references/robots-plantillas.md](references/robots-plantillas.md).

## Procedimiento de auditoría (solo lectura hasta que autoricen cambios)

1. **Docs**: releer las 4 fuentes oficiales (cambian; ver bots.md). Si una da 403 (help.openai.com
   bloquea bots), marcarla "No verificable", no inventar su contenido.
2. **robots.txt en producción**: `curl -sD - https://DOMINIO/robots.txt` → 200, `text/plain`,
   sin `Disallow` accidentales, `Sitemap:` declarado. Revisar también el `public/robots.txt` del repo.
3. **Bots contra URLs clave (simulación)** (home, listado, detalle, artículo, sitemap, llms.txt):
   `bash ~/.claude/skills/aeo-rastreadores-ia/scripts/auditar-bots.sh https://DOMINIO /ruta1 /ruta2`
   Si un bot da 429/403 y los demás 200: repetir con `--lento` (1 petición cada 6 s) para distinguir
   límite de ráfaga de regla por user-agent.
4. **Página por página**: código HTTP, `<meta name="robots">`, `X-Robots-Tag`, `canonical` propio,
   contenido en el HTML sin JS (h1 y texto presentes), redirecciones 301 limpias, 404 real.
5. **Datos estructurados** acordes al negocio (LocalBusiness/AutoDealer, Product/Car+Offer,
   BlogPosting/Article, FAQPage, BreadcrumbList); OG, title y description únicos.
6. **Sitemap**: 200, XML válido, URLs canónicas con `lastmod` real (no la fecha del build).
7. **CDN/WAF**: identificar el proveedor por cabeceras (`server: hcdn` = Hostinger CDN,
   `cf-ray` = Cloudflare…). Reglas de bots no siempre salen por API: pedir revisión en el panel.
8. **Reporte**: tabla `Plataforma | Componente | Estado (Correcto/Incorrecto/Parcial/No verificable)
   | Evidencia | Problema | Acción`, diagnóstico, prioridades, archivos, qué se verifica en local
   y qué solo en producción (logs con IP de los rangos oficiales, Search Console).

## Evidencia definitiva: logs de acceso

Probar con curl solo imita al bot. La prueba real es el log del servidor con la IP verificada:

1. Exportar el log de acceso (hPanel de Hostinger: CSV con
   `status,ipAddress,host,request,userAgent,countryCode,sizeBytes,durationSecs,timestamp`; otros
   hosts: adaptar `COLS` en el script).
2. `python3 ~/.claude/skills/aeo-rastreadores-ia/scripts/verificar-bots-log.py log.csv --excluir-ip <tu IP>`
   Descarga los rangos oficiales (OpenAI ×3, Anthropic, Perplexity ×2, Googlebot, Bingbot) y separa
   visitas **reales** de impostores/pruebas propias, con los códigos que recibió cada bot real.
3. Averiguar la IP propia (`curl -s ifconfig.me`) para excluirla: tus pruebas aparecen con UA de bot.
4. El log contiene IPs de visitantes: no subirlo al repo; documentar solo conclusiones.
5. **No usar `durationSecs` (ni duraciones de logs de origen tras CDN) como prueba de lentitud**:
   en Hostinger no coincide con lo medido en el cliente. Para velocidad: PageSpeed Insights (campo).
6. En el log también se ve `Google-InspectionTool` (inspección de URL de Search Console) y
   `Chrome-Lighthouse` (PageSpeed): no son rastreo real.

## CDN y caché (lección de Hostinger)

- `x-hcdn-cache-status: DYNAMIC` en HTML = el CDN no lo guarda; un deploy se ve sin purgar.
- Estáticos: `MISS` la primera vez **por nodo** (`phx-edgeN`), luego `HIT`. Purgar la caché en cada
  deploy vacía todos los nodos: hacerlo solo si un archivo cambió sin cambiar de nombre.
- Assets con hash (Vite `-XXXXXXXX.js|css`): `Cache-Control: public, max-age=31536000, immutable`
  vía `<FilesMatch>` en `.htaccess`. Nunca `immutable` en archivos sin hash (fuentes, fotos).

## Casos ya vistos

- **Hostinger CDN (`server: hcdn`) responde 429 a GPTBot** aun con robots.txt permitiéndolo y a
  1 petición/6 s, mientras OAI-SearchBot, Claude, Perplexity, Googlebot y Bingbot reciben 200.
  No afecta a ChatGPT Search. Soporte confirma que es un límite **global** de su infraestructura,
  previo al origen, no configurable por sitio ni plan y sin allowlist de bots: aceptar y
  documentar. Si el entrenamiento fuera crítico, la única salida es otro hosting o CDN. No apagar
  el CDN entero por esto. Antes de concluir, confirmar en logs que el GPTBot real (IP en
  gptbot.json) también recibe 429, y probar una ruta interna: si la home sale de caché
  (`x-hcdn-cache-status: HIT`), GPTBot recibe 200 ahí. Para reportar, soporte pide hora UTC, URL,
  user-agent y `x-hcdn-request-id`. En Vercel, GPTBot recibe 200.
- **SPA de Vite sin prerender = body vacío para OAI-SearchBot/Claude/Perplexity** (no ejecutan JS).
  Solución: prerender del body en el build (`src/entry-server.tsx` + `scripts/postbuild.mjs`).

Casos con nombre de sitio: `references/privado-casos.md` (si existe; no se publica).

## Complementos

- Contenido y schema para respuestas: skill `seo-aeo-best-practices`.
- En Google: enviar sitemap en Search Console; en Bing: Bing Webmaster Tools (sugerencia técnica).
