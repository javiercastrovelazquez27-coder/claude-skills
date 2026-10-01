---
name: nextjs16-app-router
description: |
  Breaking changes y patrones correctos para Next.js 16. Activar al trabajar en
  frontend-acuarium o espresso-landing, en archivos app/, route handlers, server
  actions, useChat de @ai-sdk/react, o cualquier uso de params/searchParams/cookies/headers.
allowed-tools: Read, Grep, Glob, mcp__context7__*
---

# Next.js 16 — breaking changes clave

## params / searchParams son Promises

```typescript
// ❌ Next.js 15 (roto en 16)
export default function Page({ params }: { params: { id: string } }) { return <div>{params.id}</div>; }

// ✅ Next.js 16
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <div>{id}</div>;
}
```

`cookies()`, `headers()`, `draftMode()` también son async.

## Caching opt-in

`fetch()` ya no cachea implícitamente. Usar `"use cache"` o `revalidate` explícito.

## useChat con AI SDK v6 (cliente)

```typescript
'use client';
import { useChat } from '@ai-sdk/react';

export function AssistantChat() {
  const { messages, sendMessage, status } = useChat({
    api: `${process.env.NEXT_PUBLIC_API_URL}/ai-assistant/chat`,
    headers: () => ({ Authorization: `Bearer ${getToken()}` }),
  });
  // ...
}
```

## Turbopack default

Si hay problemas: `next dev --no-turbopack`. React 19.2 requerido.

## Cuando dudes

`mcp__context7__*` con query `vercel/next.js 16 <topic>`.
