"""Công cụ 1: CÂN HÓA ĐƠN VAT."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..calculations import DEFAULT_VAT_RATE, STATUS_NEGATIVE, balance_invoice
from ..money import InputError
from .tool_page import Field, ToolPage
from .widgets import Card, MessageLabel, MoneyInput, MoneyLabel, RateSelector, set_style_flag

WAITING_TEXT = "Nhập đủ 4 thông tin để xem kết quả."


class BalancePage(ToolPage):
    title = "CÂN HÓA ĐƠN VAT"
    mini_width = 340

    def __init__(self, parent=None):
        super().__init__(parent)
        self._details_open_in_mini = False

        # ----- Cột trái: thông tin đầu vào -----
        self.input_card = Card("THÔNG TIN ĐẦU VÀO")
        self.paid_input = MoneyInput("Ví dụ: 1.000.000")
        self.invoice_input = MoneyInput("Ví dụ: 998.000")
        self.item_input = MoneyInput("Ví dụ: 125.000")
        self.rate_selector = RateSelector()
        self.fields = [
            Field("Tổng tiền khách chuyển (VNĐ)", self.paid_input, short="Khách chuyển"),
            Field("Tổng tiền hóa đơn hiện tại (VNĐ)", self.invoice_input, short="Tổng hóa đơn"),
            Field("Giá mặt hàng cần sửa (chưa VAT)", self.item_input, short="Giá cần sửa"),
            Field("Thuế suất VAT (%)", self.rate_selector, short="Thuế suất"),
        ]
        for field in self.fields:
            self.input_card.body.addWidget(field)
        self.input_hint = QLabel("Có thể nhập 1000000, 1.000.000 hoặc 1,000,000.")
        self.input_hint.setObjectName("hint")
        self.input_hint.setWordWrap(True)
        self.input_card.body.addWidget(self.input_hint)

        # ----- Cột phải: Khu vực A – kết quả chính -----
        self.main_card = Card("GIÁ MẶT HÀNG MỚI (CHƯA VAT)", main=True)
        self.main_value = self.register_money_label(MoneyLabel(object_name="mainValue"))
        self.message = MessageLabel()
        self.copy_hint = QLabel("Nhấp đúp vào số tiền để sao chép")
        self.copy_hint.setObjectName("hint")
        for w in (self.main_value, self.message, self.copy_hint):
            self.main_card.body.addWidget(w)

        # ----- Khu vực B – kiểm tra lại -----
        self.check_card = Card("KIỂM TRA LẠI")
        self.details_toggle = QPushButton()
        self.details_toggle.setObjectName("linkButton")
        self.details_toggle.setCursor(Qt.PointingHandCursor)
        self.details_toggle.clicked.connect(self._toggle_details)
        self.check_card.body.addWidget(self.details_toggle)

        self.details = QWidget()
        grid = QGridLayout(self.details)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        self.new_price_label = MoneyLabel()
        self.new_vat_label = MoneyLabel()
        self.new_total_label = MoneyLabel()
        self.expected_label = MoneyLabel()
        self.remaining_label = MoneyLabel(show_plus=True)
        rows = [
            ("Giá mới chưa VAT", "Giá chưa VAT", self.new_price_label),
            ("Thuế VAT mới", "VAT", self.new_vat_label),
            ("Giá mới sau VAT", "Giá sau VAT", self.new_total_label),
            ("Tổng hóa đơn mới dự kiến", "Tổng dự kiến", self.expected_label),
            ("Sai lệch còn lại so với tiền khách chuyển", "Sai lệch", self.remaining_label),
        ]
        self._detail_names = []  # (nhãn, chữ đầy đủ, chữ ngắn khi mini)
        for row, (text, short, label) in enumerate(rows):
            name = QLabel(text)
            name.setWordWrap(True)
            self._detail_names.append((name, text, short))
            grid.addWidget(name, row, 0)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(self.register_money_label(label), row, 1)
        grid.setColumnStretch(0, 1)
        self.check_card.body.addWidget(self.details)

        self.leftover_label = self.register_money_label(
            MoneyLabel(prefix="Chênh lệch còn lại: ", show_plus=True))
        self.leftover_label.setObjectName("leftover")
        self.check_note = QLabel("Phép kiểm tra dự kiến theo cách làm tròn của ứng dụng; "
                                 "phần mềm hóa đơn có thể làm tròn khác.")
        self.check_note.setObjectName("hint")
        self.check_note.setWordWrap(True)
        for w in (self.leftover_label, self.check_note):
            self.check_card.body.addWidget(w)

        right = QVBoxLayout()
        right.setSpacing(12)
        right.addWidget(self.main_card)
        right.addWidget(self.check_card)
        self._right = right

        self.columns.addWidget(self.input_card, 1, Qt.AlignTop)
        self.columns.addLayout(right, 1)

        # Tự tính lại ngay khi đổi dữ liệu (không cần nút Tính, không cần Enter)
        for edit in (self.paid_input, self.invoice_input, self.item_input):
            edit.textChanged.connect(self.recalculate)
        self.rate_selector.changed.connect(self.recalculate)

        self._apply_compact(False)
        self.recalculate()

    # ------------------------------------------------------------------
    def reset(self) -> None:
        for edit in (self.paid_input, self.invoice_input, self.item_input):
            edit.blockSignals(True)
            edit.clear()
            edit.blockSignals(False)
        self.rate_selector.set_rate(DEFAULT_VAT_RATE)
        self.recalculate()
        self.focus_first()

    def focus_first(self) -> None:
        self.paid_input.setFocus(Qt.OtherFocusReason)

    def _apply_compact(self, compact: bool) -> None:
        for field in self.fields:
            field.set_compact(compact)
        for card in (self.input_card, self.main_card, self.check_card):
            card.set_compact(compact)
        self.input_card.title_label.setVisible(not compact)
        self.input_hint.setVisible(not compact)
        self.check_card.title_label.setVisible(not compact)
        self.check_note.setVisible(not compact)
        self.copy_hint.setVisible(not compact)
        self.details_toggle.setVisible(compact)
        for name, full, short in self._detail_names:
            name.setText(short if compact else full)
        set_style_flag(self.main_value, "compact", compact)
        self._right.setSpacing(8 if compact else 12)
        self._update_details_visibility()

    def _toggle_details(self) -> None:
        self._details_open_in_mini = not self._details_open_in_mini
        self._update_details_visibility()
        window = self.window()
        if hasattr(window, "fit_mini_height"):
            window.fit_mini_height()

    def _update_details_visibility(self) -> None:
        open_ = not self.is_compact() or self._details_open_in_mini
        self.details.setVisible(open_)
        self.details_toggle.setText(("▾ Ẩn chi tiết kiểm tra" if open_
                                     else "▸ Xem chi tiết kiểm tra"))

    # ------------------------------------------------------------------
    def _clear_results(self) -> None:
        for label in (self.main_value, self.new_price_label,
                      self.new_vat_label, self.new_total_label, self.expected_label,
                      self.remaining_label, self.leftover_label):
            label.clear_value()
        self.leftover_label.hide()

    def recalculate(self) -> None:
        try:
            self._recalculate()
        except Exception:  # Không để ứng dụng đóng đột ngột vì dữ liệu bất thường
            self._clear_results()
            self.message.show_message("Không tính được với dữ liệu này. Vui lòng kiểm tra lại.",
                                      "warning")

    def _recalculate(self) -> None:
        inputs = {
            "paid": ("Tổng tiền khách chuyển", self.paid_input),
            "invoice_total": ("Tổng tiền hóa đơn hiện tại", self.invoice_input),
            "item_price": ("Giá mặt hàng cần sửa", self.item_input),
            "rate": ("Thuế suất VAT", self.rate_selector),
        }
        values = {}
        first_error = None
        missing = False
        for key, (name, widget) in inputs.items():
            try:
                value = widget.value()
                widget.set_invalid(False)
            except InputError as exc:
                widget.set_invalid(True)
                first_error = first_error or f"{name}: {exc}"
                continue
            if value is None:
                missing = True
            values[key] = value

        self._clear_results()
        if first_error:
            self.message.show_message("⚠ " + first_error, "warning")
            return
        if missing:
            self.message.show_message(WAITING_TEXT, "waiting")
            return

        try:
            result = balance_invoice(values["paid"], values["invoice_total"],
                                     values["item_price"], values["rate"])
        except InputError as exc:
            if exc.field in inputs:
                inputs[exc.field][1].set_invalid(True)
            self.message.show_message("⚠ " + str(exc), "warning")
            return

        if result.status == STATUS_NEGATIVE:
            self.message.show_message(
                "⚠ Không thể điều chỉnh: giá mới của mặt hàng này sẽ nhỏ hơn 0. "
                "Hãy chọn mặt hàng có giá cao hơn để điều chỉnh.", "warning")
            return

        self.message.show_message("")
        self.main_value.set_value(result.new_price)

        self.new_price_label.set_value(result.new_price)
        self.new_vat_label.set_value(result.new_vat)
        self.new_total_label.set_value(result.new_total)
        self.expected_label.set_value(result.expected_invoice_total)
        self.remaining_label.set_value(result.remaining)
        if result.remaining != 0:
            self.leftover_label.set_value(result.remaining)
            self.leftover_label.show()
