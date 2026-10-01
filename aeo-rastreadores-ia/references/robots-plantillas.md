# Plantillas de robots.txt (sin aplicar hasta que el cliente decida)

Recordatorio: un bot con grupo propio **ignora** `User-agent: *`; cada grupo lleva su regla completa.
Varias líneas `User-agent` seguidas comparten las reglas que siguen.

## Opción A — todo permitido (búsqueda, usuario y entrenamiento)

```txt
# Búsqueda y consultas de usuarios (aparecer en respuestas)
User-agent: Googlebot
User-agent: Bingbot
User-agent: OAI-SearchBot
User-agent: ChatGPT-User
User-agent: Claude-SearchBot
User-agent: Claude-User
User-agent: PerplexityBot
User-agent: Perplexity-User
Allow: /

# Entrenamiento de modelos
User-agent: GPTBot
User-agent: ClaudeBot
User-agent: Google-Extended
Allow: /

User-agent: *
Allow: /

Sitemap: https://DOMINIO/sitemap.xml
```

`User-agent: * / Allow: /` solo ya equivale a la opción A; la versión explícita documenta la
decisión y permite cambiarla por bot sin tocar a los demás.

## Opción B — búsqueda sí, entrenamiento no

Igual que A, pero el grupo de entrenamiento con `Disallow: /`:

```txt
User-agent: GPTBot
User-agent: ClaudeBot
User-agent: Google-Extended
Disallow: /
```

Efectos: el sitio sigue en Google Search (Google-Extended no afecta Search) y en ChatGPT Search
(usa OAI-SearchBot). ChatGPT-User y Perplexity-User pueden seguir leyendo páginas que pide un
usuario, porque no siguen robots.txt.

## Bloquear solo una sección (ejemplo)

```txt
User-agent: GPTBot
Disallow: /privado/
Allow: /
```
