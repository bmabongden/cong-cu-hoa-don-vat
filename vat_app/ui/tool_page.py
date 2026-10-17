"""Lớp nền cho hai công cụ: bố cục hai cột tự chuyển sang dạng dọc khi hẹp hoặc ở chế độ mini."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QBoxLayout, QLabel, QVBoxLayout, QWidget

from .widgets import MoneyLabel

# Bề rộng chuyển bố cục (có khoảng đệm để không bị chuyển qua lại liên tục khi thanh cuộn xuất hiện)
VERTICAL_BELOW = 640
HORIZONTAL_ABOVE = 680


class Field(QWidget):
    """Một dòng nhập: nhãn ở trên ô nhập (thường) hoặc bên trái (mini).

    short: nhãn ngắn dùng khi mini.
    wide=True: ô nhập rộng (thuế suất kèm nút chọn nhanh), giữ nhãn ở trên cả khi mini.
    """

    def __init__(self, label: str, editor: QWidget, short: str = "", wide: bool = False,
                 parent=None):
        super().__init__(parent)
        self._full_text = label
        self._short_text = short or label
        self._wide = wide
        self.label = QLabel(label)
        self.label.setObjectName("fieldLabel")
        self.label.setWordWrap(True)
        self.editor = editor
        self._layout = QBoxLayout(QBoxLayout.TopToBottom, self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._layout.addWidget(self.label)
        self._layout.addWidget(editor, 1)

    def set_compact(self, compact: bool) -> None:
        self.label.setText(self._short_text if compact else self._full_text)
        if compact and not self._wide:
            self._layout.setDirection(QBoxLayout.LeftToRight)
            self._layout.setSpacing(8)
            self.label.setFixedWidth(110)
        else:
            self._layout.setDirection(QBoxLayout.TopToBottom)
            self._layout.setSpacing(4)
            self.label.setMinimumWidth(0)
            self.label.setMaximumWidth(16777215)


class ToolPage(QWidget):
    copied = Signal(str)

    title = ""
    mini_width = 380

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page")
        self._compact = False
        self._vertical = False
        self._horizontal_min = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(0)
        self.columns = QBoxLayout(QBoxLayout.LeftToRight)
        self.columns.setSpacing(14)
        outer.addLayout(self.columns)
        outer.addStretch(1)
        self._outer = outer

    # --- Hàm các công cụ cần cài đặt ---
    def reset(self) -> None:
        raise NotImplementedError

    def focus_first(self) -> None:
        raise NotImplementedError

    def _apply_compact(self, compact: bool) -> None:
        """Điều chỉnh chi tiết riêng của từng công cụ khi bật/tắt mini."""

    # --- Dùng chung ---
    def register_money_label(self, label: MoneyLabel) -> MoneyLabel:
        label.copied.connect(self.copied)
        return label

    def is_compact(self) -> bool:
        return self._compact

    def set_compact(self, compact: bool) -> None:
        self._compact = compact
        if compact:
            self._outer.setContentsMargins(6, 6, 6, 6)
            self.columns.setSpacing(6)
        else:
            self._outer.setContentsMargins(16, 14, 16, 14)
            self.columns.setSpacing(14)
        self._apply_compact(compact)
        self.update_for_width(self.available_width())

    def _set_vertical(self, vertical: bool) -> None:
        if vertical != self._vertical:
            self._vertical = vertical
            self.columns.setDirection(QBoxLayout.TopToBottom if vertical else QBoxLayout.LeftToRight)

    def available_width(self) -> int:
        """Bề rộng thực có để hiển thị (vùng nhìn của khung cuộn chứa trang).

        Không dùng bề rộng của chính trang: khung cuộn không cho trang hẹp hơn
        bề rộng tối thiểu của bố cục ngang, nên trang sẽ không bao giờ tự chuyển sang dọc.
        """
        parent = self.parentWidget()
        return parent.width() if parent is not None else self.width()

    def update_for_width(self, width: int) -> None:
        if self._compact:
            self._set_vertical(True)
            return
        if not self._vertical:
            # Bề rộng tối thiểu của bố cục ngang phụ thuộc phông chữ (Windows rộng hơn).
            self._horizontal_min = self.minimumSizeHint().width()
        needed = max(VERTICAL_BELOW, self._horizontal_min)
        if width < needed:
            self._set_vertical(True)
        elif width > max(HORIZONTAL_ABOVE, needed + 40):
            self._set_vertical(False)

    def mini_size_hint(self) -> QSize:
        """Kích thước nội dung khi ở chế độ mini (bố cục dọc)."""
        self.layout().activate()
        width = max(self.mini_width, self.minimumSizeHint().width())
        height = self.sizeHint().height()
        if self.hasHeightForWidth():  # tính cả các dòng chữ tự xuống dòng
            height = max(height, self.heightForWidth(width))
        return QSize(width, height)
