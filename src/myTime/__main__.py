"""Main application class."""
from __future__ import annotations
import sys
from datetime import datetime, timedelta
from typing import Optional
from importlib.resources import files as resource_files
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
from PySide6.QtCore import QTimer, QObject, Slot

from myTime.core.models import (
    WorkSchedule, SessionType, SessionStatus, 
    SessionRecord, AppState
)
from myTime.core.engine import JourneyEngine, ScheduledBlock
from myTime.core.storage import StorageManager
from myTime.ui.tray import TrayManager
from myTime.ui.config_dialog import ConfigDialog
from myTime.ui.task_dialog import TaskDialog
from myTime.ui.main_window import MainWindow
from myTime.utils import NotificationManager, IconManager


class MyTimeApp(QObject):
    """Main application controller."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.storage = StorageManager()
        self.config = self.storage.load_config()
        self.engine = JourneyEngine(self.config)
        self.icon_manager = IconManager()
        
        # Notification manager
        self.notification_mgr = NotificationManager(
            enabled=self.config.notifications_enabled,
            sound_enabled=self.config.sound_enabled
        )
        
        # UI components
        self.tray = TrayManager(self.config)
        self.task_dialog = TaskDialog(self.storage)
        self.main_window = MainWindow(self.config)
        
        # Journey state
        self.journey_blocks: list[ScheduledBlock] = []
        self.current_block_index = -1
        self.current_task = ""
        self.session_start_time: Optional[datetime] = None
        self._paused_remaining: Optional[int] = None
        
        # Timer
        self.timer = QTimer()
        self.timer.setInterval(1000)  # 1 second
        self.timer.timeout.connect(self._on_tick)
        
        # Connect signals
        self._connect_signals()
        
        # Load saved state
        self._restore_state()
        
        # Show welcome dialog on first launch (deferred to after event loop starts)
        QTimer.singleShot(1000, self._show_welcome)
    
    def _connect_signals(self) -> None:
        """Connect UI signals to handlers."""
        self.tray.new_journey_requested.connect(self.start_journey)
        self.tray.config_requested.connect(self.show_config)
        self.tray.task_change_requested.connect(self.change_task)
        self.tray.pause_toggle_requested.connect(self.toggle_pause)
        self.tray.skip_session_requested.connect(self.skip_session)
        self.tray.restart_progress_requested.connect(self.restart_progress)
        self.tray.restart_session_requested.connect(self.restart_session)
        self.tray.quit_requested.connect(self.quit)

        self.tray.show_main_requested.connect(self._show_main)
        self.main_window.pause_toggled.connect(self.toggle_pause)
        self.main_window.skip_requested.connect(self.skip_session)
        self.main_window.new_journey_requested.connect(self.tray._request_new_journey)
        self.main_window.config_requested.connect(self.show_config)
        self.main_window.task_change_requested.connect(self.set_task)

        self.task_dialog.task_submitted.connect(self.set_task)
    
    def _show_welcome(self) -> None:
        """Show tray notification and start journey dialog on launch."""
        tray_msg = self._notif_msg()
        if tray_msg:
            self.tray.show_message(
                "myTime",
                f"Bem-vindo! {tray_msg}",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
        self.tray._request_new_journey()

    def _show_main(self) -> None:
        """Show and bring main window to front."""
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def _notif_msg(self) -> str:
        """Get daily stats summary message."""
        stats = self.storage.get_daily_stats()
        if stats.work_sessions_completed > 0:
            return (
                f"Hoje: {stats.work_sessions_completed} sessões concluídas, "
                f"{stats.work_seconds_completed // 60} min de foco."
            )
        return "Pronto para começar sua jornada produtiva!"

    def _restore_state(self) -> None:
        """Restore previous session state if any."""
        saved_state = self.storage.load_state()
        if saved_state and saved_state.current_status != SessionStatus.IDLE:
            # Could restore journey here if needed
            pass
    
    @Slot(int, str)
    def start_journey(self, total_work_minutes: int, task_name: str = "") -> None:
        """Start a new work journey."""
        self.timer.stop()
        self._paused_remaining = None

        if task_name:
            self.current_task = task_name
            self.tray.update_task(task_name)
            self.storage.add_recent_task(task_name)

        self.journey_blocks = self.engine.calculate_journey(
            total_work_minutes,
            self.current_task
        )
        self.current_block_index = 0

        self.tray.set_journey_data(self.journey_blocks, 0, self.current_task)
        self.tray.set_journey_active(True)
        self.main_window.set_journey_data(self.journey_blocks, 0)
        self.main_window.set_journey_active(True)
        self.main_window.set_task(self.current_task)
        self._show_main()

        self.notification_mgr.send_journey_start(
            total_work_minutes,
            len([b for b in self.journey_blocks if b.is_work_block])
        )

        self._start_current_block()
        self._save_state()
    
    def _start_current_block(self) -> None:
        """Start the current journey block."""
        if self.current_block_index >= len(self.journey_blocks):
            self._journey_complete()
            return
        
        block = self.journey_blocks[self.current_block_index]
        self.session_start_time = datetime.now()
        
        # Update displays
        session_type = block.session_type
        self.tray.update_status(
            session_type, 
            SessionStatus.RUNNING, 
            block.duration_seconds,
            block.duration_seconds
        )
        self.main_window.update_status(
            session_type,
            SessionStatus.RUNNING,
            block.duration_seconds,
            block.duration_seconds
        )
        
        # Send notification
        if block.is_work_block:
            self.notification_mgr.send(
                SessionType.WORK,
                f"Iniciando foco: {block.task_name or 'Trabalho'} ({self.engine.format_time(block.duration_seconds)})"
            )
        elif block.session_type == SessionType.SHORT_BREAK:
            self.notification_mgr.send_break_reminder(SessionType.SHORT_BREAK, block.duration_seconds // 60)
        elif block.session_type == SessionType.LONG_BREAK:
            self.notification_mgr.send_break_reminder(SessionType.LONG_BREAK, block.duration_seconds // 60)
        
        # Start timer
        self.timer.start()
    
    @Slot()
    def _on_tick(self) -> None:
        """Timer tick - update remaining time."""
        if self.current_block_index >= len(self.journey_blocks):
            self.timer.stop()
            return
        
        block = self.journey_blocks[self.current_block_index]
        elapsed = int((datetime.now() - self.session_start_time).total_seconds())
        remaining = max(0, block.duration_seconds - elapsed)
        
        # Update displays
        self.tray.update_status(
            block.session_type,
            SessionStatus.RUNNING,
            remaining,
            block.duration_seconds
        )
        self.main_window.update_status(
            block.session_type,
            SessionStatus.RUNNING,
            remaining,
            block.duration_seconds
        )
        
        # Check if block completed
        if remaining <= 0:
            self.timer.stop()
            self._complete_current_block()
    
    def _complete_current_block(self) -> None:
        """Handle completion of current block."""
        block = self.journey_blocks[self.current_block_index]
        actual_duration = int((datetime.now() - self.session_start_time).total_seconds())
        
        # Record session
        record = SessionRecord(
            id=f"{datetime.now().timestamp()}",
            session_type=block.session_type,
            status=SessionStatus.COMPLETED,
            planned_duration=block.duration_seconds,
            actual_duration=actual_duration,
            started_at=self.session_start_time.isoformat(),
            ended_at=datetime.now().isoformat(),
            task_name=block.task_name if block.is_work_block else ""
        )
        self.storage.append_session(record)
        
        # Move to next block
        self.current_block_index += 1

        if self.current_block_index >= len(self.journey_blocks):
            self._journey_complete()
        else:
            self.tray.set_journey_data(self.journey_blocks, self.current_block_index, self.current_task)
            self.main_window.set_journey_data(self.journey_blocks, self.current_block_index)
            # Check if next block should auto-start
            next_block = self.journey_blocks[self.current_block_index]
            should_auto_start = False
            
            if next_block.is_work_block and self.config.auto_start_work:
                should_auto_start = True
            elif not next_block.is_work_block and self.config.auto_start_breaks:
                should_auto_start = True
            
            if should_auto_start:
                self._start_current_block()
            else:
                # Show notification but wait for user
                self.tray.update_status(
                    next_block.session_type,
                    SessionStatus.IDLE,
                    next_block.duration_seconds,
                    next_block.duration_seconds
                )
                self.main_window.update_status(
                    next_block.session_type,
                    SessionStatus.IDLE,
                    next_block.duration_seconds,
                    next_block.duration_seconds
                )
                # Notify user next block is ready
                if next_block.is_work_block:
                    self.notification_mgr.send_custom(
                        "Próximo Foco Pronto",
                        f"Clique para iniciar: {next_block.task_name or 'Trabalho'}",
                        icon="media-playback-start"
                    )
                else:
                    self.notification_mgr.send_break_reminder(
                        next_block.session_type, 
                        next_block.duration_seconds // 60
                    )
        
        self._save_state()
    
    def _journey_complete(self) -> None:
        """Handle journey completion."""
        total_work = self.engine.get_work_time(self.journey_blocks)
        self.notification_mgr.send_journey_complete(total_work // 60)
        
        self.tray.update_status(
            SessionType.WORK, 
            SessionStatus.COMPLETED, 
            0, 0
        )
        self.main_window.update_status(
            SessionType.WORK,
            SessionStatus.COMPLETED,
            0, 0
        )
        self.tray.show_message(
            "Jornada Concluída! 🎉",
            f"Você completou {total_work // 60} minutos de foco produtivo!",
            QSystemTrayIcon.MessageIcon.Information,
            10000
        )
        
        # Clear state
        self.journey_blocks = []
        self.current_block_index = -1
        self._paused_remaining = None
        self.tray.set_journey_active(False)
        self.main_window.set_journey_active(False)
        self.storage.clear_state()
    
    @Slot()
    def toggle_pause(self) -> None:
        """Toggle pause/resume."""
        if self.timer.isActive():
            self.timer.stop()
            if self.current_block_index < len(self.journey_blocks):
                block = self.journey_blocks[self.current_block_index]
                elapsed = int((datetime.now() - self.session_start_time).total_seconds())
                remaining = max(0, block.duration_seconds - elapsed)
                self._paused_remaining = remaining
                self.tray.update_status(
                    block.session_type,
                    SessionStatus.PAUSED,
                    remaining,
                    block.duration_seconds
                )
                self.main_window.update_status(
                    block.session_type,
                    SessionStatus.PAUSED,
                    remaining,
                    block.duration_seconds
                )
        else:
            if self.current_block_index < len(self.journey_blocks):
                block = self.journey_blocks[self.current_block_index]
                remaining = self._paused_remaining if self._paused_remaining is not None else block.duration_seconds
                self._paused_remaining = None
                elapsed_so_far = block.duration_seconds - remaining
                self.session_start_time = datetime.now() - timedelta(seconds=elapsed_so_far)
                self.timer.start()
                self.main_window.update_status(
                    block.session_type,
                    SessionStatus.RUNNING,
                    remaining,
                    block.duration_seconds
                )
                self._on_tick()
    
    @Slot()
    def skip_session(self) -> None:
        """Skip current session."""
        if self.current_block_index < len(self.journey_blocks):
            block = self.journey_blocks[self.current_block_index]
            actual_duration = int((datetime.now() - self.session_start_time).total_seconds())
            
            record = SessionRecord(
                id=f"{datetime.now().timestamp()}",
                session_type=block.session_type,
                status=SessionStatus.SKIPPED,
                planned_duration=block.duration_seconds,
                actual_duration=actual_duration,
                started_at=self.session_start_time.isoformat(),
                ended_at=datetime.now().isoformat(),
                task_name=block.task_name if block.is_work_block else ""
            )
            self.storage.append_session(record)
            
            self.timer.stop()
            self._paused_remaining = None
            self.current_block_index += 1

            if self.current_block_index < len(self.journey_blocks):
                self.tray.set_journey_data(self.journey_blocks, self.current_block_index, self.current_task)
                self._start_current_block()
            else:
                self._journey_complete()
            
            self._save_state()

    @Slot()
    def restart_progress(self) -> None:
        """Restart journey from the first block."""
        if not self.journey_blocks:
            return
        self.timer.stop()
        self._paused_remaining = None
        self.current_block_index = 0
        self.tray.set_journey_data(self.journey_blocks, 0, self.current_task)
        self.main_window.set_journey_data(self.journey_blocks, 0)
        self._start_current_block()
        self._save_state()

    @Slot()
    def restart_session(self) -> None:
        """Restart the current session block from zero."""
        if self.current_block_index < 0 or self.current_block_index >= len(self.journey_blocks):
            return
        self.timer.stop()
        self._paused_remaining = None
        self.tray.set_journey_data(self.journey_blocks, self.current_block_index, self.current_task)
        self.main_window.set_journey_data(self.journey_blocks, self.current_block_index)
        self._start_current_block()
        self._save_state()
    
    @Slot(str)
    def set_task(self, task: str) -> None:
        """Set current task."""
        self.current_task = task
        self.tray.update_task(task)
        self.main_window.set_task(task)
        self.task_dialog.set_current_task(task)
        
        # Update current block if it's a work block
        if (self.current_block_index < len(self.journey_blocks) and 
            self.journey_blocks[self.current_block_index].is_work_block):
            self.journey_blocks[self.current_block_index].task_name = task
    
    def change_task(self, task: str) -> None:
        """Change task from tray menu."""
        self.task_dialog.set_current_task(task)
        self.task_dialog.show_at_cursor()
    
    def show_config(self) -> None:
        """Show configuration dialog."""
        dialog = ConfigDialog(self.storage, self.notification_mgr)
        if dialog.exec():
            self.config = self.storage.load_config()
            self.engine = JourneyEngine(self.config)
            self.tray.set_config(self.config)
            self.main_window.config = self.config
            self.notification_mgr.enabled = self.config.notifications_enabled
            self.notification_mgr.sound_enabled = self.config.sound_enabled
    
    def _save_state(self) -> None:
        """Save current state to disk."""
        if self.current_block_index < 0 or self.current_block_index >= len(self.journey_blocks):
            self.storage.clear_state()
            return
        
        block = self.journey_blocks[self.current_block_index]
        elapsed = int((datetime.now() - self.session_start_time).total_seconds())
        remaining = max(0, block.duration_seconds - elapsed)
        
        state = AppState(
            current_session_type=block.session_type,
            current_status=SessionStatus.PAUSED if not self.timer.isActive() else SessionStatus.RUNNING,
            remaining_seconds=remaining,
            total_planned_seconds=block.duration_seconds,
            sessions_completed_today=len(self.storage.get_today_sessions()),
            current_task=self.current_task,
            session_start_time=self.session_start_time,
            paused_at=datetime.now() if not self.timer.isActive() else None
        )
        self.storage.save_state(state)
    
    def quit(self) -> None:
        """Quit application."""
        self._save_state()
        self.tray.cleanup()
        QApplication.quit()


def main():
    """Entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("myTime")
    app.setApplicationDisplayName("myTime - Pomodoro Timer")
    app.setDesktopFileName("myTime")
    app.setQuitOnLastWindowClosed(False)

    # Set official app icon
    icon_path = resource_files("myTime").joinpath("data", "icons", "myTime.svg")
    app_icon = QIcon(str(icon_path))
    app.setWindowIcon(app_icon)

    # Create and run
    mytime = MyTimeApp()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
