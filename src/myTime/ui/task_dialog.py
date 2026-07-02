"""Task input dialog for quick task entry."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QComboBox, QPushButton, QLabel
)
from PySide6.QtCore import Qt, Signal
from myTime.core.storage import StorageManager


class TaskDialog(QDialog):
    """Quick task input dialog - shows on left click tray or shortcut."""
    
    task_submitted = Signal(str)  # task name
    
    def __init__(self, storage: StorageManager, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.setWindowTitle("myTime - Tarefa Atual")
        self.setFixedWidth(400)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        
        self._build_ui()
        self._load_recent_tasks()
    
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Current task label
        self.current_label = QLabel("Tarefa atual: (nenhuma)")
        self.current_label.setWordWrap(True)
        layout.addWidget(self.current_label)
        
        # Input with combo for recent tasks
        input_layout = QHBoxLayout()
        
        self.task_combo = QComboBox()
        self.task_combo.setEditable(True)
        self.task_combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)
        self.task_combo.setMaxCount(20)
        self.task_combo.setPlaceholderText("Digite a tarefa ou selecione recente...")
        input_layout.addWidget(self.task_combo)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._on_accept)
        self.ok_btn.setDefault(True)
        input_layout.addWidget(self.ok_btn)
        
        layout.addLayout(input_layout)
        
        # Quick buttons
        quick_layout = QHBoxLayout()
        for task in ["Código", "Estudos", "Leitura", "Email", "Reunião"]:
            btn = QPushButton(task)
            btn.clicked.connect(lambda checked, t=task: self._set_quick_task(t))
            quick_layout.addWidget(btn)
        
        layout.addLayout(quick_layout)
        
        # Connect enter key
        self.task_combo.lineEdit().returnPressed.connect(self._on_accept)
    
    def _load_recent_tasks(self) -> None:
        """Load recent tasks from storage."""
        tasks = self.storage.get_recent_tasks()
        self.task_combo.addItems(tasks[:10])
    
    def set_current_task(self, task: str) -> None:
        """Set current task display."""
        if task:
            self.current_label.setText(f"Tarefa atual: {task}")
        else:
            self.current_label.setText("Tarefa atual: (nenhuma)")
        self.task_combo.setCurrentText(task)
    
    def _set_quick_task(self, task: str) -> None:
        """Set task from quick button."""
        self.task_combo.setCurrentText(task)
    
    def _on_accept(self) -> None:
        task = self.task_combo.currentText().strip()
        if task:
            self.task_submitted.emit(task)
        self.accept()
    
    def show_at_cursor(self) -> None:
        """Show dialog at mouse cursor position."""
        from PySide6.QtGui import QCursor
        self.move(QCursor.pos())
        self.show()
        self.raise_()
        self.activateWindow()
        self.task_combo.setFocus()
        self.task_combo.lineEdit().selectAll()
