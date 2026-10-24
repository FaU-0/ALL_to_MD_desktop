from pathlib import Path
from PyQt6.QtCore import QSettings

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


class AppConfig:
    """Типизированная обертка над QSettings для хранения настроек ALL_to_MD_desktop."""

    def __init__(self):
        self._settings = QSettings("ALL_to_MD_desktop", "DesktopConfigV2")

    @property
    def theme(self) -> str:
        return self._settings.value("theme", "Slate Dark", type=str)

    @theme.setter
    def theme(self, value: str) -> None:
        self._settings.setValue("theme", value)

    @property
    def editor_font_size(self) -> int:
        return self._settings.value("editor_font_size", 11, type=int)

    @editor_font_size.setter
    def editor_font_size(self, value: int) -> None:
        self._settings.setValue("editor_font_size", max(9, min(22, int(value))))

    @property
    def auto_convert(self) -> bool:
        return self._settings.value("auto_convert", True, type=bool)

    @auto_convert.setter
    def auto_convert(self, value: bool) -> None:
        self._settings.setValue("auto_convert", bool(value))

    @property
    def last_input_dir(self) -> str:
        return self._settings.value("last_input_dir", str(Path.home()), type=str)

    @last_input_dir.setter
    def last_input_dir(self, value: str) -> None:
        self._settings.setValue("last_input_dir", value)

    @property
    def last_save_dir(self) -> str:
        return self._settings.value("last_save_dir", str(Path.home()), type=str)

    @last_save_dir.setter
    def last_save_dir(self, value: str) -> None:
        self._settings.setValue("last_save_dir", value)

    @property
    def last_batch_out_dir(self) -> str:
        default_dir = str(Path.home() / "Documents")
        return self._settings.value("last_batch_out_dir", default_dir, type=str)

    @last_batch_out_dir.setter
    def last_batch_out_dir(self, value: str) -> None:
        self._settings.setValue("last_batch_out_dir", value)

    def get_engine_options(self) -> dict:
        return {
            "enable_plugins": self._settings.value("enable_plugins", False, type=bool),
            "use_llm": self._settings.value("use_llm", False, type=bool),
            "llm_api_key": self._settings.value("llm_api_key", "", type=str),
            "llm_base_url": self._settings.value("llm_base_url", "", type=str),
            "llm_model": self._settings.value("llm_model", "gpt-4o-mini", type=str),
            "docintel_endpoint": self._settings.value("docintel_endpoint", "", type=str),
        }

    def save_engine_options(self, options: dict) -> None:
        for key, val in options.items():
            self._settings.setValue(key, val)