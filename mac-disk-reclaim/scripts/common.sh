#!/usr/bin/env bash
# common.sh — guardas compartidas. Se carga con `source` desde los 3 scripts.
# Si falta este fichero, los scripts deben abortar, no continuar sin protección.

# Con HOME vacio toda ruta "$HOME/x" pasa a ser "/x" — del sistema.
# Con HOME manipulado se puede inyectar. Ambas cosas fueron explotables aqui.
verificar_entorno() {
  local real
  case "${HOME:-}" in
    "")  echo "ABORTA: HOME vacio." >&2; exit 3 ;;
    /)   echo "ABORTA: HOME='/'." >&2; exit 3 ;;
    /*)  ;;
    *)   echo "ABORTA: HOME no es ruta absoluta: '$HOME'" >&2; exit 3 ;;
  esac
  [ -d "$HOME" ] || { echo "ABORTA: HOME no es un directorio: '$HOME'" >&2; exit 3; }
  case "${HOME#/}" in */*) ;; *) echo "ABORTA: HOME sospechoso: '$HOME'" >&2; exit 3 ;; esac
  real=$(dscl . -read "/Users/$(id -un)" NFSHomeDirectory 2>/dev/null | awk '{print $2}')
  if [ -n "$real" ] && [ "$real" != "$HOME" ]; then
    echo "ABORTA: HOME ('$HOME') no coincide con el del sistema ('$real')." >&2; exit 3
  fi
  # Correr como root convertiria cualquier fallo en un daño al sistema.
  [ "$(id -u)" -eq 0 ] && { echo "ABORTA: no ejecutes esto como root." >&2; exit 3; }
  return 0
}

# Nombres de app que van a AppleScript: solo letras, numeros, espacio, . _ -
# Evita que un nombre con comillas se convierta en codigo AppleScript.
nombre_app_valido() {
  case "$1" in
    *[!A-Za-z0-9\ ._-]*) echo "  BLOQUEADO (nombre de app no valido): $1"; return 1 ;;
    "") return 1 ;;
  esac
  return 0
}

# ¿Hay AL MENOS UN lockfile en el directorio? Uno por uno con [ -f ]: un `ls a b c`
# devuelve error si falta cualquiera, y eso marcaba "sin lockfile" a todo proyecto
# que no tuviera los cinco a la vez (es decir, a todos).
tiene_lockfile() {
  local l
  for l in package-lock.json npm-shrinkwrap.json yarn.lock pnpm-lock.yaml bun.lockb bun.lock; do
    [ -f "$1/$l" ] && return 0
  done
  return 1
}

# ¿Algun proceso vivo corre desde dentro de esta ruta? Mira la linea de comandos y el
# directorio de trabajo. Borrar una cache con procesos dentro (uvx, npx, un dev server)
# los rompe a medias. La foto se toma una vez y ANTES de comparar, y se compara en
# bash: un `ps | grep ruta` se encontraria a si mismo.
_EN_USO_FOTO=
ruta_en_uso() {
  [ -n "$_EN_USO_FOTO" ] || _EN_USO_FOTO="x
$(ps -Axww -o args= 2>/dev/null)
$(lsof -a -u "$(id -u)" -d cwd -Fn 2>/dev/null | sed -n 's|^n\(.*\)|\1/|p')"
  case "$_EN_USO_FOTO" in *"$1/"*) return 0 ;; esac
  return 1
}
