import time
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal

from all_to_md_desktop.core.converter import create_markitdown_instance


class SingleConversionWorker(QThread):
    """Фоновый поток для конвертации одного файла или URL."""

    finished = pyqtSignal(str, str, float)  # markdown_text, title, elapsed_sec
    error = pyqtSignal(str)

    def __init__(self, source: str, config: dict):
        super().__init__()
        self.source = source
        self.config = config

    def run(self) -> None:
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
    """Фоновый поток для пакетной конвертации списка файлов."""

    item_started = pyqtSignal(int)
    item_finished = pyqtSignal(int, str, str, float)  # row, saved_path, md_text, elapsed
    item_error = pyqtSignal(int, str)                 # row, error_msg
    batch_finished = pyqtSignal(int, int, str)        # ok_count, err_count, merged_file_path

    def __init__(
        self,
        items: list[tuple[int, str]],
        config: dict,
        save_mode: str,
        custom_dir: str,
        collision_mode: str,
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

    def request_stop(self) -> None:
        self._stop_requested = True

    def _resolve_output_path(self, src_path: Path) -> Optional[Path]:
        base_dir = src_path.parent if self.save_mode == "alongside" else Path(self.custom_dir)
        base_dir.mkdir(parents=True, exist_ok=True)
        candidate = base_dir / f"{src_path.stem}.md"

        if self.collision_mode == "overwrite" or not candidate.exists():
            return candidate
        if self.collision_mode == "skip" and candidate.exists():
            return None

        counter = 1
        while True:
            numbered = base_dir / f"{src_path.stem} ({counter}).md"
            if not numbered.exists():
                return numbered
            counter += 1

    def run(self) -> None:
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