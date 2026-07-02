"""Main application window - home screen."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QInputDialog, QLineEdit,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QPen
from myTime.core.models import SessionType, SessionStatus, WorkSchedule
from myTime.core.engine import ScheduledBlock
from myTime.utils import IconManager


class _BlockWidget(QFrame):
    """Single block representation in the progress bar."""

    def __init__(self, block: ScheduledBlock, is_current: bool, is_past: bool):
        super().__init__()
        self.setFixedHeight(36)
        self.setMinimumWidth(44)

        label = block.session_type.value
        if block.session_type == SessionType.WORK:
            label = "F"
        elif block.session_type == SessionType.SHORT_BREAK:
            label = "P"
        elif block.session_type == SessionType.LONG_BREAK:
            label = "L"

        if is_current:
            self.setStyleSheet(
                "background-color: #e74c3c; border: 3px solid #c0392b; "
                "border-radius: 6px; color: white; font-weight: bold;"
            )
        elif is_past:
            self.setStyleSheet(
                "background-color: #bdc3c7; border: 1px solid #95a5a6; "
                "border-radius: 6px; color: #7f8c8d;"
            )
        else:
            self.setStyleSheet(
                "background-color: #34495e; border: 1px solid #2c3e50; "
                "border-radius: 6px; color: white;"
            )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        letter = QLabel(label)
        letter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont()
        f.setBold(True)
        f.setPointSize(10)
        letter.setFont(f)
        layout.addWidget(letter)

        dur_label = QLabel(f"{block.duration_seconds // 60}'")
        dur_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        df = QFont()
        df.setPointSize(7)
        dur_label.setFont(df)
        layout.addWidget(dur_label)


class MainWindow(QWidget):
    """Home screen with clock, pause, blocks."""

    pause_toggled = Signal()
    skip_requested = Signal()
    new_journey_requested = Signal()
    config_requested = Signal()
    task_change_requested = Signal(str)

    def __init__(self, config: WorkSchedule):
        super().__init__()
        self.config = config
        self.icon_manager = IconManager()

        self._current_task = ""
        self._session_type = SessionType.WORK
        self._status = SessionStatus.IDLE
        self._remaining = 0
        self._total = 0
        self._journey_blocks: list[ScheduledBlock] = []
        self._journey_block_index = -1
        self._is_paused = False

        self.setWindowTitle("myTime")
        self.setFixedSize(380, 520)
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint
        )

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # Top bar: title + edit task
        top_row = QHBoxLayout()
        title = QLabel("⏰ myTime")
        tf = QFont()
        tf.setBold(True)
        tf.setPointSize(14)
        title.setFont(tf)
        top_row.addWidget(title)
        top_row.addStretch()
        self.task_btn = QPushButton("📋 Tarefa: (nenhuma)")
        self.task_btn.setFlat(True)
        self.task_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.task_btn.clicked.connect(self._on_task_click)
        top_row.addWidget(self.task_btn)
        layout.addLayout(top_row)

        # Clock area
        clock_widget = QWidget()
        clock_widget.setFixedSize(260, 260)
        clock_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        clock_layout = QVBoxLayout(clock_widget)
        clock_layout.setContentsMargins(0, 0, 0, 0)
        clock_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.clock_label = QLabel()
        self.clock_label.setFixedSize(240, 240)
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clock_layout.addWidget(self.clock_label)

        self.status_label = QLabel("Pronto")
        sf = QFont()
        sf.setPointSize(11)
        self.status_label.setFont(sf)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clock_layout.addWidget(self.status_label)

        layout.addWidget(clock_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # Buttons
        btn_row = QHBoxLayout()
        self.pause_btn = QPushButton("⏸ Pausar")
        self.pause_btn.setMinimumHeight(36)
        self.pause_btn.clicked.connect(self.pause_toggled.emit)
        self.pause_btn.setEnabled(False)
        btn_row.addWidget(self.pause_btn)

        self.skip_btn = QPushButton("⏭ Pular")
        self.skip_btn.setMinimumHeight(36)
        self.skip_btn.clicked.connect(self.skip_requested.emit)
        self.skip_btn.setEnabled(False)
        btn_row.addWidget(self.skip_btn)
        layout.addLayout(btn_row)

        # Blocks row
        self.blocks_widget = QWidget()
        self.blocks_layout = QVBoxLayout(self.blocks_widget)
        self.blocks_layout.setContentsMargins(0, 0, 0, 0)

        self.blocks_row_label = QLabel("Jornada:")
        blf = QFont()
        blf.setBold(True)
        blf.setPointSize(10)
        self.blocks_row_label.setFont(blf)
        self.blocks_layout.addWidget(self.blocks_row_label)

        self.blocks_row = QHBoxLayout()
        self.blocks_row.setSpacing(4)
        self.blocks_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.blocks_layout.addLayout(self.blocks_row)

        self.blocks_info = QLabel("")
        self.blocks_info.setWordWrap(True)
        bif = QFont()
        bif.setPointSize(9)
        self.blocks_info.setFont(bif)
        self.blocks_layout.addWidget(self.blocks_info)
        layout.addWidget(self.blocks_widget)

        # Bottom buttons
        bottom_row = QHBoxLayout()
        new_journey_btn = QPushButton("+ Nova Jornada")
        new_journey_btn.clicked.connect(self.new_journey_requested.emit)
        bottom_row.addWidget(new_journey_btn)

        config_btn = QPushButton("⚙ Config")
        config_btn.clicked.connect(self.config_requested.emit)
        bottom_row.addWidget(config_btn)
        layout.addLayout(bottom_row)

    def _on_task_click(self) -> None:
        text, ok = QInputDialog.getText(
            self, "Alterar Tarefa", "Nome da tarefa:",
            QLineEdit.EchoMode.Normal, self._current_task
        )
        if ok and text:
            self.task_change_requested.emit(text)

    def update_status(
        self,
        session_type: SessionType,
        status: SessionStatus,
        remaining_seconds: int,
        total_seconds: int,
    ) -> None:
        self._session_type = session_type
        self._status = status
        self._remaining = remaining_seconds
        self._total = total_seconds

        mins, secs = divmod(remaining_seconds, 60)
        time_text = f"{mins:02d}:{secs:02d}" if self.config.icon_text_show_seconds else f"{mins:02d}"

        if status == SessionStatus.PAUSED:
            self._is_paused = True
            self.pause_btn.setText("▶ Retomar")
            self.status_label.setText(f"⏸ PAUSADO {time_text}")
        else:
            self._is_paused = False
            self.pause_btn.setText("⏸ Pausar")
            type_map = {
                SessionType.WORK: "Foco",
                SessionType.SHORT_BREAK: "Pausa Curta",
                SessionType.LONG_BREAK: "Pausa Longa",
            }
            label = type_map.get(session_type, "")
            self.status_label.setText(f"{label}: {time_text}" if label else time_text)

        pause_enabled = status in (SessionStatus.RUNNING, SessionStatus.PAUSED)
        self.pause_btn.setEnabled(pause_enabled)
        self.skip_btn.setEnabled(status == SessionStatus.RUNNING)

        self._render_clock(session_type, status, remaining_seconds, total_seconds)

    def _render_clock(
        self,
        session_type: SessionType,
        status: SessionStatus,
        remaining_seconds: int,
        total_seconds: int,
    ) -> None:
        progress = 1.0 - (remaining_seconds / total_seconds) if total_seconds > 0 else 0.0
        state_map = {
            SessionType.WORK: "work",
            SessionType.SHORT_BREAK: "short_break",
            SessionType.LONG_BREAK: "long_break",
        }
        state = state_map.get(session_type, "idle")
        if status == SessionStatus.PAUSED:
            state = "paused"
        elif status == SessionStatus.COMPLETED:
            state = "completed"
        elif status == SessionStatus.IDLE:
            state = "idle"

        color_map = {
            "work": self.config.icon_color_work,
            "short_break": self.config.icon_color_short_break,
            "long_break": self.config.icon_color_long_break,
            "paused": self.config.icon_color_paused,
            "idle": self.config.icon_color_idle,
            "completed": self.config.icon_color_idle,
        }
        color = color_map.get(state, self.config.icon_color_idle)

        mins, secs = divmod(remaining_seconds, 60)
        time_text = f"{mins:02d}:{secs:02d}" if self.config.icon_text_show_seconds else f"{mins:02d}"

        icon = self.icon_manager.generate_icon(
            state=state,
            progress=progress,
            color=color,
            size=220,
            show_time=True,
            time_text=time_text,
            font_size=self.config.icon_text_font_size + 4,
            text_color=self.config.icon_text_color,
            bg_color=self.config.icon_bg_color,
            bg_opacity=self.config.icon_bg_opacity,
        )
        self.clock_label.setPixmap(icon.pixmap(220, 220))

    def set_task(self, task_name: str) -> None:
        self._current_task = task_name
        display = task_name if task_name else "(nenhuma)"
        self.task_btn.setText(f"📋 {display}")

    def set_journey_data(self, blocks: list[ScheduledBlock], current_index: int) -> None:
        self._journey_blocks = blocks
        self._journey_block_index = current_index
        self._rebuild_blocks()

    def set_journey_active(self, active: bool) -> None:
        self.blocks_widget.setVisible(active)

    def _rebuild_blocks(self) -> None:
        while self.blocks_row.count():
            item = self.blocks_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, block in enumerate(self._journey_blocks):
            is_current = i == self._journey_block_index
            is_past = i < self._journey_block_index
            bw = _BlockWidget(block, is_current, is_past)
            self.blocks_row.addWidget(bw)

            if i < len(self._journey_blocks) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet("color: #7f8c8d; font-size: 14px;")
                self.blocks_row.addWidget(arrow)

        total_work = sum(b.duration_seconds for b in self._journey_blocks if b.is_work_block)
        work_h, work_m = divmod(total_work // 60, 60)
        elapsed = sum(b.duration_seconds for b in self._journey_blocks[:self._journey_block_index])
        el_h, el_m = divmod(elapsed // 60, 60)
        self.blocks_info.setText(
            f"⏱ {work_h}h{work_m:02d}min trabalho  |  "
            f"Bloco {self._journey_block_index + 1}/{len(self._journey_blocks)}"
        )
