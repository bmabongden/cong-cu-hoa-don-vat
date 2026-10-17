"""Màn hình chọn công cụ."""

import threading

from PySide6.QtCore import QObject, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from .. import APP_VERSION
from .. import updater


class _UpdateSignals(QObject):
    finished = Signal(object)  # UpdateInfo hoặc UpdateError


class HomePage(QWidget):
    chosen = Signal(int)  # 0: cân hóa đơn, 1: tính giá trước VAT

    title = "CÔNG CỤ HÓA ĐƠN VAT"
    mini_width = 340

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        self.hint = QLabel("Chọn công cụ cần dùng")
        self.hint.setObjectName("homeHint")
        self.hint.setAlignment(Qt.AlignCenter)
        outer.addWidget(self.hint)

        self.choices = QBoxLayout(QBoxLayout.LeftToRight)
        self.choices.setSpacing(16)
        self.buttons = []
        for index, (name, desc) in enumerate([
            ("CÂN HÓA ĐƠN VAT", "Điều chỉnh giá một mặt hàng để tổng hóa đơn khớp tiền khách chuyển"),
            ("TÍNH GIÁ TRƯỚC VAT", "Tính giá chưa VAT từ giá đã bao gồm VAT"),
        ]):
            button = QPushButton()
            button.setObjectName("homeChoice")
            button.setCursor(Qt.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            inner = QVBoxLayout(button)
            inner.setContentsMargins(16, 16, 16, 16)
            inner.setSpacing(8)
            for text, object_name in ((name, "homeChoiceTitle"), (desc, "homeChoiceDesc")):
                label = QLabel(text)
                label.setObjectName(object_name)
                label.setAlignment(Qt.AlignCenter)
                label.setWordWrap(True)
                label.setAttribute(Qt.WA_TransparentForMouseEvents)
                inner.addWidget(label)
            button.setFixedHeight(120)
            button.clicked.connect(lambda _=False, i=index: self.chosen.emit(i))
            self.choices.addWidget(button)
            self.buttons.append(button)
        outer.addLayout(self.choices)

        # Dòng phiên bản + kiểm tra cập nhật (chỉ kết nối mạng khi người dùng bấm)
        update_row = QHBoxLayout()
        update_row.setSpacing(6)
        self.version_label = QLabel(f"Phiên bản {APP_VERSION}")
        self.version_label.setObjectName("hint")
        self.update_button = QPushButton("Kiểm tra cập nhật")
        self.update_button.setObjectName("linkButton")
        self.update_button.setCursor(Qt.PointingHandCursor)
        self.update_button.clicked.connect(self.check_update)
        update_row.addStretch(1)
        update_row.addWidget(self.version_label)
        update_row.addWidget(self.update_button)
        update_row.addStretch(1)
        outer.addLayout(update_row)
        self.update_message = QLabel()
        self.update_message.setObjectName("hint")
        self.update_message.setAlignment(Qt.AlignCenter)
        self.update_message.setWordWrap(True)
        self.update_message.setOpenExternalLinks(False)
        self.update_message.linkActivated.connect(lambda url: QDesktopServices.openUrl(QUrl(url)))
        self.update_message.hide()
        outer.addWidget(self.update_message)
        outer.addStretch(1)
        self._outer = outer

        self._update_signals = _UpdateSignals()
        self._update_signals.finished.connect(self._show_update_result)
        self._update_check = updater.check_for_update  # tách ra để kiểm thử

    def check_update(self) -> None:
        self.update_button.setEnabled(False)
        self.update_button.setText("Đang kiểm tra...")
        self.update_message.hide()

        def work():
            try:
                result = self._update_check()
            except updater.UpdateError as exc:
                result = exc
            except Exception:
                result = updater.UpdateError("Không kiểm tra được cập nhật.")
            self._update_signals.finished.emit(result)

        threading.Thread(target=work, daemon=True).start()

    def _show_update_result(self, result) -> None:
        self.update_button.setEnabled(True)
        self.update_button.setText("Kiểm tra cập nhật")
        if isinstance(result, updater.UpdateError):
            text = "⚠ " + str(result)
        elif result.has_update:
            text = (f"Có bản mới {result.latest}. "
                    f'<a href="{result.url}">Mở trang tải trên GitHub</a>')
        else:
            text = f"✓ Đang dùng bản mới nhất ({result.current})."
        self.update_message.setText(text)
        self.update_message.show()

    def set_compact(self, compact: bool) -> None:
        self.choices.setDirection(QBoxLayout.TopToBottom if compact else QBoxLayout.LeftToRight)
        margin = 10 if compact else 24
        self._outer.setContentsMargins(margin, margin, margin, margin)
        self._outer.setSpacing(10 if compact else 16)
        self.choices.setSpacing(10 if compact else 16)
        for button in self.buttons:
            button.setFixedHeight(100 if compact else 120)

    def mini_size_hint(self) -> QSize:
        self.layout().activate()
        return QSize(self.mini_width, self.sizeHint().height())

    def focus_first(self) -> None:
        self.buttons[0].setFocus(Qt.OtherFocusReason)
