#!/usr/bin/env bash
# optimize.sh — libera CPU/RAM cerrando trabajo de fondo innecesario.
# Sin --apply solo diagnostica. Nunca usa sudo. Nunca mata procesos del sistema.
set -uo pipefail

# Carga de guardas compartidas. Sin ellas, no se ejecuta nada.
_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
. "$_DIR/common.sh" 2>/dev/null || { echo "ABORTA: falta common.sh (guardas de seguridad)." >&2; exit 3; }
verificar_entorno
# ui.sh es cosmetico: si falta, se sigue con funciones neutras (nunca aborta por estetica).
if ! . "$_DIR/ui.sh" 2>/dev/null; then
  ui_title(){ echo "== $1"; }; ui_step(){ echo "  $1"; }; ui_ok(){ echo "  ok $1"; }
  ui_warn(){ echo "  ! $1"; }; ui_err(){ echo "  x $1"; }; ui_end(){ :; }
  ui_bar(){ :; }; ui_count_gb(){ printf '  %s: %s GB\n' "${2:-liberado}" "$1"; }
  C_DIM=; C_RST=; C_ACC=; C_OK=; C_WARN=; C_ERR=; C_BOLD=; UI_TTY=0; UI_RULE=
  ui_spin(){ local m="$1"; shift; "$@"; }
fi

APPLY=0; TARGETS=()
for a in "$@"; do
  case "$a" in
    --apply) APPLY=1 ;;
    --help|-h) sed -n '2,4p' "$0"
      echo; echo "targets: wallpaper sync docker apps indexers all"
      echo "uso: optimize.sh [--apply] [TARGET...]   (sin target = solo diagnostico)"; exit 0 ;;
    -*) echo "flag desconocida: $a" >&2; exit 2 ;;
    *) TARGETS+=("$a") ;;
  esac
done

# Procesos que NUNCA se tocan: matarlos cuelga la sesion o el sistema.
PROTEGIDOS='^(kernel_task|launchd|WindowServer|loginwindow|SystemUIServer|Dock|Finder|coreaudiod|opendirectoryd|securityd|mds|mds_stores|Terminal|iTerm2|Warp|Ghostty|Alacritty|kitty|Claude|claude|codex|Codex|gemini|copilot|Code|Cursor|node|ssh|sshd)$'

# Puerta unica: nada se mata sin pasar por aqui. Antes esta lista existia pero no se usaba.
permitido(){
  if printf '%s' "$1" | grep -qE "$PROTEGIDOS"; then
    echo "  BLOQUEADO (proceso protegido): $1"; return 1
  fi
  # no suicidarse: comprueba el padre directo. Los abuelos (terminal, agente) van
  # cubiertos por PROTEGIDOS, no por esta comprobacion.
  local me; me=$(ps -o comm= -p $PPID 2>/dev/null | sed 's|.*/||')
  [ "$1" = "$me" ] && { echo "  BLOQUEADO (es el proceso padre de este script): $1"; return 1; }
  return 0
}

vivo(){ pgrep -x "$1" >/dev/null 2>&1; }
# Una app GUI no siempre se llama como su proceso ("Microsoft Teams" corre como MSTeams),
# asi que se busca tambien por la ruta de su bundle. -f solo para DETECTAR y anclado al
# ejecutable principal del .app; para matar se sigue usando -x.
app_viva(){
  vivo "$1" && return 0
  pgrep -f "/${1//./\\.}\.app/Contents/MacOS/" >/dev/null 2>&1
}

# macOS no trae `timeout`. Sin limite, un dialogo de "guardar cambios" cuelga el script
# para siempre. Esto lo implementa a mano.
con_limite(){
  local secs="$1"; shift
  "$@" & local pid=$!
  local n=0
  while kill -0 "$pid" 2>/dev/null; do
    [ "$n" -ge "$secs" ] && { kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null; return 124; }
    sleep 1; n=$((n+1))
  done
  wait "$pid" 2>/dev/null; return $?
}
# cierra una app GUI con gracia (guarda estado); nunca con kill -9
quit_app(){
  local app="$1"
  nombre_app_valido "$app" || return
  app_viva "$app" || { echo "  (no corre) $app"; return; }
  permitido "$app" || return
  if [ $APPLY -eq 1 ]; then
    con_limite 10 osascript -e "tell application \"$app\" to quit" >/dev/null 2>&1
    case $? in
      # Que osascript devuelva 0 solo dice que la app recibio el quit. Las de barra de
      # menu cierran la ventana y siguen vivas: se comprueba el proceso antes de afirmar.
      0) local n=0
         while app_viva "$app" && [ "$n" -lt 8 ]; do sleep 1; n=$((n+1)); done
         if app_viva "$app"; then
           echo "  SIGUE VIVO  $app — acepto el quit pero el proceso no termino (app de barra"
           echo "              de menu o pide confirmar). Cierrala tu; NO la fuerzo."
         else echo "  cerrado   $app"; fi ;;
      124) echo "  TIMEOUT   $app — probablemente pide guardar cambios. Cierralo tu; NO lo fuerzo." ;;
      *) echo "  no pudo cerrarse  $app" ;;
    esac
  else echo "  [dry] cerraria  $app"; fi
}

ui_title "Optimizar rendimiento" "$([ $APPLY -eq 1 ] && echo "aplicando" || echo "diagnostico")"
sysctl -n hw.ncpu hw.memsize 2>/dev/null | awk 'NR==1{c=$1} NR==2{printf "  %s cores · %.0f GB RAM\n",c,$1/1073741824}'
sysctl vm.swapusage 2>/dev/null | sed 's/^/  /'
free=$(memory_pressure 2>/dev/null | awk -F': ' '/free percentage/{print $2}')
echo "  memoria libre: ${free:-?}"
# Captura valor Y unidad: no dar por hecho que siempre son megas.
sw_raw=$(sysctl -n vm.swapusage 2>/dev/null | sed -n 's/.*used = \([0-9.]*\)\([KMG]\).*/\1 \2/p')
sw=$(echo "$sw_raw" | awk '{v=$1; if($2=="G") v*=1024; else if($2=="K") v/=1024; printf "%.0f", v}')

# Swap ASIGNADO no es lo mismo que paginando AHORA. Una maquina puede tener GB en
# swap y ir fina si no esta paginando. Lo que duele es la tasa, no el acumulado:
# se compara Swapouts en dos instantes.
so1=$(vm_stat 2>/dev/null | awk '/Swapouts/{gsub(/[.]/,"",$NF); print $NF}')
sleep 2
so2=$(vm_stat 2>/dev/null | awk '/Swapouts/{gsub(/[.]/,"",$NF); print $NF}')
if [ -n "${so1:-}" ] && [ -n "${so2:-}" ] && [ "$so2" -gt "$so1" ] 2>/dev/null; then
  echo "  AVISO: paginando AHORA ($((so2-so1)) swapouts en 2s). El disco hace de RAM."
  echo "  Esta es la causa real de la lentitud: cierra apps o amplia RAM."
elif [ -n "${sw:-}" ] && [ "$sw" -gt 1000 ] 2>/dev/null; then
  echo "  memoria: ${sw}M en swap pero SIN paginacion activa — residuo de picos"
  echo "  anteriores, no es el cuello de botella ahora mismo."
fi
echo
echo "  -- top CPU --"
ps -Aro pcpu,rss,comm | sed -n '2,9p' | while read -r cpu rss rest; do
    printf '     %5.1f%%  %5.0fMB  %s\n' "$cpu" "$(( (rss + 512) / 1024 ))" "${rest##*/}"
  done
echo

[ ${#TARGETS[@]} -eq 0 ] && { echo "Solo diagnostico. Pasa targets para actuar (--help)."; exit 0; }
[[ " ${TARGETS[*]} " == *" all "* ]] && TARGETS=(wallpaper sync docker apps indexers)
[ $APPLY -eq 1 ] || echo ">>> DRY-RUN — nada se ejecuta. Añade --apply."

for t in "${TARGETS[@]}"; do
echo "### $t"
case "$t" in
  wallpaper)
    # Los fondos aerial reproducen video 4K en bucle: CPU+GPU constantes.
    # -x (nombre exacto), NUNCA -f: con -f caeria cualquier proceso cuya linea de
    # comandos mencione el texto (un editor con el fichero abierto, un grep, otro script).
    if pgrep -x WallpaperAerialsExtension >/dev/null 2>&1; then
      # Ramas separadas: un bloqueo de seguridad NO debe reportarse como simulacion.
      if [ $APPLY -eq 0 ]; then
        echo "  [dry] detendria WallpaperAerialsExtension"
      elif permitido WallpaperAerialsExtension; then
        pkill -x WallpaperAerialsExtension && echo "  aerial detenido (alivio inmediato)"
      fi
      echo "  PERMANENTE: Ajustes > Fondo de pantalla > elige una imagen fija."
      echo "  Sin ese cambio el proceso vuelve solo al poco rato."
    else echo "  no hay fondo aerial activo"; fi ;;
  sync)
    quit_app "Google Drive"
    echo "  nota: al cerrarlo se pausa la sincronizacion. Reabrelo cuando lo necesites." ;;
  docker)
    if pgrep -x com.docker.backend >/dev/null 2>&1 || pgrep -x "Docker Desktop" >/dev/null 2>&1; then
      quit_app "Docker Desktop"
      echo "  nota: la VM de Docker reserva RAM aunque no corra ningun contenedor."
    else echo "  Docker no corre"; fi ;;
  apps)
    # Electron: cada una cuesta cientos de MB. Solo las que no estan en uso.
    echo "  AVISO: estas apps pueden tener trabajo sin guardar. Se les PIDE cerrar"
    echo "  (nunca kill -9); si alguna pregunta, se deja abierta y se reporta."
    for a in "Notion" "Microsoft Teams" "Slack" "Discord" "Spotify" "Granola"; do
      app_viva "$a" && quit_app "$a"
    done ;;
  indexers)
    # Procesos de Apple: se pueden pausar pero vuelven. Reporta, no prometas milagros.
    for p in photoanalysisd mediaanalysisd siriinferenced; do
      pgrep -x "$p" >/dev/null 2>&1 && echo "  activo: $p (analisis de Fotos/Siri — termina solo, no lo mates en bucle)"
    done
    mdutil -s / 2>/dev/null | sed 's/^/  spotlight: /'
    echo "  Para excluir carpetas de codigo del indexado: Ajustes > Siri y Spotlight > Privacidad"
    echo "  (añade node_modules, build/, .git — reduce mucho el trabajo de mds_stores)" ;;
  *) echo "  target desconocido: $t" ;;
esac
done

echo "### despues"
memory_pressure 2>/dev/null | awk -F': ' '/free percentage/{print "  memoria libre: "$2}'
so3=$(vm_stat 2>/dev/null | awk '/Swapouts/{gsub(/[.]/,"",$NF); print $NF}')
if [ -n "${so2:-}" ] && [ -n "${so3:-}" ]; then
  echo "  swapouts durante la sesion: $((so3-so2))  (0 = sin paginar)"
fi
