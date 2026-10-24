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
    """Генерирует QSS-таблицу стилей для выбранной темы."""
    t = THEMES.get(theme_name, THEMES["Slate Dark"])
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