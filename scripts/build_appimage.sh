#!/bin/bash
# Build myTime AppImage
# Dependencies: pyinstaller, appimagetool
# Usage: ./scripts/build_appimage.sh

set -e

APP_NAME="myTime"
SRC_DIR="src"
DIST_DIR="dist"
BUILD_DIR="build_appimage"

# === Check dependencies ===
echo "==> Checking dependencies..."

# Check Python version (requires 3.11+)
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo "ERROR: Python 3.11+ required, found $PYTHON_VERSION"
    exit 1
fi
echo "  Python $PYTHON_VERSION OK"

# Check PyInstaller
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "  PyInstaller not found. Installing via pip..."
    pip3 install --user PyInstaller || pip3 install PyInstaller
    # Ensure ~/.local/bin is in PATH for PyInstaller
    export PATH="$HOME/.local/bin:$PATH"
fi
echo "  PyInstaller OK"

# Check appimagetool
if ! command -v appimagetool &>/dev/null; then
    echo "  appimagetool not found."
    echo "  Downloading appimagetool..."
    APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    mkdir -p "$HOME/.local/bin"
    wget -q "$APPIMAGETOOL_URL" -O "$HOME/.local/bin/appimagetool"
    chmod +x "$HOME/.local/bin/appimagetool"
    export PATH="$HOME/.local/bin:$PATH"
fi
echo "  appimagetool OK"

echo "==> Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$DIST_DIR/$APP_NAME" 2>/dev/null || true

echo "==> Building with PyInstaller..."
python3 -m PyInstaller \
    --name="$APP_NAME" \
    --windowed \
    --onefile \
    --add-data="src/myTime/locales:locales" \
    --hidden-import="PySide6.QtCore" \
    --hidden-import="PySide6.QtGui" \
    --hidden-import="PySide6.QtWidgets" \
    --distpath="$DIST_DIR" \
    --workpath="$BUILD_DIR" \
    --specpath="$BUILD_DIR" \
    "src/myTime/__main__.py"

echo "==> Creating AppDir structure for AppImage..."
APPDIR="$BUILD_DIR/$APP_NAME.AppDir"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

cp "$DIST_DIR/$APP_NAME" "$APPDIR/usr/bin/"

cat > "$APPDIR/usr/share/applications/$APP_NAME.desktop" << 'EOF'
[Desktop Entry]
Name=myTime
Comment=Gerenciador inteligente de Pomodoro e Jornadas
Exec=myTime
Icon=myTime
Terminal=false
Type=Application
Categories=Utility;Office;
StartupNotify=true
X-GNOME-Autostart-enabled=false
EOF

cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/myTime" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Copy icon
cp "src/myTime/data/icons/myTime.svg" "$APPDIR/usr/share/icons/hicolor/256x256/apps/myTime.svg"
# Also copy as .png if we can generate it
if command -v rsvg-convert &>/dev/null; then
    rsvg-convert -w 256 -h 256 "src/myTime/data/icons/myTime.svg" -o "$APPDIR/usr/share/icons/hicolor/256x256/apps/myTime.png"
elif command -v convert &>/dev/null; then
    convert -background none -size 256x256 "src/myTime/data/icons/myTime.svg" "$APPDIR/usr/share/icons/hicolor/256x256/apps/myTime.png"
fi

echo "==> Generating AppImage..."
ARCH=x86_64 appimagetool "$APPDIR" "$DIST_DIR/$APP_NAME-x86_64.AppImage"
echo "==> AppImage created: $DIST_DIR/$APP_NAME-x86_64.AppImage"

echo "==> Build complete!"