# Mantenimiento de los scripts

Para quien **modifique** `scripts/`. No hace falta para usar la skill. Cada fallo de aquí
existió y se cerró; la batería de regresión del final debe seguir pasando tras cualquier cambio.

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
cd <skill>/scripts
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
