import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from PyQt6.QtCore import QSettings, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QKeySequence,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

try:
    from markitdown import MarkItDown
except ImportError:
    MarkItDown = None


# Стилизация интерфейса (Современная темная тема Slate Dark без визуального шума)
STYLESHEET = """
QMainWindow, QDialog {
    background-color: #0f172a;
    color: #f8fafc;
}
QWidget {
    color: #e2e8f0;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}
QFrame#Card {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
}
QFrame#DropZone {
    background-color: #1e293b;
    border: 2px dashed #475569;
    border-radius: 10px;
}
QFrame#DropZone:hover {
    border-color: #3b82f6;
    background-color: #1e293b;
}
QFrame#DropZone[dragActive="true"] {
    border-color: #60a5fa;
    background-color: #172554;
}
QLineEdit {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 7px;
    padding: 8px 12px;
    color: #f8fafc;
    selection-background-color: #3b82f6;
}
QLineEdit:focus {
    border: 1px solid #3b82f6;
}
QPushButton {
    background-color: #334155;
    border: 1px solid #475569;
    border-radius: 7px;
    padding: 8px 14px;
    color: #f8fafc;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #475569;
}
QPushButton:pressed {
    background-color: #1e293b;
}
QPushButton:disabled {
    background-color: #1e293b;
    color: #64748b;
    border-color: #1e293b;
}
QPushButton#PrimaryBtn {
    background-color: #2563eb;
    border: 1px solid #3b82f6;
    color: #ffffff;
}
QPushButton#PrimaryBtn:hover {
    background-color: #1d4ed8;
}
QPushButton#SuccessBtn {
    background-color: #059669;
    border: 1px solid #10b981;
    color: #ffffff;
}
QPushButton#SuccessBtn:hover {
    background-color: #047857;
}
QPushButton#SegmentBtn {
    background-color: #0f172a;
    border: 1px solid #334155;
    padding: 5px 12px;
    font-weight: 500;
}
QPushButton#SegmentBtn:checked {
    background-color: #3b82f6;
    border-color: #3b82f6;
    color: #ffffff;
}
QPlainTextEdit, QTextBrowser {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px;
    color: #e2e8f0;
    selection-background-color: #3b82f6;
}
QProgressBar {
    background-color: #1e293b;
    border: none;
    border-radius: 2px;
    max-height: 4px;
}
QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 2px;
}
QLabel#Badge {
    background-color: #334155;
    color: #93c5fd;
    border-radius: 5px;
    padding: 3px 8px;
    font-weight: 700;
    font-size: 11px;
}
QLabel#Muted {
    color: #94a3b8;
    font-size: 12px;
}
QSplitter::handle {
    background-color: #334155;
    width: 2px;
}
"""

SUPPORTED_EXTENSIONS_FILTER = (
    "Все поддерживаемые форматы (*.pdf *.docx *.pptx *.xlsx *.xls *.csv *.html *.htm "
    "*.json *.xml *.zip *.epub *.msg *.jpg *.jpeg *.png *.webp *.gif *.mp3 *.wav *.m4a *.ogg *.flac *.txt);;"
    "Документы Office и PDF (*.pdf *.docx *.pptx *.xlsx *.xls *.msg *.epub);;"
    "Веб и данные (*.html *.htm *.csv *.json *.xml *.txt);;"
    "Изображения (*.jpg *.jpeg *.png *.webp *.gif);;"
    "Аудио (*.mp3 *.wav *.m4a *.ogg *.flac);;"
    "Архивы (*.zip);;"
    "Все файлы (*)"
)


class ConversionWorker(QThread):
    """Фоновый поток для выполнения конвертации через MarkItDown без зависания UI."""
    finished = pyqtSignal(str, str, float)  # markdown_text, title, elapsed_seconds
    error = pyqtSignal(str)

    def __init__(self, source: str, config: dict):
        super().__init__()
        self.source = source
        self.config = config

    def run(self):
        if MarkItDown is None:
            self.error.emit(
                "Библиотека 'markitdown' не найдена.\n"
                "Установите её командой: pip install \"markitdown[all]\""
            )
            return

        start_time = time.perf_counter()
        try:
            kwargs = {
                "enable_plugins": self.config.get("enable_plugins", False)
            }

            # Опциональная интеграция с OpenAI-совместимым LLM для описания картинок
            if self.config.get("use_llm", False):
                api_key = self.config.get("llm_api_key", "").strip()
                base_url = self.config.get("llm_base_url", "").strip() or None
                model = self.config.get("llm_model", "gpt-4o-mini").strip()

                if not api_key and not base_url:
                    self.error.emit("Для использования LLM-описаний укажите API-ключ или локальный Base URL в настройках.")
                    return

                from openai import OpenAI
                client = OpenAI(api_key=api_key or "local-key", base_url=base_url)
                kwargs["llm_client"] = client
                kwargs["llm_model"] = model

            # Опциональная интеграция с Azure Document Intelligence
            docintel = self.config.get("docintel_endpoint", "").strip()
            if docintel:
                kwargs["docintel_endpoint"] = docintel

            md_converter = MarkItDown(**kwargs)
            result = md_converter.convert(self.source)

            elapsed = time.perf_counter() - start_time
            text_content = getattr(result, "text_content", "") or ""
            title = getattr(result, "title", "") or ""

            self.finished.emit(text_content, title, elapsed)

        except Exception as exc:
            self.error.emit(f"{type(exc).__name__}: {str(exc)}")


class SettingsDialog(QDialog):
    """Компактное окно настроек движка MarkItDown."""
    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Параметры движка MarkItDown")
        self.setMinimumWidth(460)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)

        self.cb_plugins = QCheckBox("Разрешить сторонние плагины (enable_plugins)")
        self.cb_plugins.setChecked(self.settings.value("enable_plugins", False, type=bool))
        form.addRow("Плагины:", self.cb_plugins)

        self.cb_use_llm = QCheckBox("Описывать изображения через ИИ (LLM Vision)")
        self.cb_use_llm.setChecked(self.settings.value("use_llm", False, type=bool))
        form.addRow("ИИ для картинок:", self.cb_use_llm)

        self.input_api_key = QLineEdit(self.settings.value("llm_api_key", "", type=str))
        self.input_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_api_key.setPlaceholderText("sk-... (или оставьте пустым для Ollama)")
        form.addRow("OpenAI API Key:", self.input_api_key)

        self.input_base_url = QLineEdit(self.settings.value("llm_base_url", "", type=str))
        self.input_base_url.setPlaceholderText("По умолчанию OpenAI (или http://localhost:11434/v1)")
        form.addRow("Base URL (опц.):", self.input_base_url)

        self.input_model = QLineEdit(self.settings.value("llm_model", "gpt-4o-mini", type=str))
        self.input_model.setPlaceholderText("gpt-4o, gpt-4o-mini, llama3.2-vision...")
        form.addRow("Модель LLM:", self.input_model)

        self.input_docintel = QLineEdit(self.settings.value("docintel_endpoint", "", type=str))
        self.input_docintel.setPlaceholderText("https://<resource>.cognitiveservices.azure.com/")
        form.addRow("Azure DocIntel:", self.input_docintel)

        layout.addLayout(form)

        hint = QLabel(
            "Подсказка: LLM используется только при конвертации изображений (.jpg, .png) "
            "и презентаций (.pptx) для генерации описания визуального контента."
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

    def save_and_close(self):
        self.settings.setValue("enable_plugins", self.cb_plugins.isChecked())
        self.settings.setValue("use_llm", self.cb_use_llm.isChecked())
        self.settings.setValue("llm_api_key", self.input_api_key.text().strip())
        self.settings.setValue("llm_base_url", self.input_base_url.text().strip())
        self.settings.setValue("llm_model", self.input_model.text().strip() or "gpt-4o-mini")
        self.settings.setValue("docintel_endpoint", self.input_docintel.text().strip())
        self.accept()


class DropZoneFrame(QFrame):
    """Интерактивная панель для Drag-and-Drop файлов и быстрого открытия Проводника."""
    file_dropped = pyqtSignal(str)
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        icon_label = QLabel("📂")
        icon_label.setStyleSheet("font-size: 22px; background: transparent;")
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.title_lbl = QLabel("Перетащите файл сюда или нажмите для выбора в Проводнике")
        self.title_lbl.setStyleSheet("font-weight: 600; font-size: 13px; color: #f8fafc; background: transparent;")
        self.sub_lbl = QLabel("PDF, Word, Excel, PowerPoint, HTML, CSV, JSON, ZIP, Изображения, Аудио")
        self.sub_lbl.setObjectName("Muted")
        self.sub_lbl.setStyleSheet("background: transparent;")
        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.sub_lbl)
        layout.addLayout(text_layout, 1)

        self.btn_browse = QPushButton("Выбрать файл…")
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.clicked.connect(self.clicked.emit)
        layout.addWidget(self.btn_browse)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
            self.setProperty("dragActive", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event):
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent):
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)

        mime = event.mimeData()
        if mime.hasUrls():
            url = mime.urls()[0]
            if url.isLocalFile():
                self.file_dropped.emit(url.toLocalFile())
            else:
                self.file_dropped.emit(url.toString())
        elif mime.hasText():
            self.file_dropped.emit(mime.text().strip())


class MarkItDownApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("MarkItDownDesktop", "AppConfig")
        self.current_source = ""
        self.last_extracted_title = ""
        self.worker = None

        self.setWindowTitle("MarkItDown Studio")
        self.resize(1120, 760)
        self.setMinimumSize(820, 560)

        # Таймер для плавного обновления превью и статистики без лагов на больших файлах
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(180)
        self.preview_timer.timeout.connect(self.sync_preview_and_stats)

        self.init_ui()
        self.setup_shortcuts()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(16, 16, 16, 14)
        root_layout.setSpacing(12)

        # 1. ВЕРХНЯЯ ПАНЕЛЬ ВЫБОРА ИСТОЧНИКА (Файл или Ссылка)
        top_card = QFrame()
        top_card.setObjectName("Card")
        top_layout = QVBoxLayout(top_card)
        top_layout.setContentsMargins(14, 14, 14, 14)
        top_layout.setSpacing(10)

        # Зона выбора файла / Drag & Drop
        self.drop_zone = DropZoneFrame()
        self.drop_zone.clicked.connect(self.browse_input_file)
        self.drop_zone.file_dropped.connect(self.set_source)
        top_layout.addWidget(self.drop_zone)

        # Строка ввода URL + быстрые действия
        url_row = QHBoxLayout()
        url_row.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("🔗 Или вставьте ссылку (YouTube видео, статья, Wikipedia, любая веб-страница) и нажмите Enter…")
        self.url_input.returnPressed.connect(self.on_url_entered)
        url_row.addWidget(self.url_input, 1)

        btn_paste = QPushButton("Вставить URL")
        btn_paste.setToolTip("Вставить ссылку из буфера обмена")
        btn_paste.clicked.connect(self.paste_url_from_clipboard)
        url_row.addWidget(btn_paste)

        self.cb_auto_convert = QCheckBox("Авто-старт")
        self.cb_auto_convert.setToolTip("Автоматически начинать конвертацию сразу после выбора файла или ссылки")
        self.cb_auto_convert.setChecked(self.settings.value("auto_convert", True, type=bool))
        self.cb_auto_convert.toggled.connect(lambda v: self.settings.setValue("auto_convert", v))
        url_row.addWidget(self.cb_auto_convert)

        btn_settings = QPushButton("⚙️ Параметры")
        btn_settings.setToolTip("Настройки плагинов, LLM Vision для картинок и Azure DocIntel")
        btn_settings.clicked.connect(self.open_settings)
        url_row.addWidget(btn_settings)

        self.btn_convert = QPushButton("⚡ Конвертировать")
        self.btn_convert.setObjectName("PrimaryBtn")
        self.btn_convert.clicked.connect(self.start_conversion)
        url_row.addWidget(self.btn_convert)

        top_layout.addLayout(url_row)
        root_layout.addWidget(top_card)

        # Тонкий индикатор прогресса
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        root_layout.addWidget(self.progress_bar)

        # 2. ПАНЕЛЬ ИНФОРМАЦИИ О ТЕКУЩЕМ ИСТОЧНИКЕ И ПЕРЕКЛЮЧАТЕЛЬ РЕЖИМА ПРОСМОТРА
        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(2, 0, 2, 0)

        self.badge_type = QLabel("ОЖИДАНИЕ")
        self.badge_type.setObjectName("Badge")
        toolbar_row.addWidget(self.badge_type)

        self.lbl_source_info = QLabel("Файл или ссылка не выбраны")
        self.lbl_source_info.setObjectName("Muted")
        toolbar_row.addWidget(self.lbl_source_info, 1)

        # Переключатель вида: Редактор | Сплит | Превью
        self.btn_view_raw = QPushButton("📝 Код (MD)")
        self.btn_view_raw.setObjectName("SegmentBtn")
        self.btn_view_raw.setCheckable(True)

        self.btn_view_split = QPushButton("🌓 Разделенный")
        self.btn_view_split.setObjectName("SegmentBtn")
        self.btn_view_split.setCheckable(True)
        self.btn_view_split.setChecked(True)

        self.btn_view_preview = QPushButton("👁️ Превью")
        self.btn_view_preview.setObjectName("SegmentBtn")
        self.btn_view_preview.setCheckable(True)

        self.btn_view_raw.clicked.connect(lambda: self.set_view_mode("raw"))
        self.btn_view_split.clicked.connect(lambda: self.set_view_mode("split"))
        self.btn_view_preview.clicked.connect(lambda: self.set_view_mode("preview"))

        toolbar_row.addWidget(self.btn_view_raw)
        toolbar_row.addWidget(self.btn_view_split)
        toolbar_row.addWidget(self.btn_view_preview)

        root_layout.addLayout(toolbar_row)

        # 3. РАБОЧАЯ ОБЛАСТЬ (Редактор Markdown + Живое превью)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Здесь появится готовый Markdown-текст после конвертации…\nВы также можете редактировать его перед сохранением.")
        mono_font = QFont("JetBrains Mono", 11)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self.editor.setFont(mono_font)
        self.editor.textChanged.connect(lambda: self.preview_timer.start())

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        self.preview.setPlaceholderText("Предпросмотр отформатированного Markdown…")

        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([550, 550])

        root_layout.addWidget(self.splitter, 1)

        # 4. НИЖНЯЯ ПАНЕЛЬ (Статистика + Копирование и Сохранение через Проводник)
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        self.lbl_stats = QLabel("Строк: 0  |  Слов: 0  |  Символов: 0  |  ~Токенов: 0")
        self.lbl_stats.setObjectName("Muted")
        bottom_row.addWidget(self.lbl_stats, 1)

        self.btn_clear = QPushButton("Очистить")
        self.btn_clear.clicked.connect(self.clear_workspace)
        self.btn_clear.setEnabled(False)
        bottom_row.addWidget(self.btn_clear)

        self.btn_copy = QPushButton("📋 Копировать")
        self.btn_copy.setToolTip("Скопировать Markdown в буфер обмена (Ctrl+Shift+C)")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.btn_copy.setEnabled(False)
        bottom_row.addWidget(self.btn_copy)

        self.btn_save = QPushButton("💾 Сохранить как… (Ctrl+S)")
        self.btn_save.setObjectName("SuccessBtn")
        self.btn_save.setToolTip("Выбрать папку и имя файла в стандартном окне Проводника")
        self.btn_save.clicked.connect(self.save_markdown_file)
        self.btn_save.setEnabled(False)
        bottom_row.addWidget(self.btn_save)

        root_layout.addLayout(bottom_row)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.browse_input_file)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_markdown_file)
        QShortcut(QKeySequence("Ctrl+Shift+C"), self, activated=self.copy_to_clipboard)

    # --- УПРАВЛЕНИЕ ВИДОМ ---
    def set_view_mode(self, mode: str):
        self.btn_view_raw.setChecked(mode == "raw")
        self.btn_view_split.setChecked(mode == "split")
        self.btn_view_preview.setChecked(mode == "preview")

        self.editor.setVisible(mode in ("raw", "split"))
        self.preview.setVisible(mode in ("preview", "split"))

    # --- ВЫБОР ФАЙЛА ИЛИ ССЫЛКИ ---
    def browse_input_file(self):
        last_dir = self.settings.value("last_input_dir", str(Path.home()), type=str)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл для конвертации в Markdown",
            last_dir,
            SUPPORTED_EXTENSIONS_FILTER,
        )
        if file_path:
            self.settings.setValue("last_input_dir", str(Path(file_path).parent))
            self.set_source(file_path)

    def paste_url_from_clipboard(self):
        clipboard_text = QApplication.clipboard().text().strip()
        if clipboard_text:
            self.url_input.setText(clipboard_text)
            self.set_source(clipboard_text)

    def on_url_entered(self):
        url = self.url_input.text().strip()
        if url:
            self.set_source(url)

    def set_source(self, source: str):
        source = source.strip()
        if not source:
            return

        self.current_source = source
        self.last_extracted_title = ""

        # Определяем: это URL или локальный файл
        if source.startswith(("http://", "https://")):
            self.url_input.setText(source)
            domain = urlparse(source).netloc.lower()
            if "youtube.com" in domain or "youtu.be" in domain:
                self.badge_type.setText("YOUTUBE")
            else:
                self.badge_type.setText("WEB URL")
            self.lbl_source_info.setText(source)
        else:
            path = Path(source)
            if path.exists() and path.is_file():
                ext = path.suffix.upper().lstrip(".") or "FILE"
                size_kb = path.stat().st_size / 1024
                size_str = f"{size_kb:.1f} КБ" if size_kb < 1024 else f"{size_kb / 1024:.2f} МБ"
                self.badge_type.setText(ext)
                self.lbl_source_info.setText(f"{path.name}  ({size_str})  —  {path.parent}")
                self.drop_zone.title_lbl.setText(f"Выбран файл: {path.name}")
            else:
                QMessageBox.warning(self, "Источник не найден", f"Не удалось найти файл или распознать ссылку:\n{source}")
                return

        if self.cb_auto_convert.isChecked():
            self.start_conversion()

    # --- КОНВЕРТАЦИЯ ---
    def start_conversion(self):
        url_candidate = self.url_input.text().strip()
        if not self.current_source and url_candidate:
            self.current_source = url_candidate

        if not self.current_source:
            QMessageBox.information(self, "Выберите источник", "Пожалуйста, выберите файл или вставьте ссылку для конвертации.")
            return

        if self.worker and self.worker.isRunning():
            return

        config = {
            "enable_plugins": self.settings.value("enable_plugins", False, type=bool),
            "use_llm": self.settings.value("use_llm", False, type=bool),
            "llm_api_key": self.settings.value("llm_api_key", "", type=str),
            "llm_base_url": self.settings.value("llm_base_url", "", type=str),
            "llm_model": self.settings.value("llm_model", "gpt-4o-mini", type=str),
            "docintel_endpoint": self.settings.value("docintel_endpoint", "", type=str),
        }

        self.progress_bar.setVisible(True)
        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("Конвертация…")
        self.lbl_source_info.setText(f"Обработка: {self.current_source} …")

        self.worker = ConversionWorker(self.current_source, config)
        self.worker.finished.connect(self.on_conversion_success)
        self.worker.error.connect(self.on_conversion_error)
        self.worker.start()

    def on_conversion_success(self, markdown_text: str, title: str, elapsed: float):
        self.progress_bar.setVisible(False)
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("⚡ Конвертировать")

        self.last_extracted_title = title
        self.editor.setPlainText(markdown_text)
        self.sync_preview_and_stats()

        source_display = Path(self.current_source).name if not self.current_source.startswith("http") else self.current_source
        self.lbl_source_info.setText(f"✓ Готово за {elapsed:.2f} сек  |  Источник: {source_display}")

        has_content = bool(markdown_text.strip())
        self.btn_save.setEnabled(has_content)
        self.btn_copy.setEnabled(has_content)
        self.btn_clear.setEnabled(has_content)

        if not has_content:
            QMessageBox.information(
                self,
                "Пустой результат",
                "Инструмент завершил работу, но не извлек текст.\n\n"
                "Если это изображение или скан без текстового слоя, включите 'ИИ для картинок (LLM Vision)' в параметрах ⚙️."
            )

    def on_conversion_error(self, error_msg: str):
        self.progress_bar.setVisible(False)
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("⚡ Конвертировать")
        self.lbl_source_info.setText("Ошибка при конвертации")

        QMessageBox.critical(
            self,
            "Ошибка конвертации",
            f"Не удалось конвертировать источник:\n\n{error_msg}\n\n"
            "Убедитесь, что установлены все зависимости: pip install \"markitdown[all]\"",
        )

    # --- СИНХРОНИЗАЦИЯ ПРЕВЬЮ И МЕТРИК ---
    def sync_preview_and_stats(self):
        text = self.editor.toPlainText()
        # Ограничиваем живой рендер при сверхбольших файлах (> 300 КБ текста), чтобы интерфейс оставался мгновенным
        if len(text) <= 300_000:
            self.preview.setMarkdown(text)
        else:
            self.preview.setPlainText(
                "[Документ слишком большой для живого HTML-рендера (>300 тыс. символов). "
                "Используйте режим 'Код (MD)' и сохраните файл.]"
            )

        chars = len(text)
        lines = text.count("\n") + (1 if chars > 0 else 0)
        words = len(text.split()) if chars > 0 else 0
        est_tokens = int(chars / 3.8)  # Эвристическая оценка количества токенов для LLM

        self.lbl_stats.setText(
            f"Строк: {lines:,}  |  Слов: {words:,}  |  Символов: {chars:,}  |  ~Токенов: {est_tokens:,}".replace(",", " ")
        )

        has_text = chars > 0
        self.btn_save.setEnabled(has_text)
        self.btn_copy.setEnabled(has_text)
        self.btn_clear.setEnabled(has_text)

    # --- СОХРАНЕНИЕ И ЭКСПОРТ ---
    def get_suggested_save_path(self) -> str:
        """Формирует удобный путь и имя файла по умолчанию для окна 'Сохранить как...'."""
        if self.current_source and not self.current_source.startswith(("http://", "https://")):
            src_path = Path(self.current_source)
            return str(src_path.with_suffix(".md"))

        # Если конвертировали ссылку — формируем имя из заголовка страницы или URL
        base_dir = self.settings.value("last_save_dir", str(Path.home()), type=str)
        raw_name = self.last_extracted_title or urlparse(self.current_source).path.strip("/").split("/")[-1] or "converted_page"
        clean_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", raw_name).strip(" ._")[:80] or "document"
        return str(Path(base_dir) / f"{clean_name}.md")

    def save_markdown_file(self):
        text = self.editor.toPlainText()
        if not text:
            return

        suggested_path = self.get_suggested_save_path()
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить Markdown файл",
            suggested_path,
            "Markdown документ (*.md);;Текстовый файл (*.txt);;Все файлы (*)",
        )

        if save_path:
            try:
                target = Path(save_path)
                if not target.suffix:
                    target = target.with_suffix(".md")
                target.write_text(text, encoding="utf-8")
                self.settings.setValue("last_save_dir", str(target.parent))
                self.lbl_source_info.setText(f"💾 Файл успешно сохранен: {target}")
            except Exception as exc:
                QMessageBox.critical(self, "Ошибка сохранения", f"Не удалось записать файл:\n{exc}")

    def copy_to_clipboard(self):
        text = self.editor.toPlainText()
        if not text:
            return
        QApplication.clipboard().setText(text)
        old_text = self.btn_copy.text()
        self.btn_copy.setText("✓ Скопировано!")
        QTimer.singleShot(1500, lambda: self.btn_copy.setText(old_text))

    def clear_workspace(self):
        self.editor.clear()
        self.preview.clear()
        self.current_source = ""
        self.last_extracted_title = ""
        self.url_input.clear()
        self.badge_type.setText("ОЖИДАНИЕ")
        self.lbl_source_info.setText("Файл или ссылка не выбраны")
        self.drop_zone.title_lbl.setText("Перетащите файл сюда или нажмите для выбора в Проводнике")

    def open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        dlg.exec()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MarkItDownApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()