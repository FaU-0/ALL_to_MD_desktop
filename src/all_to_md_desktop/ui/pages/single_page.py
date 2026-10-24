import re
from pathlib import Path
from urllib.parse import urlparse

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from all_to_md_desktop.config import SUPPORTED_EXTENSIONS_FILTER, AppConfig
from all_to_md_desktop.core.workers import SingleConversionWorker
from all_to_md_desktop.ui.widgets.drop_zone import DropZoneFrame


class SingleModePage(QWidget):
    """Вкладка конвертации одиночного файла или веб-ссылки со встроенным редактором."""

    request_batch_switch = pyqtSignal(list)

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.current_source = ""
        self.last_extracted_title = ""
        self.worker = None

        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(180)
        self.preview_timer.timeout.connect(self.sync_preview_and_stats)

        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(10)

        top_card = QFrame()
        top_card.setObjectName("Card")
        top_layout = QVBoxLayout(top_card)
        top_layout.setContentsMargins(14, 12, 14, 12)
        top_layout.setSpacing(10)

        self.drop_zone = DropZoneFrame(
            "Перетащите файл сюда (или несколько файлов для пакетного режима)",
            "PDF, Word, Excel, PowerPoint, HTML, CSV, JSON, ZIP, Изображения, Аудио",
            "Выбрать файл…",
        )
        self.drop_zone.clicked.connect(self.browse_input_file)
        self.drop_zone.paths_dropped.connect(self.on_paths_dropped)
        top_layout.addWidget(self.drop_zone)

        url_row = QHBoxLayout()
        url_row.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "🔗 Или вставьте ссылку (YouTube видео, статья, Wikipedia, веб-страница) и нажмите Enter…"
        )
        self.url_input.returnPressed.connect(self.on_url_entered)
        url_row.addWidget(self.url_input, 1)

        btn_paste = QPushButton("Вставить URL")
        btn_paste.clicked.connect(self.paste_url_from_clipboard)
        url_row.addWidget(btn_paste)

        self.cb_auto_convert = QCheckBox("Авто-старт")
        self.cb_auto_convert.setChecked(self.config.auto_convert)
        self.cb_auto_convert.toggled.connect(self._on_auto_convert_toggled)
        url_row.addWidget(self.cb_auto_convert)

        self.btn_convert = QPushButton("⚡ Конвертировать")
        self.btn_convert.setObjectName("PrimaryBtn")
        self.btn_convert.clicked.connect(self.start_conversion)
        url_row.addWidget(self.btn_convert)

        top_layout.addLayout(url_row)
        layout.addWidget(top_card)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

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
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.btn_copy.setEnabled(False)
        bottom_row.addWidget(self.btn_copy)

        self.btn_save = QPushButton("💾 Сохранить как… (Ctrl+S)")
        self.btn_save.setObjectName("SuccessBtn")
        self.btn_save.clicked.connect(self.save_markdown_file)
        self.btn_save.setEnabled(False)
        bottom_row.addWidget(self.btn_save)

        layout.addLayout(bottom_row)

    def _on_auto_convert_toggled(self, checked: bool) -> None:
        self.config.auto_convert = checked

    def apply_fonts(self, font_size: int) -> None:
        mono_font = QFont("JetBrains Mono", font_size)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self.editor.setFont(mono_font)
        self.preview.setFont(QFont("Segoe UI", font_size))

    def set_view_mode(self, mode: str) -> None:
        self.btn_view_raw.setChecked(mode == "raw")
        self.btn_view_split.setChecked(mode == "split")
        self.btn_view_preview.setChecked(mode == "preview")
        self.editor.setVisible(mode in ("raw", "split"))
        self.preview.setVisible(mode in ("preview", "split"))

    def on_paths_dropped(self, paths: list) -> None:
        if len(paths) > 1 or (len(paths) == 1 and Path(paths[0]).is_dir()):
            self.request_batch_switch.emit(paths)
        elif len(paths) == 1:
            self.set_source(paths[0])

    def browse_input_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл для конвертации в Markdown",
            self.config.last_input_dir,
            SUPPORTED_EXTENSIONS_FILTER,
        )
        if file_path:
            self.config.last_input_dir = str(Path(file_path).parent)
            self.set_source(file_path)

    def paste_url_from_clipboard(self) -> None:
        clipboard_text = QApplication.clipboard().text().strip()
        if clipboard_text:
            self.url_input.setText(clipboard_text)
            self.set_source(clipboard_text)

    def on_url_entered(self) -> None:
        url = self.url_input.text().strip()
        if url:
            self.set_source(url)

    def set_source(self, source: str) -> None:
        source = source.strip()
        if not source:
            return

        self.current_source = source
        self.last_extracted_title = ""

        if source.startswith(("http://", "https://")):
            self.url_input.setText(source)
            domain = urlparse(source).netloc.lower()
            self.badge_type.setText(
                "YOUTUBE" if ("youtube.com" in domain or "youtu.be" in domain) else "WEB URL"
            )
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
                QMessageBox.warning(self, "Источник не найден", f"Не удалось найти файл:\n{source}")
                return

        if self.cb_auto_convert.isChecked():
            self.start_conversion()

    def start_conversion(self) -> None:
        url_candidate = self.url_input.text().strip()
        if not self.current_source and url_candidate:
            self.current_source = url_candidate

        if not self.current_source:
            QMessageBox.information(
                self, "Выберите источник", "Выберите файл или вставьте ссылку для конвертации."
            )
            return

        if self.worker and self.worker.isRunning():
            return

        self.progress_bar.setVisible(True)
        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("Конвертация…")
        self.lbl_source_info.setText(f"Обработка: {self.current_source} …")

        self.worker = SingleConversionWorker(self.current_source, self.config.get_engine_options())
        self.worker.finished.connect(self.on_conversion_success)
        self.worker.error.connect(self.on_conversion_error)
        self.worker.start()

    def on_conversion_success(self, markdown_text: str, title: str, elapsed: float) -> None:
        self.progress_bar.setVisible(False)
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("⚡ Конвертировать")

        self.last_extracted_title = title
        self.editor.setPlainText(markdown_text)
        self.sync_preview_and_stats()

        source_display = (
            Path(self.current_source).name
            if not self.current_source.startswith("http")
            else self.current_source
        )
        self.lbl_source_info.setText(f"✓ Готово за {elapsed:.2f} сек  |  Источник: {source_display}")

    def on_conversion_error(self, error_msg: str) -> None:
        self.progress_bar.setVisible(False)
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("⚡ Конвертировать")
        self.lbl_source_info.setText("Ошибка при конвертации")
        QMessageBox.critical(
            self, "Ошибка конвертации", f"Не удалось конвертировать источник:\n\n{error_msg}"
        )

    def load_external_result(
        self, source_path: str, file_ext: str, saved_path: str, markdown_text: str
    ) -> None:
        """Загружает готовый результат из пакетного режима в редактор."""
        self.current_source = source_path
        self.badge_type.setText(file_ext)
        self.lbl_source_info.setText(
            f"Просмотр из пакета: {Path(source_path).name}  →  {saved_path}"
        )
        self.editor.setPlainText(markdown_text)
        self.sync_preview_and_stats()

    def sync_preview_and_stats(self) -> None:
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
            f"Строк: {lines:,}  |  Слов: {words:,}  |  Символов: {chars:,}  |  ~Токенов: {est_tokens:,}".replace(
                ",", " "
            )
        )

        has_text = chars > 0
        self.btn_save.setEnabled(has_text)
        self.btn_copy.setEnabled(has_text)
        self.btn_clear.setEnabled(has_text)

    def _get_suggested_save_path(self) -> str:
        if self.current_source and not self.current_source.startswith(("http://", "https://")):
            return str(Path(self.current_source).with_suffix(".md"))

        raw_name = (
            self.last_extracted_title
            or urlparse(self.current_source).path.strip("/").split("/")[-1]
            or "converted_page"
        )
        clean_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", raw_name).strip(" ._")[:80] or "document"
        return str(Path(self.config.last_save_dir) / f"{clean_name}.md")

    def save_markdown_file(self) -> None:
        text = self.editor.toPlainText()
        if not text:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить Markdown файл",
            self._get_suggested_save_path(),
            "Markdown документ (*.md);;Текстовый файл (*.txt);;Все файлы (*)",
        )
        if save_path:
            try:
                target = Path(save_path)
                if not target.suffix:
                    target = target.with_suffix(".md")
                target.write_text(text, encoding="utf-8")
                self.config.last_save_dir = str(target.parent)
                self.lbl_source_info.setText(f"💾 Файл успешно сохранен: {target}")
            except Exception as exc:
                QMessageBox.critical(self, "Ошибка сохранения", f"Не удалось записать файл:\n{exc}")

    def copy_to_clipboard(self) -> None:
        text = self.editor.toPlainText()
        if not text:
            return
        QApplication.clipboard().setText(text)
        old_text = self.btn_copy.text()
        self.btn_copy.setText("✓ Скопировано!")
        QTimer.singleShot(1500, lambda: self.btn_copy.setText(old_text))

    def clear_workspace(self) -> None:
        self.editor.clear()
        self.preview.clear()
        self.current_source = ""
        self.last_extracted_title = ""
        self.url_input.clear()
        self.badge_type.setText("ОЖИДАНИЕ")
        self.lbl_source_info.setText("Файл или ссылка не выбраны")
        self.drop_zone.title_lbl.setText(
            "Перетащите файл сюда (или несколько файлов для пакетного режима)"
        )