#!/bin/bash
# Install myTime on the system
# Usage: ./scripts/install.sh [--flatpak] [--yes]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Parse flags
FLATPAK=false
YES=false
for arg in "$@"; do
    case $arg in
        --flatpak) FLATPAK=true ;;
        --yes) YES=true ;;
        --no-deps) SKIP_DEPS=true ;;
        -h|--help)
            echo "Usage: $0 [--flatpak] [--yes] [--no-deps]"
            echo "  --flatpak      Install via Flatpak (build from source)"
            echo "  --yes          Non-interactive mode"
            echo "  --no-deps      Skip automatic system dependency installation (default: auto-install)"
            exit 0
            ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

# === Detect package manager ===
detect_pkg_manager() {
    if command -v apt &>/dev/null; then
        echo "apt"
    elif command -v pacman &>/dev/null; then
        echo "pacman"
    elif command -v dnf &>/dev/null; then
        echo "dnf"
    else
        echo "unknown"
    fi
}

install_packages() {
    local mgr=$(detect_pkg_manager)
    case "$mgr" in
        apt) sudo apt update && sudo apt install -y "$@" ;;
        pacman) sudo pacman -S --needed --noconfirm "$@" ;;
        dnf) sudo dnf install -y "$@" ;;
        *) return 1 ;;
    esac
}

# === Check Python/pip ===
check_python() {
    if ! command -v python3 &>/dev/null; then
        echo "ERROR: python3 não encontrado!"
        echo "  Instale com: sudo apt install python3 python3-pip"
        echo "  Ou:          sudo pacman -S python python-pip"
        echo "  Ou:          sudo dnf install python3 python3-pip"
        exit 1
    fi
    if ! command -v pip3 &>/dev/null; then
        echo "ERROR: pip3 não encontrado!"
        echo "  Instale com: sudo apt install python3-pip"
        exit 1
    fi
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"; then
        local ver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        echo "ERROR: Python $ver encontrado, requer >= 3.11"
        exit 1
    fi
    echo "==> Python $(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')") OK"
}

# === Install system dependencies automatically ===
install_system_deps() {
    local missing=()

    for cmd in notify-send rsvg-convert gtk-update-icon-cache update-desktop-database xdg-open; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done

    # Check libxcb-cursor (Qt6 xcb plugin dependency)
    if ! ldconfig -p 2>/dev/null | grep -q libxcb-cursor; then
        missing+=("libxcb-cursor0")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        echo "==> Instalando dependências de sistema..."
        local mgr=$(detect_pkg_manager)
        case "$mgr" in
            apt)
                install_packages libnotify-bin librsvg2-bin gtk-update-icon-cache desktop-file-utils xdg-utils libxcb-cursor0
                ;;
            pacman)
                install_packages libnotify librsvg gtk-update-icon-cache desktop-file-utils xdg-utils libxcb-cursor
                ;;
            dnf)
                install_packages libnotify librsvg2-tools gtk-update-icon-cache desktop-file-utils xdg-utils libxcb-cursor
                ;;
            *)
                echo "  AVISO: Não foi possível instalar automaticamente."
                echo "  Instale manualmente:"
                echo "    Debian/Ubuntu: sudo apt install libnotify-bin librsvg2-bin gtk-update-icon-cache desktop-file-utils xdg-utils libxcb-cursor0"
                echo "    Arch:          sudo pacman -S libnotify librsvg gtk-update-icon-cache desktop-file-utils xdg-utils libxcb-cursor"
                echo "    Fedora:        sudo dnf install libnotify librsvg2-tools gtk-update-icon-cache desktop-file-utils xdg-utils libxcb-cursor"
                if [ "$YES" != true ]; then
                    read -p "  Continuar mesmo assim? (s/N) " -n 1 -r REPLY
                    echo
                    if [[ ! "$REPLY" =~ ^[Ss]$ ]]; then
                        exit 1
                    fi
                fi
                ;;
        esac
    fi

    # Audio deps (opcional - só avisa)
    for cmd in canberra-gtk-play paplay aplay; do
        if ! command -v "$cmd" &>/dev/null; then
            echo "  AVISO: $cmd não encontrado. Áudio pode não funcionar."
            echo "    Instale com: sudo apt install libcanberra-gtk3 pulseaudio-utils alsa-utils"
            break
        fi
    done
}

if [ "$FLATPAK" = true ]; then
    # === Flatpak install ===
    echo "==> Flatpak install selected"

    if ! command -v flatpak &>/dev/null; then
        echo "ERROR: flatpak not installed!"
        [ "$YES" = true ] || read -p "  Instalar flatpak? (s/N) " -n 1 -r REPLY
        echo
        if [ "$YES" = true ] || [[ "$REPLY" =~ ^[Ss]$ ]]; then
            install_packages flatpak flatpak-builder
        else
            exit 1
        fi
    fi

    if ! command -v flatpak-builder &>/dev/null; then
        echo "Installing flatpak-builder..."
        flatpak install -y flathub org.flatpak.Builder 2>/dev/null || \
            install_packages flatpak-builder
    fi

    echo "Ensuring KDE runtime..."
    flatpak install -y flathub org.kde.Platform//6.11 2>/dev/null || true
    flatpak install -y flathub org.kde.Sdk//6.11 2>/dev/null || true

    echo "Building Flatpak..."
    cd "$PROJECT_DIR"

    if command -v flatpak-builder &>/dev/null; then
        flatpak-builder --force-clean --ccache --install-deps-from=flathub build-flatpak flatpak/io.github.mytime.yml
    else
        flatpak run org.flatpak.Builder --force-clean --ccache --install-deps-from=flathub build-flatpak flatpak/io.github.mytime.yml
    fi

    flatpak build-bundle build-flatpak io.github.mytime.flatpak io.github.mytime
    flatpak install --user -y io.github.mytime.flatpak

    echo ""
    echo "========================================="
    echo "  myTime instalado via Flatpak!"
    echo "  Busque por 'myTime' no menu de apps"
    echo "  Ou execute: flatpak run io.github.mytime"
    echo "========================================="
    echo ""
    echo "  Para desinstalar:"
    echo "    flatpak uninstall io.github.mytime"

else
    # === Local install (pip + desktop entry) ===
    check_python

    if [ "$SKIP_DEPS" != true ]; then
        install_system_deps
    fi

    echo "==> Local install selected"

    # 1. Install Python package
    echo "Installing Python package..."
    cd "$PROJECT_DIR"
    pip3 install --break-system-packages -e . 2>/dev/null || pip3 install -e .

    # 2. Install icon
    echo "Installing icon..."
    ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
    mkdir -p "$ICON_DIR"
    cp "$PROJECT_DIR/src/myTime/data/icons/myTime.svg" "$ICON_DIR/myTime.svg"

    if command -v rsvg-convert &>/dev/null; then
        for size in 22 32 48 64 128 256; do
            dir="$HOME/.local/share/icons/hicolor/${size}x${size}/apps"
            mkdir -p "$dir"
            rsvg-convert -w "$size" -h "$size" \
                "$PROJECT_DIR/src/myTime/data/icons/myTime.svg" \
                -o "$dir/myTime.png"
        done
    elif command -v convert &>/dev/null; then
        for size in 22 32 48 64 128 256; do
            dir="$HOME/.local/share/icons/hicolor/${size}x${size}/apps"
            mkdir -p "$dir"
            convert -background none -size "${size}x${size}" \
                "$PROJECT_DIR/src/myTime/data/icons/myTime.svg" \
                "$dir/myTime.png"
        done
    else
        echo "  (install rsvg-convert or imagemagick for PNG icons)"
    fi

    # 3. Install desktop file
    echo "Installing desktop entry..."
    DESKTOP_DIR="$HOME/.local/share/applications"
    mkdir -p "$DESKTOP_DIR"
    cat > "$DESKTOP_DIR/myTime.desktop" << EOF
[Desktop Entry]
Type=Application
Name=myTime
Comment=Gerenciador inteligente de Pomodoro e Jornadas
Exec=myTime
Icon=myTime
Categories=Utility;Office;ProjectManagement;
Terminal=false
StartupNotify=true
EOF

    # 4. Update icon cache
    echo "Updating icon cache..."
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons" 2>/dev/null || true
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

    echo ""
    echo "========================================="
    echo "  myTime instalado no sistema!"
    echo "  Busque por 'myTime' no menu de apps"
    echo "  Ou execute: myTime"
    echo "========================================="
    echo ""
    echo "  Para desinstalar:"
    echo "    pip3 uninstall myTime"
    echo "    rm -f ~/.local/share/icons/hicolor/*/apps/myTime.*"
    echo "    rm -f ~/.local/share/applications/myTime.desktop"
    echo "    gtk-update-icon-cache -f -t ~/.local/share/icons 2>/dev/null"
    echo "    update-desktop-database ~/.local/share/applications 2>/dev/null"
    echo "    rm -rf ~/.config/myTime   # Remove dados (opcional)"
fi