#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_TRIPLE="$(rustc -Vv | grep host | cut -d' ' -f2)"
BINARY_NAME="main-${TARGET_TRIPLE}"

echo "Building sidecar for target: ${TARGET_TRIPLE}"

cd "$SCRIPT_DIR"

# Activate venv
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "Error: Python venv not found at .venv/"
    echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Ensure PyInstaller is installed
if ! command -v pyinstaller &>/dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Build one-file binary
pyinstaller \
    --onefile \
    --name "${BINARY_NAME}" \
    --add-data "data:data" \
    --add-data "migrations:migrations" \
    --noconfirm \
    --clean \
    main.py

# Copy to Tauri binaries directory
DEST_DIR="${SCRIPT_DIR}/../src-tauri/binaries"
mkdir -p "$DEST_DIR"
cp "dist/${BINARY_NAME}" "${DEST_DIR}/${BINARY_NAME}"
chmod +x "${DEST_DIR}/${BINARY_NAME}"

echo "Sidecar built: src-tauri/binaries/${BINARY_NAME}"
echo "Size: $(du -h "${DEST_DIR}/${BINARY_NAME}" | cut -f1)"
