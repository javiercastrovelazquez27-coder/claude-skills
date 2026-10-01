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
user-invocable: true
argument-hint: "[audit | clean | optimize | full] (audit y optimize sin --apply solo miden)"
allowed-tools: Bash, AskUserQuestion, Read
---

# Recuperar espacio y rendimiento — macOS

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

Dentro de Claude Code la salida de los comandos pasa por un pipe, **nunca por un TTY**:
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
bash ~/.claude/skills/mac-disk-reclaim/scripts/optimize.sh   # sin --apply: no toca nada
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
   bash ~/.claude/skills/mac-disk-reclaim/scripts/audit.sh
   ```
   Solo lee. Nunca borra. Devuelve tamaños reales por candidato.

2. **Clasificar** cada candidato en un tier (tabla abajo).

3. **Ejecutar SAFE** sin preguntar. Son regenerables por definición.

4. **Preguntar ASK** con `AskUserQuestion`, en un único bloque de opciones.
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
| `~/.vscode/extensions`, `~/.claude/plugins` | ASK | Extensiones reales, no cache. |
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
bash ~/.claude/skills/mac-disk-reclaim/scripts/optimize.sh            # solo diagnostica
bash ~/.claude/skills/mac-disk-reclaim/scripts/optimize.sh --apply wallpaper sync
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
- **Nunca matar el terminal ni el proceso de Claude** — te matas a ti mismo a mitad de tarea.
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

## Auditoría del propio modo optimizar (fallos reales encontrados)

Estos tres bugs estuvieron en `optimize.sh` y pasaron el "se ve bien". Búscalos en
cualquier script que mate procesos:

**1. La lista de protegidos no se usaba.** Existía una variable `PROTEGIDOS` con
`WindowServer`, `launchd`, etc., y una cabecera que prometía "nunca mata procesos del
sistema" — pero nada la consultaba. Era segura solo por accidente, porque la lista de
objetivos estaba escrita a mano. En cuanto alguien añadiera un objetivo dinámico, dejaba
de serlo. **Una lista de seguridad que no se invoca es peor que no tenerla: da confianza falsa.**
Haz que todo borrado/kill pase por una única función-puerta.

**2. `pkill -f` es una escopeta.** `-f` casa contra la línea de comandos **completa**, así
que `pkill -f WallpaperAerialsExtension` mata también a un editor que tenga ese fichero
abierto, a un `grep`, o a otro script que mencione el nombre. Verificado con un señuelo:
caían los dos. Usa **`pkill -x`** (nombre exacto) siempre. Reserva `-f` para cuando no
haya alternativa, y entonces ancla el patrón con la ruta completa.

**3. macOS no trae `timeout`.** `osascript -e 'tell application "X" to quit'` sobre una app
con cambios sin guardar abre un diálogo y **espera indefinidamente**: el script se cuelga.
No existe `timeout` ni `gtimeout` sin coreutils. Implementa el límite a mano:
```bash
con_limite(){ local s="$1"; shift; "$@" & local pid=$!; local n=0
  while kill -0 "$pid" 2>/dev/null; do
    [ "$n" -ge "$s" ] && { kill "$pid" 2>/dev/null; return 124; }
    sleep 1; n=$((n+1))
  done; wait "$pid"; }
```
Si salta el límite, **reporta y deja la app abierta**. No escales a `kill -9`: ese diálogo
existe porque hay trabajo sin guardar.

## Segunda auditoría (2026-09-30): cuatro fallos más, todos de "informe falso"

Ninguno borró nada indebido, pero los cuatro hacían que el script dijera algo que no era verdad.

**1. `ls a b c` no significa "existe alguno".** Devuelve error si falta *cualquiera*. El
chequeo de lockfile marcaba "sin lockfile" a todo proyecto que no tuviera los cinco a la
vez: 32 de 32. Ahora es `tiene_lockfile()` en `common.sh`, con `[ -f ]` uno por uno.

**2. SAFE de borrar no es seguro de borrar AHORA.** `~/.cache/uv` es regenerable, pero los
servidores MCP lanzados con `uvx` corren *desde dentro*; igual `node_modules` con un dev
server vivo. `nuke()` pasa por `ruta_en_uso()` y salta la ruta con `EN USO`, también en
simulación. No lo fuerces: con las sesiones cerradas, `uv cache prune`.

**3. `>/dev/null 2>&1` sobre un paso lo borra del informe.** La limpieza de npm se ejecutaba
pero no aparecía ni en el dry-run ni en el resultado, y pnpm no estaba. `pkgcaches` muestra
ahora tamaño y comando de npm y de pnpm (`store prune`, no `rm`: respeta lo referenciado).

**4. `osascript … quit` con rc 0 no es "cerrado".** Las apps de barra de menú (Granola)
aceptan el quit, cierran la ventana y siguen vivas. `quit_app` espera y comprueba el
proceso: si sigue, dice `SIGUE VIVO` y no fuerza. De paso: el nombre de la app no siempre
es el del proceso ("Microsoft Teams" corre como `MSTeams`), así que `pgrep -x` no la veía
y el target `apps` se la saltaba. `app_viva()` busca también por la ruta del bundle.

Regla común: **un mensaje de éxito se imprime después de comprobar el efecto, no después
de lanzar el comando.**

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

---

# Auditoría de seguridad — vulnerabilidades encontradas y cerradas

Estos fallos **estaban** en los scripts y se demostraron explotables. Búscalos en cualquier
script que borre ficheros.

## 1. `HOME` vacío convertía rutas de usuario en rutas de sistema

`nuke "$HOME/Library/Caches/pip"` con `HOME=""` se convierte en `/Library/Caches/pip`.
Y `find '$HOME/Library/Logs' -delete` pasaba a borrar **los logs del sistema**.

`set -u` no protege: solo falla con variables *no definidas*, no con las definidas y vacías.

Cierre: `verificar_entorno()` en `common.sh` exige que `HOME` sea absoluto, exista, sea
directorio, no sea `/`, tenga al menos dos segmentos, y **coincida con el home real del
sistema** (`dscl . -read /Users/$(id -un) NFSHomeDirectory`). Además aborta si corre como root.

## 2. `eval` daba ejecución arbitraria de comandos

```bash
run() { eval "$1"; }
run "find '$HOME/Library/Logs' -type f -mtime +30 -delete"
```
Con `HOME="/tmp/x'; echo PWNED; echo '"` la comilla cerraba la cadena y `PWNED` se ejecutó.
Comprobado en la práctica, no en teoría.

Cierre: `run()` recibe **argumentos, no una cadena**, y ejecuta `"$@"`. Sin `eval`, una ruta
con comillas o `;` es solo una ruta.
```bash
run() { if [ $APPLY -eq 1 ]; then "$@"; else echo "  [dry] $*"; fi; }
run docker volume rm "$v"        # bien
run "docker volume rm $v"        # mal: vuelve a ser una cadena que alguien interpretará
```

## 3. Dos caminos de borrado, uno solo vigilado

`nuke()` comprobaba rutas protegidas. `run()` no comprobaba nada. Todo lo que pasaba por
`run` (incluido un `find -delete`) esquivaba la guarda entera.

Cierre: el borrado de logs pasa por `purgar_logs()`, que valida la ruta y usa `find` con la
variable directamente. **Regla: un único punto de salida para lo destructivo.** Si hay dos
funciones que borran, la segunda acabará sin guarda.

## 4. Inyección en AppleScript por el nombre de app

`osascript -e "tell application \"$app\" to quit"` con un `$app` que contenga comillas
permite añadir sentencias — por ejemplo un `empty trash`.
Hoy la lista es fija, pero basta que alguien la haga dinámica.

Cierre: `nombre_app_valido()` restringe a `A-Za-z0-9`, espacio, `.`, `_`, `-`.

## Principios

- **Falla cerrado.** Si `common.sh` no está, los scripts abortan con código 3 en vez de
  seguir sin protección. Verificado.
- **Valida el entorno antes de la primera ruta**, no en medio.
- **`set -u` no basta.** Una variable vacía pasa el filtro y arruina toda ruta derivada.
- **Nunca `eval` con algo que contenga una ruta.**
- **Nunca correr como root**: convierte cualquier bug en daño al sistema.
- Prueba los ataques de verdad (`env HOME= ...`) en vez de razonar que "no puede pasar".

## Batería de regresión

Cualquier cambio en los scripts debe seguir dando ABORTA en las cuatro:
```bash
cd ~/.claude/skills/mac-disk-reclaim/scripts
for sc in audit.sh reclaim.sh optimize.sh; do
  env HOME=  bash $sc devcaches            # HOME vacio
  env HOME=/ bash $sc devcaches            # HOME raiz
  env HOME="/tmp/x'; echo PWNED; echo '" bash $sc devcaches   # inyeccion
  env HOME=/tmp bash $sc devcaches         # HOME que no es el del usuario
done
```

---

# Presentación (`ui.sh`)

Cabecera fina, marcadores `│ ✓ ! ×`, spinner braille en las operaciones lentas y un
contador que sube hasta los GB liberados. Paleta de 3 tonos apagados, sin arcoíris.

**Solo se ve si la persona ejecuta el script en su terminal.** Cuando lo lanza un agente,
la salida va por un pipe y `ui.sh` se apaga — correcto, porque si no la transcripción se
llenaría de códigos de escape. Para el progreso dentro del chat, mira
"Progreso visible" arriba: ese lo dibuja el agente en el texto, y es el que el usuario ve.

**La animación nunca cambia lo que se hace, solo cómo se ve.** Reglas que lo sostienen:

- **Se apaga sola** si la salida no es un TTY (`[ -t 1 ]`), con `NO_COLOR`, o `TERM=dumb`.
  En un pipe o un fichero de log no sale ni un código de escape, y el filete pasa a ASCII.
  Verificado: 0 escapes al redirigir en los tres scripts.
- **Es cosmética, no crítica.** Si falta `ui.sh` se definen funciones neutras y el script
  sigue. Con `common.sh` es al revés: si falta, aborta. Estética degrada, seguridad no.
- **El spinner captura la salida del comando** en un temporal y la muestra al terminar.
  Si se imprimiera durante el giro, se intercalaría con los fotogramas y rompería la
  animación en su sitio (pasó con `brew cleanup`). En éxito muestra las últimas 3 líneas
  atenuadas; en fallo, todo — hay que poder diagnosticar.
- **En simulación no gira nada**: `ui_spin_run` solo anima con `--apply`. Un spinner sobre
  un comando que no se ejecuta es mentirle al usuario.
- `trap ui_cleanup EXIT INT TERM` restaura el cursor. Sin eso, un Ctrl-C deja la terminal
  sin cursor visible.

## Trampa de bash 3.2 con UTF-8

```bash
bar="$bar▰"      # MAL: bash 3.2 se traga los bytes UTF-8 como parte del nombre
                 #      -> "bar▰: unbound variable"
bar="${bar}▰"    # BIEN: llaves para acotar el nombre
```
El substring sí es correcto por caracteres (`${f:$i:1}` sobre braille funciona, `${#f}`=10),
así que el spinner es seguro en el bash que trae macOS.
