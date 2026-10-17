"""Kiểm thử giao diện cơ bản (chạy được không cần màn hình với QT_QPA_PLATFORM=offscreen)."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    QApplication = None

if QApplication is not None:
    from vat_app.ui.main_window import MainWindow
    from vat_app.ui.styles import STYLESHEET


@unittest.skipIf(QApplication is None, "Chưa cài PySide6")
class TestMainWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(STYLESHEET)

    def setUp(self):
        self.window = MainWindow()
        self.window.show()
        QTest.qWaitForWindowExposed(self.window)

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()

    def open_balance(self):
        QTest.mouseClick(self.window.home_page.buttons[0], Qt.LeftButton)
        return self.window.balance_page

    def open_prevat(self):
        QTest.mouseClick(self.window.home_page.buttons[1], Qt.LeftButton)
        return self.window.prevat_page

    def test_home_then_tools_and_back(self):
        self.assertIs(self.window.current_page(), self.window.home_page)
        self.assertFalse(self.window.back_button.isVisible())
        page = self.open_balance()
        self.assertIs(self.window.current_page(), page)
        self.assertTrue(self.window.back_button.isVisible())
        QTest.mouseClick(self.window.back_button, Qt.LeftButton)
        self.assertIs(self.window.current_page(), self.window.home_page)
        self.assertIs(self.open_prevat(), self.window.current_page())

    def test_balance_required_example_by_typing(self):
        page = self.open_balance()
        self.assertEqual(page.main_value.text(), "—")
        self.assertIn("Nhập đủ", page.message.text())
        QTest.keyClicks(page.paid_input, "1.000.000")
        QTest.keyClicks(page.invoice_input, "998000")
        QTest.keyClicks(page.item_input, "125,000")
        self.assertEqual(page.main_value.text(), "126.852đ")
        self.assertEqual(page.new_price_label.text(), "126.852đ")
        self.assertEqual(page.new_vat_label.text(), "10.148đ")
        self.assertEqual(page.new_total_label.text(), "137.000đ")
        self.assertEqual(page.expected_label.text(), "1.000.000đ")
        self.assertEqual(page.remaining_label.text(), "0đ")
        self.assertTrue(page.leftover_label.isHidden())
        self.assertEqual(page.paid_input.text(), "1.000.000")
        self.assertEqual(page.invoice_input.text(), "998.000")  # dấu chấm hiện ngay khi gõ
        self.assertEqual(page.item_input.text(), "125,000")  # gõ dấu phẩy: giữ nguyên, vẫn hiểu là 125.000
        self.assertFalse(page.message.isVisible())

    def test_double_click_copies_digits_only(self):
        page = self.open_balance()
        page.paid_input.setText("1000000")
        page.invoice_input.setText("1002000")
        page.item_input.setText("125000")
        clipboard = QApplication.clipboard()
        QTest.mouseDClick(page.main_value, Qt.LeftButton)
        self.assertEqual(clipboard.text(), "123149")
        self.assertTrue(self.window.toast.isVisible())
        self.assertEqual(self.window.toast.text(), "✓ Đã sao chép")
        QTest.mouseDClick(page.expected_label, Qt.LeftButton)
        self.assertEqual(clipboard.text(), "1000001")
        self.assertEqual(page.leftover_label.text(), "Chênh lệch còn lại: +1đ")
        self.assertFalse(page.leftover_label.isHidden())
        QTest.mouseDClick(page.leftover_label, Qt.LeftButton)
        self.assertEqual(clipboard.text(), "1")
        QTest.qWait(1200)
        self.assertFalse(self.window.toast.isVisible())

    def test_prevat_example_and_copy(self):
        page = self.open_prevat()
        QTest.keyClicks(page.price_input, "108.000")
        self.assertEqual(page.main_value.text(), "100.000đ")
        self.assertEqual(page.vat_label.text(), "Tiền VAT: 8.000đ")
        QTest.mouseDClick(page.vat_label, Qt.LeftButton)
        self.assertEqual(QApplication.clipboard().text(), "8000")
        page.rate_selector.edit.setText("10")
        self.assertEqual(page.main_value.text(), "98.182đ")  # 98181,8 -> 98182

    def test_bad_inputs_never_crash(self):
        page = self.open_balance()
        bad_values = ["abc", "-5", "0", "1..0", "", "   ", "1e9", "NaN", "999999999999999999999999"]
        for value in bad_values:
            for edit in (page.paid_input, page.invoice_input, page.item_input):
                edit.setText(value)
                self.assertNotIn("nan", page.main_value.text().lower())
                self.assertNotIn("inf", page.main_value.text().lower())
        for rate in ["", "abc", "-1", "101", "8,5", "0"]:
            page.rate_selector.edit.setText(rate)
        page.paid_input.setText("abc")
        self.assertIn("⚠", page.message.text())
        self.assertTrue(page.paid_input.property("invalid"))
        page.paid_input.setText("100000")
        page.invoice_input.setText("300000")
        page.item_input.setText("50000")
        page.rate_selector.edit.setText("8")
        self.assertEqual(page.main_value.text(), "—")
        self.assertIn("Không thể điều chỉnh", page.message.text())
        page.rate_selector.edit.setText("150")
        self.assertIn("100%", page.message.text())

    def test_refresh_resets_only_current_tool(self):
        prevat = self.open_prevat()
        prevat.price_input.setText("108000")
        QTest.mouseClick(self.window.back_button, Qt.LeftButton)
        page = self.open_balance()
        page.paid_input.setText("1000000")
        page.rate_selector.edit.setText("10")
        self.window.pin_button.setChecked(True)
        size = self.window.size()
        QTest.mouseClick(self.window.refresh_button, Qt.LeftButton)
        self.assertEqual(page.paid_input.text(), "")
        self.assertEqual(page.rate_selector.edit.text(), "8")
        self.assertEqual(page.main_value.text(), "—")
        self.assertIs(self.window.focusWidget(), page.paid_input)
        self.assertTrue(self.window.pin_button.isChecked())
        self.assertEqual(self.window.size(), size)
        self.assertEqual(prevat.price_input.text(), "108000")

    def test_pin_toggle_keeps_data_and_geometry(self):
        page = self.open_balance()
        page.paid_input.setText("1000000")
        page.invoice_input.setText("998000")
        page.item_input.setText("125000")
        geometry = self.window.geometry()
        for _ in range(5):
            self.window.pin_button.click()
            self.assertTrue(self.window.windowFlags() & Qt.WindowStaysOnTopHint)
            self.assertEqual(self.window.pin_button.text(), "📌 Đang ghim")
            self.window.pin_button.click()
            self.assertFalse(self.window.windowFlags() & Qt.WindowStaysOnTopHint)
            self.assertEqual(self.window.pin_button.text(), "📌 Ghim")
        self.assertTrue(self.window.isVisible())
        self.assertEqual(self.window.geometry().size(), geometry.size())
        self.assertEqual(page.main_value.text(), "126.852đ")

    def test_mini_mode_and_pin_independent(self):
        page = self.open_balance()
        page.paid_input.setText("1000000")
        page.invoice_input.setText("998000")
        page.item_input.setText("125000")
        normal = self.window.size()
        self.window.mini_button.click()
        self.assertTrue(self.window.is_mini())
        self.assertLess(self.window.width(), normal.width())
        self.assertEqual(self.window.mini_button.text(), "Mở rộng")
        self.window.pin_button.click()
        self.assertTrue(self.window.is_mini())
        self.assertTrue(page.main_value.isVisible())
        self.assertTrue(page.paid_input.isVisible())
        self.assertTrue(page.leftover_label.isHidden())  # dữ liệu mẫu đã khớp
        self.assertFalse(page.details.isVisible())
        page.details_toggle.click()
        self.assertTrue(page.details.isVisible())
        # Không thanh cuộn ngang, nội dung không rộng hơn cửa sổ
        scroll = self.window.stack.currentWidget()
        self.assertLessEqual(page.minimumSizeHint().width(), scroll.viewport().width())
        # Chuyển công cụ khi đang mini
        self.window.back_button.click()
        self.open_prevat()
        self.assertTrue(self.window.is_mini())
        self.window.back_button.click()
        self.open_balance()
        self.window.mini_button.click()
        self.assertFalse(self.window.is_mini())
        self.assertEqual(self.window.size(), normal)
        self.assertTrue(self.window.pin_button.isChecked())
        self.assertEqual(page.main_value.text(), "126.852đ")

    def test_typing_decimal_in_input(self):
        page = self.open_prevat()
        page.price_input.setFocus()
        QTest.keyClicks(page.price_input, "123,4567")
        self.assertEqual(page.price_input.text(), "123,4567")
        page.price_input.selectAll()
        QTest.keyClick(page.price_input, Qt.Key_Backspace)
        QTest.keyClicks(page.price_input, "1234567,5")
        self.assertEqual(page.price_input.text(), "1.234.567,5")
        page.price_input.selectAll()
        QTest.keyClick(page.price_input, Qt.Key_Backspace)
        QTest.keyClicks(page.price_input, "1,000,000")  # gõ tay kiểu dấu phẩy hàng nghìn
        self.assertEqual(page.price_input.text(), "1.000.000")

    def test_mini_restores_maximized_window(self):
        self.window.showMaximized()
        QApplication.processEvents()
        self.window.mini_button.click()
        self.assertFalse(self.window.isMaximized())
        self.window.mini_button.click()
        QApplication.processEvents()
        self.assertTrue(self.window.windowState() & Qt.WindowMaximized)

    def test_mini_details_fit_without_vertical_scroll(self):
        page = self.open_balance()
        page.paid_input.setText("1.000.007")
        page.invoice_input.setText("1.000.000")
        page.item_input.setText("100.000")
        self.window.mini_button.click()
        page.details_toggle.click()
        QTest.qWait(20)
        scroll = self.window.stack.currentWidget()
        self.assertFalse(scroll.verticalScrollBar().isVisible())
        self.assertFalse(scroll.horizontalScrollBar().isVisible())

    def test_update_check_runs_only_when_clicked(self):
        from vat_app.updater import UpdateInfo
        home = self.window.home_page
        calls = []
        home._update_check = lambda: calls.append(1) or UpdateInfo(
            "0.3.0", "0.4.0", True, "https://github.com/a/b/releases/tag/v0.4.0", "")
        QTest.qWait(50)
        self.assertEqual(calls, [])  # không tự kiểm tra khi mở app
        QTest.mouseClick(home.update_button, Qt.LeftButton)
        for _ in range(50):
            QTest.qWait(20)
            if home.update_message.isVisible():
                break
        self.assertEqual(calls, [1])
        self.assertIn("0.4.0", home.update_message.text())
        self.assertTrue(home.update_button.isEnabled())

    def test_resize_many_times(self):
        page = self.open_balance()
        for width, height in [(920, 600), (480, 380), (700, 500), (1200, 800), (480, 360),
                              (650, 600), (660, 600), (640, 600), (500, 700)]:
            self.window.resize(width, height)
            QApplication.processEvents()
            scroll = self.window.stack.currentWidget()
            self.assertLessEqual(page.minimumSizeHint().width(), scroll.viewport().width())
            self.assertFalse(scroll.horizontalScrollBar().isVisible())
        self.window.resize(480, 500)
        QApplication.processEvents()
        self.assertTrue(page._vertical)
        self.window.resize(1000, 600)
        QApplication.processEvents()
        self.assertFalse(page._vertical)

    def test_money_input_formats_while_typing(self):
        page = self.open_balance()
        edit = page.paid_input
        edit.setFocus()
        QTest.keyClicks(edit, "15000")
        self.assertEqual(edit.text(), "15.000")
        QTest.keyClicks(edit, "00")
        self.assertEqual(edit.text(), "1.500.000")
        # Lỗi người dùng báo: xóa số 0 cuối không được báo lỗi
        QTest.keyClick(edit, Qt.Key_Backspace)
        self.assertEqual(edit.text(), "150.000")
        self.assertFalse(edit.property("invalid"))
        # Gõ chen vào giữa: con trỏ giữ đúng chỗ
        edit.setCursorPosition(1)  # 1|50.000
        QTest.keyClicks(edit, "2")
        self.assertEqual(edit.text(), "1.250.000")
        self.assertEqual(edit.cursorPosition(), 3)  # 1.2|50.000
        # Backspace ngay sau dấu chấm xóa luôn chữ số đứng trước dấu chấm
        edit.setCursorPosition(2)  # 1.|250.000
        QTest.keyClick(edit, Qt.Key_Backspace)
        self.assertEqual(edit.text(), "250.000")
        self.assertEqual(edit.cursorPosition(), 0)
        # Xóa hết
        edit.selectAll()
        QTest.keyClick(edit, Qt.Key_Backspace)
        self.assertEqual(edit.text(), "")
        self.assertIn("Nhập đủ", page.message.text())


if __name__ == "__main__":
    unittest.main()
