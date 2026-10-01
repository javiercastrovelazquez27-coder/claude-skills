#!/usr/bin/env bash
# ui.sh — presentacion en terminal. Sin efectos si la salida no es un TTY.
# Regla: la animacion nunca cambia lo que se hace, solo como se ve.

# Se anula sola al redirigir a fichero/pipe, con NO_COLOR, o en TERM=dumb.
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-dumb}" != "dumb" ]; then
  UI_TTY=1
  C_DIM=$'\033[2m'; C_RST=$'\033[0m'; C_ACC=$'\033[38;5;110m'
  C_OK=$'\033[38;5;108m'; C_WARN=$'\033[38;5;179m'; C_ERR=$'\033[38;5;167m'
  C_BOLD=$'\033[1m'; HIDE=$'\033[?25l'; SHOW=$'\033[?25h'; CLR=$'\033[2K\r'
else
  UI_TTY=0
  C_DIM=; C_RST=; C_ACC=; C_OK=; C_WARN=; C_ERR=; C_BOLD=; HIDE=; SHOW=; CLR=
fi

if [ "$UI_TTY" = 1 ]; then UI_RULE="────────────────────────────────────────────"
else UI_RULE="--------------------------------------------"; fi
ui_cleanup(){ [ "$UI_TTY" = 1 ] && printf '%s' "$SHOW"; return 0; }
trap ui_cleanup EXIT INT TERM

# Cabecera: filete fino, sin cajas pesadas.
ui_title() {
  printf '\n%s%s%s\n' "$C_BOLD" "$1" "$C_RST"
  [ -n "${2:-}" ] && printf '%s%s%s\n' "$C_DIM" "$2" "$C_RST"
  printf '%s%s%s\n' "$C_DIM" "$UI_RULE" "$C_RST"
}
ui_step(){ printf '%s│%s %s\n' "$C_DIM" "$C_RST" "$1"; }
ui_ok(){   printf '%s│%s %s✓%s %s\n' "$C_DIM" "$C_RST" "$C_OK" "$C_RST" "$1"; }
ui_warn(){ printf '%s│%s %s!%s %s\n' "$C_DIM" "$C_RST" "$C_WARN" "$C_RST" "$1"; }
ui_err(){  printf '%s│%s %s×%s %s\n' "$C_DIM" "$C_RST" "$C_ERR" "$C_RST" "$1"; }
ui_end(){  printf '%s%s%s\n' "$C_DIM" "$UI_RULE" "$C_RST"; }

# Spinner braille: gira mientras corre un comando en segundo plano.
# Uso: ui_spin "mensaje" comando args...
ui_spin() {
  local msg="$1"; shift
  local out rc
  out=$(mktemp "${TMPDIR:-/tmp}/uispin.XXXXXX") || { "$@"; return $?; }

  if [ "$UI_TTY" = 0 ]; then
    "$@" >"$out" 2>&1; rc=$?
    [ $rc -eq 0 ] && echo "  $msg" || echo "  $msg (fallo)"
    sed 's/^/    /' "$out"; rm -f "$out"; return $rc
  fi

  # La salida del comando va a fichero: si se imprimiera ahora romperia la
  # animacion en su sitio. Se muestra despues, ya ordenada.
  local frames='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏' i=0 pid
  "$@" >"$out" 2>&1 & pid=$!
  printf '%s' "$HIDE"
  while kill -0 "$pid" 2>/dev/null; do
    i=$(( (i+1) % 10 ))
    printf '%s%s│%s %s%s%s %s' "$CLR" "$C_DIM" "$C_RST" "$C_ACC" "${frames:$i:1}" "$C_RST" "$msg"
    sleep 0.08
  done
  wait "$pid"; rc=$?
  printf '%s%s' "$CLR" "$SHOW"
  [ $rc -eq 0 ] && ui_ok "$msg" || ui_err "$msg"
  # en exito, resumen atenuado; en fallo, todo (hay que poder diagnosticar)
  if [ $rc -eq 0 ]; then
    [ -s "$out" ] && sed 's/^/    /' "$out" | tail -3 | while IFS= read -r l; do
      printf '%s%s%s\n' "$C_DIM" "$l" "$C_RST"; done
  else
    sed 's/^/    /' "$out"
  fi
  rm -f "$out"
  return $rc
}

# Barra de progreso discreta. ui_bar actual total "etiqueta"
ui_bar() {
  local cur="$1" tot="$2" lab="${3:-}" w=28
  [ "$tot" -le 0 ] 2>/dev/null && return
  local pct=$(( cur * 100 / tot )) fill=$(( cur * w / tot )) i bar=
  for ((i=0;i<w;i++)); do
    if [ "$i" -lt "$fill" ]; then bar="${bar}▰"; else bar="${bar}▱"; fi
  done
  if [ "$UI_TTY" = 1 ]; then
    printf '%s%s│%s %s%s%s %3d%%  %s' "$CLR" "$C_DIM" "$C_RST" "$C_ACC" "$bar" "$C_RST" "$pct" "$lab"
    [ "$cur" -ge "$tot" ] && printf '\n'
  else
    [ "$cur" -ge "$tot" ] && printf '  [%d%%] %s\n' "$pct" "$lab"
  fi
}

# Cuenta ascendente de GB liberados. Puro adorno; el numero final es el real.
ui_count_gb() {
  local target="$1" lab="${2:-liberado}"
  if [ "$UI_TTY" = 0 ]; then printf '  %s: %s GB\n' "$lab" "$target"; return; fi
  local steps=14 i v
  for ((i=1;i<=steps;i++)); do
    v=$(printf '%.1f' "$(echo "$target $i $steps" | awk '{print $1*$2/$3}')")
    printf '%s%s│%s %s%s GB%s %s' "$CLR" "$C_DIM" "$C_RST" "$C_BOLD$C_ACC" "$v" "$C_RST" "$lab"
    sleep 0.03
  done
  printf '\n'
}
