import datetime
import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
TEXT_PREVIEW_EXTS = {".txt", ".csv", ".json", ".xml", ".html", ".htm", ".md", ".log"}


class SourceViewer(QWidget):
    """Виджет отображения исходного файла или ссылки для режима сравнения."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_source = ""
        self._current_pixmap: QPixmap | None = None
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Заголовок панели исходника
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        self.lbl_header = QLabel("ИСХОДНЫЙ ФАЙЛ")
        self.lbl_header.setObjectName("PaneHeader")
        header_row.addWidget(self.lbl_header, 1)

        self.btn_open_external = QPushButton("Открыть в системе")
        self.btn_open_external.setObjectName("ToolbarBtn")
        self.btn_open_external.clicked.connect(self.open_in_system)
        self.btn_open_external.setVisible(False)
        header_row.addWidget(self.btn_open_external)

        layout.addLayout(header_row)

        self.stack = QStackedWidget()

        # Страница 0: Текстовый просмотрщик исходника (CSV, JSON, HTML, TXT)
        self.text_view = QPlainTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setPlaceholderText("Выберите файл или ссылку для просмотра исходника…")
        self.stack.addWidget(self.text_view)

        # Страница 1: Просмотрщик изображений
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_scroll.setFrameShape(QFrame.Shape.StyledPanel)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_scroll.setWidget(self.image_label)
        self.stack.addWidget(self.image_scroll)

        # Страница 2: Карточка бинарного документа (PDF, DOCX, XLSX, PPTX, Аудио, URL)
        self.info_card = QFrame()
        self.info_card.setObjectName("Card")
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setContentsMargins(24, 24, 24, 24)
        info_layout.setSpacing(12)
        info_layout.addStretch()

        self.lbl_doc_title = QLabel("Источник не выбран")
        self.lbl_doc_title.setStyleSheet("font-size: 15px; font-weight: 600;")
        self.lbl_doc_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_doc_title.setWordWrap(True)
        info_layout.addWidget(self.lbl_doc_title)

        self.lbl_doc_meta = QLabel("")
        self.lbl_doc_meta.setObjectName("Muted")
        self.lbl_doc_meta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_doc_meta.setWordWrap(True)
        info_layout.addWidget(self.lbl_doc_meta)

        btn_holder = QHBoxLayout()
        btn_holder.addStretch()
        self.btn_card_open = QPushButton("Открыть оригинал во внешней программе")
        self.btn_card_open.clicked.connect(self.open_in_system)
        self.btn_card_open.setVisible(False)
        btn_holder.addWidget(self.btn_card_open)
        btn_holder.addStretch()
        info_layout.addLayout(btn_holder)

        info_layout.addStretch()
        self.stack.addWidget(self.info_card)

        layout.addWidget(self.stack, 1)
        self.stack.setCurrentIndex(2)

    def apply_font(self, font_size: int) -> None:
        mono = QFont("JetBrains Mono", font_size)
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self.text_view.setFont(mono)

    def set_source(self, source: str) -> None:
        self.current_source = source.strip()
        self._current_pixmap = None

        if not self.current_source:
            self.clear()
            return

        if self.current_source.startswith(("http://", "https://")):
            self.lbl_header.setText("ИСХОДНИК: ВЕБ-ССЫЛКА")
            self.btn_open_external.setVisible(True)
            self.btn_card_open.setVisible(True)
            self.btn_card_open.setText("Открыть ссылку в браузере")
            self.lbl_doc_title.setText(self.current_source)
            self.lbl_doc_meta.setText(
                "Веб-ресурс конвертируется напрямую по ссылке.\n"
                "Справа отображается извлеченное содержимое страницы в формате Markdown."
            )
            self.stack.setCurrentIndex(2)
            return

        path = Path(self.current_source)
        if not path.exists() or not path.is_file():
            self.clear()
            return

        ext = path.suffix.lower()
        size_bytes = path.stat().st_size
        size_str = (
            f"{size_bytes / 1024:.1f} КБ"
            if size_bytes < 1024 * 1024
            else f"{size_bytes / (1024 * 1024):.2f} МБ"
        )
        mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime("%d.%m.%Y %H:%M")

        self.lbl_header.setText(f"ИСХОДНИК: {path.name} ({size_str})")
        self.btn_open_external.setVisible(True)
        self.btn_card_open.setVisible(True)
        self.btn_card_open.setText("Открыть оригинал в программе по умолчанию")

        # 1. Если это изображение — рендерим саму картинку
        if ext in IMAGE_EXTS:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self._current_pixmap = pixmap
                self._update_scaled_pixmap()
                self.stack.setCurrentIndex(1)
                return

        # 2. Если это текстовый или табличный файл — показываем сырое содержимое
        if ext in TEXT_PREVIEW_EXTS:
            try:
                raw_text = path.read_text(encoding="utf-8", errors="replace")
                if len(raw_text) > 200_000:
                    raw_text = raw_text[:200_000] + "\n\n... [Показаны первые 200 КБ исходного файла]"
                self.text_view.setPlainText(raw_text)
                self.stack.setCurrentIndex(0)
                return
            except Exception:
                pass

        # 3. Для бинарных форматов (PDF, DOCX, XLSX, PPTX, ZIP, Аудио) — карточка паспорта файла
        self.lbl_doc_title.setText(path.name)
        self.lbl_doc_meta.setText(
            f"Формат: {ext.upper().lstrip('.') or 'Файл'}   |   Размер: {size_str}   |   Изменен: {mtime}\n"
            f"Расположение: {path.parent}\n\n"
            "Бинарный документ обработан движком MarkItDown. "
            "Результат конвертации доступен на правой панели."
        )
        self.stack.setCurrentIndex(2)

    def _update_scaled_pixmap(self) -> None:
        if self._current_pixmap and not self._current_pixmap.isNull():
            viewport = self.image_scroll.viewport().size()
            scaled = self._current_pixmap.scaled(
                max(200, viewport.width() - 24),
                max(200, viewport.height() - 24),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.stack.currentIndex() == 1:
            self._update_scaled_pixmap()

    def open_in_system(self) -> None:
        if not self.current_source:
            return
        if sys.platform.startswith("win"):
            os.startfile(self.current_source)
        elif sys.platform == "darwin":
            os.system(f'open "{self.current_source}"')
        else:
            os.system(f'xdg-open "{self.current_source}"')

    def clear(self) -> None:
        self.current_source = ""
        self._current_pixmap = None
        self.text_view.clear()
        self.image_label.clear()
        self.lbl_header.setText("ИСХОДНЫЙ ФАЙЛ")
        self.lbl_doc_title.setText("Источник не выбран")
        self.lbl_doc_meta.setText("Выберите файл или ссылку сверху для начала работы.")
        self.btn_open_external.setVisible(False)
        self.btn_card_open.setVisible(False)
        self.stack.setCurrentIndex(2)