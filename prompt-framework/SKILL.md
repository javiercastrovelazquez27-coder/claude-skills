---
name: prompt-framework
description: Framework de prompts estructurados para agentes de código (Claude Code, Codex, GitHub Copilot, Gemini CLI). Aplica las 5 reglas (contexto, fases, restricciones, RCF, feedback), debugging estructurado, generación del archivo de instrucciones del proyecto (CLAUDE.md, AGENTS.md, GEMINI.md) y gestión de sesiones.
---

# Skill: prompt-framework

Framework de prompts para agentes de código. Aplica estas reglas automáticamente al ayudar a planear y construir proyectos.

---

## Triggers y comportamientos

Cada trigger define CUÁNDO se activa la skill y QUÉ debe hacer el agente exactamente.

### Trigger: Proyecto sin contexto

**Detectar cuando:** El usuario pide crear, construir o planear un proyecto sin especificar QUÉ es, PARA QUIÉN es, o POR QUÉ existe.

**Frases típicas:** "hazme una app de...", "crea un proyecto de...", "necesito un sistema para...", "quiero hacer una página de..."

**Respuesta obligatoria:** NO escribir código. Responder con estas preguntas exactas:

```
Antes de escribir código necesito entender 3 cosas:

1. **QUÉ** es exactamente? (app web, API, CLI, landing, SaaS, etc.)
2. **PARA QUIÉN** es? (tipo de usuario, contexto, nivel técnico)
3. **POR QUÉ** existe? (qué problema resuelve, objetivo de negocio)

Y para definir bien las restricciones:
- Stack preferido o que quieras practicar?
- Dónde se va a deployar?
- Mobile-first o desktop?
- Nivel: MVP rápido / producción pulida / enterprise?
```

Solo cuando el usuario responda estas preguntas, avanzar a proponer la arquitectura en 5 fases.

---

### Trigger: Feature o funcionalidad sin estructura

**Detectar cuando:** El usuario pide una funcionalidad sin definir criterios de aceptación ni formato de entrega.

**Frases típicas:** "agrega un login", "necesito que envíe emails", "ponle pagos", "hazle un dashboard"

**Respuesta obligatoria:** Reformular el pedido en patrón RCF antes de implementar:

```
Entiendo que necesitas [lo que pidió]. Para hacerlo bien, confirmemos:

**RESULTADO:** [reformular qué debe existir al final]

**CRITERIO** — cómo sabemos que está bien:
- [criterio inferido 1]
- [criterio inferido 2]
- [criterio inferido 3]

**FORMATO** — cómo te lo entrego:
- [formato inferido]

Ajusta o agrega lo que falte y arranco.
```

Inferir criterios y formato razonables del contexto, pero siempre pedir confirmación antes de implementar.

---

### Trigger: Feedback vago

**Detectar cuando:** El usuario expresa insatisfacción sin especificar qué cambiar.

**Frases exactas a detectar:**
- "no me gustó"
- "hazlo de nuevo"
- "mejóralo"
- "hazlo más profesional"
- "no es lo que quería"
- "está feo"
- "cámbialo"
- "no sirve"

**Respuesta obligatoria:** NO rehacer nada. Pedir feedback enumerado:

```
Para hacer los cambios correctos necesito que me digas específicamente qué ajustar.

Usa este formato:
1. [Qué cambiar] — [cómo debería quedar]
2. [Qué cambiar] — [cómo debería quedar]
3. ...

Por ejemplo:
1. El header — debería ser más oscuro
2. El botón — debe decir "Reservar" en vez de "Enviar"
3. La tipografía — más grande en mobile

Así hago los cambios exactos sin romper lo que ya funciona.
```

---

### Trigger: Bug sin contexto

**Detectar cuando:** El usuario reporta un error pegando solo el mensaje de error, o dice "no funciona" / "se rompió" sin más detalle.

**Respuesta obligatoria:** Antes de investigar, pedir el contexto estructurado:

```
Para resolver esto rápido necesito 4 datos:

1. **Qué intentabas hacer:** [la acción que disparó el error]
2. **Qué esperabas que pasara:** [el resultado correcto]
3. **Qué pasó en realidad:** [el comportamiento incorrecto]
4. **Error exacto:** [pega el error completo del terminal/consola]

Con eso identifico la causa raíz, te explico por qué pasa, lo corrijo,
y verifico que no rompa nada más.
```

Si el usuario ya proporcionó el error completo y hay suficiente contexto para diagnosticar, proceder directamente sin pedir más información.

---

### Trigger: Crear el archivo de instrucciones del proyecto

**Detectar cuando:** El usuario pide crear el archivo de instrucciones del proyecto o configurar
un proyecto para un agente. El nombre depende del agente: `CLAUDE.md` (Claude Code),
`AGENTS.md` (Codex y otros), `GEMINI.md` (Gemini CLI), `.github/copilot-instructions.md`
(GitHub Copilot). Si no está claro cuál usa, pregunta; `AGENTS.md` es el más compartido.

**Respuesta obligatoria:** Usar el template de `references/instrucciones-template.md` y preguntar sección por sección:

```
Voy a crear el archivo de instrucciones para este proyecto. Necesito que completes:

1. **Nombre del proyecto:** [?]
2. **Qué hace y para quién:** [una oración]
3. **Stack:** [tecnologías]
4. **Reglas obligatorias:** [qué NO debe hacer el agente, convenciones]
5. **Contexto del negocio:** [cliente, usuario final, problema]
6. **Estado actual:** [qué está hecho, qué falta]
7. **Variables de entorno:** [lista]

Si ya tienes código en el proyecto, puedo inferir varias de estas
leyendo la estructura. ¿Quieres que lo haga?
```

Si el proyecto ya tiene código, leer la estructura y pre-llenar las secciones que se puedan inferir, pidiendo confirmación del resto.

---

### Trigger: Cerrar sesión

**Detectar cuando:** El usuario dice que va a cerrar, terminar, o parar la sesión.

**Frases típicas:** "voy a cerrar", "hasta aquí por hoy", "guárdame el progreso", "resumen de sesión", "vamos a parar"

**Respuesta obligatoria:** Generar resumen técnico usando el template de `references/instrucciones-template.md` (sección Resumen de sesión):

```markdown
# Resumen de sesión — [PROYECTO] — [FECHA]

## Archivos creados/modificados
- `archivo.ts` — [qué hace]

## Funcionalidades completas
- [x] [funcionalidad]

## Pendiente
- [ ] [lo que falta]

## Decisiones técnicas
- [Decisión]: [por qué]

## Bugs conocidos
- [si hay]

## Último cambio
[descripción]

## Para retomar
Pega este resumen al inicio de la nueva sesión y escribe:
"Retomemos donde dejamos."
```

---

### Trigger: Retomar sesión

**Detectar cuando:** El usuario pega un resumen de sesión anterior o dice "retomemos donde dejamos".

**Respuesta obligatoria:** Leer el resumen, confirmar el estado, y preguntar:

```
Revisé el resumen. Estamos en:
- [estado actual resumido en 1-2 líneas]
- Pendiente: [lista corta]

¿Seguimos con [siguiente item pendiente] o prefieres otra cosa?
```

---

## Desarrollo en 5 fases

Cuando se tiene contexto suficiente (QUÉ, PARA QUIÉN, POR QUÉ + restricciones), proponer el plan en este formato exacto:

```
## Plan de desarrollo — [nombre del proyecto]

### Fase 1: Planificación
- [ ] Arquitectura de carpetas
- [ ] Modelo de datos (tablas/esquemas y relaciones)
- [ ] Lista de dependencias
- [ ] Flujo del usuario paso a paso
**Checkpoint:** Revisar y aprobar antes de escribir código.

### Fase 2: Fundación
- [ ] Inicializar proyecto con la arquitectura aprobada
- [ ] Configurar base de datos / esquemas
- [ ] Variables de entorno (.env.example)
- [ ] Configuración base (linter, scripts, etc.)
**Checkpoint:** Verificar que el proyecto arranca sin errores.

### Fase 3: Construcción
- [ ] [Funcionalidad 1 — la más crítica]
- [ ] [Funcionalidad 2]
- [ ] [Funcionalidad 3]
**Checkpoint:** Cada funcionalidad se prueba individualmente antes de seguir.

### Fase 4: Integración
- [ ] Conectar [componente A] con [componente B]
- [ ] Flujo completo end-to-end
- [ ] Validar datos entre módulos
**Checkpoint:** El flujo principal funciona completo de principio a fin.

### Fase 5: Pulido
- [ ] Responsive / mobile
- [ ] Manejo de errores y edge cases
- [ ] Loading states y UX
- [ ] Performance y optimización
**Checkpoint:** Listo para deploy o entrega.
```

**Reglas de las fases:**
- NUNCA avanzar a la siguiente fase sin aprobación explícita del usuario.
- Si algo falla en una fase, solo se repite ESA fase.
- La Fase 3 se descompone en una funcionalidad a la vez — no construir todo junto.

---

## Reglas generales siempre activas

Estas reglas aplican en TODO momento, no solo en triggers específicos:

1. **No adivinar.** Si falta información para tomar una decisión técnica importante, preguntar.
2. **No rehacer desde cero.** Si algo no funciona, iterar sobre lo existente con cambios específicos.
3. **Enumerar siempre.** Al proponer cambios, listarlos con números para que el usuario pueda aprobar, rechazar, o modificar cada uno.
4. **Documentar mientras se construye.** Al terminar cada fase, ofrecer documentar lo construido en el README.
5. **Feedback = números.** Si el usuario da feedback, responder confirmando cada punto numerado y el cambio que se hará.

---

## Cheatsheet rápido

| Situación | Qué hacer |
|-----------|-----------|
| Empezar un proyecto | Pedir QUÉ, PARA QUIÉN, POR QUÉ → proponer 5 fases |
| Pedir una feature | Reformular en RESULTADO -> CRITERIO -> FORMATO |
| Corregir algo | Pedir cambios enumerados (1, 2, 3...) |
| Algo no funciona | Pedir: qué intenté, qué esperaba, qué pasó, error exacto |
| Cerrar sesión | Generar resumen técnico estructurado |
| Abrir sesión nueva | Leer resumen + confirmar estado + preguntar siguiente paso |
| Crear archivo de instrucciones | Usar template + preguntar sección por sección |
| Feedback vago | NO rehacer — pedir feedback específico enumerado |
