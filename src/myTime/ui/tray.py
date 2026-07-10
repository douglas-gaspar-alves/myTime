"""System tray icon and menu."""
from __future__ import annotations
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QAction, QIcon, QCursor
from myTime.core.models import SessionType, SessionStatus, WorkSchedule
from myTime.core.engine import ScheduledBlock
from myTime.utils import IconManager


class TrayManager(QObject):
    """Manages system tray icon, menu, and user interactions."""

    new_journey_requested = Signal(int, str)
    config_requested = Signal()
    task_change_requested = Signal(str)
    pause_toggle_requested = Signal()
    skip_session_requested = Signal()
    continue_requested = Signal()
    restart_progress_requested = Signal()
    restart_session_requested = Signal()
    show_main_requested = Signal()
    quit_requested = Signal()

    def __init__(self, config: WorkSchedule):
        super().__init__()
        self.config = config
        self.icon_manager = IconManager()
        self._current_task = ""
        self._current_state = "idle"
        self._current_progress = 0.0
        self._time_text = ""
        self._journey_active = False
        self._journey_blocks: list[ScheduledBlock] = []
        self._journey_block_index = -1

        self.tray = QSystemTrayIcon()
        self.tray.setToolTip("myTime - Pronto para iniciar")

        self._is_waiting = False
        self.status_action: QAction | None = None
        self.task_action: QAction | None = None
        self.pause_action: QAction | None = None
        self.continue_action: QAction | None = None
        self.restart_progress_action: QAction | None = None
        self.restart_session_action: QAction | None = None

        self._update_icon()
        self._build_menu()
        self.tray.show()
        self.tray.activated.connect(self._on_tray_activated)

    def _build_menu(self) -> None:
        self.menu = QMenu()
        menu = self.menu

        self.status_action = QAction("Status: Pronto", menu)
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)

        self.task_action = QAction("📋 Tarefa: (nenhuma)", menu)
        self.task_action.triggered.connect(self._request_task_input)
        menu.addAction(self.task_action)

        menu.addSeparator()

        act = QAction("Nova Jornada...", menu)
        act.triggered.connect(self._request_new_journey)
        menu.addAction(act)

        act = QAction("Configurações...", menu)
        act.triggered.connect(self.config_requested.emit)
        menu.addAction(act)

        menu.addSeparator()

        self.pause_action = QAction("Pausar", menu)
        self.pause_action.triggered.connect(self.pause_toggle_requested.emit)
        menu.addAction(self.pause_action)

        self.continue_action = QAction("▶ Continuar", menu)
        self.continue_action.triggered.connect(self.continue_requested.emit)
        self.continue_action.setVisible(False)
        menu.addAction(self.continue_action)

        act = QAction("Pular Sessão", menu)
        act.triggered.connect(self.skip_session_requested.emit)
        menu.addAction(act)

        self.restart_progress_action = QAction("Reiniciar Progresso", menu)
        self.restart_progress_action.triggered.connect(self._restart_progress)
        self.restart_progress_action.setEnabled(False)
        menu.addAction(self.restart_progress_action)

        self.restart_session_action = QAction("Reiniciar Sessão", menu)
        self.restart_session_action.triggered.connect(self._restart_session)
        self.restart_session_action.setEnabled(False)
        menu.addAction(self.restart_session_action)

        menu.addSeparator()

        act = QAction("Sair", menu)
        act.triggered.connect(self.quit_requested.emit)
        menu.addAction(act)

        self.tray.setContextMenu(self.menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Context:
            if self.menu:
                self.menu.popup(QCursor.pos())
        elif reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.MiddleClick,
        ):
            self.show_main_requested.emit()

    # --- Journey data ---

    def set_journey_data(self, blocks: list[ScheduledBlock], current_index: int, task_name: str) -> None:
        """Store journey data for progress display."""
        self._journey_blocks = blocks
        self._journey_block_index = current_index
        self._current_task = task_name

    def set_journey_active(self, active: bool) -> None:
        """Enable/disable journey-related actions."""
        self._journey_active = active
        if self.restart_progress_action:
            self.restart_progress_action.setEnabled(active)
        if self.restart_session_action:
            self.restart_session_action.setEnabled(active)

    # --- Task / progress actions ---

    def _request_task_input(self) -> None:
        """Open task dialog or show main window based on journey state."""
        if self._journey_active and self._journey_blocks:
            self.show_main_requested.emit()
        else:
            self.task_change_requested.emit("")

    def _restart_progress(self) -> None:
        self.restart_progress_requested.emit()

    def _restart_session(self) -> None:
        self.restart_session_requested.emit()

    # --- Journey creation ---

    def _request_new_journey(self) -> None:
        """Show custom JourneyDialog with hours+minutes+task."""
        from myTime.ui.journey_dialog import JourneyDialog

        task = self._current_task
        dialog = JourneyDialog(current_task=task)
        dialog.journey_confirmed.connect(self._on_journey_confirmed)
        dialog.exec()

    def _on_journey_confirmed(self, total_minutes: int, task_name: str) -> None:
        self.new_journey_requested.emit(total_minutes, task_name)

    # --- Status updates ---

    def update_status(
        self,
        session_type: SessionType,
        status: SessionStatus,
        remaining_seconds: int,
        total_seconds: int,
        is_waiting: bool = False,
    ) -> None:
        """Update tray icon, tooltip, and menu status."""
        if is_waiting:
            self._is_waiting = True
        mins, secs = divmod(remaining_seconds, 60)
        if self.config.icon_text_show_seconds:
            self._time_text = f"{mins:02d}:{secs:02d}"
        else:
            self._time_text = f"{mins:02d}"
        progress = 1.0 - (remaining_seconds / total_seconds) if total_seconds > 0 else 0.0
        self._current_progress = progress

        if status == SessionStatus.PAUSED:
            self._current_state = "paused"
            status_text = f"[PAUSADO] {self._time_text}"
        elif self._is_waiting and status == SessionStatus.IDLE:
            self._current_state = "idle"
            status_text = "▶ Aguardando continuar"
        elif session_type == SessionType.WORK:
            self._current_state = "work"
            status_text = f"Foco: {self._time_text}"
        elif session_type == SessionType.SHORT_BREAK:
            self._current_state = "short_break"
            status_text = f"Pausa Curta: {self._time_text}"
        elif session_type == SessionType.LONG_BREAK:
            self._current_state = "long_break"
            status_text = f"Pausa Longa: {self._time_text}"
        elif status == SessionStatus.COMPLETED:
            self._current_state = "completed"
            status_text = "Jornada Concluída"
            progress = 1.0
        else:
            self._current_state = "idle"
            status_text = "Pronto"
            progress = 0.0

        self.tray.setToolTip(f"myTime | {status_text}")
        if self.status_action:
            self.status_action.setText(f"Status: {status_text}")

        if self.task_action:
            task_display = self._current_task if self._current_task else "(nenhuma)"
            self.task_action.setText(f"📋 Tarefa: {task_display}")

        if self.pause_action:
            self.pause_action.setText("Retomar" if status == SessionStatus.PAUSED else "Pausar")

        if self.continue_action:
            self.continue_action.setVisible(self._is_waiting and status == SessionStatus.IDLE)

        self._update_icon()

    def _update_icon(self) -> None:
        """Regenerate tray icon based on current state and config."""
        color_map = {
            "work": self.config.icon_color_work,
            "short_break": self.config.icon_color_short_break,
            "long_break": self.config.icon_color_long_break,
            "paused": self.config.icon_color_paused,
            "idle": self.config.icon_color_idle,
            "completed": self.config.icon_color_idle,
        }
        color = color_map.get(self._current_state, self.config.icon_color_idle)

        icon = self.icon_manager.generate_icon(
            state=self._current_state,
            progress=self._current_progress,
            color=color,
            size=self.config.icon_size,
            show_time=False,
            time_text="",
            font_size=14,
            text_color=self.config.icon_text_color,
            bg_color=self.config.icon_bg_color,
            bg_opacity=self.config.icon_bg_opacity,
            show_letter=self.config.icon_show_letter,
        )
        self.tray.setIcon(icon)

    def update_task(self, task_name: str) -> None:
        """Update displayed task name in the menu."""
        self._current_task = task_name
        if self.task_action:
            task_display = task_name if task_name else "(nenhuma)"
            self.task_action.setText(f"📋 Tarefa: {task_display}")

    def show_message(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
        msecs: int = 5000,
    ) -> None:
        """Show tray notification bubble."""
        self.tray.showMessage(title, message, icon, msecs)

    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable pause action."""
        if self.pause_action:
            self.pause_action.setEnabled(enabled)

    def set_config(self, config: WorkSchedule) -> None:
        """Update config reference and refresh icon."""
        self.config = config
        self._update_icon()

    def set_waiting_continue(self, waiting: bool) -> None:
        """Set whether we are waiting for user to continue after a block."""
        self._is_waiting = waiting
        if self.continue_action:
            self.continue_action.setVisible(waiting)

    def cleanup(self) -> None:
        """Clean up tray icon."""
        self.tray.hide()
