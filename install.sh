#!/usr/bin/env bash
set -e

# ============================================================
# Observo Installer
# Usage: curl -sL https://raw.githubusercontent.com/PranavJa1n/Observo/main/install.sh | bash
# ============================================================

REPO_URL="https://github.com/PranavJa1n/Observo.git"
INSTALL_DIR="$HOME/.observo-src"
BIN_DIR="/usr/local/bin"
BINARY_NAME="observo"
WRAPPER="$BIN_DIR/$BINARY_NAME"

BOLD=$(tput bold 2>/dev/null || echo "")
RESET=$(tput sgr0 2>/dev/null || echo "")
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m"

info()    { echo -e "  ${GREEN}✓${NC} $1"; }
warn()    { echo -e "  ${YELLOW}!${NC} $1"; }
error()   { echo -e "  ${RED}✗${NC} $1"; exit 1; }
section() { echo -e "\n${BOLD}$1${RESET}"; }

echo ""
echo -e "${BOLD}  Observo Installer${RESET}"
echo "  Intelligent log analysis with AI-powered root cause detection"
echo "  ─────────────────────────────────────────────────────────────"

# ── 1. Check OS ────────────────────────────────────────────
section "Checking environment..."

OS="$(uname -s)"
case "$OS" in
  Linux*)             PLATFORM="linux" ;;
  Darwin*)            PLATFORM="macos" ;;
  CYGWIN*|MINGW*|MSYS*) PLATFORM="windows" ;;
  *)                  error "Unsupported OS: $OS" ;;
esac
info "Platform: $PLATFORM"

# ── 2. Check Go ────────────────────────────────────────────
if ! command -v go &>/dev/null; then
  error "Go is not installed. Please install Go 1.21+ from https://go.dev/dl/"
fi

GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
GO_MAJOR=$(echo "$GO_VERSION" | cut -d. -f1)
GO_MINOR=$(echo "$GO_VERSION" | cut -d. -f2)

if [ "$GO_MAJOR" -lt 1 ] || { [ "$GO_MAJOR" -eq 1 ] && [ "$GO_MINOR" -lt 21 ]; }; then
  error "Go 1.21+ required, found go$GO_VERSION. Upgrade at https://go.dev/dl/"
fi
info "Go $GO_VERSION"

# ── 3. Check Python ────────────────────────────────────────
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
  PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
  PYTHON_BIN="python"
else
  error "Python is not installed. Please install Python 3.9+ from https://python.org"
fi

PY_VERSION=$($PYTHON_BIN --version 2>&1 | awk '{print $2}')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
  error "Python 3.9+ required, found $PY_VERSION."
fi
info "Python $PY_VERSION"

# ── 4. Check git ───────────────────────────────────────────
if ! command -v git &>/dev/null; then
  error "git is not installed. Install it with: sudo apt install git  (or brew install git)"
fi
info "git $(git --version | awk '{print $3}')"

# ── 5. Clone or update repo ────────────────────────────────
section "Downloading Observo..."

if [ -d "$INSTALL_DIR/.git" ]; then
  warn "Existing install found at $INSTALL_DIR — updating..."
  git -C "$INSTALL_DIR" pull --ff-only origin main 2>/dev/null || \
    git -C "$INSTALL_DIR" fetch --all && git -C "$INSTALL_DIR" reset --hard origin/main
  info "Updated to latest"
else
  git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
  info "Cloned to $INSTALL_DIR"
fi

# ── 6. Install Python dependencies ────────────────────────
section "Installing Python dependencies..."

PIP_BIN="pip3"
if ! command -v pip3 &>/dev/null; then
  PIP_BIN="pip"
fi

$PIP_BIN install -q -r "$INSTALL_DIR/requirements.txt"
info "Python packages installed"

# ── 7. Build Go binary ─────────────────────────────────────
section "Building Observo binary..."

cd "$INSTALL_DIR"
go build -o "$INSTALL_DIR/observo-bin" ./cmd/main.go

# On Windows, Go appends .exe
if [ "$PLATFORM" = "windows" ] && [ -f "$INSTALL_DIR/observo-bin.exe" ]; then
  mv "$INSTALL_DIR/observo-bin.exe" "$INSTALL_DIR/observo-bin"
fi
info "Binary built"

# ── 8. Install wrapper script ──────────────────────────────
section "Installing to system PATH..."

if [ "$PLATFORM" = "windows" ]; then
  # On Windows (Git Bash) — install to ~/.local/bin, no sudo needed
  LOCAL_BIN="$HOME/.local/bin"
  mkdir -p "$LOCAL_BIN"
  WRAPPER="$LOCAL_BIN/$BINARY_NAME"

  cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
export OBSERVO_HOME="$INSTALL_DIR"
exec "$INSTALL_DIR/observo-bin" "\$@"
EOF
  chmod +x "$WRAPPER"
  info "Installed to $WRAPPER"

  # Check if ~/.local/bin is on PATH
  if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
    warn "$LOCAL_BIN is not in your PATH."
    warn "Add this line to your ~/.bashrc or ~/.bash_profile:"
    warn "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  fi

elif [ -w "$BIN_DIR" ] || sudo -n true 2>/dev/null; then
  # Linux/macOS with write access or sudo
  NEEDS_SUDO=true
  if [ -w "$BIN_DIR" ]; then
    NEEDS_SUDO=false
  fi

  WRAPPER_CONTENT="#!/usr/bin/env bash
export OBSERVO_HOME=\"$INSTALL_DIR\"
exec \"$INSTALL_DIR/observo-bin\" \"\$@\""

  if [ "$NEEDS_SUDO" = true ]; then
    echo "$WRAPPER_CONTENT" | sudo tee "$WRAPPER" > /dev/null
    sudo chmod +x "$WRAPPER"
  else
    echo "$WRAPPER_CONTENT" > "$WRAPPER"
    chmod +x "$WRAPPER"
  fi
  info "Installed to $WRAPPER"

else
  # Linux/macOS — fall back to ~/.local/bin
  LOCAL_BIN="$HOME/.local/bin"
  mkdir -p "$LOCAL_BIN"
  WRAPPER="$LOCAL_BIN/$BINARY_NAME"

  cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
export OBSERVO_HOME="$INSTALL_DIR"
exec "$INSTALL_DIR/observo-bin" "\$@"
EOF
  chmod +x "$WRAPPER"

  warn "Could not write to $BIN_DIR — installed to $LOCAL_BIN instead."
  warn "Add this to your shell profile if not already present:"
  warn "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# ── 9. Verify installation ─────────────────────────────────
section "Verifying..."

if command -v observo &>/dev/null; then
  info "observo is available on PATH"
elif [ -x "$HOME/.local/bin/observo" ]; then
  warn "'observo' not yet on PATH — restart your terminal or run:"
  echo "     source ~/.bashrc  (or ~/.zshrc)"
fi

# ── Done ───────────────────────────────────────────────────
echo ""
echo -e "  ${GREEN}${BOLD}Installation complete!${RESET}"
echo ""
echo "  Next steps:"
echo "    1.  observo init     — configure log path and API key"
echo "    2.  observo start    — start monitoring and open dashboard"
echo "    3.  open http://localhost:6969 in your browser"
echo ""
echo "  Installed to: $INSTALL_DIR"
echo "  Docs:         https://github.com/PranavJa1n/Observo"
echo ""