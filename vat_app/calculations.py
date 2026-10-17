"""Công thức tính toán của hai công cụ. Không phụ thuộc giao diện để kiểm thử độc lập.

Quy tắc làm tròn (theo đặc tả, không tự ý thay đổi):
- Giá chưa VAT mới / giá trước VAT: luôn làm tròn LÊN đến đồng nguyên (ROUND_CEILING).
- Tiền VAT tính bằng VNĐ: làm tròn thông thường (ROUND_HALF_UP) đến đồng nguyên.
"""

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal, localcontext

from .money import InputError

ONE = Decimal(1)
HUNDRED = Decimal(100)
DEFAULT_VAT_RATE = Decimal(8)
MAX_VAT_RATE = HUNDRED


def ceil_vnd(value: Decimal) -> Decimal:
    """Làm tròn lên đến đồng nguyên: 126851,01 -> 126852; 126852,00 -> 126852."""
    return value.quantize(ONE, rounding=ROUND_CEILING)


def vat_amount(price: Decimal, rate: Decimal) -> Decimal:
    """Tiền VAT của một giá chưa thuế, làm tròn ROUND_HALF_UP đến đồng."""
    with localcontext() as ctx:
        ctx.prec = 60  # đủ để phép nhân/chia không bị làm tròn trước khi quantize
        return (price * rate / HUNDRED).quantize(ONE, rounding=ROUND_HALF_UP)


def _divide_up(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Phép chia làm tròn hướng lên ở độ chính xác cao.

    Sai số (nếu có) luôn nằm về phía lớn hơn, nên khi làm tròn lên đến đồng
    nguyên vẫn cho đúng kết quả như phép chia chính xác tuyệt đối.
    """
    with localcontext() as ctx:
        ctx.prec = 60
        ctx.rounding = ROUND_CEILING
        return numerator / denominator


def validate_rate(rate: Decimal) -> None:
    if rate < 0:
        raise InputError("Thuế suất không được âm", "rate")
    if rate > MAX_VAT_RATE:
        raise InputError("Thuế suất không được lớn hơn 100%", "rate")


# ---------------------------------------------------------------------------
# Công cụ 1: Cân hóa đơn VAT
# ---------------------------------------------------------------------------

STATUS_ADJUSTED = "adjusted"     # đã tính giá mới (tăng hoặc giảm)
STATUS_UNCHANGED = "unchanged"   # hóa đơn đã khớp, giữ nguyên giá
STATUS_NEGATIVE = "negative"     # giá mới < 0, không thể điều chỉnh


@dataclass(frozen=True)
class BalanceResult:
    status: str
    difference: Decimal            # D = A - B
    theoretical_price: Decimal     # C + D / (1 + T/100), chưa làm tròn (để tham khảo)
    new_price: Decimal | None      # giá mới chưa VAT cần nhập (None nếu không thể)
    price_change: Decimal | None   # giá mới - giá cũ
    old_vat: Decimal
    old_total: Decimal             # giá cũ sau VAT
    new_vat: Decimal | None
    new_total: Decimal | None      # giá mới sau VAT
    expected_invoice_total: Decimal | None
    remaining: Decimal | None      # tổng hóa đơn dự kiến - tiền khách chuyển


def balance_invoice(paid: Decimal, invoice_total: Decimal,
                    item_price: Decimal, rate: Decimal) -> BalanceResult:
    """Tính giá chưa VAT mới của một mặt hàng để tổng hóa đơn về gần nhất với tiền khách chuyển.

    paid (A): tổng tiền khách chuyển; invoice_total (B): tổng hóa đơn hiện tại;
    item_price (C): giá mặt hàng cũ chưa VAT; rate (T): thuế suất %.
    """
    if paid <= 0:
        raise InputError("Tổng tiền khách chuyển phải lớn hơn 0", "paid")
    if invoice_total <= 0:
        raise InputError("Tổng tiền hóa đơn hiện tại phải lớn hơn 0", "invoice_total")
    if item_price < 0:
        raise InputError("Giá mặt hàng cần sửa không được âm", "item_price")
    validate_rate(rate)

    difference = paid - invoice_total
    old_vat = vat_amount(item_price, rate)
    old_total = item_price + old_vat

    if difference == 0:
        theoretical = item_price
        new_price = item_price
        status = STATUS_UNCHANGED
    else:
        with localcontext() as ctx:
            ctx.prec = 60
            ctx.rounding = ROUND_CEILING
            theoretical = item_price + _divide_up(difference * HUNDRED, HUNDRED + rate)
        new_price = ceil_vnd(theoretical)
        status = STATUS_ADJUSTED
        if new_price < 0:
            return BalanceResult(STATUS_NEGATIVE, difference, theoretical, None, None,
                                 old_vat, old_total, None, None, None, None)

    # Kiểm tra lại bằng giá mới ĐÃ làm tròn, không dùng kết quả lý thuyết.
    new_vat = vat_amount(new_price, rate)
    new_total = new_price + new_vat
    expected = invoice_total - old_total + new_total
    return BalanceResult(
        status=status,
        difference=difference,
        theoretical_price=theoretical,
        new_price=new_price,
        price_change=new_price - item_price,
        old_vat=old_vat,
        old_total=old_total,
        new_vat=new_vat,
        new_total=new_total,
        expected_invoice_total=expected,
        remaining=expected - paid,
    )


# ---------------------------------------------------------------------------
# Công cụ 2: Tính giá trước VAT
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PreVatResult:
    pre_vat_price: Decimal   # giá trước VAT, đã làm tròn lên
    vat: Decimal             # giá sau VAT - giá trước VAT đã làm tròn


def pre_vat_price(price_with_vat: Decimal, rate: Decimal) -> PreVatResult:
    """Giá trước VAT = Giá sau VAT / (1 + VAT/100), làm tròn lên đến đồng nguyên."""
    if price_with_vat < 0:
        raise InputError("Giá đã bao gồm VAT không được âm", "price")
    validate_rate(rate)
    pre = ceil_vnd(_divide_up(price_with_vat * HUNDRED, HUNDRED + rate))
    vat = price_with_vat - pre
    if vat < 0:
        # Chỉ xảy ra khi giá nhỏ hơn 1đ (có phần lẻ): làm tròn lên vượt quá giá sau VAT.
        raise InputError("Giá đã bao gồm VAT quá nhỏ để tính", "price")
    return PreVatResult(pre_vat_price=pre, vat=vat)
