import unittest
from decimal import Decimal as D

from vat_app.money import (
    InputError, copy_text, format_money, live_format, parse_money, parse_percent,
)


class TestParseMoney(unittest.TestCase):
    def test_common_vietnamese_formats(self):
        for text in ["1000000", "1.000.000", "1,000,000", " 1 000 000 ", "1.000.000đ",
                     "1.000.000 VNĐ", "1000000vnd"]:
            with self.subTest(text=text):
                self.assertEqual(parse_money(text), D(1_000_000))

    def test_single_separator(self):
        self.assertEqual(parse_money("1.000"), D(1000))
        self.assertEqual(parse_money("125,000"), D(125_000))
        self.assertEqual(parse_money("126851,01"), D("126851.01"))
        self.assertEqual(parse_money("126851.5"), D("126851.5"))

    def test_mixed_separators(self):
        self.assertEqual(parse_money("1.000.000,50"), D("1000000.50"))
        self.assertEqual(parse_money("1,000,000.50"), D("1000000.50"))

    def test_too_many_decimals(self):
        self.assertEqual(parse_money("1,2345"), D("1.2345"))
        with self.assertRaises(InputError):
            parse_money("1,23456")

    def test_too_large_amount(self):
        self.assertEqual(parse_money("999.999.999.999.999"), D("999999999999999"))
        with self.assertRaises(InputError):
            parse_money("1.000.000.000.000.000")

    def test_sign(self):
        self.assertEqual(parse_money("-1.000"), D(-1000))
        self.assertEqual(parse_money("+500"), D(500))

    def test_empty_is_none(self):
        self.assertIsNone(parse_money(""))
        self.assertIsNone(parse_money("   "))
        self.assertIsNone(parse_money("đ"))

    def test_invalid(self):
        for text in ["abc", "12a", "1..000", "1.00.000", "1,000.000,5", "-", ".5", "5.",
                     "1.000,000.5", "NaN", "inf", "1e5"]:
            with self.subTest(text=text):
                with self.assertRaises(InputError):
                    parse_money(text)


class TestParsePercent(unittest.TestCase):
    def test_values(self):
        self.assertEqual(parse_percent("8"), D(8))
        self.assertEqual(parse_percent("8%"), D(8))
        self.assertEqual(parse_percent("8,5"), D("8.5"))
        self.assertEqual(parse_percent("8.5 %"), D("8.5"))
        self.assertEqual(parse_percent("0"), D(0))
        self.assertIsNone(parse_percent(""))

    def test_invalid(self):
        for text in ["abc", "8..5", "8,5,1", "x%", "%"]:
            with self.subTest(text=text):
                if text == "%":
                    self.assertIsNone(parse_percent(text))
                else:
                    with self.assertRaises(InputError):
                        parse_percent(text)


class TestFormat(unittest.TestCase):
    def test_format_money(self):
        self.assertEqual(format_money(D(126852)), "126.852đ")
        self.assertEqual(format_money(D(1_000_000)), "1.000.000đ")
        self.assertEqual(format_money(D(0)), "0đ")
        self.assertEqual(format_money(D(-1)), "-1đ")
        self.assertEqual(format_money(D(1852), show_plus=True), "+1.852đ")
        self.assertEqual(format_money(D(0), show_plus=True), "0đ")
        self.assertEqual(format_money(D("-0")), "0đ")
        self.assertEqual(format_money(D("1000.50")), "1.000,5đ")

    def test_copy_text_has_only_digits(self):
        self.assertEqual(copy_text(D(126852)), "126852")
        self.assertEqual(copy_text(D(1_000_000)), "1000000")
        self.assertEqual(copy_text(D(-1851)), "-1851")
        self.assertEqual(copy_text(D("-0")), "0")
        self.assertEqual(copy_text(D("126852.00")), "126852")



class TestLiveFormat(unittest.TestCase):
    def check(self, text, cursor, expected):
        """expected: chuỗi kết quả với | đánh dấu vị trí con trỏ."""
        new_text, new_cursor = live_format(text, cursor)
        self.assertEqual(new_text[:new_cursor] + "|" + new_text[new_cursor:], expected)

    def test_typing_adds_dots(self):
        self.check("1500000", 7, "1.500.000|")
        self.check("1.500.0001", 10, "15.000.001|")
        self.check("-1234", 5, "-1.234|")

    def test_deleting_last_zero(self):
        # Lỗi người dùng báo: 1.500.000 xóa số 0 cuối -> phải là 150.000
        self.check("1.500.00", 8, "150.000|")
        self.check("1.50.000", 4, "150|.000")

    def test_cursor_in_middle(self):
        self.check("15000001", 3, "15.0|00.001")
        self.check("1500.000", 4, "1.500|.000")

    def test_decimal_and_paste(self):
        self.check("126851,01", 9, "126.851,01|")
        self.check("126851,", 7, "126.851,|")
        self.check("1,000,000", 9, "1.000.000|")
        self.check("125,000", 7, "125.000|")
        self.check("1.000.000đ", 10, "1.000.000|")

    def test_pasted_decimals_keep_their_value(self):
        # Lỗi ChatGPT báo: dán "126851.5" từng bị hiểu thành 1.268.515
        self.check("126851.5", 8, "126.851,5|")
        self.check("1,000,000.50", 12, "1.000.000,50|")
        self.check("1.000.000,50", 12, "1.000.000,50|")

    def test_typing_decimal_part_after_comma(self):
        # Lỗi ChatGPT báo: gõ "123,4567" từng bị đổi thành 1.234.567
        self.check("123,", 4, "123,|")
        new_text, _ = live_format("123,456", 7, decimal_comma=True)
        self.assertEqual(new_text, "123,456")
        new_text, _ = live_format("123,4567", 8, decimal_comma=True)
        self.assertEqual(new_text, "123,4567")
        self.assertEqual(parse_money(new_text), D("123.4567"))

    def test_leading_zeros_and_empty(self):
        self.check("00012", 5, "12|")
        self.check("0", 1, "0|")
        self.check("", 0, "|")

    def test_invalid_text_left_unchanged(self):
        self.check("12a", 3, "12a|")
        self.check("abc", 3, "abc|")

    def test_result_always_parses_back(self):
        cases = {"1500000": D(1_500_000), "1.500.00": D(150_000), "126851,01": D("126851.01"),
                 "1,000,000": D(1_000_000), "999": D(999), "1000": D(1000), "-5000": D(-5000)}
        for raw, expected in cases.items():
            text, _ = live_format(raw, len(raw))
            self.assertEqual(parse_money(text), expected)


if __name__ == "__main__":
    unittest.main()
