"""Công cụ 2: TÍNH GIÁ TRƯỚC VAT."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from ..calculations import DEFAULT_VAT_RATE, pre_vat_price
from ..money import InputError
from .tool_page import Field, ToolPage
from .widgets import Card, MessageLabel, MoneyInput, MoneyLabel, RateSelector, set_style_flag

WAITING_TEXT = "Nhập giá đã bao gồm VAT để xem kết quả."


class PreVatPage(ToolPage):
    title = "TÍNH GIÁ TRƯỚC VAT"
    mini_width = 320

    def __init__(self, parent=None):
        super().__init__(parent)

        self.input_card = Card("THÔNG TIN ĐẦU VÀO")
        self.price_input = MoneyInput("Ví dụ: 108.000")
        self.rate_selector = RateSelector()
        self.fields = [
            Field("Giá đã bao gồm VAT (VNĐ)", self.price_input, short="Giá có VAT"),
            Field("Thuế suất VAT (%)", self.rate_selector, short="Thuế suất"),
        ]
        for field in self.fields:
            self.input_card.body.addWidget(field)

        self.main_card = Card("GIÁ TRƯỚC VAT", main=True)
        self.main_value = self.register_money_label(MoneyLabel(object_name="mainValue"))
        self.vat_label = self.register_money_label(MoneyLabel(prefix="Tiền VAT: "))
        self.message = MessageLabel()
        self.note = QLabel("Giá trước VAT được làm tròn lên đến đồng. "
                           "Tiền VAT = Giá sau VAT − Giá trước VAT.")
        self.note.setObjectName("hint")
        self.note.setWordWrap(True)
        self.copy_hint = QLabel("Nhấp đúp vào số tiền để sao chép")
        self.copy_hint.setObjectName("hint")
        for w in (self.main_value, self.vat_label, self.message, self.note, self.copy_hint):
            self.main_card.body.addWidget(w)

        self.columns.addWidget(self.input_card, 1, Qt.AlignTop)
        self.columns.addWidget(self.main_card, 1, Qt.AlignTop)

        self.price_input.textChanged.connect(self.recalculate)
        self.rate_selector.changed.connect(self.recalculate)

        self._apply_compact(False)
        self.recalculate()

    def reset(self) -> None:
        self.price_input.clear()  # không chặn tín hiệu, xem BalancePage.reset
        self.rate_selector.set_rate(DEFAULT_VAT_RATE)
        self.recalculate()
        self.focus_first()

    def focus_first(self) -> None:
        self.price_input.setFocus(Qt.OtherFocusReason)

    def _apply_compact(self, compact: bool) -> None:
        for field in self.fields:
            field.set_compact(compact)
        for card in (self.input_card, self.main_card):
            card.set_compact(compact)
        self.input_card.title_label.setVisible(not compact)
        self.note.setVisible(not compact)
        self.copy_hint.setVisible(not compact)
        set_style_flag(self.main_value, "compact", compact)

    def _clear_results(self) -> None:
        self.main_value.clear_value()
        self.vat_label.clear_value()
        self.vat_label.hide()

    def recalculate(self) -> None:
        try:
            self._recalculate()
        except Exception:  # Không để ứng dụng đóng đột ngột vì dữ liệu bất thường
            self._clear_results()
            self.message.show_message("Không tính được với dữ liệu này. Vui lòng kiểm tra lại.",
                                      "warning")

    def _recalculate(self) -> None:
        self._clear_results()
        errors = []
        values = {}
        for key, name, widget in (("price", "Giá đã bao gồm VAT", self.price_input),
                                  ("rate", "Thuế suất VAT", self.rate_selector)):
            try:
                values[key] = widget.value()
                widget.set_invalid(False)
            except InputError as exc:
                widget.set_invalid(True)
                errors.append(f"{name}: {exc}")

        if errors:
            self.message.show_message("⚠ " + errors[0], "warning")
            return
        if values["price"] is None or values["rate"] is None:
            self.message.show_message(WAITING_TEXT if values["price"] is None
                                      else "Nhập thuế suất VAT.", "waiting")
            return

        try:
            result = pre_vat_price(values["price"], values["rate"])
        except InputError as exc:
            widget = self.price_input if exc.field == "price" else self.rate_selector
            widget.set_invalid(True)
            self.message.show_message("⚠ " + str(exc), "warning")
            return

        self.message.show_message("")
        self.main_value.set_value(result.pre_vat_price)
        self.vat_label.set_value(result.vat)
        self.vat_label.show()
