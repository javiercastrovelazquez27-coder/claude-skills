---
name: mac-disk-reclaim
description: |
  Diagnostica y mejora un Mac en dos ejes: espacio en disco Y rendimiento (CPU, RAM,
  swap, procesos en segundo plano). SIEMPRE revisa ambos, aunque solo pidan uno.
  Usar cuando el usuario diga
  "me quedé sin espacio", "limpia el disco", "libera espacio", "el Mac está lleno",
  "disk full", "clean up my mac", o pida borrar caches / node_modules / Docker /
  Xcode DerivedData. También al actualizar Homebrew como parte de mantenimiento.
  Tambien para rendimiento: "el Mac va lento", "optimiza", "libera RAM", "va lento
  programando", "quita cosas en segundo plano", "que corra mejor", "mucha CPU",
  "se calienta", "los ventiladores", "revisa el rendimiento".
  NO usar para borrar archivos concretos que el usuario nombra (eso es un rm normal),
  ni para limpiar un repo de git (eso es git clean).
compatibility: Solo macOS. Usa bash, du, df, ps, osascript y, si existen, brew y docker.
---

# Recuperar espacio y rendimiento — macOS

`<skill>` es la carpeta de esta skill (donde está este `SKILL.md`). Modos: `audit`, `clean`, `optimize`, `full`; `audit` y
`optimize` sin `--apply` solo miden.

Recuperar espacio es **destructivo e irreversible**. La regla central de esta skill:
**medir primero, clasificar por riesgo, y no borrar nada del tier ASK sin confirmación explícita.**

Nunca ejecutes un borrado masivo "porque el comando existe". El fallo más caro no es dejar
1 GB sin recuperar — es borrar la única copia de unos datos.

## Qué hacer según el argumento

| Invocación | Qué haces |
|---|---|
| `/mac-disk-reclaim` (sin nada) | Paso 0 (rendimiento) + auditoría de disco. **Solo mides**, no borras. Propones y esperas. |
| `/mac-disk-reclaim optimize` | **Solo rendimiento.** Corres `optimize.sh`, reportas, y propones qué apagar. No auditas disco ni borras nada. |
| `/mac-disk-reclaim audit` | Solo `audit.sh` + paso 0. Cero cambios. |
| `/mac-disk-reclaim clean` | Auditas, ejecutas tier SAFE, y **preguntas** por el tier ASK. |
| `/mac-disk-reclaim full` | `clean` + propuesta de rendimiento en la misma pasada. |

Frases equivalentes en lenguaje natural: "va lento", "optimiza", "mucha CPU", "se calienta"
→ trátalo como `optimize`. "libera espacio", "limpia el disco" → como `clean`.

Con `optimize`, si el diagnóstico encuentra algo accionable, **propón antes de aplicar**:
matar procesos y cerrar apps puede perder trabajo del usuario. Solo `--apply` tras un sí.

## Progreso visible (OBLIGATORIO en cada respuesta larga)

Dentro de un agente (Claude Code, Codex, Copilot, Gemini CLI…) la salida de los comandos
pasa por un pipe, **nunca por un TTY**:
`ui.sh` se apaga solo y el usuario no ve ningún spinner. El spinner de `ui.sh` existe
únicamente para cuando la persona ejecuta el script en su propia terminal.

Así que **el progreso lo dibujas tú en el texto de la respuesta**, entre fase y fase.
No es adorno: en una limpieza de varios minutos es lo único que le dice al usuario
dónde está. Bloque de código plano, sin lenguaje, y se repite actualizado en cada paso:

```
MAC  ▸  fase 3/6
▰▰▰▰▰▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱  60%
 ✓ diagnostico       CPU 12% · swap 3.3 GB · RAM 8 GB
 ✓ auditoria disco   31 candidatos
 ✓ caches dev        5.0 GB
 ⟳ brew upgrade      12 outdated…
 ○ docker
 ○ informe (disco + rendimiento)
```

La primera línea es el diagnóstico de rendimiento y la última cierra con ambos ejes.
Un informe que solo habla de GB deja al usuario sin saber por qué su Mac sigue lento.

Reglas:
- `✓` hecho · `⟳` en curso · `○` pendiente · `!` saltado con motivo.
- Cifras reales ya medidas. **Nunca** rellenes una cifra que aún no tienes.
- Un bloque por respuesta, no uno por comando.
- Al terminar, sustitúyelo por la tabla de resultados. No dejes la barra a medias.
- Si algo se salta (Docker apagado, tier ASK rechazado), márcalo `!` y dilo en el informe.

## Flujo

**Disco y rendimiento son dos ejes distintos, y esta skill cubre los dos.** El usuario que
dice "optimiza mi Mac" casi nunca sabe cuál de los dos le duele: pide espacio y en realidad
le molesta la lentitud, o al revés. Diagnosticar ambos cuesta segundos y es de solo lectura.

**Paso 0 — SIEMPRE, con cualquier invocación, incluso si solo piden limpiar disco:**
```bash
bash <skill>/scripts/optimize.sh   # sin --apply: no toca nada
```
Y menciona el resultado aunque esté bien ("CPU holgada, swap normal"). Es una línea, y evita
el error de vaciar 40 GB de caches cuando lo que frenaba la máquina era un fondo de pantalla
en vídeo o 3 GB de swap. **Nunca entregues un informe de limpieza sin decir cómo está la CPU
y la memoria.**

Si el diagnóstico saca algo (swap > 1 GB, un proceso por encima del 20% de forma sostenida),
proponlo junto al plan de disco. Actúa solo con `--apply` y tras confirmar lo que sea tier ASK.

**Usa SIEMPRE los scripts. No improvises `du -sh` sueltos**: los scripts llevan las guardas
de seguridad, la clasificación por tiers y la comprobación de lockfiles. Un `du` a mano se
salta todo eso y además da resultados peores.

1. **Auditar** (siempre, aunque el usuario pida limpiar directo):
   ```bash
   bash <skill>/scripts/audit.sh
   ```
   Solo lee. Nunca borra. Devuelve tamaños reales por candidato.

2. **Clasificar** cada candidato en un tier (tabla abajo).

3. **Ejecutar SAFE** sin preguntar. Son regenerables por definición.

4. **Preguntar ASK** en un único bloque de opciones (con la herramienta de preguntas de tu
   agente si la tiene; si no, una lista numerada y esperas la respuesta).
   Di qué se pierde, cuánto se recupera, y si es reversible. No agrupes ASK con SAFE.

5. **Verificar**: `df -h` antes y después. Reporta el delta real, no el estimado.

6. **Reportar** qué NO se hizo y por qué (daemon apagado, permiso denegado, tier ASK rechazado).

## Tiers de riesgo

### SAFE — borrar sin preguntar
Regenerable sin pérdida de trabajo, offline o con un comando.

| Candidato | Cómo se regenera |
|---|---|
| `~/Library/Caches/*` (dev tools) | solo |
| `~/.npm/_cacache`, yarn/pnpm/bun store | `npm ci` |
| `~/.cache/{uv,ms-playwright,giget,puppeteer}` | reinstall |
| `~/.cache/huggingface`, `~/.cache/torch` | re-descarga (¡puede ser lento!) |
| Homebrew cache + logs | `brew cleanup -s --prune=all` |
| Xcode `DerivedData`, `iOS DeviceSupport` viejo | recompilar |
| `~/Library/Developer/CoreSimulator/Caches` | solo |
| Docker: build cache, imágenes dangling | rebuild |
| Logs > 30 días en `~/Library/Logs` | n/a |
| Simuladores marcados `unavailable` | `simctl delete unavailable` |

**`node_modules`: SAFE solo si hay lockfile.** Verifica *por directorio* antes de borrar:
```bash
# borra node_modules SOLO donde exista lockfile hermano
find "$ROOT" -type d -name node_modules -prune | while read -r nm; do
  d=$(dirname "$nm")
  ok=0; for l in package-lock.json yarn.lock pnpm-lock.yaml bun.lockb bun.lock; do
    [ -f "$d/$l" ] && ok=1; done     # NO `ls a b c`: falla si falta cualquiera de ellos
  if [ $ok -eq 1 ]; then
    rm -rf "$nm"
  else
    echo "SKIP (sin lockfile): $d"
  fi
done
```
Sin lockfile las versiones instaladas no son reproducibles → trátalo como ASK, no SAFE.

### ASK — confirmación explícita, siempre
Contiene datos que quizá no existan en otro sitio.

- **Volúmenes Docker con nombre** (`mysql-data`, `pgdata`, …) — datos de BD.
- **Imágenes Docker construidas localmente** — no se bajan de ningún registry.
- Bases de datos locales: `~/Library/Application Support/Postgres`, `~/.mysql`, `*.sqlite`.
- Máquinas virtuales / bundles de VM.
- `~/Downloads`, Papelera, cualquier cosa bajo `~/Documents` o `~/Desktop`.
- Backups: `.dump`, `.bak`, `.tar.gz` en carpetas de proyecto.

### NEVER — no tocar, ni ofrecer
`~/Library/Mobile Documents` (iCloud), Photos Library, Mail, Keychains, snapshots de
Time Machine, `/System`, `/Library` fuera de `Developer`, y todo lo que pida `sudo`.
Si algo pide `sudo`, **dáselo al usuario como comando para que lo corra él** — no lo ejecutes.

## Docker — la trampa

`docker system prune -af --volumes` **borra volúmenes con nombre** si su contenedor está parado.
Con todo parado eso es "borra todas mis bases de datos locales". Nunca lo sugieras como default.

Escalera correcta, de menor a mayor daño:
```bash
docker builder prune -af                   # SAFE — build cache
docker image prune -f                      # SAFE — solo dangling
docker volume ls -f dangling=true          # inspecciona ANTES
docker image prune -a -f                   # ASK-lite — respeta contenedores parados
docker system prune -af --volumes          # ASK — destruye datos. Solo si el usuario lo pide sabiendo.
```
Para volúmenes anónimos, filtra por nombre-hash y conserva los nombrados:
```bash
docker volume ls -f dangling=true --format '{{.Name}}' | grep -E '^[0-9a-f]{64}$'
```
Mide un volumen antes de proponerlo:
```bash
docker run --rm -v NOMBRE:/v alpine du -sh /v
```

## Mantenimiento (no borra nada, ofrécelo aparte)

```bash
brew update && brew upgrade && brew cleanup -s --prune=all && brew autoremove
brew doctor
```
`brew doctor` suele avisar de Command Line Tools viejas. Ese arreglo necesita `sudo` →
entrégalo como comando al usuario:
```bash
sudo rm -rf /Library/Developer/CommandLineTools && sudo xcode-select --install
```
CLT ≠ Xcode.app. Sin `/Applications/Xcode.app` no hay `xcodebuild` ni `simctl`, y eso
**no es un error** si el usuario no hace desarrollo nativo iOS/macOS.

## Reglas de reporte

- Cifras reales de `df -h`, medidas antes y después. Nunca sumes estimaciones.
- Tabla de qué se borró y cuánto.
- Sección explícita de **pendiente** con el motivo (ej. "Docker apagado", "rechazaste el tier ASK").
- Cómo restaurar: `npm ci` / `bun install` / `pnpm i`, `brew install X`.
- Si el espacio recuperado no cuadra con lo estimado, dilo. En Docker las capas se comparten,
  así que borrar 7 imágenes de 2.3 GB puede liberar solo 540 MB. Es normal — explícalo.

## Errores a no cometer

- Borrar `node_modules` sin comprobar lockfile en ESE directorio.
- `docker system prune --volumes` sin listar antes qué volúmenes nombrados morirían.
- Ejecutar comandos con `sudo`.
- Reportar "liberé X GB" sumando estimaciones en vez de leer `df`.
- Vaciar la Papelera. Es la última red de seguridad del usuario, y es ASK como mínimo.
- Tocar `~/Library/Mobile Documents`: parece cache, es iCloud Drive del usuario.
- Silenciar un paso fallido. Si Docker no responde o falta una herramienta, dilo en el reporte.

## Dónde se esconde el espacio de verdad

`~/Library` suele ser el 25-40% del disco y `du -sh ~/Library` no dice nada útil.
Baja siempre dos niveles: `Application Support`, `Containers`, `Group Containers`.

Patrones recurrentes, con su tier:

| Patrón | Tier | Nota |
|---|---|---|
| `Chrome/OptGuideOnDeviceModel`, `screen_ai`, `optimization_guide_model_store` | ASK-lite | Modelos de IA on-device. Chrome los re-descarga solo. Pueden ser GB. |
| `<AppElectron>/Partitions/*` (Notion, Slack, Discord) | ASK | Cache web de Electron. Borrarlo suele **cerrar la sesión**. |
| `Code/CachedExtensionVSIXs` | SAFE | Solo instaladores `.vsix` ya usados. |
| `Code/User/workspaceStorage` | ASK | Estado por workspace: histórico de chat, undo, índices. |
| `~/.vscode/extensions`, plugins de agentes (`~/.claude/plugins`, `~/.codex`, `~/.gemini`) | ASK | Extensiones reales, no cache. |
| `Containers/com.apple.AMPArtworkAgent` | SAFE | Carátulas de Música. Se regenera. |
| `Google/DriveFS`, `GoogleUpdater` | ASK-lite | DriveFS re-sincroniza (tráfico). Updater: versiones viejas, seguro. |
| `com.apple.wallpaper` | ASK-lite | Aerials 4K de Apple. Se re-descargan al usarlos. |
| `minecraft`, saves de juegos | **NEVER** | Mundos del usuario. Parece cache, es su partida. |
| `~/.serena/language_servers`, runtimes de IDE | SAFE | Se re-descargan al abrir el proyecto. |

Regla: en `~/Library`, **si el nombre no dice explícitamente "Cache", asume que son datos**
hasta comprobar lo contrario. `Application Support` es literalmente donde las apps guardan
lo del usuario.

## Datos huérfanos: la mejor relación espacio/riesgo

Una app desinstalada deja su `Application Support`, `Caches` y `Preferences` intactos, para siempre.
Nadie los limpia. En una máquina con años de uso esto suele ser 1-3 GB, y es el borrado
con mejor relación espacio/riesgo que existe: la app ya no está, nada va a romperse.

Detección: para cada directorio grande en `Application Support`, comprueba si su app existe.

```bash
# NUNCA con globs sueltos en zsh (ver aviso abajo). Con -d explícito:
[ -d "/Applications/Arc.app" ] || echo "huerfano: Arc"
```

Aun así **es tier ASK, no SAFE**: no es cache regenerable, son datos del usuario cuya app
murió. Si reinstala el navegador, esos marcadores y sesiones ya no vuelven. Pregunta,
diciendo qué se pierde si algún día reinstala.

Antes de proponerlo, mira dentro: si solo hay `ProgramData`, `Temp`, `Cache`, `Default Effects`,
es basura del instalador y puedes decirlo con confianza. Si hay `Projects`, `Documents`,
`saves` o `Profiles`, es trabajo del usuario.

## Trampa: el glob de zsh da falsos negativos

`ls -d /Applications/*Teams*` en zsh, cuando **no** hay match, imprime `no matches found`
y **aborta la línea entera** — los checks siguientes ni se ejecutan. Si iteras apps así,
concluirás que apps instaladas no lo están, y borrarás datos vivos.

Pasó en esta máquina: Teams y Podcasts se reportaron "NO INSTALADA" siendo falso.

Usa siempre `[ -d "ruta.app" ]` con la ruta completa entre comillas, y confirma con
`mdfind` si dudas. **Ante una conclusión de "no instalada", verifícala por segunda vía
antes de borrar nada.**

## Respalda lo irreemplazable barato antes de borrar

Si el usuario pide borrar algo que contiene trabajo suyo insustituible, y ese trabajo es
una fracción pequeña del total, **cópialo aparte y borra el resto**. Cumples la petición,
entregas casi todo el espacio, y no destruyes lo único que no se puede rehacer.

Caso real: "borra minecraft" = 1.6 GB, de los que 140 MB eran 3 mundos guardados.
Respaldar los mundos en `~/Desktop` costó el 9% del espacio y salvó lo insustituible.
Dilo explícitamente en el reporte y da el comando para borrar el respaldo. No lo hagas
en silencio: el usuario debe saber que existe.

No apliques esto si el respaldo es la mayor parte del volumen — ahí pregunta.

## Objetivos concretos verificados

```bash
# Modelos IA on-device de Chrome — se re-descargan solos; Chrome debe estar cerrado
~/Library/Application Support/Google/Chrome/OptGuideOnDeviceModel          # puede ser 4 GB
~/Library/Application Support/Google/Chrome/screen_ai
~/Library/Application Support/Google/Chrome/optimization_guide_model_store

# GoogleUpdater: borra crx_cache, CONSERVA el directorio de version activo
~/Library/Application Support/Google/GoogleUpdater/crx_cache               # ~700 MB
# ojo: 'Current' es un symlink al updater en uso. Borrarlo lo rompe.

# Caches de Apple que se regeneran solas
~/Library/Containers/com.apple.AMPArtworkAgent/Data/Documents/artwork      # caratulas Musica
~/Library/Group Containers/243LU875E5.groups.com.apple.podcasts/Library/Cache  # episodios

# VS Code: solo el cache de instaladores
~/Library/Application Support/Code/CachedExtensionVSIXs
# NO: ~/.vscode/extensions ni Code/User/*  (extensiones y ajustes reales)
```

Antes de borrar en `Application Support` de una app **instalada**, ciérrala.
Con Chrome abierto, los modelos se re-crean al instante y el borrado no sirve de nada.

---

# Modo optimizar — rendimiento, no espacio

```bash
bash <skill>/scripts/optimize.sh            # solo diagnostica
bash <skill>/scripts/optimize.sh --apply wallpaper sync
```

Espacio y rendimiento son problemas **distintos**. Un disco lleno no ralentiza un Mac
(salvo por debajo del ~10% libre). Si el usuario dice "va lento", no le limpies caches:
diagnostica CPU y RAM.

## Diagnostica antes de tocar

```bash
sysctl -n hw.memsize hw.ncpu           # cuánta RAM tiene realmente
sysctl -n vm.swapusage                 # ojo: con -n los campos se desplazan
ps -Aro pcpu,rss,comm | head -10       # quién consume de verdad
```

**Swap asignado NO es lo mismo que paginar ahora.** Una máquina puede tener 4 GB en swap
e ir perfectamente: son residuo de un pico anterior que nadie ha reclamado. Lo que duele es
la *tasa* de paginación en este momento. Mídela con dos muestras de `Swapouts`:

```bash
so1=$(vm_stat | awk '/Swapouts/{gsub(/[.]/,"",$NF); print $NF}')
sleep 2
so2=$(vm_stat | awk '/Swapouts/{gsub(/[.]/,"",$NF); print $NF}')
[ "$so2" -gt "$so1" ] && echo "paginando AHORA"   # esto sí es el cuello de botella
```

Decirle a alguien "tu swap es la causa de la lentitud" cuando no hay paginación activa le
manda a cerrar apps y borrar caches para arreglar un problema que no tiene. **El peor fallo
posible en una herramienta de diagnóstico es señalar una causa falsa con seguridad.**

Dos avisos sobre el parseo:
- Con `sysctl -n` no hay prefijo `vm.swapusage:` y los campos se desplazan: busca la
  etiqueta `used =`, nunca una posición fija.
- Captura también la unidad (`K`/`M`/`G`) y normaliza. Un `sed` que exija `M` literal
  devuelve vacío y el aviso muere en silencio justo en la máquina más cargada.

Y **`vm.swapusage used` sí baja** — se comprobó bajando de 3523M a 3013M en una sola sesión,
con el fichero de swap encogiendo de 5120M a 4096M. No es un contador acumulado.

## Sospechosos por orden de retorno

| Objetivo | Ganancia | Nota |
|---|---|---|
| **Fondo aerial** (`WallpaperAerialsExtension`) | 20-30% CPU **constante** | Reproduce vídeo 4K en bucle. El mayor ladrón silencioso. |
| Google Drive / Dropbox / OneDrive | 10-20% CPU | Cerrarlo pausa la sync. |
| Docker Desktop | 1-2 GB RAM reservada | La VM cuesta RAM aunque no haya contenedores. |
| Electron sin usar (Notion, Slack, Teams) | 200-600 MB c/u | Cerrar, no minimizar. |
| Spotlight indexando `node_modules` | picos de `mds_stores` | Excluir en Ajustes > Siri y Spotlight > Privacidad. |
| `photoanalysisd`, `mediaanalysisd` | temporal | Termina solo. **No lo mates en bucle.** |

El fondo aerial merece mención aparte: 20-30% de CPU permanente por un fondo de pantalla.

Secuencia correcta, y **hacen falta los dos pasos**:
1. El usuario cambia a imagen fija en Ajustes (si no, el proceso revive).
2. **Después** matas el proceso: cambiar el ajuste NO lo termina, sigue vivo consumiendo
   igual hasta que se reinicia la sesión. Verificado: con el proveedor ya en
   `choice.image`, el proceso seguía a 34% de CPU. Tras matarlo, no volvió.

Comprueba el cambio en la config, no solo de palabra:
```bash
plutil -p ~/Library/Application\ Support/com.apple.wallpaper/Store/Index.plist | grep -i provider
# choice.aerials = vídeo (malo) · choice.image = imagen fija (bien)
```

**El salvapantallas es un ajuste aparte.** Un usuario puede poner fondo fijo y seguir con
salvapantallas aerial; el mismo proceso vuelve al activarse. Recuérdale los dos sitios.

**Vocabulario:** no digas "aerial" a secas. Casi nadie sabe que es el nombre de Apple para
los fondos en vídeo. Di "fondo de pantalla en movimiento (un vídeo en bucle)" y explica que
por eso gasta CPU. Jerga sin traducir en un informe de rendimiento no comunica nada.

## Reglas

- **Nunca `kill -9` una app GUI.** Usa `osascript -e 'tell application "X" to quit'`:
  respeta el guardado. Un `-9` sobre un editor pierde trabajo del usuario.
- **Nunca matar**: `kernel_task`, `launchd`, `WindowServer`, `loginwindow`, `coreaudiod`,
  `securityd`, `opendirectoryd`, `mds`. Cuelgan la sesión.
- **Nunca matar el terminal ni el proceso del agente** (Claude, Codex, Copilot en VS Code,
  Gemini CLI…): te matas a ti mismo a mitad de tarea.
- **Nunca uses `$3` de `ps` para el nombre**: corta en el primer espacio y convierte
  `Claude Helper (Renderer)` en `Claude`, o `Visual Studio Code` en `Visual`. Justo los
  procesos que más consumen salen con nombres inventados. Lee el resto de la línea:
  `ps -Aro pcpu,rss,comm | sed -n '2,9p' | while read -r cpu rss rest; do ... "${rest##*/}"`
- **Un bloqueo de seguridad no se reporta como `[dry]`.** Si `permitido()` frena algo con
  `--apply` activo, dilo como bloqueo. Meter ambos casos en el mismo `else` hace que el
  usuario crea que fue una simulación cuando fue la guarda.
- Los demonios de Apple **reaparecen** por launchd. Prometer que "los quitaste" es mentira:
  repórtalos y explica el ajuste permanente.
- Nada de `sudo`, nada de tocar `/System`, nada de descargar `launchctl` de servicios del
  sistema. Si el arreglo real necesita privilegios, entrega el comando al usuario.
- Distingue **alivio inmediato** de **arreglo permanente**, y di cuál estás aplicando.

## Si la RAM es el límite

Con 8 GB y swap saturado, cerrar procesos es un parche. Lo honesto es decirlo:
el arreglo estructural es menos cosas abiertas a la vez (un navegador, no tres) o más RAM.
No prometas que un script convierte 8 GB en 16.

## Desinstalar una app del todo

1. Comprueba primero si hay **datos sin sincronizar** (clientes de nube) o proyectos dentro.
   En Google Drive: `DriveFS/<cuenta>/content_cache` y directorios `*upload*`/`*staged*`.
   `content_cache` en unos KB = nada pendiente, todo está en la nube.
2. Quita el **login item**:
   `osascript -e 'tell application "System Events" to delete login item "X"'`
3. Borra datos de usuario: `Application Support`, `Group Containers`, `Caches`,
   `Preferences`, `Containers`, `Application Scripts`.
4. **`/Applications/*.app` suele ser `root:wheel` → necesita `sudo`. Entrégalo al usuario.**
5. **No borres actualizadores compartidos.** `com.google.keystone` y `GoogleUpdater`
   actualizan también Chrome: quitarlos al desinstalar Drive rompe las updates de Chrome.
   Mira qué más depende del agente antes de tocarlo.
6. Algunos `Containers/*.fpext` (extensiones de Finder) están protegidos por TCC y
   `rm -rf` falla aunque seas el dueño. Repórtalo, no lo escondas.

## Si vas a modificar los scripts

Lee `references/mantenimiento-scripts.md`: fallos ya cerrados (informes falsos, `HOME`
vacío, `eval`, inyección en AppleScript), los principios de seguridad y la batería de
regresión que debe seguir dando ABORTA.
