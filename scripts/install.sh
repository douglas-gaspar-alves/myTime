#!/bin/bash
# Install myTime on the system
# Usage: ./scripts/install.sh [--flatpak] [--yes] [--install-deps]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Parse flags
FLATPAK=false
YES=false
INSTALL_DEPS=false
for arg in "$@"; do
    case $arg in
        --flatpak) FLATPAK=true ;;
        --yes) YES=true ;;
        --install-deps) INSTALL_DEPS=true ;;
        -h|--help)
            echo "Usage: $0 [--flatpak] [--yes] [--install-deps]"
            echo "  --flatpak      Install via Flatpak (build from source)"
            echo "  --yes          Non-interactive mode (assume yes to prompts)"
            echo "  --install-deps Attempt to install system dependencies via package manager"
            exit 0
            ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

# === Check Python/pip (required for local install) ===
check_python() {
    if ! command -v python3 &>/dev/null; then
        echo "ERROR: python3 não encontrado!"
        echo "  Instale com:"
        echo "    Debian/Ubuntu: sudo apt install python3 python3-pip python3-venv"
        echo "    Arch:          sudo pacman -S python python-pip"
        echo "    Fedora:        sudo dnf install python3 python3-pip"
        exit 1
    fi

    if ! command -v pip3 &>/dev/null; then
        echo "ERROR: pip3 não encontrado!"
        echo "  Instale com:"
        echo "    Debian/Ubuntu: sudo apt install python3-pip"
        echo "    Arch:          sudo pacman -S python-pip"
        echo "    Fedora:        sudo dnf install python3-pip"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        echo "ERROR: Python 3.11+ required, found $PYTHON_VERSION"
        exit 1
    fi
    echo "==> Python $PYTHON_VERSION OK"
}

# === Check system dependencies ===
check_deps() {
    local missing=()
    local warnings=()

    for cmd in notify-send rsvg-convert gtk-update-icon-cache update-desktop-database xdg-open; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done

    # Check libxcb-cursor (Qt6 xcb plugin dependency)
    if ! ldconfig -p 2>/dev/null | grep -q libxcb-cursor; then
        missing+=("libxcb-cursor0")
    fi

    for cmd in canberra-gtk-play paplay aplay; do
        if ! command -v "$cmd" &>/dev/null; then
            warnings+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        echo "==> Dependências de sistema necessárias ausentes:"
        printf '    - %s\n' "${missing[@]}"
        echo ""

        if [ "$INSTALL_DEPS" = true ]; then
            echo "==> Tentando instalar automaticamente..."
            if command -v apt &>/dev/null; then
                sudo apt update && sudo apt install -y libnotify-bin librsvg2-bin gtk-update-icon-cache desktop-file-utils xdg-utils libxcb-cursor0
            elif command -v pacman &>/dev/null; then
                sudo pacman -S --needed --noconfirm libnotify librsvg gtk-update-icon-cache desktop-file-utils xdg-utils libxcb-cursor
            elif command -v dnf &>/dev/null; then
                sudo dnf install -y libnotify librsvg2-tools gtk-update-icon-cache desktop-file-utils xdg-utils libxcb-cursor
            else
                echo "  Gerenciador de pacotes não suportado. Instale manualmente:"
                echo "    Debian/Ubuntu: sudo apt install libnotify-bin librsvg2-bin gtk-update-icon-cache desktop-file-utils xdg-utils"
                echo "    Arch:          sudo pacman -S libnotify librsvg gtk-update-icon-cache desktop-file-utils xdg-utils"
                echo "    Fedora:        sudo dnf install libnotify librsvg2-tools gtk-update-icon-cache desktop-file-utils xdg-utils"
            fi
        elif [ "$YES" = true ]; then
            echo "  Modo --yes: continuando sem dependências opcionais..."
        else
            echo "  Instale com:"
            echo "    Debian/Ubuntu: sudo apt install libnotify-bin librsvg2-bin gtk-update-icon-cache desktop-file-utils xdg-utils libxcb-cursor0"
            echo "    Arch:          sudo pacman -S libnotify librsvg gtk-update-icon-cache desktop-file-utils xdg-utils libxcb-cursor"
            echo "    Fedora:        sudo dnf install libnotify librsvg2-tools gtk-update-icon-cache desktop-file-utils xdg-utils libxcb-cursor"
            echo ""
            read -p "  Continuar mesmo assim? (s/N) " -n 1 -r REPLY
            echo
            if [[ ! "$REPLY" =~ ^[Ss]$ ]]; then
                exit 1
            fi
        fi
    fi

    if [ ${#warnings[@]} -gt 0 ]; then
        echo "==> Dependências opcionais ausentes (apenas áudio):"
        printf '    - %s\n' "${warnings[@]}"
        echo "  O áudio pode não funcionar. Instale com:"
        echo "    Debian/Ubuntu: sudo apt install libcanberra-gtk3 pulseaudio-utils alsa-utils"
        echo "    Arch:          sudo pacman -S libcanberra pulseaudio-utils alsa-utils"
        echo "    Fedora:        sudo dnf install libcanberra-gtk3 pulseaudio-utils alsa-utils"
        echo ""
    fi
}

if [ "$FLATPAK" = true ]; then
    # === Flatpak install ===
    echo "==> Flatpak install selected"

    if ! command -v flatpak &>/dev/null; then
        echo "ERROR: flatpak not installed!"
        echo "  Install it first:"
        echo "    Arch:   sudo pacman -S flatpak flatpak-builder"
        echo "    Debian: sudo apt install flatpak flatpak-builder"
        echo "    Fedora: sudo dnf install flatpak flatpak-builder"
        exit 1
    fi

    # Install flatpak-builder via flatpak if not available
    if ! command -v flatpak-builder &>/dev/null; then
        echo "Installing flatpak-builder..."
        flatpak install -y flathub org.flatpak.Builder
        alias flatpak-builder="flatpak run org.flatpak.Builder"
    fi

    # Ensure KDE runtime
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

else
    # === Local install (pip + desktop entry) ===
    check_python
    check_deps

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

    # Generate PNG icons at common sizes
    if command -v rsvg-convert &>/dev/null; then
        for size in 22 32 48 64 128 256; do
            dir="$HOME/.local/share/icons/hicolor/${size}x${size}/apps"
            mkdir -p "$dir"
            rsvg-convert -w "$size" -h "$size" \
                "$PROJECT_DIR/src/myTime/data/icons/myTime.svg" \
                -o "$dir/myTime.png"
        done
    elif command -v convert &>/dev/null; then
        # imagemagick fallback
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
fi