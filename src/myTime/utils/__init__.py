"""Notification and sound utilities."""
from __future__ import annotations
import subprocess
import shutil
from pathlib import Path
from typing import Optional
from importlib.resources import files as resource_files
from myTime.core.models import SessionType


class NotificationManager:
    """Manages system notifications via notify-send (libnotify)."""
    
    ICON_MAP = {
        SessionType.WORK: "preferences-system-time",
        SessionType.SHORT_BREAK: "coffee",
        SessionType.LONG_BREAK: "face-smile",
    }
    
    TITLE_MAP = {
        SessionType.WORK: "Hora de Focar!",
        SessionType.SHORT_BREAK: "Pausa Curta",
        SessionType.LONG_BREAK: "Pausa Longa",
    }
    
    def __init__(self, enabled: bool = True, sound_enabled: bool = True):
        self.enabled = enabled
        self.sound_enabled = sound_enabled
        self._notify_send = shutil.which("notify-send")
        self._canberra = shutil.which("canberra-gtk-play")
        self._custom_sound: Optional[str] = None
        # Bundled default notification sound
        self._bundled_sound: Optional[str] = None
        try:
            bundled = resource_files("myTime").joinpath("data", "sounds", "notification.wav")
            if bundled.exists():
                self._bundled_sound = str(bundled)
        except (ModuleNotFoundError, FileNotFoundError):
            pass
    
    def is_available(self) -> bool:
        """Check if notify-send is available."""
        return self._notify_send is not None
    
    def set_custom_sound(self, sound_path: str) -> None:
        """Set custom notification sound file."""
        if Path(sound_path).exists():
            self._custom_sound = sound_path
    
    def get_bundled_sound_path(self) -> str:
        """Get path to the bundled notification sound."""
        return self._bundled_sound or ""

    def send_journey_start(self, total_work_minutes: int, block_count: int) -> bool:
        """Notify journey started."""
        return self.send_custom(
            "Jornada Iniciada",
            f"{block_count} blocos de foco • {total_work_minutes} min de trabalho",
            icon="media-playback-start",
            duration_ms=8000,
        )

    def send_journey_complete(self, total_work_minutes: int) -> bool:
        """Notify journey completed."""
        return self.send_custom(
            "Parabéns! Jornada Concluída",
            f"Você completou {total_work_minutes} minutos de foco produtivo!",
            icon="emblem-default",
            duration_ms=10000,
            urgency="normal",
        )

    def send_break_reminder(self, break_type: SessionType, minutes: int) -> bool:
        """Send break reminder notification."""
        titles = {
            SessionType.SHORT_BREAK: "Hora da Pausa Curta",
            SessionType.LONG_BREAK: "Hora da Pausa Longa",
        }
        return self.send_custom(
            titles.get(break_type, "Pausa"),
            f"Faça uma pausa de {minutes} minutos. Levante-se, alongue-se!",
            icon=self.ICON_MAP.get(break_type, "coffee"),
            duration_ms=8000,
        )
    
    def send(
        self, 
        session_type: SessionType, 
        message: str,
        duration_ms: int = 6000,
        urgency: str = "normal"
    ) -> bool:
        """Send a system notification."""
        if not self.enabled or not self._notify_send:
            return False
        
        icon = self.ICON_MAP.get(session_type, "preferences-system-time")
        title = self.TITLE_MAP.get(session_type, "myTime")
        
        try:
            subprocess.run([
                self._notify_send,
                title,
                message,
                "-i", icon,
                "-t", str(duration_ms),
                "-u", urgency,
                "-a", "myTime"
            ], check=False, timeout=2, capture_output=True)

            if self.sound_enabled:
                self._play_sound(session_type)
            return True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError, OSError):
            return False
    
    def send_custom(
        self, 
        title: str, 
        message: str, 
        icon: Optional[str] = None,
        duration_ms: int = 6000,
        urgency: str = "normal",
        session_type: Optional[SessionType] = None,
    ) -> bool:
        """Send a custom notification."""
        if not self.enabled or not self._notify_send:
            return False
        
        icon = icon or "preferences-system-time"
        
        try:
            subprocess.run([
                self._notify_send,
                title,
                message,
                "-i", icon,
                "-t", str(duration_ms),
                "-u", urgency,
                "-a", "myTime"
            ], check=False, timeout=2, capture_output=True)

            if self.sound_enabled:
                if session_type:
                    self._play_sound(session_type)
                else:
                    self._play_sound(SessionType.WORK)
            return True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError, OSError):
            return False
    
    def _play_sound(self, session_type: SessionType) -> None:
        """Play notification sound."""
        if self._custom_sound:
            self._play_file(self._custom_sound)
            return
        
        # Try freedesktop sound theme via canberra first
        if self._canberra:
            sound_map = {
                SessionType.WORK: "message-new-instant",
                SessionType.SHORT_BREAK: "complete",
                SessionType.LONG_BREAK: "alarm-clock-elapsed",
            }
            sound_name = sound_map.get(session_type, "message")
            try:
                subprocess.run([
                    self._canberra,
                    "-i", sound_name,
                    "-d", "myTime"
                ], check=False, timeout=1)
                return
            except (subprocess.SubprocessError, TimeoutError):
                pass
        
        # Fallback: play bundled sound file
        if self._bundled_sound:
            self._play_file(self._bundled_sound)
    
    def _play_file(self, file_path: str) -> None:
        """Play a sound file using paplay/aplay."""
        for player in ("paplay", "aplay", "ffplay"):
            if shutil.which(player):
                try:
                    if player == "ffplay":
                        subprocess.run([player, "-nodisp", "-autoexit", file_path], 
                                     check=False, timeout=3)
                    else:
                        subprocess.run([player, file_path], check=False, timeout=3)
                    return
                except (subprocess.SubprocessError, TimeoutError):
                    continue


class IconManager:
    """Manages application icons for tray and UI."""

    DEFAULT_COLORS = {
        "work": "#e74c3c",
        "short_break": "#2ecc71",
        "long_break": "#3498db",
        "paused": "#f39c12",
        "idle": "#95a5a6",
    }

    def __init__(self):
        self._icons: dict = {}

    def get_icon(self, name: str, fallback: str = "") -> QIcon:
        """Get icon by name with fallback chain."""
        key = (name, fallback)
        if key in self._icons:
            return self._icons[key]

        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            self._icons[key] = icon
            return icon

        if fallback:
            icon = QIcon.fromTheme(fallback)
            if not icon.isNull():
                self._icons[key] = icon
                return icon

        self._icons[key] = QIcon()
        return self._icons[key]

    def generate_icon(
        self,
        state: str = "idle",
        progress: float = 0.0,
        color: str = "",
        size: int = 48,
        show_time: bool = False,
        time_text: str = "",
        font_size: int = 0,
        text_color: str = "",
        bg_color: str = "#ecf0f1",
        bg_opacity: int = 255,
        show_letter: bool = True,
    ) -> QIcon:
        """Generate a tray icon with optional progress fill.

        Args:
            state: One of 'work', 'short_break', 'long_break', 'paused', 'idle'
            progress: 0.0 to 1.0 - fraction of the circle filled
            color: Hex color string for the filled portion
            size: Pixel size (square)
            show_time: If True, render time_text in the center
            time_text: Text to render (e.g., "25:00")
            font_size: Font size in pixels (0 = auto based on icon size)
            text_color: Hex color for time text
            bg_color: Hex color for background circle
            bg_opacity: Background opacity 0-255
            show_letter: If True and show_time is False, render F/P/L letter
        """
        from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QFont
        from PySide6.QtCore import Qt, QRectF

        fill_color = color or self.DEFAULT_COLORS.get(state, "#95a5a6")
        progress = max(0.0, min(1.0, progress))

        # Determine what text to render
        text_to_show = ""
        text_pen_color = text_color or "#2c3e50"
        if show_time and time_text:
            text_to_show = time_text
            text_pen_color = text_color or "#2c3e50"
        elif show_letter and state in ("work", "short_break", "long_break"):
            text_to_show = {"work": "F", "short_break": "P", "long_break": "L"}.get(state, "")
            text_pen_color = "#ffffff"

        # ─── NORMAL (SQUARE) MODE ───────────────────────────────────
        render_size = size * 2
        pixmap = QPixmap(render_size, render_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg_qcolor = QColor(bg_color)
        bg_qcolor.setAlpha(max(0, min(255, bg_opacity)))
        margin = render_size * 0.08
        circle_rect = QRectF(margin, margin, render_size - 2 * margin, render_size - 2 * margin)
        painter.setBrush(QBrush(bg_qcolor))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(circle_rect)

        if progress > 0.0 and state not in ("idle", "paused"):
            sweep = int(progress * 360 * 16)
            painter.setBrush(QBrush(QColor(fill_color)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPie(circle_rect, 90 * 16, -sweep)
        elif state == "paused":
            painter.setBrush(QBrush(QColor(fill_color)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(circle_rect)
        elif state in ("work", "short_break", "long_break"):
            painter.setBrush(QBrush(QColor(fill_color)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(circle_rect)

        border_width = max(2, render_size // 32)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#34495e"), border_width))
        painter.drawEllipse(circle_rect)

        if show_time and time_text:
            painter.setPen(QColor(text_pen_color))
            fs = font_size if font_size > 0 else int(render_size * (0.22 if len(time_text) <= 5 else 0.16))
            painter.setFont(QFont("Sans", fs, QFont.Weight.Bold))
            tr = pixmap.rect().adjusted(2, 2, -2, -2)
            painter.drawText(tr, Qt.AlignmentFlag.AlignCenter, time_text)
        elif show_letter and state in ("work", "short_break", "long_break"):
            symbol = {"work": "F", "short_break": "P", "long_break": "L"}.get(state, "")
            if symbol:
                painter.setPen(QColor("#ffffff"))
                painter.setFont(QFont("Sans", int(render_size * 0.42), QFont.Weight.Bold))
                painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, symbol)

        painter.end()
        scaled = pixmap.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        return QIcon(scaled)

    def get_tray_icons(self) -> dict:
        """Get standard tray icons (legacy fallback only)."""
        return {
            "work": self.get_icon("preferences-system-time", "appointment-new"),
            "short_break": self.get_icon("coffee", "weather-clear"),
            "long_break": self.get_icon("face-smile", "avatar-default"),
            "paused": self.get_icon("media-playback-pause", "dialog-warning"),
            "idle": self.get_icon("chronometer", "appointment-new"),
            "completed": self.get_icon("emblem-default", "dialog-information"),
        }


# Need QIcon for type hints
from PySide6.QtGui import QIcon
