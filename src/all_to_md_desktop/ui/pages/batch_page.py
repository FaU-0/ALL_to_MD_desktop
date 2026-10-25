import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from all_to_md_desktop.config import SUPPORTED_EXTENSIONS_FILTER, SUPPORTED_EXTS, AppConfig
from all_to_md_desktop.core.workers import BatchConversionWorker
from all_to_md_desktop.ui.widgets.drop_zone import DropZoneFrame


class BatchModePage(QWidget):
    """Вкладка пакетной конвертации файлов и папок."""

    queue_count_changed = pyqtSignal(int)
    open_in_editor_requested = pyqtSignal(str, str, str, str)

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.batch_worker = None
        self.batch_results_cache: dict[int, str] = {}
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(10)

        batch_top_card = QFrame()
        batch_top_card.setObjectName("Card")
        bt_layout = QVBoxLayout(batch_top_card)
        bt_layout.setContentsMargins(14, 12, 14, 12)
        bt_layout.setSpacing(10)

        self.drop_zone = DropZoneFrame(
            "Перетащите сюда файлы или папки для пакетной конвертации",
            "Автоматическая фильтрация всех поддерживаемых форматов документов и медиа",
            "+ Добавить файлы…",
        )
        self.drop_zone.clicked.connect(self.add_files_dialog)
        self.drop_zone.paths_dropped.connect(self.add_paths)
        bt_layout.addWidget(self.drop_zone)

        queue_actions_row = QHBoxLayout()
        queue_actions_row.setSpacing(8)

        btn_add_folder = QPushButton("📁 Добавить папку…")
        btn_add_folder.clicked.connect(self.add_folder_dialog)
        queue_actions_row.addWidget(btn_add_folder)

        self.cb_recursive = QCheckBox("Включая вложенные подпапки")
        self.cb_recursive.setChecked(True)
        queue_actions_row.addWidget(self.cb_recursive)

        queue_actions_row.addStretch()

        btn_remove_sel = QPushButton("Удалить выбранные")
        btn_remove_sel.clicked.connect(self.remove_selected)
        queue_actions_row.addWidget(btn_remove_sel)

        btn_clear_queue = QPushButton("Очистить список")
        btn_clear_queue.clicked.connect(self.clear_all)
        queue_actions_row.addWidget(btn_clear_queue)

        bt_layout.addLayout(queue_actions_row)
        layout.addWidget(batch_top_card)

        save_card = QFrame()
        save_card.setObjectName("Card")
        sc_layout = QVBoxLayout(save_card)
        sc_layout.setContentsMargins(14, 10, 14, 10)
        sc_layout.setSpacing(8)

        row_dest = QHBoxLayout()
        row_dest.setSpacing(8)

        row_dest.addWidget(QLabel("Сохранение:"))
        self.combo_save_mode = QComboBox()
        self.combo_save_mode.addItems([
            "В выбранную папку",
            "Рядом с исходными файлами",
        ])
        self.combo_save_mode.currentIndexChanged.connect(self._on_save_mode_changed)
        row_dest.addWidget(self.combo_save_mode)

        self.input_out_dir = QLineEdit()
        self.input_out_dir.setText(self.config.last_batch_out_dir)
        self.input_out_dir.setPlaceholderText("Путь к папке сохранения…")
        row_dest.addWidget(self.input_out_dir, 1)

        self.btn_browse_out_dir = QPushButton("📂 Обзор…")
        self.btn_browse_out_dir.clicked.connect(self.browse_output_dir)
        row_dest.addWidget(self.btn_browse_out_dir)

        row_dest.addWidget(QLabel("При совпадении имен:"))
        self.combo_collision = QComboBox()
        self.combo_collision.addItems([
            "Добавлять номер: файл (1).md",
            "Перезаписывать",
            "Пропускать",
        ])
        row_dest.addWidget(self.combo_collision)
        sc_layout.addLayout(row_dest)

        row_merge = QHBoxLayout()
        self.cb_merge_all = QCheckBox(
            "Дополнительно объединить все результаты в общий файл (_merged_bundle.md)"
        )
        row_merge.addWidget(self.cb_merge_all)
        row_merge.addStretch()

        hint_dbl = QLabel("Двойной клик по готовой строке откроет файл в Превью")
        hint_dbl.setObjectName("Muted")
        row_merge.addWidget(hint_dbl)
        sc_layout.addLayout(row_merge)

        layout.addWidget(save_card)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Статус", "Исходный файл", "Формат", "Размер", "Результат / Путь сохранения"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table, 1)

        batch_bottom = QHBoxLayout()
        batch_bottom.setSpacing(10)

        self.lbl_status = QLabel("Очередь пуста")
        self.lbl_status.setObjectName("Muted")
        batch_bottom.addWidget(self.lbl_status)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        batch_bottom.addWidget(self.progress, 1)

        self.btn_open_folder = QPushButton("📂 Открыть папку")
        self.btn_open_folder.clicked.connect(self.open_output_folder)
        batch_bottom.addWidget(self.btn_open_folder)

        self.btn_stop = QPushButton("Остановить")
        self.btn_stop.setObjectName("DangerBtn")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_conversion)
        batch_bottom.addWidget(self.btn_stop)

        self.btn_start = QPushButton("Запустить пакетную конвертацию")
        self.btn_start.setObjectName("PrimaryBtn")
        self.btn_start.clicked.connect(self.start_conversion)
        batch_bottom.addWidget(self.btn_start)

        layout.addLayout(batch_bottom)

    def _on_save_mode_changed(self, idx: int) -> None:
        is_custom_dir = idx == 0
        self.input_out_dir.setEnabled(is_custom_dir)
        self.btn_browse_out_dir.setEnabled(is_custom_dir)

    def browse_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения Markdown-файлов",
            self.input_out_dir.text() or str(Path.home()),
        )
        if folder:
            self.input_out_dir.setText(folder)
            self.config.last_batch_out_dir = folder

    def add_files_dialog(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите файлы для пакетной конвертации",
            self.config.last_input_dir,
            SUPPORTED_EXTENSIONS_FILTER,
        )
        if files:
            self.config.last_input_dir = str(Path(files[0]).parent)
            self.add_paths(files)

    def add_folder_dialog(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку с документами", self.config.last_input_dir
        )
        if folder:
            self.config.last_input_dir = folder
            self.add_paths([folder])

    def add_paths(self, raw_paths: list) -> None:
        existing_sources = {
            self.table.item(r, 1).data(Qt.ItemDataRole.UserRole)
            for r in range(self.table.rowCount())
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

        for f_path in files_to_add:
            full_str = str(f_path.resolve())
            if full_str in existing_sources:
                continue
            existing_sources.add(full_str)

            row = self.table.rowCount()
            self.table.insertRow(row)

            status_item = QTableWidgetItem("Ожидание")
            name_item = QTableWidgetItem(f_path.name)
            name_item.setToolTip(full_str)
            name_item.setData(Qt.ItemDataRole.UserRole, full_str)

            ext_item = QTableWidgetItem(f_path.suffix.upper().lstrip(".") or "FILE")
            size_kb = f_path.stat().st_size / 1024
            size_str = f"{size_kb:.1f} КБ" if size_kb < 1024 else f"{size_kb / 1024:.2f} МБ"
            size_item = QTableWidgetItem(size_str)
            out_item = QTableWidgetItem("—")

            self.table.setItem(row, 0, status_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, ext_item)
            self.table.setItem(row, 3, size_item)
            self.table.setItem(row, 4, out_item)

        self._update_counters()

    def remove_selected(self) -> None:
        selected_rows = sorted(
            {idx.row() for idx in self.table.selectedIndexes()}, reverse=True
        )
        for r in selected_rows:
            self.table.removeRow(r)
            self.batch_results_cache.pop(r, None)
        self._update_counters()

    def clear_all(self) -> None:
        self.table.setRowCount(0)
        self.batch_results_cache.clear()
        self.progress.setValue(0)
        self._update_counters()

    def _update_counters(self) -> None:
        total = self.table.rowCount()
        self.lbl_status.setText(f"Файлов в очереди: {total}")
        self.queue_count_changed.emit(total)

    def start_conversion(self) -> None:
        total = self.table.rowCount()
        if total == 0:
            QMessageBox.information(
                self, "Очередь пуста", "Добавьте файлы или папку для запуска пакетной конвертации."
            )
            return

        save_mode = "custom_dir" if self.combo_save_mode.currentIndex() == 0 else "alongside"
        custom_dir = self.input_out_dir.text().strip()
        if save_mode == "custom_dir" and not custom_dir:
            QMessageBox.warning(self, "Не выбрана папка", "Укажите папку для сохранения результатов.")
            return

        if save_mode == "custom_dir":
            self.config.last_batch_out_dir = custom_dir

        collision_map = {0: "rename", 1: "overwrite", 2: "skip"}
        collision_mode = collision_map.get(self.combo_collision.currentIndex(), "rename")

        items = []
        for r in range(total):
            src_full = self.table.item(r, 1).data(Qt.ItemDataRole.UserRole)
            self.table.item(r, 0).setText("Ожидание")
            self.table.item(r, 4).setText("—")
            items.append((r, src_full))

        merge_all = self.cb_merge_all.isChecked()
        merge_base = Path(custom_dir) if save_mode == "custom_dir" else Path(items[0][1]).parent
        merge_file_path = str(merge_base / "_merged_bundle.md") if merge_all else ""

        self.batch_results_cache.clear()
        self.progress.setRange(0, total)
        self.progress.setValue(0)

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self.batch_worker = BatchConversionWorker(
            items=items,
            config=self.config.get_engine_options(),
            save_mode=save_mode,
            custom_dir=custom_dir,
            collision_mode=collision_mode,
            merge_all=merge_all,
            merge_file_path=merge_file_path,
        )
        self.batch_worker.item_started.connect(self._on_item_started)
        self.batch_worker.item_finished.connect(self._on_item_finished)
        self.batch_worker.item_error.connect(self._on_item_error)
        self.batch_worker.batch_finished.connect(self._on_batch_finished)
        self.batch_worker.start()

    def stop_conversion(self) -> None:
        if self.batch_worker and self.batch_worker.isRunning():
            self.batch_worker.request_stop()
            self.lbl_status.setText("Остановка после завершения текущего файла…")
            self.btn_stop.setEnabled(False)

    def _on_item_started(self, row: int) -> None:
        self.table.item(row, 0).setText("В работе…")
        self.table.scrollToItem(self.table.item(row, 0))
        self.lbl_status.setText(
            f"Обработка ({row + 1}/{self.table.rowCount()}): {self.table.item(row, 1).text()}"
        )

    def _on_item_finished(self, row: int, saved_path: str, md_text: str, elapsed: float) -> None:
        self.table.item(row, 0).setText(f"✓ {elapsed:.1f}с")
        out_item = self.table.item(row, 4)
        out_item.setText(saved_path)
        out_item.setToolTip(saved_path)
        if md_text:
            self.batch_results_cache[row] = md_text
        self.progress.setValue(self.progress.value() + 1)

    def _on_item_error(self, row: int, error_msg: str) -> None:
        self.table.item(row, 0).setText("Ошибка")
        out_item = self.table.item(row, 4)
        out_item.setText(error_msg)
        out_item.setToolTip(error_msg)
        self.progress.setValue(self.progress.value() + 1)

    def _on_batch_finished(self, ok_count: int, err_count: int, merged_path: str) -> None:
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

        msg = f"✓ Завершено. Успешно: {ok_count}, Ошибок: {err_count}"
        if merged_path:
            msg += f"  |  Общий файл: {Path(merged_path).name}"
        self.lbl_status.setText(msg)

    def _on_row_double_clicked(self, row: int, _col: int) -> None:
        md_text = self.batch_results_cache.get(row)
        saved_path = self.table.item(row, 4).text()

        if not md_text and saved_path and Path(saved_path).is_file():
            try:
                md_text = Path(saved_path).read_text(encoding="utf-8")
            except Exception:
                pass

        if md_text:
            src_full = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
            ext = self.table.item(row, 2).text()
            self.open_in_editor_requested.emit(src_full, ext, saved_path, md_text)

    def open_output_folder(self) -> None:
        target_dir = self.input_out_dir.text().strip()
        if not target_dir or not Path(target_dir).exists():
            target_dir = str(Path.home())
        if sys.platform.startswith("win"):
            os.startfile(target_dir)
        elif sys.platform == "darwin":
            os.system(f'open "{target_dir}"')
        else:
            os.system(f'xdg-open "{target_dir}"')