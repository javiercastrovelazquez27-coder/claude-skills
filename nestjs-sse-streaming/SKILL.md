---
name: nestjs-sse-streaming
description: |
  Patrones de streaming SSE en NestJS 11 compatibles con Vercel AI SDK UI Message Stream.
  Activar al crear controllers con stream, endpoints /chat, handlers que usen Response,
  pipeUIMessageStreamToResponse, o cualquier endpoint que devuelva text/event-stream.
---

# NestJS 11 + SSE streaming con AI SDK v6

## Patrón canónico

```typescript
import { Controller, Post, Body, Req, Res, UseGuards } from '@nestjs/common';
import type { Response } from 'express';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { PermissionsGuard } from '../common/guards/permissions.guard';
import { Permissions } from '../common/decorators/permissions.decorator';

@Controller('ai-assistant')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class AiAssistantController {
  constructor(private readonly assistantService: AiAssistantService) {}

  @Post('chat')
  @Permissions('ASSISTANT.USE')
  async chat(
    @Req() req: AuthenticatedRequest,
    @Res() res: Response,
    @Body() body: ChatRequestDto,
  ) {
    const result = await this.assistantService.streamChat(body.messages, req.user);
    return result.pipeUIMessageStreamToResponse(res);
  }
}
```

## Anti-patrones

- ❌ NO usar `@Sse()` decorator — incompatible con UI Message Stream format.
- ❌ NO poner `tenantId` en el DTO body — siempre del JWT.
- ❌ NO usar `res.json()` ni `return result` en endpoint de streaming.
- ❌ NO setear headers manualmente — `pipeUIMessageStreamToResponse` los maneja.

## DTO

```typescript
import { IsArray, ArrayMinSize, ArrayMaxSize, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';

export class ChatRequestDto {
  @IsArray()
  @ArrayMinSize(1)
  @ArrayMaxSize(50)
  @ValidateNested({ each: true })
  @Type(() => UIMessageDto)
  messages!: UIMessageDto[];
}
```

Validación a nivel HTTP con class-validator. Validación a nivel tool con Zod (skill aparte).

## Debug rápido

```bash
curl -N -H "Accept: text/event-stream" \
     -H "Authorization: Bearer $JWT" \
     -H "Content-Type: application/json" \
     -d '{"messages":[{"role":"user","parts":[{"type":"text","text":"qué vence esta semana"}]}]}' \
     http://localhost:3000/ai-assistant/chat
```

Si la respuesta no chunkea: verificar nginx/Cloudflare con `proxy_buffering off` y
`X-Accel-Buffering: no` (configurarlo también si está detrás de un proxy como Traefik o Nginx).

## Rate limiting

Usar `@nestjs/throttler` (verificar si ya está instalado en este repo). Límite:
30 req/min por `user.id`. Endpoint `/ai-assistant/chat` específicamente.
