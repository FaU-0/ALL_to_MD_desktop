import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from PyQt6.QtCore import QSettings, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QKeySequence,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

try:
    from markitdown import MarkItDown
except ImportError:
    MarkItDown = None


# Поддерживаемые расширения для фильтра Проводника и сканирования папок
SUPPORTED_EXTS = {
    ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".csv",
    ".html", ".htm", ".json", ".xml", ".zip", ".epub",
    ".msg", ".jpg", ".jpeg", ".png", ".webp", ".gif",
    ".mp3", ".wav", ".m4a", ".ogg", ".flac", ".txt",
}

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


# =====================================================================
# ПАЛИТРЫ ТЕМ ОФОРМЛЕНИЯ И ГЕНЕРАТОР QSS
# =====================================================================
THEMES = {
    "Slate Dark": {
        "bg_main": "#0f172a",
        "bg_card": "#1e293b",
        "bg_input": "#0f172a",
        "bg_hover": "#334155",
        "border": "#334155",
        "border_subtle": "#475569",
        "text_main": "#f8fafc",
        "text_secondary": "#e2e8f0",
        "text_muted": "#94a3b8",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "accent_light": "#3b82f6",
        "drop_active_bg": "#172554",
        "success": "#059669",
        "success_hover": "#047857",
        "danger": "#dc2626",
        "danger_hover": "#b91c1c",
        "badge_bg": "#334155",
        "badge_text": "#93c5fd",
    },
    "Daylight Clean": {
        "bg_main": "#f8fafc",
        "bg_card": "#ffffff",
        "bg_input": "#f1f5f9",
        "bg_hover": "#e2e8f0",
        "border": "#cbd5e1",
        "border_subtle": "#94a3b8",
        "text_main": "#0f172a",
        "text_secondary": "#1e293b",
        "text_muted": "#64748b",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "accent_light": "#3b82f6",
        "drop_active_bg": "#eff6ff",
        "success": "#059669",
        "success_hover": "#047857",
        "danger": "#dc2626",
        "danger_hover": "#b91c1c",
        "badge_bg": "#dbeafe",
        "badge_text": "#1e40af",
    },
    "Nordic Frost": {
        "bg_main": "#2e3440",
        "bg_card": "#3b4252",
        "bg_input": "#2e3440",
        "bg_hover": "#434c5e",
        "border": "#4c566a",
        "border_subtle": "#616e88",
        "text_main": "#eceff4",
        "text_secondary": "#e5e9f0",
        "text_muted": "#d8dee9",
        "accent": "#5e81ac",
        "accent_hover": "#81a1c1",
        "accent_light": "#88c0d0",
        "drop_active_bg": "#434c5e",
        "success": "#a3be8c",
        "success_hover": "#8fbcbb",
        "danger": "#bf616a",
        "danger_hover": "#d08770",
        "badge_bg": "#4c566a",
        "badge_text": "#88c0d0",
    },
    "Catppuccin Mocha": {
        "bg_main": "#1e1e2e",
        "bg_card": "#181825",
        "bg_input": "#11111b",
        "bg_hover": "#313244",
        "border": "#313244",
        "border_subtle": "#45475a",
        "text_main": "#cdd6f4",
        "text_secondary": "#bac2de",
        "text_muted": "#a6adc8",
        "accent": "#89b4fa",
        "accent_hover": "#74c7ec",
        "accent_light": "#b4befe",
        "drop_active_bg": "#313244",
        "success": "#a6e3a1",
        "success_hover": "#94e2d5",
        "danger": "#f38ba8",
        "danger_hover": "#eba0ac",
        "badge_bg": "#313244",
        "badge_text": "#89b4fa",
    },
}


def build_stylesheet(theme_name: str) -> str:
    t = THEMES.get(theme_name, THEMES["Slate Dark"])
    # Определяем цвет текста на акцентных кнопках (для светлых пастельных акцентов — темный текст)
    btn_text_on_accent = "#11111b" if theme_name == "Catppuccin Mocha" else "#ffffff"
    btn_text_on_success = "#11111b" if theme_name in ("Catppuccin Mocha", "Nordic Frost") else "#ffffff"

    return f"""
    QMainWindow, QDialog {{
        background-color: {t['bg_main']};
        color: {t['text_main']};
    }}
    QWidget {{
        color: {t['text_secondary']};
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
        font-size: 13px;
    }}
    QFrame#Card {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        border-radius: 10px;
    }}
    QFrame#DropZone {{
        background-color: {t['bg_card']};
        border: 2px dashed {t['border_subtle']};
        border-radius: 10px;
    }}
    QFrame#DropZone:hover {{
        border-color: {t['accent_light']};
    }}
    QFrame#DropZone[dragActive="true"] {{
        border-color: {t['accent_light']};
        background-color: {t['drop_active_bg']};
    }}
    QLineEdit, QComboBox, QSpinBox {{
        background-color: {t['bg_input']};
        border: 1px solid {t['border']};
        border-radius: 7px;
        padding: 7px 11px;
        color: {t['text_main']};
        selection-background-color: {t['accent_light']};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border: 1px solid {t['accent_light']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        color: {t['text_main']};
        selection-background-color: {t['accent']};
        selection-color: {btn_text_on_accent};
    }}
    QPushButton {{
        background-color: {t['bg_hover']};
        border: 1px solid {t['border_subtle']};
        border-radius: 7px;
        padding: 7px 13px;
        color: {t['text_main']};
        font-weight: 600;
    }}
    QPushButton:hover {{
        border-color: {t['accent_light']};
    }}
    QPushButton:pressed {{
        background-color: {t['bg_input']};
    }}
    QPushButton:disabled {{
        background-color: {t['bg_card']};
        color: {t['text_muted']};
        border-color: {t['border']};
    }}
    QPushButton#PrimaryBtn {{
        background-color: {t['accent']};
        border: 1px solid {t['accent_light']};
        color: {btn_text_on_accent};
    }}
    QPushButton#PrimaryBtn:hover {{
        background-color: {t['accent_hover']};
    }}
    QPushButton#SuccessBtn {{
        background-color: {t['success']};
        border: 1px solid {t['success']};
        color: {btn_text_on_success};
    }}
    QPushButton#SuccessBtn:hover {{
        background-color: {t['success_hover']};
    }}
    QPushButton#DangerBtn {{
        background-color: {t['danger']};
        border: 1px solid {t['danger']};
        color: #ffffff;
    }}
    QPushButton#DangerBtn:hover {{
        background-color: {t['danger_hover']};
    }}
    QPushButton#SegmentBtn, QPushButton#ModeTabBtn {{
        background-color: {t['bg_input']};
        border: 1px solid {t['border']};
        padding: 6px 14px;
        font-weight: 600;
        color: {t['text_muted']};
    }}
    QPushButton#SegmentBtn:checked, QPushButton#ModeTabBtn:checked {{
        background-color: {t['accent']};
        border-color: {t['accent_light']};
        color: {btn_text_on_accent};
    }}
    QPlainTextEdit, QTextBrowser {{
        background-color: {t['bg_input']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 12px;
        color: {t['text_main']};
        selection-background-color: {t['accent_light']};
    }}
    QTableWidget {{
        background-color: {t['bg_input']};
        alternate-background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        gridline-color: {t['border']};
        color: {t['text_main']};
        selection-background-color: {t['accent']};
        selection-color: {btn_text_on_accent};
    }}
    QHeaderView::section {{
        background-color: {t['bg_card']};
        color: {t['text_muted']};
        font-weight: 600;
        padding: 6px 10px;
        border: none;
        border-bottom: 1px solid {t['border']};
        border-right: 1px solid {t['border']};
    }}
    QProgressBar {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        border-radius: 5px;
        text-align: center;
        color: {t['text_main']};
        font-weight: 600;
        max-height: 16px;
    }}
    QProgressBar::chunk {{
        background-color: {t['accent']};
        border-radius: 4px;
    }}
    QLabel#Badge {{
        background-color: {t['badge_bg']};
        color: {t['badge_text']};
        border-radius: 5px;
        padding: 3px 8px;
        font-weight: 700;
        font-size: 11px;
    }}
    QLabel#Muted {{
        color: {t['text_muted']};
        font-size: 12px;
    }}
    QSplitter::handle {{
        background-color: {t['border']};
        width: 2px;
    }}
    """


# =====================================================================
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ СОЗДАНИЯ ЭКЗЕМПЛЯРА MARKITDOWN
# =====================================================================
def create_markitdown_instance(config: dict):
    if MarkItDown is None:
        raise RuntimeError(
            "Библиотека 'markitdown' не найдена.\n"
            "Установите её командой: pip install \"markitdown[all]\""
        )

    kwargs = {"enable_plugins": config.get("enable_plugins", False)}

    if config.get("use_llm", False):
        api_key = config.get("llm_api_key", "").strip()
        base_url = config.get("llm_base_url", "").strip() or None
        model = config.get("llm_model", "gpt-4o-mini").strip()

        if not api_key and not base_url:
            raise ValueError("Для использования LLM-описаний укажите API-ключ или локальный Base URL в настройках.")

        from openai import OpenAI
        client = OpenAI(api_key=api_key or "local-key", base_url=base_url)
        kwargs["llm_client"] = client
        kwargs["llm_model"] = model

    docintel = config.get("docintel_endpoint", "").strip()
    if docintel:
        kwargs["docintel_endpoint"] = docintel

    return MarkItDown(**kwargs)


# =====================================================================
# ПОТОКИ КОНВЕРТАЦИИ (ОДИНОЧНЫЙ И ПАКЕТНЫЙ)
# =====================================================================
class SingleConversionWorker(QThread):
    finished = pyqtSignal(str, str, float)  # markdown_text, title, elapsed
    error = pyqtSignal(str)

    def __init__(self, source: str, config: dict):
        super().__init__()
        self.source = source
        self.config = config

    def run(self):
        start_time = time.perf_counter()
        try:
            md_converter = create_markitdown_instance(self.config)
            result = md_converter.convert(self.source)
            elapsed = time.perf_counter() - start_time
            text_content = getattr(result, "text_content", "") or ""
            title = getattr(result, "title", "") or ""
            self.finished.emit(text_content, title, elapsed)
        except Exception as exc:
            self.error.emit(f"{type(exc).__name__}: {str(exc)}")


class BatchConversionWorker(QThread):
    item_started = pyqtSignal(int)
    item_finished = pyqtSignal(int, str, str, float)  # row, saved_path, markdown_text, elapsed
    item_error = pyqtSignal(int, str)                 # row, error_msg
    batch_finished = pyqtSignal(int, int, str)        # ok_count, err_count, merged_file_path

    def __init__(
        self,
        items: list,           # Список кортежей (row_index, source_path)
        config: dict,
        save_mode: str,        # "alongside" | "custom_dir"
        custom_dir: str,
        collision_mode: str,   # "rename" | "overwrite" | "skip"
        merge_all: bool,
        merge_file_path: str,
    ):
        super().__init__()
        self.items = items
        self.config = config
        self.save_mode = save_mode
        self.custom_dir = custom_dir
        self.collision_mode = collision_mode
        self.merge_all = merge_all
        self.merge_file_path = merge_file_path
        self._stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def _resolve_output_path(self, src_path: Path) -> Path:
        base_dir = src_path.parent if self.save_mode == "alongside" else Path(self.custom_dir)
        base_dir.mkdir(parents=True, exist_ok=True)
        candidate = base_dir / f"{src_path.stem}.md"

        if self.collision_mode == "overwrite" or not candidate.exists():
            return candidate
        if self.collision_mode == "skip" and candidate.exists():
            return None

        # Режим "rename": добавляем (1), (2)...
        counter = 1
        while True:
            numbered = base_dir / f"{src_path.stem} ({counter}).md"
            if not numbered.exists():
                return numbered
            counter += 1

    def run(self):
        ok_count = 0
        err_count = 0
        merged_sections = []

        try:
            md_converter = create_markitdown_instance(self.config)
        except Exception as exc:
            for row_idx, _ in self.items:
                self.item_error.emit(row_idx, str(exc))
            self.batch_finished.emit(0, len(self.items), "")
            return

        for row_idx, source in self.items:
            if self._stop_requested:
                break

            self.item_started.emit(row_idx)
            t0 = time.perf_counter()

            try:
                src_path = Path(source)
                out_path = self._resolve_output_path(src_path)

                if out_path is None:
                    elapsed = time.perf_counter() - t0
                    self.item_finished.emit(row_idx, "Пропущен (уже существует)", "", elapsed)
                    ok_count += 1
                    continue

                result = md_converter.convert(str(src_path))
                md_text = getattr(result, "text_content", "") or ""
                elapsed = time.perf_counter() - t0

                out_path.write_text(md_text, encoding="utf-8")

                if self.merge_all:
                    merged_sections.append(f"# Файл: {src_path.name}\n\n{md_text.strip()}\n")

                ok_count += 1
                self.item_finished.emit(row_idx, str(out_path), md_text, elapsed)

            except Exception as exc:
                err_count += 1
                self.item_error.emit(row_idx, f"{type(exc).__name__}: {str(exc)}")

        merged_saved_to = ""
        if self.merge_all and merged_sections and self.merge_file_path:
            try:
                m_path = Path(self.merge_file_path)
                m_path.parent.mkdir(parents=True, exist_ok=True)
                m_path.write_text("\n\n---\n\n".join(merged_sections), encoding="utf-8")
                merged_saved_to = str(m_path)
            except Exception:
                pass

        self.batch_finished.emit(ok_count, err_count, merged_saved_to)


# =====================================================================
# ОКНО НАСТРОЕК ДВИЖКА И ОФОРМЛЕНИЯ
# =====================================================================
class SettingsDialog(QDialog):
    settings_changed = pyqtSignal()

    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Параметры движка и оформления")
        self.setMinimumWidth(480)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)

        self.combo_theme = QComboBox()
        self.combo_theme.addItems(list(THEMES.keys()))
        current_theme = self.settings.value("theme", "Slate Dark", type=str)
        self.combo_theme.setCurrentText(current_theme)
        form.addRow("Тема оформления:", self.combo_theme)

        self.spin_font = QSpinBox()
        self.spin_font.setRange(9, 22)
        self.spin_font.setSuffix(" pt")
        self.spin_font.setValue(self.settings.value("editor_font_size", 11, type=int))
        form.addRow("Размер шрифта редактора:", self.spin_font)

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

    def save_and_close(self):
        self.settings.setValue("theme", self.combo_theme.currentText())
        self.settings.setValue("editor_font_size", self.spin_font.value())
        self.settings.setValue("enable_plugins", self.cb_plugins.isChecked())
        self.settings.setValue("use_llm", self.cb_use_llm.isChecked())
        self.settings.setValue("llm_api_key", self.input_api_key.text().strip())
        self.settings.setValue("llm_base_url", self.input_base_url.text().strip())
        self.settings.setValue("llm_model", self.input_model.text().strip() or "gpt-4o-mini")
        self.settings.setValue("docintel_endpoint", self.input_docintel.text().strip())
        self.settings_changed.emit()
        self.accept()


# =====================================================================
# ПАНЕЛЬ DRAG & DROP (ПОДДЕРЖИВАЕТ ОДИНОЧНЫЕ И МНОЖЕСТВЕННЫЕ СБРОСЫ)
# =====================================================================
class DropZoneFrame(QFrame):
    paths_dropped = pyqtSignal(list)  # Список путей или URL
    clicked = pyqtSignal()

    def __init__(self, title_text: str, subtitle_text: str, button_text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        icon_label = QLabel("📂")
        icon_label.setStyleSheet("font-size: 22px; background: transparent;")
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.title_lbl = QLabel(title_text)
        self.title_lbl.setStyleSheet("font-weight: 600; font-size: 13px; background: transparent;")
        self.sub_lbl = QLabel(subtitle_text)
        self.sub_lbl.setObjectName("Muted")
        self.sub_lbl.setStyleSheet("background: transparent;")
        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.sub_lbl)
        layout.addLayout(text_layout, 1)

        self.btn_browse = QPushButton(button_text)
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
        collected = []
        if mime.hasUrls():
            for u in mime.urls():
                collected.append(u.toLocalFile() if u.isLocalFile() else u.toString())
        elif mime.hasText():
            for line in mime.text().splitlines():
                if line.strip():
                    collected.append(line.strip())

        if collected:
            self.paths_dropped.emit(collected)


# =====================================================================
# ГЛАВНОЕ ОКНО ПРИЛОЖЕНИЯ
# =====================================================================
class MarkItDownApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("MarkItDownDesktop", "AppConfigV2")
        self.current_source = ""
        self.last_extracted_title = ""
        self.single_worker = None
        self.batch_worker = None

        # Словарь для хранения текста сконвертированных файлов в пакетном режиме (row -> markdown)
        self.batch_results_cache = {}

        self.setWindowTitle("MarkItDown Studio 2.0")
        self.resize(1160, 790)
        self.setMinimumSize(880, 600)

        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(180)
        self.preview_timer.timeout.connect(self.sync_preview_and_stats)

        self.init_ui()
        self.setup_shortcuts()
        self.apply_appearance()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(10)

        # -----------------------------------------------------------------
        # ШАПКА: ПЕРЕКЛЮЧАТЕЛЬ РЕЖИМОВ (ОДИНОЧНЫЙ / ПАКЕТНЫЙ) + ТЕМА + ШРИФТ
        # -----------------------------------------------------------------
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        self.btn_mode_single = QPushButton("📄 Одиночный файл / URL")
        self.btn_mode_single.setObjectName("ModeTabBtn")
        self.btn_mode_single.setCheckable(True)
        self.btn_mode_single.setChecked(True)
        self.btn_mode_single.clicked.connect(lambda: self.switch_mode(0))

        self.btn_mode_batch = QPushButton("📚 Пакетная конвертация (0)")
        self.btn_mode_batch.setObjectName("ModeTabBtn")
        self.btn_mode_batch.setCheckable(True)
        self.btn_mode_batch.clicked.connect(lambda: self.switch_mode(1))

        header_row.addWidget(self.btn_mode_single)
        header_row.addWidget(self.btn_mode_batch)
        header_row.addStretch()

        lbl_theme = QLabel("🎨 Тема:")
        lbl_theme.setObjectName("Muted")
        header_row.addWidget(lbl_theme)

        self.combo_quick_theme = QComboBox()
        self.combo_quick_theme.addItems(list(THEMES.keys()))
        saved_theme = self.settings.value("theme", "Slate Dark", type=str)
        self.combo_quick_theme.setCurrentText(saved_theme)
        self.combo_quick_theme.currentTextChanged.connect(self.on_quick_theme_changed)
        header_row.addWidget(self.combo_quick_theme)

        btn_font_dec = QPushButton("A-")
        btn_font_dec.setToolTip("Уменьшить шрифт редактора")
        btn_font_dec.setFixedWidth(36)
        btn_font_dec.clicked.connect(lambda: self.adjust_font_size(-1))
        header_row.addWidget(btn_font_dec)

        btn_font_inc = QPushButton("A+")
        btn_font_inc.setToolTip("Увеличить шрифт редактора")
        btn_font_inc.setFixedWidth(36)
        btn_font_inc.clicked.connect(lambda: self.adjust_font_size(1))
        header_row.addWidget(btn_font_inc)

        btn_settings = QPushButton("⚙️ Параметры")
        btn_settings.setToolTip("Настройки LLM Vision, Azure DocIntel и оформления")
        btn_settings.clicked.connect(self.open_settings)
        header_row.addWidget(btn_settings)

        root_layout.addLayout(header_row)

        # -----------------------------------------------------------------
        # СТЕК ЭКРАНОВ: [0] ОДИНОЧНЫЙ РЕЖИМ, [1] ПАКЕТНЫЙ РЕЖИМ
        # -----------------------------------------------------------------
        self.stack = QStackedWidget()
        self.stack.addWidget(self.build_single_mode_page())
        self.stack.addWidget(self.build_batch_mode_page())
        root_layout.addWidget(self.stack, 1)

    # =====================================================================
    # СТРАНИЦА 1: ОДИНОЧНЫЙ РЕЖИМ
    # =====================================================================
    def build_single_mode_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(10)

        top_card = QFrame()
        top_card.setObjectName("Card")
        top_layout = QVBoxLayout(top_card)
        top_layout.setContentsMargins(14, 12, 14, 12)
        top_layout.setSpacing(10)

        self.single_drop_zone = DropZoneFrame(
            "Перетащите файл сюда (или несколько файлов для пакетного режима)",
            "PDF, Word, Excel, PowerPoint, HTML, CSV, JSON, ZIP, Изображения, Аудио",
            "Выбрать файл…",
        )
        self.single_drop_zone.clicked.connect(self.browse_single_input_file)
        self.single_drop_zone.paths_dropped.connect(self.handle_dropped_paths)
        top_layout.addWidget(self.single_drop_zone)

        url_row = QHBoxLayout()
        url_row.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("🔗 Или вставьте ссылку (YouTube видео, статья, Wikipedia, веб-страница) и нажмите Enter…")
        self.url_input.returnPressed.connect(self.on_url_entered)
        url_row.addWidget(self.url_input, 1)

        btn_paste = QPushButton("Вставить URL")
        btn_paste.clicked.connect(self.paste_url_from_clipboard)
        url_row.addWidget(btn_paste)

        self.cb_auto_convert = QCheckBox("Авто-старт")
        self.cb_auto_convert.setChecked(self.settings.value("auto_convert", True, type=bool))
        self.cb_auto_convert.toggled.connect(lambda v: self.settings.setValue("auto_convert", v))
        url_row.addWidget(self.cb_auto_convert)

        self.btn_convert = QPushButton("⚡ Конвертировать")
        self.btn_convert.setObjectName("PrimaryBtn")
        self.btn_convert.clicked.connect(self.start_single_conversion)
        url_row.addWidget(self.btn_convert)

        top_layout.addLayout(url_row)
        layout.addWidget(top_card)

        self.single_progress = QProgressBar()
        self.single_progress.setRange(0, 0)
        self.single_progress.setVisible(False)
        layout.addWidget(self.single_progress)

        # Панель информации и переключатель вида
        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(2, 0, 2, 0)

        self.badge_type = QLabel("ОЖИДАНИЕ")
        self.badge_type.setObjectName("Badge")
        toolbar_row.addWidget(self.badge_type)

        self.lbl_source_info = QLabel("Файл или ссылка не выбраны")
        self.lbl_source_info.setObjectName("Muted")
        toolbar_row.addWidget(self.lbl_source_info, 1)

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
        layout.addLayout(toolbar_row)

        # Редактор и Превью
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Здесь появится готовый Markdown-текст после конвертации…")
        self.editor.textChanged.connect(lambda: self.preview_timer.start())

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        self.preview.setPlaceholderText("Предпросмотр отформатированного Markdown…")

        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([560, 560])
        layout.addWidget(self.splitter, 1)

        # Нижняя панель одиночного режима
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        self.lbl_stats = QLabel("Строк: 0  |  Слов: 0  |  Символов: 0  |  ~Токенов: 0")
        self.lbl_stats.setObjectName("Muted")
        bottom_row.addWidget(self.lbl_stats, 1)

        self.btn_clear = QPushButton("Очистить")
        self.btn_clear.clicked.connect(self.clear_single_workspace)
        self.btn_clear.setEnabled(False)
        bottom_row.addWidget(self.btn_clear)

        self.btn_copy = QPushButton("📋 Копировать")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.btn_copy.setEnabled(False)
        bottom_row.addWidget(self.btn_copy)

        self.btn_save = QPushButton("💾 Сохранить как… (Ctrl+S)")
        self.btn_save.setObjectName("SuccessBtn")
        self.btn_save.clicked.connect(self.save_single_markdown_file)
        self.btn_save.setEnabled(False)
        bottom_row.addWidget(self.btn_save)

        layout.addLayout(bottom_row)
        return page

    # =====================================================================
    # СТРАНИЦА 2: ПАКЕТНЫЙ РЕЖИМ (BATCH CONVERSION)
    # =====================================================================
    def build_batch_mode_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(10)

        # Верхняя карточка управления очередью и добавлением файлов
        batch_top_card = QFrame()
        batch_top_card.setObjectName("Card")
        bt_layout = QVBoxLayout(batch_top_card)
        bt_layout.setContentsMargins(14, 12, 14, 12)
        bt_layout.setSpacing(10)

        self.batch_drop_zone = DropZoneFrame(
            "Перетащите сюда файлы или целые папки для пакетной конвертации",
            "Поддерживается добавление сотен файлов за раз с автоматической фильтрацией форматов",
            "➕ Добавить файлы…",
        )
        self.batch_drop_zone.clicked.connect(self.batch_add_files_dialog)
        self.batch_drop_zone.paths_dropped.connect(self.batch_add_paths)
        bt_layout.addWidget(self.batch_drop_zone)

        # Кнопки управления очередью
        queue_actions_row = QHBoxLayout()
        queue_actions_row.setSpacing(8)

        btn_add_folder = QPushButton("📁 Добавить папку…")
        btn_add_folder.clicked.connect(self.batch_add_folder_dialog)
        queue_actions_row.addWidget(btn_add_folder)

        self.cb_recursive = QCheckBox("Включая вложенные подпапки")
        self.cb_recursive.setChecked(True)
        queue_actions_row.addWidget(self.cb_recursive)

        queue_actions_row.addStretch()

        btn_remove_sel = QPushButton("Удалить выбранные")
        btn_remove_sel.clicked.connect(self.batch_remove_selected)
        queue_actions_row.addWidget(btn_remove_sel)

        btn_clear_queue = QPushButton("Очистить список")
        btn_clear_queue.clicked.connect(self.batch_clear_all)
        queue_actions_row.addWidget(btn_clear_queue)

        bt_layout.addLayout(queue_actions_row)
        layout.addWidget(batch_top_card)

        # Карточка настроек сохранения пакета
        save_card = QFrame()
        save_card.setObjectName("Card")
        sc_layout = QVBoxLayout(save_card)
        sc_layout.setContentsMargins(14, 10, 14, 10)
        sc_layout.setSpacing(8)

        row_dest = QHBoxLayout()
        row_dest.setSpacing(8)

        row_dest.addWidget(QLabel("Куда сохранять:"))
        self.combo_save_mode = QComboBox()
        self.combo_save_mode.addItems([
            "В выбранную папку",
            "Рядом с исходными файлами (в те же папки)",
        ])
        self.combo_save_mode.currentIndexChanged.connect(self.on_batch_save_mode_changed)
        row_dest.addWidget(self.combo_save_mode)

        self.input_batch_out_dir = QLineEdit()
        default_out = self.settings.value("last_batch_out_dir", str(Path.home() / "Documents"), type=str)
        self.input_batch_out_dir.setText(default_out)
        self.input_batch_out_dir.setPlaceholderText("Путь к папке сохранения…")
        row_dest.addWidget(self.input_batch_out_dir, 1)

        self.btn_browse_out_dir = QPushButton("Обзор…")
        self.btn_browse_out_dir.clicked.connect(self.browse_batch_output_dir)
        row_dest.addWidget(self.btn_browse_out_dir)

        row_dest.addWidget(QLabel("Если файл существует:"))
        self.combo_collision = QComboBox()
        self.combo_collision.addItems([
            "Добавлять номер: файл (1).md",
            "Перезаписывать",
            "Пропускать",
        ])
        row_dest.addWidget(self.combo_collision)
        sc_layout.addLayout(row_dest)

        # Опция склейки всех файлов в один общий документ
        row_merge = QHBoxLayout()
        self.cb_merge_all = QCheckBox("Дополнительно склеить все результаты в один общий файл (_merged_bundle.md)")
        self.cb_merge_all.setToolTip("Удобно, если нужно загрузить всю папку документов в LLM одним файлом")
        row_merge.addWidget(self.cb_merge_all)
        row_merge.addStretch()

        hint_dbl = QLabel("💡 Двойной клик по готовой строке откроет результат в Редакторе")
        hint_dbl.setObjectName("Muted")
        row_merge.addWidget(hint_dbl)
        sc_layout.addLayout(row_merge)

        layout.addWidget(save_card)

        # Таблица очереди файлов
        self.batch_table = QTableWidget(0, 5)
        self.batch_table.setHorizontalHeaderLabels([
            "Статус", "Исходный файл", "Формат", "Размер", "Результат / Куда сохранен"
        ])
        self.batch_table.setAlternatingRowColors(True)
        self.batch_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.batch_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.batch_table.verticalHeader().setVisible(False)
        self.batch_table.cellDoubleClicked.connect(self.on_batch_row_double_clicked)

        header = self.batch_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.batch_table, 1)

        # Нижняя панель пакетного режима (прогресс-бар и кнопки запуска/остановки)
        batch_bottom = QHBoxLayout()
        batch_bottom.setSpacing(10)

        self.lbl_batch_status = QLabel("Очередь пуста")
        self.lbl_batch_status.setObjectName("Muted")
        batch_bottom.addWidget(self.lbl_batch_status)

        self.batch_progress = QProgressBar()
        self.batch_progress.setValue(0)
        batch_bottom.addWidget(self.batch_progress, 1)

        self.btn_open_out_folder = QPushButton("📂 Открыть папку")
        self.btn_open_out_folder.clicked.connect(self.open_batch_output_folder)
        batch_bottom.addWidget(self.btn_open_out_folder)

        self.btn_stop_batch = QPushButton("⏹ Остановить")
        self.btn_stop_batch.setObjectName("DangerBtn")
        self.btn_stop_batch.setEnabled(False)
        self.btn_stop_batch.clicked.connect(self.stop_batch_conversion)
        batch_bottom.addWidget(self.btn_stop_batch)

        self.btn_start_batch = QPushButton("🚀 Запустить пакетную конвертацию")
        self.btn_start_batch.setObjectName("SuccessBtn")
        self.btn_start_batch.clicked.connect(self.start_batch_conversion)
        batch_bottom.addWidget(self.btn_start_batch)

        layout.addLayout(batch_bottom)
        return page

    # =====================================================================
    # ПЕРЕКЛЮЧЕНИЕ ТЕМ, ШРИФТА И РЕЖИМОВ
    # =====================================================================
    def switch_mode(self, index: int):
        self.stack.setCurrentIndex(index)
        self.btn_mode_single.setChecked(index == 0)
        self.btn_mode_batch.setChecked(index == 1)

    def on_quick_theme_changed(self, theme_name: str):
        self.settings.setValue("theme", theme_name)
        self.apply_appearance()

    def adjust_font_size(self, delta: int):
        current = self.settings.value("editor_font_size", 11, type=int)
        new_size = max(9, min(22, current + delta))
        self.settings.setValue("editor_font_size", new_size)
        self.apply_appearance()

    def apply_appearance(self):
        theme_name = self.settings.value("theme", "Slate Dark", type=str)
        font_size = self.settings.value("editor_font_size", 11, type=int)

        if self.combo_quick_theme.currentText() != theme_name:
            self.combo_quick_theme.blockSignals(True)
            self.combo_quick_theme.setCurrentText(theme_name)
            self.combo_quick_theme.blockSignals(False)

        QApplication.instance().setStyleSheet(build_stylesheet(theme_name))

        mono_font = QFont("JetBrains Mono", font_size)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self.editor.setFont(mono_font)

        preview_font = QFont("Segoe UI", font_size)
        self.preview.setFont(preview_font)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.browse_single_input_file)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_single_markdown_file)
        QShortcut(QKeySequence("Ctrl+Shift+C"), self, activated=self.copy_to_clipboard)
        QShortcut(QKeySequence("Ctrl+="), self, activated=lambda: self.adjust_font_size(1))
        QShortcut(QKeySequence("Ctrl+-"), self, activated=lambda: self.adjust_font_size(-1))

    def get_engine_config(self) -> dict:
        return {
            "enable_plugins": self.settings.value("enable_plugins", False, type=bool),
            "use_llm": self.settings.value("use_llm", False, type=bool),
            "llm_api_key": self.settings.value("llm_api_key", "", type=str),
            "llm_base_url": self.settings.value("llm_base_url", "", type=str),
            "llm_model": self.settings.value("llm_model", "gpt-4o-mini", type=str),
            "docintel_endpoint": self.settings.value("docintel_endpoint", "", type=str),
        }

    # =====================================================================
    # ЛОГИКА УМНОГО DRAG & DROP (ОДИНОЧНЫЙ VS ПАКЕТНЫЙ)
    # =====================================================================
    def handle_dropped_paths(self, paths: list):
        """Если сброшена папка или больше 1 файла — автоматически переходим в Пакетный режим."""
        if len(paths) > 1 or (len(paths) == 1 and Path(paths[0]).is_dir()):
            self.switch_mode(1)
            self.batch_add_paths(paths)
        elif len(paths) == 1:
            self.set_single_source(paths[0])

    # =====================================================================
    # ЛОГИКА ОДИНОЧНОГО РЕЖИМА
    # =====================================================================
    def set_view_mode(self, mode: str):
        self.btn_view_raw.setChecked(mode == "raw")
        self.btn_view_split.setChecked(mode == "split")
        self.btn_view_preview.setChecked(mode == "preview")
        self.editor.setVisible(mode in ("raw", "split"))
        self.preview.setVisible(mode in ("preview", "split"))

    def browse_single_input_file(self):
        last_dir = self.settings.value("last_input_dir", str(Path.home()), type=str)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл для конвертации в Markdown",
            last_dir,
            SUPPORTED_EXTENSIONS_FILTER,
        )
        if file_path:
            self.settings.setValue("last_input_dir", str(Path(file_path).parent))
            self.set_single_source(file_path)

    def paste_url_from_clipboard(self):
        clipboard_text = QApplication.clipboard().text().strip()
        if clipboard_text:
            self.url_input.setText(clipboard_text)
            self.set_single_source(clipboard_text)

    def on_url_entered(self):
        url = self.url_input.text().strip()
        if url:
            self.set_single_source(url)

    def set_single_source(self, source: str):
        source = source.strip()
        if not source:
            return

        self.current_source = source
        self.last_extracted_title = ""

        if source.startswith(("http://", "https://")):
            self.url_input.setText(source)
            domain = urlparse(source).netloc.lower()
            self.badge_type.setText("YOUTUBE" if ("youtube.com" in domain or "youtu.be" in domain) else "WEB URL")
            self.lbl_source_info.setText(source)
        else:
            path = Path(source)
            if path.exists() and path.is_file():
                ext = path.suffix.upper().lstrip(".") or "FILE"
                size_kb = path.stat().st_size / 1024
                size_str = f"{size_kb:.1f} КБ" if size_kb < 1024 else f"{size_kb / 1024:.2f} МБ"
                self.badge_type.setText(ext)
                self.lbl_source_info.setText(f"{path.name}  ({size_str})  —  {path.parent}")
                self.single_drop_zone.title_lbl.setText(f"Выбран файл: {path.name}")
            else:
                QMessageBox.warning(self, "Источник не найден", f"Не удалось найти файл:\n{source}")
                return

        if self.cb_auto_convert.isChecked():
            self.start_single_conversion()

    def start_single_conversion(self):
        url_candidate = self.url_input.text().strip()
        if not self.current_source and url_candidate:
            self.current_source = url_candidate

        if not self.current_source:
            QMessageBox.information(self, "Выберите источник", "Выберите файл или вставьте ссылку для конвертации.")
            return

        if self.single_worker and self.single_worker.isRunning():
            return

        self.single_progress.setVisible(True)
        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("Конвертация…")
        self.lbl_source_info.setText(f"Обработка: {self.current_source} …")

        self.single_worker = SingleConversionWorker(self.current_source, self.get_engine_config())
        self.single_worker.finished.connect(self.on_single_conversion_success)
        self.single_worker.error.connect(self.on_single_conversion_error)
        self.single_worker.start()

    def on_single_conversion_success(self, markdown_text: str, title: str, elapsed: float):
        self.single_progress.setVisible(False)
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("⚡ Конвертировать")

        self.last_extracted_title = title
        self.editor.setPlainText(markdown_text)
        self.sync_preview_and_stats()

        source_display = Path(self.current_source).name if not self.current_source.startswith("http") else self.current_source
        self.lbl_source_info.setText(f"✓ Готово за {elapsed:.2f} сек  |  Источник: {source_display}")

    def on_single_conversion_error(self, error_msg: str):
        self.single_progress.setVisible(False)
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("⚡ Конвертировать")
        self.lbl_source_info.setText("Ошибка при конвертации")
        QMessageBox.critical(self, "Ошибка конвертации", f"Не удалось конвертировать источник:\n\n{error_msg}")

    def sync_preview_and_stats(self):
        text = self.editor.toPlainText()
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
        est_tokens = int(chars / 3.8)

        self.lbl_stats.setText(
            f"Строк: {lines:,}  |  Слов: {words:,}  |  Символов: {chars:,}  |  ~Токенов: {est_tokens:,}".replace(",", " ")
        )

        has_text = chars > 0
        self.btn_save.setEnabled(has_text)
        self.btn_copy.setEnabled(has_text)
        self.btn_clear.setEnabled(has_text)

    def get_suggested_save_path(self) -> str:
        if self.current_source and not self.current_source.startswith(("http://", "https://")):
            return str(Path(self.current_source).with_suffix(".md"))

        base_dir = self.settings.value("last_save_dir", str(Path.home()), type=str)
        raw_name = self.last_extracted_title or urlparse(self.current_source).path.strip("/").split("/")[-1] or "converted_page"
        clean_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", raw_name).strip(" ._")[:80] or "document"
        return str(Path(base_dir) / f"{clean_name}.md")

    def save_single_markdown_file(self):
        text = self.editor.toPlainText()
        if not text:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить Markdown файл",
            self.get_suggested_save_path(),
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

    def clear_single_workspace(self):
        self.editor.clear()
        self.preview.clear()
        self.current_source = ""
        self.last_extracted_title = ""
        self.url_input.clear()
        self.badge_type.setText("ОЖИДАНИЕ")
        self.lbl_source_info.setText("Файл или ссылка не выбраны")
        self.single_drop_zone.title_lbl.setText("Перетащите файл сюда (или несколько файлов для пакетного режима)")

    # =====================================================================
    # ЛОГИКА ПАКЕТНОГО РЕЖИМА (BATCH CONVERSION)
    # =====================================================================
    def on_batch_save_mode_changed(self, idx: int):
        is_custom_dir = idx == 0
        self.input_batch_out_dir.setEnabled(is_custom_dir)
        self.btn_browse_out_dir.setEnabled(is_custom_dir)

    def browse_batch_output_dir(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения Markdown-файлов",
            self.input_batch_out_dir.text() or str(Path.home()),
        )
        if folder:
            self.input_batch_out_dir.setText(folder)
            self.settings.setValue("last_batch_out_dir", folder)

    def batch_add_files_dialog(self):
        last_dir = self.settings.value("last_input_dir", str(Path.home()), type=str)
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите файлы для пакетной конвертации",
            last_dir,
            SUPPORTED_EXTENSIONS_FILTER,
        )
        if files:
            self.settings.setValue("last_input_dir", str(Path(files[0]).parent))
            self.batch_add_paths(files)

    def batch_add_folder_dialog(self):
        last_dir = self.settings.value("last_input_dir", str(Path.home()), type=str)
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с документами", last_dir)
        if folder:
            self.settings.setValue("last_input_dir", folder)
            self.batch_add_paths([folder])

    def batch_add_paths(self, raw_paths: list):
        existing_sources = {
            self.batch_table.item(r, 1).data(Qt.ItemDataRole.UserRole)
            for r in range(self.batch_table.rowCount())
        }

        files_to_add = []
        recursive = self.cb_recursive.isChecked()

        for p_str in raw_paths:
            p = Path(p_str)
            if p.is_file():
                files_to_add.append(p)
            elif p.is_dir():
                iterator = p.rglob("*") if recursive else p.glob("*")
                for child in iterator:
                    if child.is_file() and child.suffix.lower() in SUPPORTED_EXTS:
                        files_to_add.append(child)

        added_count = 0
        for f_path in files_to_add:
            full_str = str(f_path.resolve())
            if full_str in existing_sources:
                continue
            existing_sources.add(full_str)

            row = self.batch_table.rowCount()
            self.batch_table.insertRow(row)

            status_item = QTableWidgetItem("⏳ Ожидание")
            name_item = QTableWidgetItem(f_path.name)
            name_item.setToolTip(full_str)
            name_item.setData(Qt.ItemDataRole.UserRole, full_str)

            ext_item = QTableWidgetItem(f_path.suffix.upper().lstrip(".") or "FILE")
            size_kb = f_path.stat().st_size / 1024
            size_str = f"{size_kb:.1f} КБ" if size_kb < 1024 else f"{size_kb / 1024:.2f} МБ"
            size_item = QTableWidgetItem(size_str)
            out_item = QTableWidgetItem("—")

            self.batch_table.setItem(row, 0, status_item)
            self.batch_table.setItem(row, 1, name_item)
            self.batch_table.setItem(row, 2, ext_item)
            self.batch_table.setItem(row, 3, size_item)
            self.batch_table.setItem(row, 4, out_item)
            added_count += 1

        self.update_batch_counters()

    def batch_remove_selected(self):
        selected_rows = sorted({idx.row() for idx in self.batch_table.selectedIndexes()}, reverse=True)
        for r in selected_rows:
            self.batch_table.removeRow(r)
            self.batch_results_cache.pop(r, None)
        self.update_batch_counters()

    def batch_clear_all(self):
        self.batch_table.setRowCount(0)
        self.batch_results_cache.clear()
        self.batch_progress.setValue(0)
        self.update_batch_counters()

    def update_batch_counters(self):
        total = self.batch_table.rowCount()
        self.btn_mode_batch.setText(f"📚 Пакетная конвертация ({total})")
        self.lbl_batch_status.setText(f"Файлов в очереди: {total}")

    def start_batch_conversion(self):
        total = self.batch_table.rowCount()
        if total == 0:
            QMessageBox.information(self, "Очередь пуста", "Добавьте файлы или папку для запуска пакетной конвертации.")
            return

        save_mode = "custom_dir" if self.combo_save_mode.currentIndex() == 0 else "alongside"
        custom_dir = self.input_batch_out_dir.text().strip()
        if save_mode == "custom_dir" and not custom_dir:
            QMessageBox.warning(self, "Не выбрана папка", "Укажите папку для сохранения результатов.")
            return

        if save_mode == "custom_dir":
            self.settings.setValue("last_batch_out_dir", custom_dir)

        collision_map = {0: "rename", 1: "overwrite", 2: "skip"}
        collision_mode = collision_map.get(self.combo_collision.currentIndex(), "rename")

        items = []
        for r in range(total):
            src_full = self.batch_table.item(r, 1).data(Qt.ItemDataRole.UserRole)
            self.batch_table.item(r, 0).setText("⏳ Ожидание")
            self.batch_table.item(r, 4).setText("—")
            items.append((r, src_full))

        merge_all = self.cb_merge_all.isChecked()
        merge_base = Path(custom_dir) if save_mode == "custom_dir" else Path(items[0][1]).parent
        merge_file_path = str(merge_base / "_merged_bundle.md") if merge_all else ""

        self.batch_results_cache.clear()
        self.batch_progress.setRange(0, total)
        self.batch_progress.setValue(0)

        self.btn_start_batch.setEnabled(False)
        self.btn_stop_batch.setEnabled(True)

        self.batch_worker = BatchConversionWorker(
            items=items,
            config=self.get_engine_config(),
            save_mode=save_mode,
            custom_dir=custom_dir,
            collision_mode=collision_mode,
            merge_all=merge_all,
            merge_file_path=merge_file_path,
        )
        self.batch_worker.item_started.connect(self.on_batch_item_started)
        self.batch_worker.item_finished.connect(self.on_batch_item_finished)
        self.batch_worker.item_error.connect(self.on_batch_item_error)
        self.batch_worker.batch_finished.connect(self.on_batch_all_finished)
        self.batch_worker.start()

    def stop_batch_conversion(self):
        if self.batch_worker and self.batch_worker.isRunning():
            self.batch_worker.request_stop()
            self.lbl_batch_status.setText("Остановка после завершения текущего файла…")
            self.btn_stop_batch.setEnabled(False)

    def on_batch_item_started(self, row: int):
        self.batch_table.item(row, 0).setText("⚙️ В работе…")
        self.batch_table.scrollToItem(self.batch_table.item(row, 0))
        self.lbl_batch_status.setText(f"Конвертация ({row + 1}/{self.batch_table.rowCount()}): {self.batch_table.item(row, 1).text()}")

    def on_batch_item_finished(self, row: int, saved_path: str, md_text: str, elapsed: float):
        self.batch_table.item(row, 0).setText(f"✅ {elapsed:.1f}с")
        out_item = self.batch_table.item(row, 4)
        out_item.setText(saved_path)
        out_item.setToolTip(saved_path)
        if md_text:
            self.batch_results_cache[row] = md_text
        self.batch_progress.setValue(self.batch_progress.value() + 1)

    def on_batch_item_error(self, row: int, error_msg: str):
        self.batch_table.item(row, 0).setText("❌ Ошибка")
        out_item = self.batch_table.item(row, 4)
        out_item.setText(error_msg)
        out_item.setToolTip(error_msg)
        self.batch_progress.setValue(self.batch_progress.value() + 1)

    def on_batch_all_finished(self, ok_count: int, err_count: int, merged_path: str):
        self.btn_start_batch.setEnabled(True)
        self.btn_stop_batch.setEnabled(False)

        msg = f"Готово! Успешно: {ok_count}, Ошибок: {err_count}"
        if merged_path:
            msg += f"  |  Общий файл: {Path(merged_path).name}"
        self.lbl_batch_status.setText(msg)

    def on_batch_row_double_clicked(self, row: int, _col: int):
        """По двойному клику открывает сконвертированный файл из пакета во встроенном редакторе/превью."""
        md_text = self.batch_results_cache.get(row)
        saved_path = self.batch_table.item(row, 4).text()

        if not md_text and saved_path and Path(saved_path).is_file():
            try:
                md_text = Path(saved_path).read_text(encoding="utf-8")
            except Exception:
                pass

        if md_text:
            src_full = self.batch_table.item(row, 1).data(Qt.ItemDataRole.UserRole)
            self.current_source = src_full
            self.badge_type.setText(self.batch_table.item(row, 2).text())
            self.lbl_source_info.setText(f"Просмотр из пакета: {Path(src_full).name}  →  {saved_path}")
            self.editor.setPlainText(md_text)
            self.sync_preview_and_stats()
            self.switch_mode(0)

    def open_batch_output_folder(self):
        target_dir = self.input_batch_out_dir.text().strip()
        if not target_dir or not Path(target_dir).exists():
            target_dir = str(Path.home())
        if sys.platform.startswith("win"):
            os.startfile(target_dir)
        elif sys.platform == "darwin":
            os.system(f'open "{target_dir}"')
        else:
            os.system(f'xdg-open "{target_dir}"')

    def open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        dlg.settings_changed.connect(self.apply_appearance)
        dlg.exec()


def main():
    app = QApplication(sys.argv)
    window = MarkItDownApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()