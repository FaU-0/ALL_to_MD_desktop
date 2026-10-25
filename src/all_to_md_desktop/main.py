import ctypes
import sys

from PyQt6.QtWidgets import QApplication

from all_to_md_desktop.ui.main_window import MainWindow, create_app_icon


def main() -> None:
    # На Windows регистрируем AppUserModelID, чтобы панель задач показывала нашу иконку
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "all_to_md.desktop.app.v0_3"
            )
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setWindowIcon(create_app_icon())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()