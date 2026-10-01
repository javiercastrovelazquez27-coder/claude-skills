# Templates de referencia

## Template: archivo de instrucciones del proyecto (CLAUDE.md, AGENTS.md, GEMINI.md)

```markdown
# Proyecto: [NOMBRE]

## Qué es
[Una oración: qué hace y para quién]

## Stack
[Lista de tecnologías que usas]

## Estructura del proyecto
[Carpetas principales y qué tiene cada una]

## Reglas que SIEMPRE debe seguir
- [Cosas que NO quieres que haga]
- [Convenciones de nombrado]
- [Restricciones técnicas]

## Contexto del negocio
- Cliente: [tipo de negocio]
- Usuario final: [quién usa la app]
- Problema que resuelve: [dolor principal]

## Estado actual
- [x] Lo que ya está hecho
- [ ] Lo que falta por hacer

## Variables de entorno
- [Lista de las que necesita]
```

---

## Template: Restricciones técnicas

Usar cuando el usuario no especifica restricciones. Guiarlo a completar:

```markdown
## Restricciones del proyecto

Tecnologías preferidas: [las que use o quiera aprender]
Servicios a integrar: [pagos, email, auth, APIs externas]
Hosting/deploy: [dónde va a vivir esto]
Dispositivo principal: [mobile, desktop, ambos]

Lo que NO quiero:
- [tecnologías que no le gustan o no conoce]
- [complejidad innecesaria]
- [dependencias pesadas]

Nivel de complejidad: [MVP rápido / producción pulida / enterprise]
```

---

## Template: Resumen de sesión

Usar al final de cada sesión para preservar el contexto:

```markdown
# Resumen de sesión — [PROYECTO] — [FECHA]

## Archivos creados/modificados
- `archivo1.ts` — [qué hace]
- `archivo2.ts` — [qué hace]

## Funcionalidades completas
- [x] [Funcionalidad 1]
- [x] [Funcionalidad 2]

## Pendiente
- [ ] [Lo que falta]
- [ ] [Lo que falta]

## Decisiones técnicas
- [Decisión]: [Por qué se tomó]

## Bugs conocidos
- [Bug o cosa por revisar]

## Último cambio
[Descripción del último cambio realizado]

## Para retomar
Pega este resumen al inicio de la nueva sesión y escribe:
"Retomemos donde dejamos."
```
