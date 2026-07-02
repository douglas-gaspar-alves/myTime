"""Icon utilities for system tray and UI."""
from __future__ import annotations
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QSize
from typing import Optional
import os


class IconManager:
    """Manages application icons for tray and notifications."""
    
    # Freedesktop standard icon names
    ICON_MAP = {
        "work": ["chronometer", "appointment-new", "preferences-system-time", "x-office-calendar"],
        "short_break": ["weather-clear", "face-smile", "emblem-favorite", "stock_take-break"],
        "long_break": ["weather-few-clouds", "face-cool", "emblem-ok", "stock_coffee"],
        "paused": ["media-playback-pause", "process-stop", "emblem-important"],
        "idle": ["chronometer", "appointment-new"],
        "complete": ["emblem-default", "emblem-ok", "task-done"],
        "settings": ["preferences-system", "configure", "applications-system"],
        "quit": ["application-exit", "window-close", "system-shutdown"],
    }
    
    # Colors for generated icons
    COLORS = {
        "work": "#e74c3c",       # Red - focus
        "short_break": "#2ecc71", # Green - short break
        "long_break": "#3498db",  # Blue - long break
        "paused": "#f39c12",      # Orange - paused
        "idle": "#95a5a6",        # Gray - idle
        "complete": "#27ae60",    # Dark green - complete
    }
    
    def __init__(self, size: int = 24):
        self.size = size
        self._cache: dict[str, QIcon] = {}
    
    def get_icon(self, state: str) -> QIcon:
        """Get icon for a given state, with caching."""
        if state in self._cache:
            return self._cache[state]
        
        icon = self._load_system_icon(state)
        if icon.isNull():
            icon = self._generate_icon(state)
            
        self._cache[state] = icon
        return icon
    
    def _load_system_icon(self, state: str) -> QIcon:
        """Try to load icon from system theme."""
        names = self.ICON_MAP.get(state, ["chronometer"])
        for name in names:
            icon = QIcon.fromTheme(name)
            if not icon.isNull():
                return icon
        return QIcon()
    
    def _generate_icon(self, state: str) -> QIcon:
        """Generate a simple colored icon programmatically."""
        color = self.COLORS.get(state, "#95a5a6")
        pixmap = QPixmap(self.size, self.size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw circle
        margin = 2
        painter.drawEllipse(margin, margin, self.size - 2*margin, self.size - 2*margin)
        
        # Add text for work/break states
        if state in ("work", "short_break", "long_break"):
            painter.setPen(QColor("#ffffff"))
            painter.setFont(QFont("Arial", self.size // 2, QFont.Weight.Bold))
            text = {
                "work": "🎯",
                "short_break": "☕",
                "long_break": "🌴",
            }.get(state, "")
            if text:
                painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        
        painter.end()
        return QIcon(pixmap)
    
    def get_tray_icon(self, session_type: str, is_paused: bool = False) -> QIcon:
        """Get appropriate tray icon for current session."""
        if is_paused:
            return self.get_icon("paused")
        
        state_map = {
            "work": "work",
            "short_break": "short_break",
            "long_break": "long_break",
        }
        return self.get_icon(state_map.get(session_type, "idle"))
    
    def get_notification_icon(self, session_type: str) -> str:
        """Get icon name for notify-send."""
        icon_names = {
            "work": "chronometer",
            "short_break": "weather-clear",
            "long_break": "weather-few-clouds",
            "complete": "emblem-default",
        }
        return icon_names.get(session_type, "chronometer")
    
    def set_size(self, size: int) -> None:
        """Change icon size and clear cache."""
        self.size = size
        self._cache.clear()


# Global instance
icon_manager = IconManager()
