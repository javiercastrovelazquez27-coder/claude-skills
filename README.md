# claude-skills

Skills para [Claude Code](https://code.claude.com), en español. Cada carpeta es una skill: un
`SKILL.md` con cuándo se activa y qué hacer, más los scripts y referencias que necesite.
Salen de trabajo real y se mantienen al día con lo que se va aprendiendo.

## Skills

| Skill | Para qué sirve |
|---|---|
| [informe-visual-pdf](./informe-visual-pdf/) | Informes en PDF con la marca del cliente: resúmenes ejecutivos, reportes para junta, one-pagers. HTML con gráficas SVG, impreso con Chrome headless y revisado página por página. Incluye un Word acompañante. |
| [reporte-search-console](./reporte-search-console/) | Reporte PDF del desempeño de un sitio en Google a partir del export de Search Console. |
| [aeo-rastreadores-ia](./aeo-rastreadores-ia/) | Auditar si ChatGPT, Gemini, Claude y Perplexity pueden rastrear y citar un sitio: robots.txt por bot, bloqueos de CDN/WAF, llms.txt. |
| [mac-disk-reclaim](./mac-disk-reclaim/) | Diagnóstico de disco y rendimiento en macOS: cachés, `node_modules`, Docker, Xcode, CPU, RAM y procesos en segundo plano. |
| [prompt-framework](./prompt-framework/) | Prompts estructurados para planear y construir proyectos: contexto, fases, restricciones, debugging y generación de `CLAUDE.md`. |
| [nextjs16-app-router](./nextjs16-app-router/) | Cambios incompatibles y patrones correctos de Next.js 16 (App Router, route handlers, server actions). |
| [expo54-rn81-newarch](./expo54-rn81-newarch/) | Compatibilidad de Expo SDK 54 + React Native 0.81 + New Architecture. |
| [nestjs-sse-streaming](./nestjs-sse-streaming/) | Streaming SSE en NestJS 11 compatible con el UI Message Stream del Vercel AI SDK. |
| [vercel-ai-sdk-v6-tools](./vercel-ai-sdk-v6-tools/) | Patrones del Vercel AI SDK v6: `tool()` con Zod, `streamText`, contexto multi-tenant y fallback de providers. |
| [zod-contract](./zod-contract/) | Schemas Zod estrictos para tools de IA, validación de lo que devuelve el LLM y contratos compartidos. |

Algunas nombran proyectos concretos en su descripción (en qué repos activarse). Cámbialos por
los tuyos al instalarla.

## Instalación

Clona el repo y enlaza las skills que quieras en `~/.claude/skills/`:

```bash
git clone https://gitlab.com/JCastro-bit/claude-skills.git ~/claude-skills

# Todas
for s in ~/claude-skills/*/; do ln -sfn "$s" ~/.claude/skills/$(basename "$s"); done

# O solo una
ln -sfn ~/claude-skills/informe-visual-pdf ~/.claude/skills/informe-visual-pdf
```

Claude Code lee la descripción de cada skill al iniciar y el resto solo cuando la tarea la
activa. Para actualizar: `git -C ~/claude-skills pull`.

## Requisitos por skill

- **informe-visual-pdf:** Google Chrome y Poppler (`pdftoppm`, `pdffonts`); Node con `docx` para el Word.
- **reporte-search-console:** Python 3 (`scripts/setup.sh` instala lo necesario).
- **aeo-rastreadores-ia:** `curl` y Python 3.
- **mac-disk-reclaim:** macOS. Los scripts piden confirmación antes de borrar.

## Créditos

`prompt-framework` está basado en el trabajo de **Erik Taveras**
([@eriktaveras](https://eriktaveras.dev)), de Taveras Solutions.
