#!/bin/bash
# Controlla e installa quello che serve al kit di montaggio. Si lancia dalla cartella del kit: ./installa.sh
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
manca=0

ok()   { echo "  ok    $1"; }
no()   { echo "  MANCA $1"; manca=1; }

echo "Kit in $KIT"
[ "$(uname)" = "Darwin" ] || { echo "Il kit funziona solo su macOS."; exit 1; }

presente() { command -v "$1" >/dev/null 2>&1 || [ -x "$HOME/.local/bin/$1" ]; }
# come installarlo senza Homebrew
a_mano() {
  case "$1" in
    uv) echo "curl -LsSf https://astral.sh/uv/install.sh | sh" ;;
    node) echo "installer da https://nodejs.org (versione LTS)" ;;
    ffmpeg) echo "ffmpeg e ffprobe statici in ~/.local/bin, vedi INSTALLA.md" ;;
  esac
}

risposta=""
mancanti=""
for p in ffmpeg uv node; do presente "$p" || mancanti="$mancanti $p"; done
if [ -n "$mancanti" ] && command -v brew >/dev/null 2>&1; then
  read -r -p "Mancano:$mancanti. Li installo con Homebrew? [s/N] " risposta
fi
installa() { [ "$risposta" = "s" ] || [ "$risposta" = "S" ]; }

echo
echo "Programmi"
for p in ffmpeg uv node; do
  if presente "$p"; then
    ok "$p"
  elif installa; then
    brew install "$p" && ok "$p (installato)" || no "$p"
  elif command -v brew >/dev/null 2>&1; then
    no "$p (brew install $p)"
  else
    no "$p ($(a_mano "$p"))"
  fi
done

FF="$(command -v ffmpeg || echo "$HOME/.local/bin/ffmpeg")"
if [ -x "$FF" ]; then
  filtri="$("$FF" -hide_banner -filters 2>/dev/null)"
  for f in zscale subtitles; do
    if echo "$filtri" | grep -q " $f "; then ok "ffmpeg con il filtro $f"
    else no "ffmpeg senza il filtro $f: serve un ffmpeg completo, vedi INSTALLA.md"; fi
  done
  command -v ffprobe >/dev/null 2>&1 || [ -x "$HOME/.local/bin/ffprobe" ] && ok "ffprobe" || no "ffprobe"
fi

if command -v node >/dev/null 2>&1; then
  v="$(node -v | sed 's/^v//; s/\..*//')"
  [ "$v" -ge 18 ] && ok "node $(node -v)" || no "node 18 o superiore (ora $(node -v))"
fi
command -v python3 >/dev/null 2>&1 && ok "python3 $(python3 --version 2>&1 | cut -d' ' -f2)" || no "python3 (xcode-select --install)"

echo
echo "App"
if [ -d /Applications/CapCut.app ]; then
  vc="$(defaults read /Applications/CapCut.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null)"
  if [ "$vc" = "9.5.0" ]; then ok "CapCut $vc"
  else echo "  nota  CapCut $vc: gli strumenti sono collaudati su 9.5.0, il primo progetto va controllato (INSTALLA.md)"; fi
else
  echo "  nota  CapCut non c'è: serve solo per i metodi CapCut e ibrido"
fi
[ -d "/Applications/Google Chrome.app" ] && ok "Google Chrome" || echo "  nota  Google Chrome non c'è: serve a stock.py per cercare su Pexels"
command -v claude >/dev/null 2>&1 && ok "Claude Code" || no "Claude Code (https://claude.com/claude-code)"

echo
echo "Remotion"
if command -v npm >/dev/null 2>&1; then
  if [ -d "$KIT/_REMOTION/node_modules" ]; then ok "dipendenze già installate"
  else (cd "$KIT/_REMOTION" && npm ci --loglevel=error) && ok "dipendenze installate" || no "npm ci in _REMOTION"; fi
  (cd "$KIT/_REMOTION" && npx tsc --noEmit) && ok "controllo dei tipi" || no "controllo dei tipi in _REMOTION"
fi

echo
echo "Chiavi"
if [ ! -f "$KIT/.env" ]; then
  cp "$KIT/.env.esempio" "$KIT/.env"
  echo "  creato .env: apri $KIT/.env e incolla la chiave fal dopo FAL_KEY="
  manca=1
elif grep -q '^FAL_KEY=..*' "$KIT/.env"; then ok "FAL_KEY nel .env"
else no "FAL_KEY vuota nel .env"; fi

echo
mkdir -p "$KIT/CLIENTI"
if [ "$manca" = 0 ]; then
  echo "Tutto pronto. Apri Claude Code in questa cartella (cd \"$KIT\" && claude) e scrivi /editing."
else
  echo "Sistema le righe MANCA e rilancia ./installa.sh"
fi
