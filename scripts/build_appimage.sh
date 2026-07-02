#!/bin/bash
# Build myTime AppImage
# Dependencies: pyinstaller, appimagetool
# Usage: ./scripts/build_appimage.sh

set -e

APP_NAME="myTime"
SRC_DIR="src"
DIST_DIR="dist"
BUILD_DIR="build_appimage"

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

cat > "$APPDIR/usr/share/applications/$APP_NAME.desktop" << EOF
[Desktop Entry]
Name=myTime
Comment=Gerenciador inteligente de Pomodoro e Jornadas
Exec=$APP_NAME
Icon=$APP_NAME
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

echo "==> Generating AppImage..."
if command -v appimagetool &>/dev/null; then
    ARCH=x86_64 appimagetool "$APPDIR" "$DIST_DIR/$APP_NAME-x86_64.AppImage"
    echo "==> AppImage created: $DIST_DIR/$APP_NAME-x86_64.AppImage"
else
    echo "⚠ appimagetool not found. AppDir is ready at $APPDIR"
    echo "  Install appimagetool: https://github.com/AppImage/AppImageKit"
fi

echo "==> Build complete!"
EOF