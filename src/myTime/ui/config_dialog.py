"""Advanced configuration dialog."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QFormLayout,
    QSpinBox, QCheckBox, QComboBox, QLineEdit, QDialogButtonBox,
    QLabel, QGroupBox, QHBoxLayout, QFileDialog, QPushButton,
    QTimeEdit, QMessageBox, QButtonGroup, QRadioButton,
    QFrame, QSlider
)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QFont, QColor, QPixmap, QPainter
from myTime.core.models import WorkSchedule
from myTime.core.storage import StorageManager
from myTime.utils import NotificationManager


class ConfigDialog(QDialog):
    """Advanced configuration dialog with tabs."""
    
    def __init__(self, storage: StorageManager, notification_mgr: NotificationManager, parent=None):
        super().__init__(parent)
        self.storage = storage
        self.notification_mgr = notification_mgr
        self.config = storage.load_config()
        
        self.setWindowTitle("myTime - Configurações")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self._build_ui()
        self._load_config()
    
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Build tabs
        self._build_general_tab()
        self._build_times_tab()
        self._build_notifications_tab()
        self._build_icon_tab()
        self._build_advanced_tab()
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply)
        layout.addWidget(buttons)
    
    def _build_general_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Language
        lang_group = QGroupBox("Idioma / Language")
        lang_layout = QFormLayout(lang_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["pt_BR", "en_US"])
        lang_layout.addRow("Idioma:", self.language_combo)
        
        layout.addWidget(lang_group)
        
        # Daily schedule
        schedule_group = QGroupBox("Horário de Trabalho")
        schedule_layout = QFormLayout(schedule_group)
        
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm")
        self.start_time.setTime(QTime(9, 0))
        schedule_layout.addRow("Início do dia:", self.start_time)
        
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm")
        self.end_time.setTime(QTime(18, 0))
        schedule_layout.addRow("Fim do dia:", self.end_time)
        
        self.daily_goal = QSpinBox()
        self.daily_goal.setRange(1, 20)
        self.daily_goal.setSuffix(" sessões")
        schedule_layout.addRow("Meta diária:", self.daily_goal)
        
        layout.addWidget(schedule_group)
        
        # Auto behaviors
        auto_group = QGroupBox("Comportamento Automático")
        auto_layout = QFormLayout(auto_group)
        
        self.auto_start_breaks = QCheckBox("Iniciar pausas automaticamente")
        auto_layout.addRow(self.auto_start_breaks)
        
        self.auto_start_work = QCheckBox("Iniciar foco automaticamente após pausa")
        auto_layout.addRow(self.auto_start_work)
        
        self.minimize_to_tray = QCheckBox("Minimizar para bandeja ao fechar janela")
        self.minimize_to_tray.setChecked(True)
        auto_layout.addRow(self.minimize_to_tray)
        
        layout.addWidget(auto_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Geral")
    
    def _build_times_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Pomodoro durations
        pomo_group = QGroupBox("Durações do Pomodoro")
        pomo_layout = QFormLayout(pomo_group)
        
        self.work_duration = QSpinBox()
        self.work_duration.setRange(1, 120)
        self.work_duration.setSuffix(" min")
        self.work_duration.setSingleStep(1)
        pomo_layout.addRow("Foco:", self.work_duration)
        
        self.short_break = QSpinBox()
        self.short_break.setRange(1, 60)
        self.short_break.setSuffix(" min")
        pomo_layout.addRow("Pausa Curta:", self.short_break)
        
        self.long_break = QSpinBox()
        self.long_break.setRange(1, 60)
        self.long_break.setSuffix(" min")
        pomo_layout.addRow("Pausa Longa:", self.long_break)
        
        self.sessions_before_long = QSpinBox()
        self.sessions_before_long.setRange(2, 10)
        self.sessions_before_long.setSuffix(" sessões")
        pomo_layout.addRow("Sessões antes da pausa longa:", self.sessions_before_long)
        
        layout.addWidget(pomo_group)
        
        # Preview
        preview_group = QGroupBox("Prévia da Jornada (8h de trabalho)")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        self.preview_label.setFont(QFont("monospace", 9))
        preview_layout.addWidget(self.preview_label)
        
        # Connect spinboxes to update preview
        for spin in [self.work_duration, self.short_break, self.long_break, self.sessions_before_long]:
            spin.valueChanged.connect(self._update_preview)
        
        layout.addWidget(preview_group)
        layout.addStretch()
        self.tabs.addTab(tab, "Tempos")
    
    def _build_notifications_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Desktop notifications
        notif_group = QGroupBox("Notificações de Desktop")
        notif_layout = QFormLayout(notif_group)
        
        self.enable_notifications = QCheckBox("Ativar notificações do sistema")
        notif_layout.addRow(self.enable_notifications)
        
        self.notification_duration = QSpinBox()
        self.notification_duration.setRange(3, 30)
        self.notification_duration.setSuffix(" seg")
        self.notification_duration.setValue(6)
        notif_layout.addRow("Duração:", self.notification_duration)
        
        layout.addWidget(notif_group)
        
        # Sounds
        sound_group = QGroupBox("Sons")
        sound_layout = QFormLayout(sound_group)
        
        self.enable_sounds = QCheckBox("Tocar sons de notificação")
        sound_layout.addRow(self.enable_sounds)
        
        sound_file_layout = QHBoxLayout()
        self.sound_file = QLineEdit()
        self.sound_file.setPlaceholderText("Usar som embutido ou do sistema")
        self.sound_file.setReadOnly(True)
        sound_file_layout.addWidget(self.sound_file)
        
        self.browse_sound_btn = QPushButton("Procurar...")
        self.browse_sound_btn.clicked.connect(self._browse_sound)
        sound_file_layout.addWidget(self.browse_sound_btn)
        
        self.test_sound_btn = QPushButton("Testar")
        self.test_sound_btn.clicked.connect(self._test_sound)
        sound_file_layout.addWidget(self.test_sound_btn)
        
        sound_layout.addRow("Som personalizado:", sound_file_layout)
        
        layout.addWidget(sound_group)
        layout.addStretch()
        self.tabs.addTab(tab, "Notificações")
    
    def _build_icon_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Icon size
        size_group = QGroupBox("Tamanho do Ícone")
        size_layout = QVBoxLayout(size_group)
        self.icon_size_group = QButtonGroup(self)
        sizes = [(22, "Pequeno (22px)"), (32, "Médio (32px)"),
                 (48, "Grande (48px)"), (64, "Extra (64px)")]
        for val, label in sizes:
            rb = QRadioButton(label)
            self.icon_size_group.addButton(rb, val)
            size_layout.addWidget(rb)
        layout.addWidget(size_group)

        # Time text options
        time_group = QGroupBox("Texto no Ícone")
        time_layout = QVBoxLayout(time_group)

        self.icon_font_size = QSpinBox()
        self.icon_font_size.setRange(6, 72)
        self.icon_font_size.setValue(48)
        self.icon_font_size.setSuffix(" px")

        self.icon_show_seconds = QCheckBox("Mostrar segundos (MM:SS)")

        text_color_row = QHBoxLayout()
        self.icon_text_color_preview = QFrame()
        self.icon_text_color_preview.setFixedSize(36, 28)
        self.icon_text_color_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.icon_text_color_preview.setFrameShape(QFrame.Shape.Box)
        self.icon_text_color_edit = QLineEdit()
        self.icon_text_color_edit.setFixedWidth(80)
        text_color_row.addWidget(self.icon_text_color_preview)
        text_color_row.addWidget(self.icon_text_color_edit)

        self._setup_preview_click(self.icon_text_color_preview, "icon_text_color", self.icon_text_color_edit)
        self.icon_text_color_edit.textChanged.connect(
            lambda text: self._update_preview_frame(self.icon_text_color_preview, text)
        )

        fmt = QFormLayout()
        fmt.addRow("Tamanho da fonte:", self.icon_font_size)
        fmt.addRow(self.icon_show_seconds)
        fmt.addRow("Cor do texto:", text_color_row)
        time_layout.addLayout(fmt)

        self.show_letter_cb = QCheckBox("Mostrar letra (F/P/L) — quando o tempo não estiver visível")
        self.show_letter_cb.setChecked(True)
        time_layout.addWidget(self.show_letter_cb)

        layout.addWidget(time_group)

        # Colors
        colors_group = QGroupBox("Cores por Estado")
        colors_layout = QFormLayout(colors_group)

        self._color_buttons = {}
        states = [
            ("icon_color_work", "Foco", "#e74c3c"),
            ("icon_color_short_break", "Pausa Curta", "#2ecc71"),
            ("icon_color_long_break", "Pausa Longa", "#3498db"),
            ("icon_color_paused", "Pausado", "#f39c12"),
            ("icon_color_idle", "Parado", "#95a5a6"),
        ]
        for attr, label, _ in states:
            row = QHBoxLayout()
            preview = QFrame()
            preview.setFixedSize(36, 28)
            preview.setCursor(Qt.CursorShape.PointingHandCursor)
            preview.setFrameShape(QFrame.Shape.Box)
            color_edit = QLineEdit()
            color_edit.setFixedWidth(80)
            row.addWidget(preview)
            row.addWidget(color_edit)
            colors_layout.addRow(f"{label}:", row)
            self._color_buttons[attr] = (preview, color_edit)

            self._setup_preview_click(preview, attr, color_edit)
            color_edit.textChanged.connect(lambda text, p=preview: self._update_preview_frame(p, text))

        layout.addWidget(colors_group)

        # Background
        bg_group = QGroupBox("Fundo do Ícone")
        bg_layout = QFormLayout(bg_group)

        bg_color_row = QHBoxLayout()
        self.icon_bg_color_preview = QFrame()
        self.icon_bg_color_preview.setFixedSize(36, 28)
        self.icon_bg_color_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.icon_bg_color_preview.setFrameShape(QFrame.Shape.Box)
        self.icon_bg_color_edit = QLineEdit()
        self.icon_bg_color_edit.setFixedWidth(80)
        bg_color_row.addWidget(self.icon_bg_color_preview)
        bg_color_row.addWidget(self.icon_bg_color_edit)
        bg_layout.addRow("Cor:", bg_color_row)
        self._setup_preview_click(self.icon_bg_color_preview, "icon_bg_color", self.icon_bg_color_edit)
        self.icon_bg_color_edit.textChanged.connect(
            lambda text: self._update_preview_frame(self.icon_bg_color_preview, text)
        )

        opacity_row = QHBoxLayout()
        self.icon_bg_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.icon_bg_opacity_slider.setRange(0, 255)
        self.icon_bg_opacity_label = QLabel("180")
        self.icon_bg_opacity_label.setFixedWidth(30)
        opacity_row.addWidget(self.icon_bg_opacity_slider)
        opacity_row.addWidget(self.icon_bg_opacity_label)
        bg_layout.addRow("Opacidade:", opacity_row)
        self.icon_bg_opacity_slider.valueChanged.connect(
            lambda v: self.icon_bg_opacity_label.setText(str(v))
        )

        layout.addWidget(bg_group)
        layout.addStretch()
        self.tabs.addTab(tab, "Ícone")

    def _setup_preview_click(self, preview: QFrame, attr: str, color_edit: QLineEdit) -> None:
        preview.mousePressEvent = lambda event: self._pick_color(attr, color_edit)

    def _pick_color(self, attr: str, color_edit: QLineEdit) -> None:
        from PySide6.QtWidgets import QColorDialog
        current = QColor(color_edit.text())
        color = QColorDialog.getColor(current, self, f"Cor para {attr}")
        if color.isValid():
            color_edit.setText(color.name())

    def _update_preview_frame(self, preview: QFrame, text: str) -> None:
        color = QColor(text)
        border_color = preview.palette().color(preview.foregroundRole()).darker(130).name()
        if color.isValid():
            preview.setStyleSheet(
                f"background-color: {color.name()}; border: 2px solid {border_color}; border-radius: 4px;"
            )
        else:
            preview.setStyleSheet(
                f"background-color: white; border: 2px solid {border_color}; border-radius: 4px;"
            )

    def _build_advanced_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Data management
        data_group = QGroupBox("Dados")
        data_layout = QVBoxLayout(data_group)
        
        export_btn = QPushButton("Exportar Dados...")
        export_btn.clicked.connect(self._export_data)
        data_layout.addWidget(export_btn)
        
        import_btn = QPushButton("Importar Dados...")
        import_btn.clicked.connect(self._import_data)
        data_layout.addWidget(import_btn)
        
        reset_btn = QPushButton("Redefinir Configurações")
        reset_btn.clicked.connect(self._reset_config)
        reset_btn.setStyleSheet("QPushButton { color: red; }")
        data_layout.addWidget(reset_btn)
        
        layout.addWidget(data_group)
        
        # Config directory
        dir_group = QGroupBox("Diretório de Configuração")
        dir_layout = QVBoxLayout(dir_group)
        
        self.config_dir_label = QLabel()
        self.config_dir_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.config_dir_label.setWordWrap(True)
        dir_layout.addWidget(self.config_dir_label)
        
        open_dir_btn = QPushButton("Abrir Pasta")
        open_dir_btn.clicked.connect(self._open_config_dir)
        dir_layout.addWidget(open_dir_btn)
        
        layout.addWidget(dir_group)
        
        # About
        about_group = QGroupBox("Sobre")
        about_layout = QVBoxLayout(about_group)
        
        about_text = QLabel("""<b>myTime</b> v0.1.0
        <br>Gerenciador inteligente de Pomodoro e Jornadas
        <br><br>Desenvolvido com PySide6
        <br>Licença MIT""")
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)
        
        layout.addWidget(about_group)
        layout.addStretch()
        self.tabs.addTab(tab, "Avançado")
    
    def _load_config(self) -> None:
        """Load config into UI."""
        c = self.config
        
        self.language_combo.setCurrentText(c.language)
        self.start_time.setTime(QTime.fromString(c.work_start_time, "HH:mm"))
        self.end_time.setTime(QTime.fromString(c.work_end_time, "HH:mm"))
        self.daily_goal.setValue(c.daily_goal_sessions)
        
        self.work_duration.setValue(c.work_duration // 60)
        self.short_break.setValue(c.short_break_duration // 60)
        self.long_break.setValue(c.long_break_duration // 60)
        self.sessions_before_long.setValue(c.sessions_before_long_break)
        
        self.auto_start_breaks.setChecked(c.auto_start_breaks)
        self.auto_start_work.setChecked(c.auto_start_work)
        self.minimize_to_tray.setChecked(True)  # Default
        
        self.enable_notifications.setChecked(c.notifications_enabled)
        self.enable_sounds.setChecked(c.sound_enabled)
        bundled = self.notification_mgr.get_bundled_sound_path()
        if bundled:
            self.sound_file.setPlaceholderText(f"Som embutido: {bundled}")
        
        self._update_preview()
        self._update_config_dir_label()

        # Icon settings
        btn = self.icon_size_group.button(c.icon_size)
        if btn:
            btn.setChecked(True)
        else:
            fallback = self.icon_size_group.button(48)
            if fallback:
                fallback.setChecked(True)
        self.show_letter_cb.setChecked(c.icon_show_letter if hasattr(c, 'icon_show_letter') else True)
        self.icon_font_size.setValue(c.icon_text_font_size if hasattr(c, 'icon_text_font_size') else 48)
        self.icon_show_seconds.setChecked(c.icon_text_show_seconds if hasattr(c, 'icon_text_show_seconds') else True)
        self.icon_text_color_edit.setText(c.icon_text_color if hasattr(c, 'icon_text_color') else "#2c3e50")
        for attr, (preview, color_edit) in self._color_buttons.items():
            val = getattr(c, attr, "")
            color_edit.setText(val)

        # Icon background
        self.icon_bg_color_edit.setText(c.icon_bg_color)
        self.icon_bg_opacity_slider.setValue(c.icon_bg_opacity)
        self.icon_bg_opacity_label.setText(str(c.icon_bg_opacity))
    
    def _update_preview(self) -> None:
        """Update journey preview."""
        work = self.work_duration.value()
        short_b = self.short_break.value()
        long_b = self.long_break.value()
        interval = self.sessions_before_long.value()
        
        total_work = 480  # 8 hours
        sessions = []
        remaining = total_work
        count = 0
        
        while remaining > 0:
            w = min(work, remaining)
            sessions.append(f"Foco {w}min")
            remaining -= w
            count += 1
            
            if remaining > 0:
                if count % interval == 0:
                    sessions.append(f"Pausa Longa {long_b}min")
                else:
                    sessions.append(f"Pausa Curta {short_b}min")
        
        total_break = sum(int(s.split()[-1].replace("min", "")) for s in sessions if "Pausa" in s)
        text = " → ".join(sessions)
        text += f"\n\nTotal: {total_work}min trabalho + {total_break}min pausas = {(total_work + total_break)//60}h{(total_work + total_break)%60:02d}min"
        self.preview_label.setText(text)
    
    def _update_config_dir_label(self) -> None:
        """Update config directory label."""
        from myTime.core.storage import storage
        self.config_dir_label.setText(f"Pasta: {storage.get_config_dir()}")
    
    def _browse_sound(self) -> None:
        """Browse for custom sound file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo de Som",
            "", "Arquivos de Som (*.wav *.ogg *.mp3);;Todos (*.*)"
        )
        if file_path:
            self.sound_file.setText(file_path)
    
    def _test_sound(self) -> None:
        """Test notification sound."""
        self.notification_mgr.send_custom(
            "Teste de Som", 
            "Este é o som de notificação configurado",
            duration_ms=3000
        )
    
    def _export_data(self) -> None:
        """Export all data to JSON file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Dados", "myTime_export.json", "JSON (*.json)"
        )
        if file_path:
            if self.storage.export_data(file_path):
                QMessageBox.information(self, "Sucesso", "Dados exportados com sucesso!")
            else:
                QMessageBox.warning(self, "Erro", "Falha ao exportar dados.")
    
    def _import_data(self) -> None:
        """Import data from JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Dados", "", "JSON (*.json)"
        )
        if file_path:
            try:
                self.storage.import_data(file_path)
                QMessageBox.information(self, "Sucesso", "Dados importados com sucesso!")
                self._load_config()
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Falha ao importar: {e}")
    
    def _reset_config(self) -> None:
        """Reset to default config."""
        reply = QMessageBox.question(
            self, "Confirmar", 
            "Redefinir todas as configurações para os padrões?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from myTime.core.models import WorkSchedule
            default = WorkSchedule()
            self.storage.save_config(default)
            self.config = default
            self._load_config()
    
    def _open_config_dir(self) -> None:
        """Open config directory in file manager."""
        import subprocess
        dir_path = str(self.storage.get_config_dir())
        subprocess.Popen(["xdg-open", dir_path])
    
    def _apply(self) -> None:
        """Apply config without closing."""
        self._save_config()
        QMessageBox.information(self, "Aplicado", "Configurações salvas!")
    
    def _on_accept(self) -> None:
        """Save and close."""
        self._save_config()
        self.accept()
    
    def _save_config(self) -> None:
        """Save UI values to config."""
        self.config.language = self.language_combo.currentText()
        self.config.work_start_time = self.start_time.time().toString("HH:mm")
        self.config.work_end_time = self.end_time.time().toString("HH:mm")
        self.config.daily_goal_sessions = self.daily_goal.value()
        
        self.config.work_duration = self.work_duration.value() * 60
        self.config.short_break_duration = self.short_break.value() * 60
        self.config.long_break_duration = self.long_break.value() * 60
        self.config.sessions_before_long_break = self.sessions_before_long.value()
        
        self.config.auto_start_breaks = self.auto_start_breaks.isChecked()
        self.config.auto_start_work = self.auto_start_work.isChecked()

        # Icon settings
        self.config.icon_size = self.icon_size_group.checkedId()
        if self.config.icon_size <= 0:
            self.config.icon_size = 48
        self.config.icon_show_letter = self.show_letter_cb.isChecked()
        self.config.icon_text_font_size = self.icon_font_size.value()
        self.config.icon_text_show_seconds = self.icon_show_seconds.isChecked()
        self.config.icon_text_color = self.icon_text_color_edit.text()
        for attr, (_preview, color_edit) in self._color_buttons.items():
            setattr(self.config, attr, color_edit.text())
        self.config.icon_bg_color = self.icon_bg_color_edit.text()
        self.config.icon_bg_opacity = self.icon_bg_opacity_slider.value()

        self.config.notifications_enabled = self.enable_notifications.isChecked()
        self.config.sound_enabled = self.enable_sounds.isChecked()
        
        # Update notification manager
        self.notification_mgr.enabled = self.config.notifications_enabled
        self.notification_mgr.sound_enabled = self.config.sound_enabled
        
        sound_file = self.sound_file.text().strip()
        if sound_file:
            self.notification_mgr.set_custom_sound(sound_file)
        
        self.storage.save_config(self.config)
