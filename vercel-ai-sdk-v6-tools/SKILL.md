---
name: vercel-ai-sdk-v6-tools
description: |
  Patrones canónicos para Vercel AI SDK v6: tool() con Zod, streamText con providers,
  experimental_context para multi-tenant, fallback de providers. Activar al ver imports
  de `ai`, `@ai-sdk/google`, `@ai-sdk/groq`, `@ai-sdk/react`, archivos en `*/ai-assistant/*`,
  uso de `streamText`, `generateText`, `tool()`, `useChat`, `pipeUIMessageStreamToResponse`.
---

# Vercel AI SDK v6 — patrones canónicos

Stack: `ai@^6`, `@ai-sdk/google@^2`, `@ai-sdk/groq@^2`, `@ai-sdk/react@^2`, `zod@^3.23`.

## Configuración de providers

- **Primario**: `google('gemini-2.5-flash-lite')` con `thinkingConfig.thinkingBudget = 0`
  (baja latencia, no necesitamos razonamiento extendido en chat operativo).
- **Fallback**: `groq('llama-3.3-70b-versatile')` con `serviceTier: 'flex'` y
  `user: hashUserId(userId)` (anti-abuse).
- API keys vienen de `GOOGLE_GENERATIVE_AI_API_KEY` y `GROQ_API_KEY` (ya en `.env.global`).
- Modelo se lee de `AI_PRIMARY_MODEL` y `AI_FALLBACK_MODEL`.

## Tool definition correcto

```typescript
import { tool } from 'ai';
import { z } from 'zod';

export const getProductStockTool = tool({
  description: 'Get current stock for a product by SKU or name in the authenticated tenant.',
  inputSchema: z.object({
    query: z.string().min(1).max(200).describe('SKU exact or product name to search'),
  }),
  execute: async (args, { experimental_context }) => {
    // tenantId NUNCA viene de args
    const ctx = experimental_context as { tenantId: string; userId: string };
    const result = await productsService.findStockForTenant(ctx.tenantId, args.query);
    if (!result) return { found: false, query: args.query };
    return { found: true, sku: result.sku, name: result.name, total_quantity: result.qty };
  },
});
```

## Checklist por tool

- [ ] `inputSchema` Zod estricto: sin `.passthrough()`, sin `.any()`, sin `.unknown()` salvo en outputs internos.
- [ ] `description` específica (menciona tenant cuando aplique). El LLM la usa para decidir cuándo invocarla.
- [ ] Cada campo de Zod tiene `.describe()` corto y útil.
- [ ] `execute` retorna objeto estructurado en errores (no `throw` al LLM).
- [ ] `tenantId` y `userId` vienen de `experimental_context`.
- [ ] El service llamado es read-only (Fase 1: sin tools de escritura).
- [ ] Output no expone PII ni datos cross-tenant.

## Tool loop

Acotá con `stopWhen: stepCountIs(5)` en el caller para evitar bucles. El LLM puede
invocar varias tools en paralelo (`parallel_tool_calls: true` por default en v6).

## Streaming en NestJS

Usar `result.pipeUIMessageStreamToResponse(res)` desde un controller con `@Res() res: Response`.
NO usar `@Sse()` decorator de NestJS — el formato no es compatible con UI Message Stream del SDK.

## Fallback pattern

```typescript
async streamChat(messages, user) {
  const userHash = hashUser(user);
  const baseConfig = {
    system: SYSTEM_PROMPT,
    messages: convertToModelMessages(messages),
    tools: this.toolsRegistry.buildFor(user),
    stopWhen: stepCountIs(5),
    maxOutputTokens: 600,
    experimental_context: { tenantId: user.tenantId, userId: user.id },
  };
  try {
    return await streamText({
      model: google(process.env.AI_PRIMARY_MODEL!),
      ...baseConfig,
      providerOptions: { google: { thinkingConfig: { thinkingBudget: 0 } } },
    });
  } catch (err) {
    if (!isProviderError(err)) throw err;
    return streamText({
      model: groq(process.env.AI_FALLBACK_MODEL!),
      ...baseConfig,
      providerOptions: { groq: { user: userHash, serviceTier: 'flex' } },
    });
  }
}
```

## Cuando dudes

Consulta la documentación actual del AI SDK v6. Si tu agente tiene una herramienta de
documentación (por ejemplo Context7 por MCP), búscala con `vercel/ai v6 <tema>`.
