"""Notification utilities for system notifications."""
from __future__ import annotations
import subprocess
import shutil
from typing import Optional
from myTime.core.models import SessionType


class NotificationManager:
    """Manages system notifications via notify-send (libnotify)."""
    
    ICON_MAP = {
        SessionType.WORK: "preferences-system-time",
        SessionType.SHORT_BREAK: "coffee",
        SessionType.LONG_BREAK: "face-smile",
        SessionType.COMPLETED: "emblem-default",
        SessionType.SKIPPED: "dialog-warning",
    }
    
    TITLE_MAP = {
        SessionType.WORK: "Hora de Focar!",
        SessionType.SHORT_BREAK: "Pausa Curta",
        SessionType.LONG_BREAK: "Pausa Longa",
        SessionType.COMPLETED: "Jornada Concluída!",
        SessionType.SKIPPED: "Sessão Pulada",
    }
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._notify_send = shutil.which("notify-send")
        
    def is_available(self) -> bool:
        """Check if notify-send is available."""
        return self._notify_send is not None
    
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
            ], check=False, timeout=2)
            return True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
            return False
    
    def send_custom(
        self, 
        title: str, 
        message: str, 
        icon: Optional[str] = None,
        duration_ms: int = 6000,
        urgency: str = "normal"
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
            ], check=False, timeout=2)
            return True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
            return False
    
    def send_journey_start(self, total_work_minutes: int, block_count: int) -> bool:
        """Notify journey started."""
        return self.send_custom(
            "myTime - Jornada Iniciada",
            f"{block_count} blocos de foco • {total_work_minutes} min de trabalho",
            icon="media-playback-start",
            duration_ms=8000
        )
    
    def send_journey_complete(self, total_work_minutes: int) -> bool:
        """Notify journey completed."""
        return self.send_custom(
            "Parabéns! Jornada Concluída",
            f"Você completou {total_work_minutes} minutos de foco produtivo!",
            icon="emblem-default",
            duration_ms=10000,
            urgency="normal"
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
            duration_ms=8000
        )
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable notifications."""
        self.enabled = enabled
