from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class DropZoneFrame(QFrame):
    """Интерактивная зона Drag-and-Drop с поддержкой одиночных и групповых сбросов."""

    paths_dropped = pyqtSignal(list)
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

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
            self.setProperty("dragActive", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event) -> None:
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent) -> None:
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