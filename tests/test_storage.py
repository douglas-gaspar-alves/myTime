"""Tests for StorageManager."""
import json
import os
import tempfile
from datetime import datetime, date
from pathlib import Path

import pytest
from myTime.core.models import (
    WorkSchedule, SessionRecord, SessionType, SessionStatus, AppState
)
from myTime.core.storage import StorageManager


class TestStorageManager:
    """Test JSON storage operations."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            yield tmp

    @pytest.fixture
    def storage(self, temp_dir):
        return StorageManager(config_dir=temp_dir)

    def test_initialization_creates_dir(self, temp_dir):
        StorageManager(config_dir=os.path.join(temp_dir, "new_config"))
        assert Path(temp_dir, "new_config").exists()

    def test_load_default_config(self, storage):
        config = storage.load_config()
        assert isinstance(config, WorkSchedule)
        assert config.work_duration == 25 * 60
        assert config.language == "pt_BR"

    def test_save_and_load_config(self, storage):
        config = WorkSchedule(
            work_duration=30 * 60,
            language="en_US",
            auto_start_breaks=False,
        )
        storage.save_config(config)
        loaded = storage.load_config()
        assert loaded.work_duration == 30 * 60
        assert loaded.language == "en_US"
        assert loaded.auto_start_breaks is False

    def test_config_persistence(self, storage):
        original = WorkSchedule(work_duration=20 * 60)
        storage.save_config(original)
        # Create new storage pointing to same dir
        storage2 = StorageManager(config_dir=storage.get_config_dir())
        loaded = storage2.load_config()
        assert loaded.work_duration == 20 * 60

    def test_append_session(self, storage):
        record = SessionRecord(
            id="test1",
            session_type=SessionType.WORK,
            status=SessionStatus.COMPLETED,
            planned_duration=1500,
            actual_duration=1480,
            started_at=datetime.now().isoformat(),
            ended_at=datetime.now().isoformat(),
            task_name="Test task",
        )
        assert storage.append_session(record)
        sessions = storage.get_today_sessions()
        assert len(sessions) == 1
        assert sessions[0].task_name == "Test task"

    def test_multiple_sessions(self, storage):
        for i in range(5):
            record = SessionRecord(
                id=f"test_{i}",
                session_type=SessionType.WORK,
                status=SessionStatus.COMPLETED,
                planned_duration=1500,
                actual_duration=1500,
                started_at=datetime.now().isoformat(),
            )
            storage.append_session(record)
        sessions = storage.get_today_sessions()
        assert len(sessions) == 5

    def test_save_and_load_state(self, storage):
        state = AppState(
            current_session_type=SessionType.WORK,
            current_status=SessionStatus.RUNNING,
            remaining_seconds=900,
            total_planned_seconds=1500,
            current_task="Coding",
        )
        assert storage.save_state(state)
        loaded = storage.load_state()
        assert loaded.current_task == "Coding"
        assert loaded.remaining_seconds == 900

    def test_clear_state(self, storage):
        state = AppState(current_task="Test")
        storage.save_state(state)
        assert storage.clear_state()
        assert storage.load_state() is None

    def test_no_state_on_clean_dir(self, storage):
        loaded = storage.load_state()
        assert loaded is None

    def test_empty_history(self, storage):
        sessions = storage.load_history()
        assert sessions == []

    def test_get_daily_stats(self, storage):
        record = SessionRecord(
            id="test1",
            session_type=SessionType.WORK,
            status=SessionStatus.COMPLETED,
            planned_duration=1500,
            actual_duration=1500,
            started_at=datetime.now().isoformat(),
            ended_at=datetime.now().isoformat(),
            task_name="Coding",
        )
        storage.append_session(record)
        stats = storage.get_daily_stats()
        assert stats.work_sessions_completed == 1
        assert stats.work_seconds_completed == 1500
        assert "Coding" in stats.tasks_completed

    def test_skipped_session_stats(self, storage):
        record = SessionRecord(
            id="test1",
            session_type=SessionType.WORK,
            status=SessionStatus.SKIPPED,
            planned_duration=1500,
            actual_duration=0,
            started_at=datetime.now().isoformat(),
        )
        storage.append_session(record)
        stats = storage.get_daily_stats()
        assert stats.work_sessions_completed == 0
        assert stats.skipped_sessions == 1

    def test_break_sessions_stats(self, storage):
        storage.append_session(SessionRecord(
            id="test1", session_type=SessionType.SHORT_BREAK,
            status=SessionStatus.COMPLETED, planned_duration=300,
            actual_duration=300, started_at=datetime.now().isoformat(),
        ))
        storage.append_session(SessionRecord(
            id="test2", session_type=SessionType.LONG_BREAK,
            status=SessionStatus.COMPLETED, planned_duration=900,
            actual_duration=900, started_at=datetime.now().isoformat(),
        ))
        stats = storage.get_daily_stats()
        assert stats.short_breaks_completed == 1
        assert stats.long_breaks_completed == 1

    def test_weekly_stats(self, storage):
        stats = storage.get_weekly_stats(weeks=1)
        assert len(stats) == 7  # 7 days

    def test_export_import(self, storage, temp_dir):
        # Save some config and history
        config = WorkSchedule(work_duration=30 * 60)
        storage.save_config(config)
        storage.append_session(SessionRecord(
            id="test1", session_type=SessionType.WORK,
            status=SessionStatus.COMPLETED, planned_duration=1500,
            actual_duration=1500, started_at=datetime.now().isoformat(),
            task_name="Coding",
        ))
        export_path = os.path.join(temp_dir, "export.json")
        assert storage.export_data(export_path)
        assert os.path.isfile(export_path)
        # Verify exported content
        with open(export_path, "r") as f:
            data = json.load(f)
        assert data["config"]["work_duration"] == 30 * 60
        assert len(data["history"]) == 1

    def test_import_data(self, storage, temp_dir):
        export_path = os.path.join(temp_dir, "export.json")
        config = WorkSchedule(work_duration=50 * 60, language="pt_BR")
        storage.save_config(config)
        storage.export_data(export_path)
        # Create new storage and import
        new_dir = os.path.join(temp_dir, "imported")
        storage2 = StorageManager(config_dir=new_dir)
        storage2.import_data(export_path)
        loaded = storage2.load_config()
        assert loaded.work_duration == 50 * 60

    def test_config_dir_returns_path(self, storage):
        path = storage.get_config_dir()
        assert isinstance(path, Path)
        assert path.exists()
