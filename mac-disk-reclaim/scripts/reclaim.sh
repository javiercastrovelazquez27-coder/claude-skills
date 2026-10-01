#!/usr/bin/env bash
# reclaim.sh — borra SOLO los targets SAFE que se nombran explicitamente.
# Sin --apply no borra nada (dry-run por defecto). Nunca usa sudo.
# Nunca toca volumenes Docker nombrados, Papelera, Downloads ni iCloud.
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

APPLY=0
TARGETS=()
for a in "$@"; do
  case "$a" in
    --apply) APPLY=1 ;;
    --help|-h) sed -n '2,4p' "$0"; echo
      echo "targets: devcaches pkgcaches node_modules xcode ide docker brew logs mlcaches all"
      echo "  (all NO incluye mlcaches: re-descarga cara, pidelo aparte)"
      echo "uso: reclaim.sh [--apply] TARGET [TARGET...]"; exit 0 ;;
    -*) echo "flag desconocida: $a" >&2; exit 2 ;;
    *) TARGETS+=("$a") ;;
  esac
done
[ ${#TARGETS[@]} -eq 0 ] && { echo "sin targets. usa --help" >&2; exit 2; }
[[ " ${TARGETS[*]} " == *" all "* ]] && \
  TARGETS=(devcaches pkgcaches node_modules xcode ide docker brew logs)

BEFORE=$(df -k /System/Volumes/Data | awk 'NR==2{print $4}')
ui_title "Recuperar espacio" "$([ $APPLY -eq 1 ] && echo "aplicando cambios" || echo "simulacion — no se borra nada")"

# borra una ruta con guardas de seguridad
nuke() {
  local p="$1"
  case "$p" in
    "$HOME"|"$HOME/"|/|""|"$HOME/Downloads"*|"$HOME/Documents"*|"$HOME/Desktop"*|"$HOME/.Trash"*|"$HOME/Library/Mobile Documents"*)
      echo "  BLOQUEADO (ruta protegida): $p"; return ;;
  esac
  [ -e "$p" ] || return
  local s; s=$(du -sh "$p" 2>/dev/null | cut -f1)
  # Tambien en simulacion: es un bloqueo, no un [dry].
  if ruta_en_uso "$p"; then echo "  EN USO   $s  $p — hay procesos corriendo desde ahi, no se toca"; return; fi
  if [ $APPLY -eq 1 ]; then rm -rf "$p" && echo "  borrado  $s  $p"
  else echo "  [dry]    $s  $p"; fi
}
# Sin eval: recibe el comando como argumentos separados. Una ruta con comillas
# o punto y coma ya no puede convertirse en un comando.
run() {
  if [ $APPLY -eq 1 ]; then "$@"
  else echo "  [dry] $*"; fi
}

# Anima solo cuando de verdad se ejecuta; en simulacion no lanza nada.
ui_spin_run() {
  local msg="$1"; shift
  if [ $APPLY -eq 1 ]; then ui_spin "$msg" "$@"
  else echo "  [dry] $*"; fi
}

# Borrado de logs viejos por ruta guardada, no por cadena interpretada.
purgar_logs() {
  local dir="$HOME/Library/Logs"
  case "$dir" in "$HOME/Library/Logs") ;; *) echo "  BLOQUEADO: ruta de logs inesperada"; return ;; esac
  [ -d "$dir" ] || { echo "  no existe $dir"; return; }
  if [ $APPLY -eq 1 ]; then
    find "$dir" -type f -mtime +30 -delete 2>/dev/null
    echo "  purgados logs de mas de 30 dias en ~/Library/Logs"
  else echo "  [dry] borraria logs >30d en $dir"; fi
}

for t in "${TARGETS[@]}"; do
ui_step "$C_BOLD$t$C_RST"
case "$t" in
  devcaches)
    for p in "$HOME/Library/Caches/pip" "$HOME/Library/Caches/JetBrains" \
             "$HOME/Library/Caches/ms-playwright" "$HOME/Library/Caches/typescript" \
             "$HOME/.cache/uv" "$HOME/.cache/ms-playwright" "$HOME/.cache/puppeteer" \
             "$HOME/.cache/giget"; do nuke "$p"; done ;;
  pkgcaches)
    # Por comando, no por rm: npm y pnpm saben que parte de su cache sigue referenciada.
    # Sin redirigir la salida: con >/dev/null el paso desaparecia del informe y del dry-run.
    if command -v npm >/dev/null 2>&1; then
      npm_sz=$(du -sh "$HOME/.npm/_cacache" 2>/dev/null | cut -f1)
      echo "  npm      ${npm_sz:-0B}  $HOME/.npm/_cacache"
      ui_spin_run "npm cache clean" npm cache clean --force
    fi
    if command -v pnpm >/dev/null 2>&1; then
      ps_dir=$(pnpm store path 2>/dev/null)
      if [ -n "$ps_dir" ] && [ -d "$ps_dir" ]; then
        echo "  pnpm     $(du -sh "$ps_dir" 2>/dev/null | cut -f1)  $ps_dir (prune: solo lo que ningun proyecto referencia)"
        ui_spin_run "pnpm store prune" pnpm store prune
      fi
    fi
    for p in "$HOME/.bun/install/cache" "$HOME/.gradle/caches" \
             "$HOME/.cargo/registry/cache" "$HOME/.m2/repository" \
             "$HOME/go/pkg/mod"; do nuke "$p"; done ;;
  node_modules)
    # SOLO donde exista lockfile hermano — sin lockfile no es reproducible
    for r in "$HOME/Projects" "$HOME/Proyectos" "$HOME/dev" "$HOME/code" "$HOME/src"; do
      [ -d "$r" ] || continue
      while IFS= read -r nm; do
        d=$(dirname "$nm")
        if tiene_lockfile "$d"; then nuke "$nm"
        else echo "  SKIP (sin lockfile): $d"; fi
      done < <(find "$r" -type d -name node_modules -prune 2>/dev/null)
    done ;;
  xcode)
    nuke "$HOME/Library/Developer/Xcode/DerivedData"
    nuke "$HOME/Library/Developer/CoreSimulator/Caches"
    xcrun simctl help >/dev/null 2>&1 && run xcrun simctl delete unavailable \
      || echo "  simctl no disponible — saltado" ;;
  docker)
    if docker info >/dev/null 2>&1; then
      ui_spin_run "docker: build cache" docker builder prune -af
      # respeta contenedores parados, pero una imagen construida en local cuyo
      # contenedor ya no exista NO se puede recuperar de ningun registry
      echo "  AVISO: borra imagenes sin contenedor, incluidas builds locales."
      ui_spin_run "docker: imagenes sin contenedor" docker image prune -a -f
      # SOLO volumenes anonimos: los nombrados pueden ser datos de BD
      docker volume ls -f dangling=true --format '{{.Name}}' 2>/dev/null \
        | grep -E '^[0-9a-f]{64}$' | while read -r v; do run docker volume rm "$v"; done
      echo "  NOTA: volumenes nombrados conservados a proposito (tier ASK)."
    else echo "  docker apagado — saltado"; fi ;;
  brew)
    command -v brew >/dev/null 2>&1 \
      && { ui_spin_run "brew cleanup" brew cleanup -s --prune=all; ui_spin_run "brew autoremove" brew autoremove; } \
      || echo "  brew no instalado" ;;
  mlcaches)
    # SAFE pero la re-descarga es de GB y lenta — avisa antes de correrlo
    echo "  AVISO: re-descargar estos modelos puede tardar mucho."
    nuke "$HOME/.cache/huggingface"; nuke "$HOME/.cache/torch" ;;
  ide)
    nuke "$HOME/Library/Application Support/Code/CachedExtensionVSIXs"
    nuke "$HOME/Library/Caches/JetBrains"
    nuke "$HOME/Library/Caches/CocoaPods"
    # NO: ~/.vscode/extensions ni Code/User (extensiones y settings reales)
    ;;
  logs)
    purgar_logs ;;
  *) echo "  target desconocido: $t" ;;
esac
done

AFTER=$(df -k /System/Volumes/Data | awk 'NR==2{print $4}')
ui_end
if [ $APPLY -eq 1 ]; then
  ui_count_gb "$(( (AFTER-BEFORE)/1048576 ))" "liberado  ·  $((AFTER/1048576)) GB libres"
else
  ui_step "simulacion terminada — sin cambios. $((AFTER/1048576)) GB libres"
fi
