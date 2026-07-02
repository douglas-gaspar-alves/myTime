"""Custom dialog for journey input with hours + minutes + optional task."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSpinBox, QLineEdit,
    QLabel, QPushButton, QComboBox
)
from PySide6.QtCore import Qt, Signal


class JourneyDialog(QDialog):
    """Dialog to input journey duration in hours+minutes + optional task."""

    journey_confirmed = Signal(int, str)  # total_minutes, task_name

    def __init__(self, current_task: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("myTime - Nova Jornada")
        self.setMinimumWidth(380)
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.CustomizeWindowHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title = QLabel("<b>Configurar Jornada de Trabalho</b>")
        layout.addWidget(title)

        # Hours and Minutes row
        time_layout = QHBoxLayout()

        time_layout.addWidget(QLabel("Horas:"))
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 8)
        self.hours_spin.setValue(2)
        self.hours_spin.setSuffix(" h")
        self.hours_spin.setFixedWidth(100)
        time_layout.addWidget(self.hours_spin)

        time_layout.addSpacing(10)
        time_layout.addWidget(QLabel("Minutos:"))
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 55)
        self.minutes_spin.setValue(0)
        self.minutes_spin.setSuffix(" min")
        self.minutes_spin.setSingleStep(5)
        self.minutes_spin.setFixedWidth(100)
        time_layout.addWidget(self.minutes_spin)

        time_layout.addStretch()
        layout.addLayout(time_layout)

        # Total label (auto-updates)
        self.total_label = QLabel()
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.total_label)

        self.hours_spin.valueChanged.connect(self._update_total)
        self.minutes_spin.valueChanged.connect(self._update_total)

        # Task (optional)
        task_layout = QHBoxLayout()
        task_layout.addWidget(QLabel("Tarefa:"))
        self.task_combo = QComboBox()
        self.task_combo.setEditable(True)
        self.task_combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)
        self.task_combo.setPlaceholderText("(opcional)")
        self.task_combo.setMinimumWidth(200)
        if current_task:
            self.task_combo.setCurrentText(current_task)
        task_layout.addWidget(self.task_combo)
        task_layout.addStretch()
        layout.addLayout(task_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        self.start_btn = QPushButton("Iniciar Jornada")
        self.start_btn.setDefault(True)
        self.start_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.start_btn)
        layout.addLayout(btn_layout)

        self._update_total()

    def _update_total(self) -> None:
        total = self.hours_spin.value() * 60 + self.minutes_spin.value()
        hours = total // 60
        mins = total % 60
        if hours > 0:
            self.total_label.setText(
                f"Total: <b>{total} min</b> ({hours}h{mins:02d}min de trabalho)"
            )
        else:
            self.total_label.setText(f"Total: <b>{total} min</b> de trabalho")
        self.start_btn.setEnabled(total > 0)

    def _on_confirm(self) -> None:
        total = self.hours_spin.value() * 60 + self.minutes_spin.value()
        task = self.task_combo.currentText().strip()
        if total > 0:
            self.journey_confirmed.emit(total, task)
            self.accept()
