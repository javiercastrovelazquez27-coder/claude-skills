---
name: expo54-rn81-newarch
description: |
  Compatibilidad y caveats de Expo SDK 54 + React Native 0.81 + New Architecture.
  Activar en proyectos con Expo 54 o React Native 0.81: al instalar dependencias, tocar
  código nativo, Reanimated, NativeWind, navegación o streaming SSE en RN.
---

# Expo 54 + RN 0.81 + New Architecture — reglas

## Stack de referencia (no cambiarlo sin hablarlo con el usuario)

- Expo SDK 54 (última que permite Legacy Arch; esta skill asume New Arch).
- React Native 0.81.
- **Reanimated v3** (NO v4 — NativeWind aún no lo soporta).
- NativeWind 4.2.
- Hermes engine (JSC removido).
- Android edge-to-edge obligatorio (Android 16).

## Reglas

- Después de cualquier `expo install`, correr `npx expo-doctor` y reportar.
- Si una lib requiere Reanimated v4, detente y pregunta.
- Token storage: SIEMPRE `expo-secure-store`, NUNCA AsyncStorage.
- `shadcn/ui` no corre en RN — alternativas: `react-native-reusables` o `gluestack-ui v3`.

## Streaming SSE en RN para un chat con IA

`@ai-sdk/react` `useChat` debería funcionar con el polyfill nativo de fetch en RN 0.81.
Si falla streaming (no chunkea, llega toda la respuesta de golpe), **detente y pregunta**
antes de agregar `react-native-sse` u otra dep. POC obligatorio de 30 min.

## Checklist antes de cambios nativos

- [ ] ¿La lib soporta New Architecture?
- [ ] ¿Hay config plugin? ¿Se agregó a `app.json`?
- [ ] ¿Corre `npx expo-doctor` sin errores?
- [ ] ¿Si toca `ios/` o `android/` manualmente, hay justificación?

## Limitaciones de red

Expo Go contra API dev solo funciona desde casa o datos móviles, NO desde la red de
oficina (workspace convention).
