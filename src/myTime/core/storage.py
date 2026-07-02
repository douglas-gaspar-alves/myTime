"""JSON-based storage for configuration and history."""
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from myTime.core.models import (
    WorkSchedule, SessionRecord, DailyStats, AppState, 
    SessionType, SessionStatus
)


class StorageManager:
    """Manages persistent JSON storage for config and history."""
    
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            config_dir = os.path.join(
                os.environ.get("XDG_CONFIG_HOME", 
                os.path.expanduser("~/.config")), 
                "myTime"
            )
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.history_file = self.config_dir / "history.json"
        self.state_file = self.config_dir / "state.json"
        self.recent_tasks_file = self.config_dir / "recent_tasks.json"
        
    # --- Config Methods ---
    
    def load_config(self) -> WorkSchedule:
        """Load configuration from JSON file."""
        if not self.config_file.exists():
            return WorkSchedule()  # Default config
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return WorkSchedule.from_dict(data)
        except (json.JSONDecodeError, OSError, KeyError):
            return WorkSchedule()
    
    def save_config(self, config: WorkSchedule) -> bool:
        """Save configuration to JSON file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False
    
    # --- State Methods ---
    
    def load_state(self) -> Optional[AppState]:
        """Load application runtime state."""
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AppState.from_dict(data)
        except (json.JSONDecodeError, OSError, KeyError):
            return None
    
    def save_state(self, state: AppState) -> bool:
        """Save application runtime state."""
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False
    
    def clear_state(self) -> bool:
        """Clear saved state (e.g., on journey completion)."""
        try:
            if self.state_file.exists():
                self.state_file.unlink()
            return True
        except OSError:
            return False
    
    # --- Recent Tasks ---

    def get_recent_tasks(self, max_items: int = 20) -> list[str]:
        """Get list of recent task names."""
        if not self.recent_tasks_file.exists():
            return []
        try:
            with open(self.recent_tasks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data[:max_items] if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def save_recent_tasks(self, tasks: list[str]) -> bool:
        """Save recent task list."""
        try:
            with open(self.recent_tasks_file, "w", encoding="utf-8") as f:
                json.dump(tasks[:50], f, ensure_ascii=False)
            return True
        except OSError:
            return False

    def add_recent_task(self, task: str) -> bool:
        """Add a task to the recent list (dedup, max 50)."""
        tasks = self.get_recent_tasks()
        if task in tasks:
            tasks.remove(task)
        tasks.insert(0, task)
        return self.save_recent_tasks(tasks[:50])

    # --- History Methods ---
    
    def load_history(self) -> List[SessionRecord]:
        """Load all session records."""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            records = []
            for item in data:
                try:
                    records.append(SessionRecord.from_dict(item))
                except (KeyError, ValueError):
                    continue  # Skip corrupted records
            return records
        except (json.JSONDecodeError, OSError):
            return []
    
    def save_history(self, records: List[SessionRecord]) -> bool:
        """Save all session records."""
        try:
            data = [r.to_dict() for r in records]
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False
    
    def append_session(self, record: SessionRecord) -> bool:
        """Append a single session record to history."""
        records = self.load_history()
        records.append(record)
        return self.save_history(records)
    
    def get_today_sessions(self) -> List[SessionRecord]:
        """Get all sessions for today."""
        today = date.today().isoformat()
        records = self.load_history()
        return [r for r in records if r.started_at.startswith(today)]
    
    def get_daily_stats(self, target_date: Optional[date] = None) -> DailyStats:
        """Calculate daily statistics for a given date."""
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        records = self.load_history()
        today_records = [r for r in records if r.started_at.startswith(date_str)]
        
        stats = DailyStats(date=date_str)
        tasks_completed = set()
        
        for record in today_records:
            if record.status == SessionStatus.COMPLETED:
                if record.session_type == SessionType.WORK:
                    stats.work_sessions_completed += 1
                    stats.work_seconds_completed += record.actual_duration
                    if record.task_name:
                        tasks_completed.add(record.task_name)
                elif record.session_type == SessionType.SHORT_BREAK:
                    stats.short_breaks_completed += 1
                elif record.session_type == SessionType.LONG_BREAK:
                    stats.long_breaks_completed += 1
            elif record.status == SessionStatus.SKIPPED:
                stats.skipped_sessions += 1
        
        stats.tasks_completed = list(tasks_completed)
        return stats
    
    def get_weekly_stats(self, weeks: int = 4) -> List[DailyStats]:
        """Get daily stats for the last N weeks."""
        from datetime import timedelta
        
        stats = []
        today = date.today()
        
        for i in range(weeks * 7):
            target_date = today - timedelta(days=i)
            stats.append(self.get_daily_stats(target_date))
        
        return list(reversed(stats))
    
    def cleanup_old_history(self, days_to_keep: int = 365) -> int:
        """Remove history older than specified days."""
        from datetime import timedelta
        
        records = self.load_history()
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.isoformat()
        
        filtered = [
            r for r in records 
            if r.started_at >= cutoff_str
        ]
        
        removed = len(records) - len(filtered)
        if removed > 0:
            self.save_history(filtered)
        return removed
    
    def export_history(self, export_path: str) -> bool:
        """Export full history to a JSON file."""
        try:
            records = self.load_history()
            data = [r.to_dict() for r in records]
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False
    
    def export_data(self, export_path: str) -> bool:
        """Export all data (config, history, state) to a single JSON file."""
        try:
            config = self.load_config()
            history = self.load_history()
            state = self.load_state()
            data = {
                "config": config.to_dict(),
                "history": [r.to_dict() for r in history],
                "state": state.to_dict() if state else None,
                "exported_at": datetime.now().isoformat(),
            }
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False

    def import_data(self, import_path: str) -> None:
        """Import all data from a JSON file."""
        import json
        with open(import_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "config" in data:
            config = WorkSchedule.from_dict(data["config"])
            self.save_config(config)
        if "history" in data:
            history = [SessionRecord.from_dict(r) for r in data["history"]]
            self.save_history(history)
        if "state" in data and data["state"]:
            state = AppState.from_dict(data["state"])
            self.save_state(state)

    def get_config_dir(self) -> Path:
        """Get the config directory path."""
        return self.config_dir


# Global instance
storage = StorageManager()
