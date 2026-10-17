"""Các thành phần giao diện dùng chung cho hai công cụ."""

from decimal import Decimal

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget,
)

from ..calculations import DEFAULT_VAT_RATE
from ..money import (
    InputError, copy_text, format_money, format_percent, live_format, parse_money,
    parse_percent,
)

EMPTY = "—"


def repolish(widget: QWidget) -> None:
    """Áp dụng lại stylesheet sau khi đổi dynamic property."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def set_style_flag(widget: QWidget, name: str, value: bool) -> None:
    """Đặt dynamic property dùng trong stylesheet, ví dụ [compact="true"]."""
    if bool(widget.property(name)) != value:
        widget.setProperty(name, value)
        repolish(widget)


class Card(QFrame):
    """Khung nền trắng bo góc chứa một nhóm nội dung."""

    def __init__(self, title: str = "", main: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("mainCard" if main else "card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(16, 12, 16, 14)
        self.body.setSpacing(8)
        self.title_label = None
        if title:
            self.title_label = QLabel(title)
            self.title_label.setObjectName("mainTitle" if main else "cardTitle")
            self.body.addWidget(self.title_label)

    def set_compact(self, compact: bool) -> None:
        if compact:
            self.body.setContentsMargins(8, 6, 8, 8)
            self.body.setSpacing(5)
        else:
            self.body.setContentsMargins(16, 12, 16, 14)
            self.body.setSpacing(8)


class MoneyLabel(QLabel):
    """Nhãn hiển thị số tiền. Nhấp đúp để sao chép số (chỉ chữ số, giữ dấu trừ)."""

    copied = Signal(str)

    def __init__(self, prefix: str = "", show_plus: bool = False, object_name: str = "money",
                 parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self._prefix = prefix
        self._show_plus = show_plus
        self._value: Decimal | None = None
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setToolTip("Nhấp đúp để sao chép số")
        self.clear_value()

    @property
    def value(self) -> Decimal | None:
        return self._value

    def set_value(self, value: Decimal | None) -> None:
        self._value = value
        shown = EMPTY if value is None else format_money(value, self._show_plus)
        self.setText(self._prefix + shown)
        self.setCursor(Qt.PointingHandCursor if value is not None else Qt.ArrowCursor)
        if self.property("empty") != (value is None):
            self.setProperty("empty", value is None)
            repolish(self)

    def clear_value(self) -> None:
        self.set_value(None)

    def copy_value(self) -> str | None:
        if self._value is None:
            return None
        text = copy_text(self._value)
        QApplication.clipboard().setText(text)
        self.copied.emit(text)
        return text

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.copy_value()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class MessageLabel(QLabel):
    """Dòng thông báo trạng thái: chờ nhập, cảnh báo, thành công."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("message")
        self.setWordWrap(True)
        self.show_message("", "waiting")

    def show_message(self, text: str, kind: str = "waiting") -> None:
        self.setText(text)
        self.setVisible(bool(text))
        if self.property("kind") != kind:
            self.setProperty("kind", kind)
            repolish(self)


class MoneyInput(QLineEdit):
    """Ô nhập tiền. Tự thêm dấu chấm hàng nghìn ngay khi gõ, con trỏ giữ đúng vị trí."""

    def __init__(self, placeholder: str = "0", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setMaxLength(30)
        self.setClearButtonEnabled(False)
        self._last_text = ""
        self.textChanged.connect(self._remember_text)
        self.textEdited.connect(self._format_while_typing)

    def _remember_text(self, _text: str) -> None:
        # Qt phát textEdited trước textChanged, nên khi định dạng, _last_text vẫn là nội dung
        # trước lần gõ này: dùng để biết ô đã có dấu phẩy thập phân hay chưa.
        self._last_text = self.text()

    def _format_while_typing(self, text: str) -> None:
        new_text, new_cursor = live_format(text, self.cursorPosition(),
                                           decimal_comma="," in self._last_text)
        if new_text != text:
            self.setText(new_text)
        self.setCursorPosition(new_cursor)

    def keyPressEvent(self, event):
        # Xóa qua dấu chấm hàng nghìn thì xóa luôn chữ số bên cạnh (dấu chấm tự sinh lại).
        if not self.hasSelectedText():
            pos = self.cursorPosition()
            text = self.text()
            if event.key() == Qt.Key_Backspace and pos > 0 and text[pos - 1] == ".":
                self.setCursorPosition(pos - 1)
            elif event.key() == Qt.Key_Delete and pos < len(text) and text[pos] == ".":
                self.setCursorPosition(pos + 1)
        super().keyPressEvent(event)

    def value(self) -> Decimal | None:
        """Giá trị hiện tại; None nếu trống; ném InputError nếu không hợp lệ."""
        return parse_money(self.text())

    def set_invalid(self, invalid: bool) -> None:
        if bool(self.property("invalid")) != invalid:
            self.setProperty("invalid", invalid)
            repolish(self)



class RateSelector(QWidget):
    """Ô nhập thuế suất (%), mặc định 8%."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.edit = QLineEdit()
        self.edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.edit.setMaxLength(8)
        self.edit.setToolTip("Ví dụ: 8 hoặc 8,5")
        layout.addWidget(self.edit, 1)
        layout.addWidget(QLabel("%"))
        self.edit.textChanged.connect(lambda _text: self.changed.emit())
        self.set_rate(DEFAULT_VAT_RATE)

    def set_rate(self, rate: Decimal) -> None:
        self.edit.setText(format_percent(rate))

    def value(self) -> Decimal | None:
        return parse_percent(self.edit.text())

    def set_invalid(self, invalid: bool) -> None:
        if bool(self.edit.property("invalid")) != invalid:
            self.edit.setProperty("invalid", invalid)
            repolish(self.edit)


class Toast(QLabel):
    """Thông báo nhỏ tự biến mất, ví dụ '✓ Đã sao chép'."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_text(self, text: str, msec: int = 1000) -> None:
        self.setText(text)
        self.adjustSize()
        parent = self.parentWidget()
        x = (parent.width() - self.width()) // 2
        y = parent.height() - self.height() - 16
        self.move(max(0, x), max(0, y))
        self.raise_()
        self.show()
        self._timer.start(msec)
