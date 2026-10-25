THEMES = {
    "Carbon Dark": {
        "bg_main": "#141416",
        "bg_card": "#1c1c1f",
        "bg_input": "#111113",
        "bg_hover": "#27272b",
        "border": "#2c2c31",
        "border_subtle": "#3f3f46",
        "text_main": "#f4f4f5",
        "text_secondary": "#d4d4d8",
        "text_muted": "#8e8e96",
        "accent": "#3b82f6",
        "accent_hover": "#2563eb",
        "accent_text": "#ffffff",
        "drop_active_bg": "#1e293b",
        "action_primary": "#e4e4e7",
        "action_primary_hover": "#ffffff",
        "action_primary_text": "#141416",
        "danger": "#b91c1c",
        "danger_hover": "#991b1b",
        "badge_bg": "#27272a",
        "badge_text": "#e4e4e7",
    },
    "Paper Light": {
        "bg_main": "#f4f3ef",
        "bg_card": "#ffffff",
        "bg_input": "#f9f8f6",
        "bg_hover": "#eae8e1",
        "border": "#d6d3cd",
        "border_subtle": "#b8b4ac",
        "text_main": "#18181b",
        "text_secondary": "#27272a",
        "text_muted": "#71717a",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "accent_text": "#ffffff",
        "drop_active_bg": "#eff6ff",
        "action_primary": "#18181b",
        "action_primary_hover": "#27272a",
        "action_primary_text": "#ffffff",
        "danger": "#dc2626",
        "danger_hover": "#b91c1c",
        "badge_bg": "#e4e2dd",
        "badge_text": "#18181b",
    },
    "Obsidian Mono": {
        "bg_main": "#0a0a0a",
        "bg_card": "#121212",
        "bg_input": "#080808",
        "bg_hover": "#1f1f1f",
        "border": "#262626",
        "border_subtle": "#383838",
        "text_main": "#fafafa",
        "text_secondary": "#d4d4d4",
        "text_muted": "#737373",
        "accent": "#d97706",
        "accent_hover": "#b45309",
        "accent_text": "#ffffff",
        "drop_active_bg": "#1c1917",
        "action_primary": "#f59e0b",
        "action_primary_hover": "#d97706",
        "action_primary_text": "#0a0a0a",
        "danger": "#991b1b",
        "danger_hover": "#7f1d1d",
        "badge_bg": "#1f1f1f",
        "badge_text": "#fbbf24",
    },
    "Nordic Slate": {
        "bg_main": "#242933",
        "bg_card": "#2e3440",
        "bg_input": "#1e222a",
        "bg_hover": "#3b4252",
        "border": "#3b4252",
        "border_subtle": "#4c566a",
        "text_main": "#eceff4",
        "text_secondary": "#e5e9f0",
        "text_muted": "#9aa5b8",
        "accent": "#5e81ac",
        "accent_hover": "#81a1c1",
        "accent_text": "#ffffff",
        "drop_active_bg": "#3b4252",
        "action_primary": "#88c0d0",
        "action_primary_hover": "#8fbcbb",
        "action_primary_text": "#242933",
        "danger": "#bf616a",
        "danger_hover": "#a54e56",
        "badge_bg": "#3b4252",
        "badge_text": "#88c0d0",
    },
}


def build_stylesheet(theme_name: str) -> str:
    """Генерирует QSS-таблицу стилей без смещения геометрии кнопок."""
    t = THEMES.get(theme_name, THEMES["Carbon Dark"])

    return f"""
    QMainWindow, QDialog {{
        background-color: {t['bg_main']};
        color: {t['text_main']};
    }}
    QWidget {{
        color: {t['text_secondary']};
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Inter', Roboto, sans-serif;
        font-size: 13px;
    }}
    QFrame#Card {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        border-radius: 6px;
    }}
    QFrame#DropZone {{
        background-color: {t['bg_input']};
        border: 1px dashed {t['border_subtle']};
        border-radius: 5px;
    }}
    QFrame#DropZone:hover {{
        border-color: {t['text_muted']};
        background-color: {t['bg_card']};
    }}
    QFrame#DropZone[dragActive="true"] {{
        border: 1px solid {t['accent']};
        background-color: {t['drop_active_bg']};
    }}
    QLineEdit, QComboBox, QSpinBox {{
        background-color: {t['bg_input']};
        border: 1px solid {t['border']};
        border-radius: 5px;
        padding: 6px 10px;
        min-height: 20px;
        color: {t['text_main']};
        selection-background-color: {t['accent']};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border: 1px solid {t['border_subtle']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border_subtle']};
        color: {t['text_main']};
        selection-background-color: {t['bg_hover']};
        selection-color: {t['text_main']};
        outline: 0;
    }}
    QPushButton {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border_subtle']};
        border-radius: 5px;
        padding: 6px 14px;
        min-height: 20px;
        color: {t['text_main']};
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {t['bg_hover']};
        border-color: {t['text_muted']};
    }}
    QPushButton:pressed {{
        background-color: {t['bg_input']};
    }}
    QPushButton:disabled {{
        background-color: {t['bg_main']};
        color: {t['text_muted']};
        border-color: {t['border']};
    }}
    QPushButton#ToolbarBtn {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        border-radius: 5px;
        padding: 6px 12px;
        min-height: 20px;
        font-weight: 600;
        color: {t['text_main']};
    }}
    QPushButton#ToolbarBtn:hover {{
        background-color: {t['bg_hover']};
        border-color: {t['border_subtle']};
    }}
    QPushButton#PrimaryBtn {{
        background-color: {t['action_primary']};
        border: 1px solid {t['action_primary']};
        color: {t['action_primary_text']};
        font-weight: 600;
    }}
    QPushButton#PrimaryBtn:hover {{
        background-color: {t['action_primary_hover']};
    }}
    QPushButton#PrimaryBtn:disabled {{
        background-color: {t['bg_hover']};
        border-color: {t['border']};
        color: {t['text_muted']};
    }}
    QPushButton#AccentBtn {{
        background-color: {t['accent']};
        border: 1px solid {t['accent']};
        color: {t['accent_text']};
        font-weight: 600;
    }}
    QPushButton#AccentBtn:hover {{
        background-color: {t['accent_hover']};
    }}
    QPushButton#AccentBtn:disabled {{
        background-color: {t['bg_hover']};
        border-color: {t['border']};
        color: {t['text_muted']};
    }}
    QPushButton#DangerBtn {{
        background-color: {t['danger']};
        border: 1px solid {t['danger']};
        color: #ffffff;
        font-weight: 600;
    }}
    QPushButton#DangerBtn:hover {{
        background-color: {t['danger_hover']};
    }}
    QPushButton#SegmentBtn, QPushButton#ModeTabBtn {{
        background-color: {t['bg_input']};
        border: 1px solid {t['border']};
        border-radius: 5px;
        padding: 6px 16px;
        min-height: 20px;
        font-weight: 600;
        color: {t['text_muted']};
    }}
    QPushButton#SegmentBtn:hover, QPushButton#ModeTabBtn:hover {{
        color: {t['text_main']};
        background-color: {t['bg_hover']};
    }}
    QPushButton#SegmentBtn:checked, QPushButton#ModeTabBtn:checked {{
        background-color: {t['bg_hover']};
        border: 1px solid {t['text_muted']};
        color: {t['text_main']};
        font-weight: 600;
    }}
    QPlainTextEdit, QTextBrowser {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        padding: 12px;
        color: {t['text_main']};
        selection-background-color: {t['accent']};
    }}
    QTableWidget {{
        background-color: {t['bg_card']};
        alternate-background-color: {t['bg_input']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        gridline-color: {t['border']};
        color: {t['text_main']};
        selection-background-color: {t['bg_hover']};
        selection-color: {t['text_main']};
    }}
    QHeaderView::section {{
        background-color: {t['bg_input']};
        color: {t['text_muted']};
        font-weight: 600;
        padding: 6px 10px;
        border: none;
        border-bottom: 1px solid {t['border']};
        border-right: 1px solid {t['border']};
    }}
    QProgressBar {{
        background-color: {t['bg_input']};
        border: 1px solid {t['border']};
        border-radius: 4px;
        text-align: center;
        color: {t['text_main']};
        font-weight: 600;
        min-height: 16px;
        max-height: 16px;
    }}
    QProgressBar::chunk {{
        background-color: {t['accent']};
        border-radius: 3px;
    }}
    QLabel#Badge {{
        background-color: {t['badge_bg']};
        color: {t['badge_text']};
        border: 1px solid {t['border_subtle']};
        border-radius: 4px;
        padding: 3px 8px;
        font-weight: 600;
        font-size: 11px;
    }}
    QLabel#PaneHeader {{
        background-color: {t['bg_input']};
        color: {t['text_muted']};
        border: 1px solid {t['border']};
        border-radius: 4px;
        padding: 5px 10px;
        font-weight: 600;
        font-size: 11px;
    }}
    QLabel#Muted {{
        color: {t['text_muted']};
        font-size: 12px;
    }}
    QSplitter::handle {{
        background-color: {t['border']};
        width: 3px;
    }}
    """