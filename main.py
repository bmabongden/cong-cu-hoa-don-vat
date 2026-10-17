"""Khởi chạy Công cụ hóa đơn VAT:  python main.py"""

import sys
import traceback
from pathlib import Path

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from vat_app import APP_NAME, APP_VERSION
from vat_app.ui.main_window import MainWindow
from vat_app.ui.styles import FONT_FAMILY, STYLESHEET


def _log_unexpected_error(exc_type, exc, tb):
    # Ghi lỗi ra màn hình dòng lệnh thay vì để ứng dụng đóng đột ngột.
    traceback.print_exception(exc_type, exc, tb)


def _resource(relative: str) -> str:
    """Đường dẫn tới file đi kèm, dùng được cả khi chạy mã nguồn lẫn khi đóng gói EXE."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base / relative)


def main() -> int:
    sys.excepthook = _log_unexpected_error
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setFont(QFont(FONT_FAMILY, 10))
    app.setStyleSheet(STYLESHEET)
    app.setWindowIcon(QIcon(_resource("assets/app.ico")))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
