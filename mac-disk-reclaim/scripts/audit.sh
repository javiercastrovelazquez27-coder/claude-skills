#!/usr/bin/env bash
# audit.sh — inventario de espacio recuperable en macOS.
# SOLO LEE. No borra, no modifica, no usa sudo. Seguro de correr siempre.
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

ROOTS=("$HOME/Projects" "$HOME/Proyectos" "$HOME/dev" "$HOME/code" "$HOME/src" "$HOME/repos")
[ $# -gt 0 ] && ROOTS=("$@")

hr() { printf '%s\n' "------------------------------------------------------------"; }
# tamaño legible; distingue "no existe" de "no se puede medir" (TCC/permisos)
sz() {
  [ -e "$1" ] || { echo "__MISSING__"; return; }
  local out; out=$(du -sh "$1" 2>/dev/null | cut -f1)
  [ -n "$out" ] && echo "$out" || echo "__DENIED__"
}
row() {
  local s; s=$(sz "$2")
  case "$s" in
    __MISSING__) return ;;
    __DENIED__)  printf '  %-10s %-6s %s\n' "$1" "sin-med" "$2 (permiso denegado — revisar a mano)" ;;
    *)           local nota=""
                 # SAFE de borrar no es lo mismo que seguro de borrar AHORA.
                 [ "$1" = SAFE ] && ruta_en_uso "$2" && nota="  (EN USO ahora: reclaim.sh la salta)"
                 printf '  %-10s %-6s %s%s\n' "$1" "$s" "$2" "$nota" ;;
  esac
}

ui_title "Auditoria de espacio" "solo lectura — no se borra nada"
echo "=== DISCO ==="
df -h /System/Volumes/Data | awk 'NR==1||NR==2'
hr

echo "=== SAFE: caches de herramientas (regenerables) ==="
for p in \
  "$HOME/Library/Caches/Homebrew" \
  "$HOME/Library/Caches/pip" \
  "$HOME/Library/Caches/JetBrains" \
  "$HOME/Library/Caches/ms-playwright" \
  "$HOME/Library/Caches/typescript" \
  "$HOME/Library/Caches/CocoaPods" \
  "$HOME/.npm/_cacache" \
  "$HOME/.cache/uv" \
  "$HOME/.cache/ms-playwright" \
  "$HOME/.cache/puppeteer" \
  "$HOME/.cache/giget" \
  "$HOME/.cache/huggingface" \
  "$HOME/.cache/torch" \
  "$HOME/.bun/install/cache" \
  "$HOME/Library/pnpm/store" \
  "$HOME/.gradle/caches" \
  "$HOME/.cargo/registry/cache" \
  "$HOME/.m2/repository" \
  "$HOME/go/pkg/mod" \
  "$HOME/Library/Developer/Xcode/DerivedData" \
  "$HOME/Library/Developer/Xcode/Archives" \
  "$HOME/Library/Developer/CoreSimulator/Caches" ; do
  row SAFE "$p"
done
hr

echo "=== node_modules (SAFE solo con lockfile) ==="
total_lock=0; total_nolock=0; n_lock=0; n_nolock=0
for r in "${ROOTS[@]}"; do
  [ -d "$r" ] || continue
  while IFS= read -r nm; do
    d=$(dirname "$nm")
    kb=$(du -sk "$nm" 2>/dev/null | cut -f1); kb=${kb:-0}
    if tiene_lockfile "$d"; then
      total_lock=$((total_lock+kb)); n_lock=$((n_lock+1))
    else
      total_nolock=$((total_nolock+kb)); n_nolock=$((n_nolock+1))
      echo "  ASK   sin lockfile: $d ($(( (kb + 512) / 1024 )) MB)"
    fi
  done < <(find "$r" -type d -name node_modules -prune 2>/dev/null)
done
echo "  SAFE  con lockfile:  $n_lock dirs, $(( (total_lock + 512) / 1024 )) MB"
echo "  ASK   sin lockfile:  $n_nolock dirs, $(( (total_nolock + 512) / 1024 )) MB"
hr

echo "=== Docker ==="
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  docker system df 2>/dev/null | sed 's/^/  /'
  echo "  -- volumes NOMBRADOS (ASK: pueden ser datos de BD) --"
  docker volume ls --format '{{.Name}}' 2>/dev/null \
    | grep -Ev '^[0-9a-f]{64}$' | sed 's/^/    /' || echo "    (ninguno)"
  echo "  -- volumes anonimos dangling (SAFE) --"
  docker volume ls -f dangling=true --format '{{.Name}}' 2>/dev/null \
    | grep -E '^[0-9a-f]{64}$' | wc -l | xargs echo "   " 
  echo "  -- contenedores --"
  docker ps -a --format '    {{.Names}}\t{{.Status}}' 2>/dev/null || true
else
  echo "  docker no disponible o daemon apagado — saltado"
fi
hr

echo "=== Homebrew ==="
if command -v brew >/dev/null 2>&1; then
  echo "  outdated: $(brew outdated 2>/dev/null | wc -l | tr -d ' ')"
  brew outdated 2>/dev/null | sed 's/^/    /' | head -20
else
  echo "  brew no instalado"
fi
hr

echo "=== Simuladores / Xcode ==="
if xcrun simctl help >/dev/null 2>&1; then
  echo "  unavailable: $(xcrun simctl list devices unavailable 2>/dev/null | grep -c '^ ')"
else
  echo "  simctl no disponible (Xcode.app no instalado) — nada que limpiar"
fi
row SAFE "$HOME/Library/Developer/Xcode/iOS DeviceSupport"
hr

echo "=== ASK: revisar a mano, NO borrar sin preguntar ==="
row ASK "$HOME/Downloads"
row ASK "$HOME/.Trash"
row ASK "$HOME/Library/Containers/com.docker.docker/Data/vms"
for p in "$HOME/Library/Application Support/Postgres" "$HOME/Library/Application Support/Claude"; do
  row ASK "$p"
done
hr

echo "=== TOP 15 directorios en \$HOME ==="
du -sh "$HOME"/* "$HOME"/.[a-z]* 2>/dev/null | sort -rh | head -15 | sed 's/^/  /'
hr
echo "Auditoria completa. Nada fue borrado."
