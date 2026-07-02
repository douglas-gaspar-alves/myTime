"""Core data models with i18n support."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional
import json


class SessionType(Enum):
    """Types of work sessions."""
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class SessionStatus(Enum):
    """Current session state."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class WorkSchedule:
    """User's work schedule configuration."""
    work_duration: int = 25 * 60          # 25 min in seconds
    short_break_duration: int = 5 * 60    # 5 min
    long_break_duration: int = 15 * 60    # 15 min
    sessions_before_long_break: int = 4   # Pomodoros before long break
    daily_goal_sessions: int = 8          # Target work sessions per day
    auto_start_breaks: bool = True        # Auto-start breaks
    auto_start_work: bool = False         # Auto-start work after break
    work_start_time: str = "09:00"        # Daily start time HH:MM
    work_end_time: str = "18:00"          # Daily end time HH:MM
    sound_enabled: bool = True            # Play notification sounds
    notifications_enabled: bool = True    # Show desktop notifications
    language: str = "pt_BR"               # Language code for i18n

    # Icon customization
    icon_size: int = 48                   # Tray icon size in pixels (22/32/48/64)
    show_time_in_tray: bool = False       # Render time text IN the icon (small, less readable)
    icon_text_font_size: int = 14         # Font size for time text in icon
    icon_text_show_seconds: bool = False  # Show seconds (MM:SS vs MM)
    icon_text_color: str = "#2c3e50"      # Color for time text
    icon_show_letter: bool = True         # Show F/P/L letter when time text is off
    icon_wide_mode: bool = False          # Wide icon: circle + text side by side
    icon_color_work: str = "#e74c3c"      # Red - focus
    icon_color_short_break: str = "#2ecc71"  # Green - short break
    icon_color_long_break: str = "#3498db"   # Blue - long break
    icon_color_paused: str = "#f39c12"    # Orange - paused
    icon_color_idle: str = "#95a5a6"      # Gray - idle/stopped
    icon_bg_color: str = "#ecf0f1"        # Background circle color
    icon_bg_opacity: int = 180            # Background opacity 0-255 (180≈70%)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> WorkSchedule:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def get_work_seconds(self) -> int:
        return self.work_duration

    def get_short_break_seconds(self) -> int:
        return self.short_break_duration

    def get_long_break_seconds(self) -> int:
        return self.long_break_duration


@dataclass
class SessionRecord:
    """Record of a completed session."""
    id: str
    session_type: SessionType
    status: SessionStatus
    planned_duration: int      # seconds
    actual_duration: int       # seconds
    started_at: str            # ISO format
    ended_at: Optional[str] = None
    task_name: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["session_type"] = self.session_type.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> SessionRecord:
        data = data.copy()
        data["session_type"] = SessionType(data["session_type"])
        data["status"] = SessionStatus(data["status"])
        return cls(**data)


@dataclass
class DailyStats:
    """Daily statistics aggregation."""
    date: str                    # YYYY-MM-DD
    work_sessions_completed: int = 0
    work_seconds_completed: int = 0
    short_breaks_completed: int = 0
    long_breaks_completed: int = 0
    skipped_sessions: int = 0
    tasks_completed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> DailyStats:
        return cls(**data)

    def get_work_hours(self) -> float:
        return self.work_seconds_completed / 3600

    def get_total_break_minutes(self) -> int:
        return (self.short_breaks_completed * 5) + (self.long_breaks_completed * 15)


@dataclass
class AppState:
    """Current application runtime state."""
    current_session_type: SessionType = SessionType.WORK
    current_status: SessionStatus = SessionStatus.IDLE
    remaining_seconds: int = 25 * 60
    total_planned_seconds: int = 25 * 60
    sessions_completed_today: int = 0
    current_task: str = ""
    session_start_time: Optional[datetime] = None
    paused_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "current_session_type": self.current_session_type.value,
            "current_status": self.current_status.value,
            "remaining_seconds": self.remaining_seconds,
            "total_planned_seconds": self.total_planned_seconds,
            "sessions_completed_today": self.sessions_completed_today,
            "current_task": self.current_task,
            "session_start_time": self.session_start_time.isoformat() if self.session_start_time else None,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AppState:
        d = data.copy()
        d["current_session_type"] = SessionType(d["current_session_type"])
        d["current_status"] = SessionStatus(d["current_status"])
        if d.get("session_start_time"):
            d["session_start_time"] = datetime.fromisoformat(d["session_start_time"])
        if d.get("paused_at"):
            d["paused_at"] = datetime.fromisoformat(d["paused_at"])
        return cls(**d)


class Translator:
    """Simple i18n translator using JSON files."""
    
    def __init__(self, locale_dir: str, language: str = "pt_BR"):
        self.locale_dir = locale_dir
        self.language = language
        self._translations: dict = {}
        self.load_language(language)

    def load_language(self, language: str) -> None:
        """Load translations for a language."""
        self.language = language
        import os
        path = os.path.join(self.locale_dir, f"{language}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._translations = json.load(f)
        except FileNotFoundError:
            # Fallback to English
            fallback_path = os.path.join(self.locale_dir, "en_US.json")
            try:
                with open(fallback_path, "r", encoding="utf-8") as f:
                    self._translations = json.load(f)
            except FileNotFoundError:
                self._translations = {}

    def t(self, key: str, **kwargs) -> str:
        """Translate a key with optional formatting."""
        keys = key.split(".")
        value = self._translations
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, key)
            else:
                value = key
                break
        if isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError:
                return value
        return key

    def get_available_languages(self) -> list[str]:
        """Get list of available language files."""
        import os
        langs = []
        for f in os.listdir(self.locale_dir):
            if f.endswith(".json"):
                langs.append(f[:-5])
        return langs
