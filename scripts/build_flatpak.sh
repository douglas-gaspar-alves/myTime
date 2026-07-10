#!/bin/bash
# Build myTime Flatpak
# Dependencies: flatpak, flatpak-builder
# Usage: ./scripts/build_flatpak.sh

set -e

APP_ID="io.github.mytime"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MANIFEST="$PROJECT_DIR/flatpak/$APP_ID.yml"
BUILD_DIR="$PROJECT_DIR/build-flatpak"
BUNDLE="$PROJECT_DIR/$APP_ID.flatpak"

echo "==> Verifying Flatpak..."
flatpak --version

echo "==> Installing flatpak-builder (if needed)..."
flatpak install -y flathub org.flatpak.Builder 2>/dev/null || true

echo "==> Building Flatpak..."
cd "$PROJECT_DIR"

# Use host flatpak-builder if available, otherwise use flatpak version
if command -v flatpak-builder &>/dev/null; then
    flatpak-builder \
        --force-clean \
        --ccache \
        --install-deps-from=flathub \
        --build-options='--share=network' \
        "$BUILD_DIR" "$MANIFEST"
else
    flatpak run org.flatpak.Builder \
        --force-clean \
        --ccache \
        --install-deps-from=flathub \
        "$BUILD_DIR" "$MANIFEST"
fi

echo "==> Creating bundle..."
flatpak build-bundle "$BUILD_DIR" "$BUNDLE" "$APP_ID"

echo "==> Installing locally..."
flatpak install --user -y "$BUNDLE" 2>/dev/null || flatpak install -y "$BUNDLE"

echo ""
echo "========================================="
echo "  myTime instalado via Flatpak!"
echo "  Busque por 'myTime' no menu de apps"
echo "  Ou execute: flatpak run $APP_ID"
echo "========================================="
echo ""
echo "Para desinstalar: flatpak uninstall $APP_ID"
echo "Bundle: $BUNDLE"