#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BIN="$ROOT/bin"
mkdir -p "$BIN"

MF6_VERSION="6.7.0"
MF6_RELEASE_BASE="https://github.com/MODFLOW-ORG/modflow6/releases/download/${MF6_VERSION}"

fail() {
  echo "ERROR: $*" >&2
  exit 44
}

ensure_command() {
  command -v "$1" >/dev/null 2>&1 || fail "'$1' is required but not found in PATH"
}

ensure_mf6() {
  if [ -n "${MF6_BIN:-}" ]; then
    [ -x "$MF6_BIN" ] || fail "MF6_BIN is set but not executable: $MF6_BIN"
    printf '%s\n' "$MF6_BIN"
    return
  fi

  local OS ARCH asset target executable_name
  OS="$(uname -s)"
  ARCH="$(uname -m)"
  executable_name="mf6"

  case "$OS" in
    Darwin)
      case "$ARCH" in
        arm64|aarch64)
          asset="mf6.7.0_macarm.zip"
          target="$BIN/mf6.macos-arm64"
          ;;
        *)
          fail "Unsupported macOS architecture: $ARCH (need Apple Silicon arm64)"
          ;;
      esac
      ;;
    Linux)
      case "$ARCH" in
        x86_64|amd64)
          asset="mf6.7.0_linux.zip"
          target="$BIN/mf6.linux-x86_64"
          ;;
        *)
          fail "Unsupported Linux architecture: $ARCH"
          ;;
      esac
      ;;
    MINGW*|MSYS*|CYGWIN*)
      fail "Use start.bat on Windows x64 (POSIX shell path not supported here)."
      ;;
    *)
      fail "Unsupported OS: $OS/$ARCH"
      ;;
  esac

  if [ ! -x "$target" ]; then
    ensure_command curl
    ensure_command unzip

    local url tmp found
    url="${MF6_RELEASE_BASE}/${asset}"
    tmp="$(mktemp -d)"
    trap 'rm -rf "$tmp"' EXIT

    echo "Downloading USGS MODFLOW ${MF6_VERSION}: $asset" >&2
    echo "URL: $url" >&2
    curl -L --fail --show-error -o "$tmp/mf6.zip" "$url" || fail "Download failed: $url"
    mkdir -p "$tmp/out"
    unzip -q "$tmp/mf6.zip" -d "$tmp/out" || fail "Failed to extract $asset"

    found="$(find "$tmp/out" -type f -name "$executable_name" -print | sed -n '1p')"
    [ -n "$found" ] || fail "$executable_name not found in $asset"

    cp "$found" "$target"
    chmod +x "$target"

    rm -rf "$tmp"
    trap - EXIT
  fi

  printf '%s\n' "$target"
}

pick="$(ensure_mf6)"
"$pick" -v >/dev/null || fail "MODFLOW executable failed version check: $pick"
export MF6_BIN="$pick"
export PORT="${PORT:-18888}"

if command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON="python"
else
  fail "Python 3 was not found in PATH"
fi

echo "UNDERGROUND Workbench -> http://127.0.0.1:${PORT}" >&2
echo "MF6: $MF6_BIN" >&2
cd "$ROOT"
exec "$PYTHON" "$ROOT/api_server.py"
