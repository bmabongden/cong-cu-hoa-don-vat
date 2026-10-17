"""Cửa sổ chính duy nhất: thanh điều khiển + màn hình lựa chọn / một công cụ tại một thời điểm."""

from PySide6.QtCore import QEvent, QRect, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QScrollArea, QSizePolicy,
    QStackedWidget, QVBoxLayout, QWidget,
)

from .. import APP_NAME
from .balance_page import BalancePage
from .home_page import HomePage
from .prevat_page import PreVatPage
from .widgets import Toast

NORMAL_SIZE = (900, 560)
NORMAL_MIN_SIZE = (480, 360)
MINI_MIN_SIZE = (300, 200)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self._mini = False
        self._normal_geometry: QRect | None = None
        self._was_maximized = False

        central = QWidget()
        central.setObjectName("central")
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setCentralWidget(central)

        # ----- Thanh điều khiển -----
        header = QWidget()
        header.setObjectName("header")
        bar = QHBoxLayout(header)
        bar.setContentsMargins(10, 6, 10, 6)
        self._bar = bar
        bar.setSpacing(6)
        self.back_button = self._header_button("← Quay lại", "Quay lại màn hình chọn công cụ")
        self.title_label = QLabel()
        self.title_label.setObjectName("headerTitle")
        self.title_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.refresh_button = self._header_button("↻ Làm mới", "Xóa dữ liệu của công cụ hiện tại")
        self.pin_button = self._header_button("📌 Ghim", "Bật/tắt luôn nổi trên các cửa sổ khác")
        self.pin_button.setCheckable(True)
        self.mini_button = self._header_button("Mini", "Chuyển sang cửa sổ nhỏ gọn")
        bar.addWidget(self.back_button)
        bar.addWidget(self.title_label, 1)
        bar.addStretch(0)
        bar.addWidget(self.refresh_button)
        bar.addWidget(self.pin_button)
        bar.addWidget(self.mini_button)
        root.addWidget(header)
        self.header = header

        # ----- Nội dung: mỗi lúc chỉ hiển thị một trang -----
        self.stack = QStackedWidget()
        self.home_page = HomePage()
        self.balance_page = BalancePage()
        self.prevat_page = PreVatPage()
        self.pages = [self.home_page, self.balance_page, self.prevat_page]
        for page in self.pages:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.NoFrame)
            # Chỉ hiện thanh cuộn ngang nếu người dùng kéo cửa sổ hẹp hơn mức nội dung cần,
            # thay vì cắt mất nội dung.
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setWidget(page)
            scroll.viewport().installEventFilter(self)
            self.stack.addWidget(scroll)
        root.addWidget(self.stack, 1)

        self.toast = Toast(central)

        # ----- Kết nối -----
        self.home_page.chosen.connect(lambda i: self.show_page(i + 1))
        self.back_button.clicked.connect(lambda: self.show_page(0))
        self.refresh_button.clicked.connect(self.refresh_current)
        self.pin_button.toggled.connect(self.set_pinned)
        self.mini_button.clicked.connect(self.toggle_mini)
        for page in (self.balance_page, self.prevat_page):
            page.copied.connect(lambda _text: self.toast.show_text("✓ Đã sao chép"))

        self.setMinimumSize(*NORMAL_MIN_SIZE)
        self.resize(*NORMAL_SIZE)
        self.show_page(0)

    def _header_button(self, text: str, tooltip: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("headerButton")
        button.setToolTip(tooltip)
        button.setCursor(Qt.PointingHandCursor)
        button.setFocusPolicy(Qt.NoFocus)  # không lấy mất con trỏ khỏi ô đang nhập
        return button

    # ------------------------------------------------------------------
    def current_page(self):
        return self.pages[self.stack.currentIndex()]

    def show_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        is_tool = index != 0
        self.back_button.setVisible(is_tool)
        self.refresh_button.setVisible(is_tool)
        self._update_header_texts()
        if self._mini:
            self._resize_to_mini()
        self.current_page().focus_first()

    def refresh_current(self) -> None:
        page = self.current_page()
        if hasattr(page, "reset"):
            page.reset()

    # ----- Ghim cửa sổ -----
    def set_pinned(self, pinned: bool) -> None:
        if bool(self.windowFlags() & Qt.WindowStaysOnTopHint) == pinned:
            self._update_header_texts()
            return
        # Đổi cờ cửa sổ làm Qt tạo lại cửa sổ: lưu và khôi phục vị trí, kích thước, con trỏ.
        geometry = self.geometry()
        state = self.windowState()
        was_visible = self.isVisible()
        focus = QApplication.focusWidget()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, pinned)
        if was_visible:
            if state & (Qt.WindowMaximized | Qt.WindowFullScreen):
                self.setWindowState(state)
                self.show()
            else:
                self.setGeometry(geometry)
                self.show()
                self.setGeometry(geometry)
            self.raise_()
            self.activateWindow()
            if focus is not None and self.isAncestorOf(focus):
                focus.setFocus(Qt.OtherFocusReason)
        self._update_header_texts()

    # ----- Chế độ mini -----
    def toggle_mini(self) -> None:
        self.set_mini(not self._mini)

    def set_mini(self, mini: bool) -> None:
        if mini == self._mini:
            return
        if mini:
            self._was_maximized = self.isMaximized() or self.isFullScreen()
            if self._was_maximized:
                self.showNormal()
            self._normal_geometry = self.geometry()
        self._mini = mini
        for page in self.pages:
            page.set_compact(mini)
        self._update_header_texts()
        if mini:
            self.setMinimumSize(*MINI_MIN_SIZE)
            self._resize_to_mini()
        else:
            self.setMinimumSize(*NORMAL_MIN_SIZE)
            if self._normal_geometry is not None:
                self.setGeometry(self._normal_geometry)
            else:
                self.resize(*NORMAL_SIZE)
            if self._was_maximized:
                self.showMaximized()

    def is_mini(self) -> bool:
        return self._mini

    def _mini_size(self):
        page = self.current_page()
        hint = page.mini_size_hint()
        self.header.layout().activate()
        height = self.header.sizeHint().height() + hint.height() + 4
        # Không hẹp hơn bề rộng tối thiểu nội dung cần (phông chữ Windows có thể rộng hơn),
        # cộng chỗ cho thanh cuộn dọc để không bao giờ phải cuộn ngang.
        scroll_bar = self.style().pixelMetric(self.style().PixelMetric.PM_ScrollBarExtent)
        needed = page.minimumSizeHint().width() + scroll_bar + 2
        width = max(hint.width(), needed, self.header.minimumSizeHint().width())
        screen = self.screen().availableGeometry() if self.screen() else None
        if screen is not None:
            height = min(height, screen.height() - 60)
        return width, height

    def _resize_to_mini(self) -> None:
        width, height = self._mini_size()
        self.setMinimumWidth(max(MINI_MIN_SIZE[0], width))
        self.resize(width, height)
        # Tính lại sau khi bố cục mini đã ổn định để cửa sổ ôm sát nội dung.
        QTimer.singleShot(0, self._refit_mini)

    def _refit_mini(self) -> None:
        if self._mini:
            width, height = self._mini_size()
            self.setMinimumWidth(max(MINI_MIN_SIZE[0], width))
            self.resize(width, height)

    def fit_mini_height(self) -> None:
        """Gọi khi mở/đóng phần chi tiết ở chế độ mini để cửa sổ vừa nội dung."""
        if self._mini:
            _, height = self._mini_size()
            self.resize(self.width(), height)

    def _update_header_texts(self) -> None:
        self._bar.setContentsMargins(*((6, 4, 6, 4) if self._mini else (10, 6, 10, 6)))
        self.title_label.setText(self.current_page().title)
        self.title_label.setVisible(not self._mini)  # mini: tên đã có trên thanh tiêu đề Windows
        self.header.layout().setStretch(2, 1 if self.title_label.isHidden() else 0)
        self.back_button.setText("←" if self._mini else "← Quay lại")
        self.refresh_button.setText("↻" if self._mini else "↻ Làm mới")
        self.mini_button.setText("Mở rộng" if self._mini else "Mini")
        self.mini_button.setToolTip("Trở lại kích thước bình thường" if self._mini
                                    else "Chuyển sang cửa sổ nhỏ gọn")
        self.pin_button.setText("📌 Đang ghim" if self.pin_button.isChecked() else "📌 Ghim")

    def eventFilter(self, watched, event):
        # Chọn bố cục ngang/dọc theo bề rộng vùng nhìn của khung cuộn.
        if event.type() == QEvent.Resize:
            for page in (self.balance_page, self.prevat_page):
                if page.parentWidget() is watched:
                    page.update_for_width(watched.width())
        return super().eventFilter(watched, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.toast.isVisible():
            self.toast.show_text(self.toast.text())
