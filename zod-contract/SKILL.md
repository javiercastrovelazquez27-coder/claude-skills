---
name: zod-contract
description: |
  Patrones estrictos de Zod para schemas de AI tools, validación de input del LLM,
  y contratos compartidos. Activar al definir schemas Zod, especialmente en tools de
  un asistente de IA o cuando el contrato cruce repos.
---

# Zod — contratos estrictos

## Reglas

- **Estricto por default**. `.strict()` en schemas que vienen de afuera.
- **NUNCA `.passthrough()`** en tools del AI SDK.
- **NUNCA `z.any()`** — usá `z.unknown()` + narrowing si hace falta.
- Límites explícitos: `z.string().max(500)`, `z.number().int().min(0).max(100)`.
- Defaults explícitos: `z.number().int().min(1).max(365).default(30)`.

## Para AI tools específicamente

- `.describe()` en cada campo: el LLM lo usa.
- Enums cuando haya opciones finitas: `z.enum(['low', 'normal', 'high'])`.
- No agregar campos opcionales "por si acaso". Solo los que el LLM realmente usa.
- Strings sin límite son vector de abuso (token bombing). Siempre `.max()`.

## Patrón completo

```typescript
const ListExpiringBatchesInput = z.object({
  window_days: z.number().int().min(1).max(365).default(30)
    .describe('Days ahead to look for expiring batches'),
  limit: z.number().int().min(1).max(20).default(10)
    .describe('Max batches to return'),
}).strict();

type ListExpiringBatchesArgs = z.infer<typeof ListExpiringBatchesInput>;
```
