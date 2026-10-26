#!/usr/bin/env bash
# Instalador de vd0 para Linux y macOS.
#   Usuario normal:  ./install.sh        -> ~/.local/share/vd0  + ~/.local/bin/vd0
#   Administrador:   sudo ./install.sh   -> /opt/vd0            + /usr/local/bin/vd0 (todos los usuarios)
#
# Desde GitHub (sin clonar):
#   curl -fsSL https://raw.githubusercontent.com/sam9neREYES/vd0/main/install.sh | bash
set -euo pipefail

REPO_URL="https://github.com/sam9neREYES/vd0.git"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"

if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
  SOURCE="$SCRIPT_DIR"
else
  SOURCE="git+${REPO_URL}"
fi

if [ "$(id -u)" -eq 0 ]; then
  PREFIX="/opt/vd0"
  BIN_DIR="/usr/local/bin"
else
  PREFIX="${HOME}/.local/share/vd0"
  BIN_DIR="${HOME}/.local/bin"
fi

say() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

# 1) Python 3.8+
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
[ -n "$PY" ] || die "Se requiere Python 3.8 o superior. Instalalo (apt install python3 / dnf install python3 / brew install python)."

# 2) Entorno virtual propio (evita el error 'externally-managed-environment')
say "Creando entorno en ${PREFIX}"
mkdir -p "$PREFIX" "$BIN_DIR"
if ! "$PY" -m venv "$PREFIX/venv" 2>/dev/null; then
  die "No se pudo crear el entorno virtual. En Debian/Ubuntu ejecuta: sudo apt install python3-venv"
fi

# 3) Instalar vd0 y sus dependencias (yt-dlp + ffmpeg incluido)
say "Instalando vd0 y dependencias"
"$PREFIX/venv/bin/python" -m pip install --quiet --upgrade pip
"$PREFIX/venv/bin/python" -m pip install --quiet --upgrade "$SOURCE"

# 4) Comando global
ln -sf "$PREFIX/venv/bin/vd0" "$BIN_DIR/vd0"
say "Comando instalado en ${BIN_DIR}/vd0"

# 5) PATH (solo instalaciones de usuario)
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    if [ "$(id -u)" -ne 0 ]; then
      LINE="export PATH=\"$BIN_DIR:\$PATH\""
      for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        if [ -f "$rc" ] && ! grep -qs "$BIN_DIR" "$rc"; then
          printf '\n# vd0\n%s\n' "$LINE" >> "$rc"
        fi
      done
      say "Se agrego ${BIN_DIR} al PATH. Abre una terminal nueva o ejecuta: ${LINE}"
    fi
    ;;
esac

say "Listo. Ejecuta:  vd0"
