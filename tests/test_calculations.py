import unittest
from decimal import Decimal as D

from vat_app.calculations import (
    STATUS_ADJUSTED, STATUS_NEGATIVE, STATUS_UNCHANGED,
    balance_invoice, ceil_vnd, pre_vat_price, vat_amount,
)
from vat_app.money import InputError


class TestRounding(unittest.TestCase):
    def test_ceil_examples_from_spec(self):
        self.assertEqual(ceil_vnd(D("126851.01")), D(126852))
        self.assertEqual(ceil_vnd(D("126851.85")), D(126852))
        self.assertEqual(ceil_vnd(D("126852.00")), D(126852))

    def test_ceil_negative_goes_up(self):
        self.assertEqual(ceil_vnd(D("-1.5")), D(-1))

    def test_vat_half_up(self):
        self.assertEqual(vat_amount(D(126852), D(8)), D(10148))  # 10148,16
        self.assertEqual(vat_amount(D(12345), D(10)), D(1235))   # 1234,5 -> 1235
        self.assertEqual(vat_amount(D(12344), D(10)), D(1234))   # 1234,4 -> 1234


class TestBalanceInvoice(unittest.TestCase):
    def test_required_example(self):
        r = balance_invoice(D(1_000_000), D(998_000), D(125_000), D(8))
        self.assertEqual(r.status, STATUS_ADJUSTED)
        self.assertEqual(r.new_price, D(126_852))
        self.assertEqual(r.price_change, D(1_852))
        self.assertEqual(r.new_vat, D(10_148))
        self.assertEqual(r.new_total, D(137_000))
        self.assertEqual(r.old_vat, D(10_000))
        self.assertEqual(r.old_total, D(135_000))
        self.assertEqual(r.expected_invoice_total, D(1_000_000))
        self.assertEqual(r.remaining, D(0))

    def test_invoice_too_high_price_decreases(self):
        r = balance_invoice(D(1_000_000), D(1_002_000), D(125_000), D(8))
        # 125000 - 2000/1,08 = 123148,148... -> làm tròn lên 123149
        self.assertEqual(r.new_price, D(123_149))
        self.assertEqual(r.price_change, D(-1_851))
        self.assertEqual(r.new_vat, D(9_852))   # 9851,92
        self.assertEqual(r.new_total, D(133_001))
        self.assertEqual(r.expected_invoice_total, D(1_000_001))
        self.assertEqual(r.remaining, D(1))

    def test_already_balanced_keeps_price(self):
        r = balance_invoice(D(500_000), D(500_000), D(125_000), D(8))
        self.assertEqual(r.status, STATUS_UNCHANGED)
        self.assertEqual(r.new_price, D(125_000))
        self.assertEqual(r.price_change, D(0))
        self.assertEqual(r.remaining, D(0))

    def test_negative_price_is_rejected(self):
        r = balance_invoice(D(100_000), D(300_000), D(50_000), D(8))
        self.assertEqual(r.status, STATUS_NEGATIVE)
        self.assertIsNone(r.new_price)
        self.assertIsNone(r.remaining)
        self.assertLess(r.theoretical_price, 0)

    def test_result_exactly_zero_is_allowed(self):
        # 108.000 sau VAT 8% = 100.000 chưa VAT; giảm đúng 108.000 -> giá mới 0
        r = balance_invoice(D(892_000), D(1_000_000), D(100_000), D(8))
        self.assertEqual(r.status, STATUS_ADJUSTED)
        self.assertEqual(r.new_price, D(0))
        self.assertEqual(r.remaining, D(0))

    def test_zero_vat_rate(self):
        r = balance_invoice(D(1_000_000), D(998_000), D(125_000), D(0))
        self.assertEqual(r.new_price, D(127_000))
        self.assertEqual(r.new_vat, D(0))
        self.assertEqual(r.remaining, D(0))

    def test_check_uses_rounded_price_and_reports_leftover(self):
        # 100000 + 1/1,08 = 100000,925... -> 100001; VAT 8.000,08 -> 8000
        # giá sau VAT tăng 1đ đúng bằng chênh lệch => khớp
        r = balance_invoice(D(1_000_001), D(1_000_000), D(100_000), D(8))
        self.assertEqual(r.new_price, D(100_001))
        self.assertEqual(r.remaining, D(0))
        # Thêm 2đ: 100000 + 2/1,08 = 100001,85 -> 100002; VAT 8000,16 -> 8000
        # giá sau VAT chỉ tăng 2đ -> khớp; thử 3đ: 100002,77 -> 100003, VAT 8000,24 -> 8000
        r = balance_invoice(D(1_000_003), D(1_000_000), D(100_000), D(8))
        self.assertEqual(r.new_price, D(100_003))
        self.assertEqual(r.remaining, D(0))
        # 10%: 100000 + 7/1,1 = 100006,36 -> 100007; VAT 10000,7 -> 10001; sau VAT 110008
        r = balance_invoice(D(1_000_007), D(1_000_000), D(100_000), D(10))
        self.assertEqual(r.new_price, D(100_007))
        self.assertEqual(r.new_total, D(110_008))
        self.assertEqual(r.remaining, D(1))

    def test_remaining_matches_definition_on_many_inputs(self):
        for diff in range(-5000, 5001, 37):
            for rate in (D(0), D(5), D(8), D(10), D("8.5")):
                r = balance_invoice(D(1_000_000) + diff, D(1_000_000), D(250_000), rate)
                self.assertEqual(r.new_price, ceil_vnd(r.theoretical_price))
                self.assertGreaterEqual(r.new_price, r.theoretical_price)
                self.assertLess(r.new_price - r.theoretical_price, 1)
                self.assertEqual(r.new_total, r.new_price + vat_amount(r.new_price, rate))
                self.assertEqual(r.expected_invoice_total, D(1_000_000) - r.old_total + r.new_total)
                self.assertEqual(r.remaining, r.expected_invoice_total - (D(1_000_000) + diff))

    def test_extreme_but_valid_inputs_are_exact(self):
        big = D("999999999999999")
        r = balance_invoice(big, big - 1, D("999999999999.9999"), D("99.9999"))
        self.assertEqual(r.new_vat, vat_amount(r.new_price, D("99.9999")))
        self.assertEqual(r.remaining, r.expected_invoice_total - big)
        self.assertEqual(vat_amount(D("999999999999999"), D("8")), D("80000000000000"))

    def test_invalid_inputs_raise_input_error(self):
        cases = [
            (D(0), D(998_000), D(125_000), D(8)),
            (D(-1), D(998_000), D(125_000), D(8)),
            (D(1_000_000), D(0), D(125_000), D(8)),
            (D(1_000_000), D(998_000), D(-5), D(8)),
            (D(1_000_000), D(998_000), D(125_000), D(-1)),
            (D(1_000_000), D(998_000), D(125_000), D(101)),
        ]
        for args in cases:
            with self.assertRaises(InputError):
                balance_invoice(*args)


class TestPreVat(unittest.TestCase):
    def test_required_example(self):
        r = pre_vat_price(D(108_000), D(8))
        self.assertEqual(r.pre_vat_price, D(100_000))
        self.assertEqual(r.vat, D(8_000))

    def test_decimal_results_always_round_up(self):
        cases = [
            # (giá sau VAT, thuế suất, giá trước VAT, tiền VAT)
            (D(100_000), D(8), D(92_593), D(7_407)),   # 92592,59...
            (D(100_001), D(8), D(92_594), D(7_407)),   # 92593,51...
            (D(1_000), D(10), D(910), D(90)),          # 909,09...
            (D(50_000), D(5), D(47_620), D(2_380)),    # 47619,04...
            (D(1), D(8), D(1), D(0)),                  # 0,925...
            (D(137_000), D(8), D(126_852), D(10_148)), # 126851,85...
            (D(108_001), D(8), D(100_001), D(8_000)),  # 100000,925...
        ]
        for price, rate, pre, vat in cases:
            with self.subTest(price=price, rate=rate):
                r = pre_vat_price(price, rate)
                self.assertEqual(r.pre_vat_price, pre)
                self.assertEqual(r.vat, vat)

    def test_always_ceiling_property(self):
        for price in range(0, 300_000, 997):
            for rate in (D(0), D(5), D(8), D(10), D("8.5"), D("3.33")):
                r = pre_vat_price(D(price), rate)
                exact_times = r.pre_vat_price * (100 + rate)
                # pre >= giá/(1+T) và pre - 1 < giá/(1+T)
                self.assertGreaterEqual(exact_times, D(price) * 100)
                self.assertLess((r.pre_vat_price - 1) * (100 + rate), D(price) * 100)
                self.assertEqual(r.pre_vat_price + r.vat, D(price))

    def test_zero_rate_and_zero_price(self):
        self.assertEqual(pre_vat_price(D(108_000), D(0)).pre_vat_price, D(108_000))
        self.assertEqual(pre_vat_price(D(0), D(8)).pre_vat_price, D(0))

    def test_price_below_one_dong_never_gives_negative_vat(self):
        with self.assertRaises(InputError):
            pre_vat_price(D("0.5"), D(8))

    def test_invalid(self):
        with self.assertRaises(InputError):
            pre_vat_price(D(-1), D(8))
        with self.assertRaises(InputError):
            pre_vat_price(D(1000), D(150))


if __name__ == "__main__":
    unittest.main()
