import sys
from pathlib import Path

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QKeySequence, QPainter, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from all_to_md_desktop import __app_name__, __version__
from all_to_md_desktop.config import AppConfig
from all_to_md_desktop.themes.palettes import THEMES, build_stylesheet
from all_to_md_desktop.ui.dialogs.settings_dialog import SettingsDialog
from all_to_md_desktop.ui.pages.batch_page import BatchModePage
from all_to_md_desktop.ui.pages.single_page import SingleModePage


def create_app_icon() -> QIcon:
    """
    Загружает иконку из папки assets/ (icon.ico или icon.png).
    Если файл еще не добавлен, программно рисует строгую векторную иконку 'MD'.
    """
    base_paths = [
        Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3])),
        Path.cwd(),
    ]
    for base in base_paths:
        for name in ("assets/icon.ico", "assets/icon.png", "icon.ico", "icon.png"):
            candidate = base / name
            if candidate.exists():
                return QIcon(str(candidate))

    # Программная векторная иконка 64x64 (графитовый квадрат со знаком MD)
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QColor("#18181b"))
    painter.setPen(QColor("#3f3f46"))
    painter.drawRoundedRect(2, 2, 60, 60, 14, 14)

    font = QFont("Segoe UI", 20, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#f4f4f5"))
    painter.drawText(QRect(0, 4, 64, 38), Qt.AlignmentFlag.AlignCenter, "MD")

    painter.setBrush(QColor("#f59e0b"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(16, 46, 32, 5, 2, 2)
    painter.end()

    return QIcon(pixmap)


class MainWindow(QMainWindow):
    """Главное окно приложения ALL_to_MD_desktop."""

    def __init__(self):
        super().__init__()
        self.config = AppConfig()

        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.setWindowIcon(create_app_icon())
        self.resize(1180, 800)
        self.setMinimumSize(900, 620)

        self.init_ui()
        self.setup_shortcuts()
        self.apply_appearance()

    def init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        self.btn_mode_single = QPushButton("Одиночный файл / URL")
        self.btn_mode_single.setObjectName("ModeTabBtn")
        self.btn_mode_single.setCheckable(True)
        self.btn_mode_single.setChecked(True)
        self.btn_mode_single.clicked.connect(lambda: self.switch_mode(0))

        self.btn_mode_batch = QPushButton("Пакетная конвертация (0)")
        self.btn_mode_batch.setObjectName("ModeTabBtn")
        self.btn_mode_batch.setCheckable(True)
        self.btn_mode_batch.clicked.connect(lambda: self.switch_mode(1))

        header_row.addWidget(self.btn_mode_single)
        header_row.addWidget(self.btn_mode_batch)
        header_row.addStretch()

        lbl_theme = QLabel("Тема:")
        lbl_theme.setObjectName("Muted")
        header_row.addWidget(lbl_theme)

        self.combo_quick_theme = QComboBox()
        self.combo_quick_theme.addItems(list(THEMES.keys()))
        self.combo_quick_theme.setCurrentText(self.config.theme)
        self.combo_quick_theme.currentTextChanged.connect(self.on_quick_theme_changed)
        header_row.addWidget(self.combo_quick_theme)

        btn_font_dec = QPushButton("A-")
        btn_font_dec.setObjectName("ToolbarBtn")
        btn_font_dec.setToolTip("Уменьшить шрифт (Ctrl+-)")
        btn_font_dec.clicked.connect(lambda: self.adjust_font_size(-1))
        header_row.addWidget(btn_font_dec)

        btn_font_inc = QPushButton("A+")
        btn_font_inc.setObjectName("ToolbarBtn")
        btn_font_inc.setToolTip("Увеличить шрифт (Ctrl+=)")
        btn_font_inc.clicked.connect(lambda: self.adjust_font_size(1))
        header_row.addWidget(btn_font_inc)

        btn_settings = QPushButton("Параметры")
        btn_settings.setObjectName("ToolbarBtn")
        btn_settings.setToolTip("Настройки движка MarkItDown, LLM Vision и оформления")
        btn_settings.clicked.connect(self.open_settings)
        header_row.addWidget(btn_settings)

        root_layout.addLayout(header_row)

        self.stack = QStackedWidget()
        self.single_page = SingleModePage(self.config, self)
        self.batch_page = BatchModePage(self.config, self)

        self.stack.addWidget(self.single_page)
        self.stack.addWidget(self.batch_page)
        root_layout.addWidget(self.stack, 1)

        self.single_page.request_batch_switch.connect(self._on_batch_switch_requested)
        self.batch_page.queue_count_changed.connect(
            lambda count: self.btn_mode_batch.setText(f"Пакетная конвертация ({count})")
        )
        self.batch_page.open_in_editor_requested.connect(self._on_open_in_editor_from_batch)

    def switch_mode(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.btn_mode_single.setChecked(index == 0)
        self.btn_mode_batch.setChecked(index == 1)

    def _on_batch_switch_requested(self, paths: list) -> None:
        self.switch_mode(1)
        self.batch_page.add_paths(paths)

    def _on_open_in_editor_from_batch(
        self, src_full: str, ext: str, saved_path: str, md_text: str
    ) -> None:
        self.single_page.load_external_result(src_full, ext, saved_path, md_text)
        self.switch_mode(0)

    def on_quick_theme_changed(self, theme_name: str) -> None:
        self.config.theme = theme_name
        self.apply_appearance()

    def adjust_font_size(self, delta: int) -> None:
        self.config.editor_font_size += delta
        self.apply_appearance()

    def apply_appearance(self) -> None:
        theme_name = self.config.theme
        font_size = self.config.editor_font_size

        if self.combo_quick_theme.currentText() != theme_name:
            self.combo_quick_theme.blockSignals(True)
            self.combo_quick_theme.setCurrentText(theme_name)
            self.combo_quick_theme.blockSignals(False)

        QApplication.instance().setStyleSheet(build_stylesheet(theme_name))
        self.single_page.apply_fonts(font_size)

    def setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.single_page.browse_input_file)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.single_page.save_markdown_file)
        QShortcut(QKeySequence("Ctrl+Shift+C"), self, activated=self.single_page.copy_to_clipboard)
        QShortcut(QKeySequence("Ctrl+="), self, activated=lambda: self.adjust_font_size(1))
        QShortcut(QKeySequence("Ctrl+-"), self, activated=lambda: self.adjust_font_size(-1))

    def open_settings(self) -> None:
        dlg = SettingsDialog(self.config, self)
        dlg.settings_changed.connect(self.apply_appearance)
        dlg.exec()