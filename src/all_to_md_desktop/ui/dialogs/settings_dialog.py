from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from all_to_md_desktop.config import AppConfig
from all_to_md_desktop.themes.palettes import THEMES


class SettingsDialog(QDialog):
    """Модальное окно параметров MarkItDown и оформления."""

    settings_changed = pyqtSignal()

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Параметры движка и оформления")
        self.setMinimumWidth(480)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        engine_opts = self.config.get_engine_options()

        form = QFormLayout()
        form.setSpacing(10)

        self.combo_theme = QComboBox()
        self.combo_theme.addItems(list(THEMES.keys()))
        self.combo_theme.setCurrentText(self.config.theme)
        form.addRow("Тема оформления:", self.combo_theme)

        self.spin_font = QSpinBox()
        self.spin_font.setRange(9, 22)
        self.spin_font.setSuffix(" pt")
        self.spin_font.setValue(self.config.editor_font_size)
        form.addRow("Размер шрифта редактора:", self.spin_font)

        self.cb_plugins = QCheckBox("Разрешить сторонние плагины (enable_plugins)")
        self.cb_plugins.setChecked(engine_opts["enable_plugins"])
        form.addRow("Плагины:", self.cb_plugins)

        self.cb_use_llm = QCheckBox("Описывать изображения через ИИ (LLM Vision)")
        self.cb_use_llm.setChecked(engine_opts["use_llm"])
        form.addRow("ИИ для картинок:", self.cb_use_llm)

        self.input_api_key = QLineEdit(engine_opts["llm_api_key"])
        self.input_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_api_key.setPlaceholderText("sk-... (или оставьте пустым для Ollama)")
        form.addRow("OpenAI API Key:", self.input_api_key)

        self.input_base_url = QLineEdit(engine_opts["llm_base_url"])
        self.input_base_url.setPlaceholderText("По умолчанию OpenAI (или http://localhost:11434/v1)")
        form.addRow("Base URL (опц.):", self.input_base_url)

        self.input_model = QLineEdit(engine_opts["llm_model"])
        self.input_model.setPlaceholderText("gpt-4o, gpt-4o-mini, llama3.2-vision...")
        form.addRow("Модель LLM:", self.input_model)

        self.input_docintel = QLineEdit(engine_opts["docintel_endpoint"])
        self.input_docintel.setPlaceholderText("https://<resource>.cognitiveservices.azure.com/")
        form.addRow("Azure DocIntel:", self.input_docintel)

        layout.addLayout(form)

        hint = QLabel(
            "Подсказка: Настройки LLM и Azure применяются как в одиночном, так и в пакетном режиме."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Сохранить")
        btn_save.setObjectName("PrimaryBtn")
        btn_save.clicked.connect(self.save_and_close)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def save_and_close(self) -> None:
        self.config.theme = self.combo_theme.currentText()
        self.config.editor_font_size = self.spin_font.value()
        self.config.save_engine_options({
            "enable_plugins": self.cb_plugins.isChecked(),
            "use_llm": self.cb_use_llm.isChecked(),
            "llm_api_key": self.input_api_key.text().strip(),
            "llm_base_url": self.input_base_url.text().strip(),
            "llm_model": self.input_model.text().strip() or "gpt-4o-mini",
            "docintel_endpoint": self.input_docintel.text().strip(),
        })
        self.settings_changed.emit()
        self.accept()