"""Đọc và định dạng số tiền, thuế suất theo cách viết thông dụng tại Việt Nam.

Toàn bộ giá trị dùng Decimal, không dùng float.
"""

import re
from decimal import Decimal, InvalidOperation


class InputError(ValueError):
    """Lỗi dữ liệu nhập, thông điệp viết bằng tiếng Việt để hiển thị cho người dùng.

    field (tùy chọn) cho biết ô nhập gây lỗi để giao diện đánh dấu.
    """

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


# Giới hạn số tiền (dưới 1 triệu tỷ đồng, tối đa 4 chữ số lẻ) để mọi phép tính Decimal
# luôn chính xác tuyệt đối.
MAX_AMOUNT = Decimal("999999999999999")
MAX_DECIMALS = 4

_CURRENCY_SUFFIX = re.compile(r"(vnđ|vnd|đ|d)$", re.IGNORECASE)
_SPACES = re.compile(r"[\s  ]+")


def _to_decimal(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise InputError("Số không hợp lệ") from None
    if not value.is_finite():
        raise InputError("Số không hợp lệ")
    return value


def _is_thousand_groups(text: str, sep: str) -> bool:
    return re.fullmatch(r"\d{1,3}(" + re.escape(sep) + r"\d{3})+", text) is not None


def parse_money(text: str) -> Decimal | None:
    """Chuyển chuỗi người dùng nhập thành Decimal.

    Trả về None nếu ô trống. Hiểu được các cách viết:
    1000000, 1.000.000, 1,000,000, 1.000.000đ, 126851,01, 1.000.000,50 ...
    Ném InputError nếu không đọc được.
    """
    s = _SPACES.sub("", text or "")
    s = _CURRENCY_SUFFIX.sub("", s)
    if not s:
        return None

    sign = ""
    if s[0] in "+-":
        sign, s = ("-" if s[0] == "-" else ""), s[1:]
    if not s:
        raise InputError("Số không hợp lệ")
    if not re.fullmatch(r"[\d.,]+", s) or not s[0].isdigit() or not s[-1].isdigit():
        raise InputError("Chỉ nhập chữ số, dấu chấm hoặc dấu phẩy")

    has_dot, has_comma = "." in s, "," in s
    if has_dot and has_comma:
        # Dấu xuất hiện sau cùng là dấu thập phân, dấu còn lại phân cách hàng nghìn.
        dec_sep = "." if s.rfind(".") > s.rfind(",") else ","
        thou_sep = "," if dec_sep == "." else "."
        int_part, _, frac_part = s.rpartition(dec_sep)
        if dec_sep in int_part or not _is_thousand_groups(int_part, thou_sep):
            raise InputError("Cách viết số không hợp lệ")
        number = int_part.replace(thou_sep, "") + "." + frac_part
    elif has_dot or has_comma:
        sep = "." if has_dot else ","
        if s.count(sep) > 1:
            if not _is_thousand_groups(s, sep):
                raise InputError("Cách viết số không hợp lệ")
            number = s.replace(sep, "")
        elif _is_thousand_groups(s, sep):
            # Ví dụ 1.000 hoặc 125,000 -> phân cách hàng nghìn.
            number = s.replace(sep, "")
        else:
            # Ví dụ 126851,01 -> phần thập phân.
            number = s.replace(sep, ".")
    else:
        number = s

    value = _to_decimal(sign + number)
    if abs(value) > MAX_AMOUNT:
        raise InputError("Số tiền quá lớn")
    if -value.as_tuple().exponent > MAX_DECIMALS:
        raise InputError(f"Tối đa {MAX_DECIMALS} chữ số sau dấu phẩy")
    return value


def parse_percent(text: str) -> Decimal | None:
    """Đọc thuế suất (%), ví dụ: 8, 8%, 8,5, 8.5. Trả về None nếu ô trống."""
    s = _SPACES.sub("", text or "").rstrip("%")
    if not s:
        return None
    if not re.fullmatch(r"[+-]?\d{1,3}([.,]\d{1,4})?", s):
        raise InputError("Thuế suất không hợp lệ")
    return _to_decimal(s.replace(",", "."))


def _split_parts(value: Decimal) -> tuple[str, str, str]:
    """Tách thành (dấu, phần nguyên, phần thập phân đã bỏ số 0 thừa)."""
    sign = "-" if value < 0 else ""
    text = format(abs(value), "f")
    int_part, _, frac_part = text.partition(".")
    return sign, int_part, frac_part.rstrip("0")


def format_money(value: Decimal, show_plus: bool = False) -> str:
    """Định dạng hiển thị: 1.000.000đ (thập phân, nếu có, dùng dấu phẩy)."""
    if value == 0:
        value = Decimal(0)  # tránh hiển thị "-0"
    sign, int_part, frac_part = _split_parts(value)
    if show_plus and value > 0:
        sign = "+"
    groups = []
    while len(int_part) > 3:
        groups.insert(0, int_part[-3:])
        int_part = int_part[:-3]
    groups.insert(0, int_part)
    text = sign + ".".join(groups)
    if frac_part:
        text += "," + frac_part
    return text + "đ"


def copy_text(value: Decimal) -> str:
    """Chuỗi đưa vào clipboard: chỉ chữ số, giữ dấu trừ nếu âm. Ví dụ 126852, -1."""
    if value == 0:
        return "0"
    sign, int_part, frac_part = _split_parts(value)
    return sign + int_part + ("," + frac_part if frac_part else "")


def format_percent(value: Decimal) -> str:
    sign, int_part, frac_part = _split_parts(value)
    return sign + int_part + ("," + frac_part if frac_part else "")


_LIVE_ALLOWED = re.compile(r"[+-]?[\d.,]*")


def _group_thousands(digits: str) -> str:
    groups = []
    while len(digits) > 3:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    groups.insert(0, digits)
    return ".".join(groups)


def _decimal_separator_index(body: str, decimal_comma: bool) -> int | None:
    """Vị trí dấu thập phân trong chuỗi chỉ gồm chữ số, '.' và ','; None nếu là số nguyên."""
    dots, commas = body.count("."), body.count(",")
    if decimal_comma and commas > 1 and not dots:
        return None                  # đang gõ 1,000,000 bằng dấu phẩy
    if commas and (decimal_comma or dots):
        if decimal_comma or body.rfind(",") > body.rfind("."):
            return body.rfind(",")   # 1.000.000,50 hoặc đang gõ phần thập phân sau dấu phẩy
        return body.rfind(".")       # dán dạng 1,000,000.50
    if commas:
        if commas == 1 and not re.fullmatch(r"\d{1,3},\d{3}", body):
            return body.find(",")    # 126851,01
        return None                  # 1,000,000 hoặc 125,000
    if dots == 1:
        before, after = body.split(".")
        if len(before) > 3 and len(after) != 3:
            return body.find(".")    # dán dạng 126851.5
    return None                      # 1.500.000 hoặc 1.500.00 (đang xóa số)


def live_format(text: str, cursor: int, decimal_comma: bool = False) -> tuple[str, int]:
    """Định dạng dấu chấm hàng nghìn ngay khi đang gõ, giữ đúng vị trí con trỏ.

    Ví dụ: "1500000" -> "1.500.000"; xóa số 0 cuối của "1.500.000" ("1.500.00") -> "150.000".
    Dấu phẩy là dấu thập phân ("126851,01" -> "126.851,01"), trừ khi là chuỗi dán vào
    dạng 1,000,000 (phân cách hàng nghìn bằng dấu phẩy).
    decimal_comma=True: ô đã có dấu phẩy thập phân từ trước (người dùng đang gõ phần lẻ),
    nên dấu phẩy luôn là dấu thập phân.
    Chuỗi có ký tự lạ được giữ nguyên để báo lỗi cho người dùng.
    """
    before = text[:cursor]
    s = _SPACES.sub("", text)
    s_before = _SPACES.sub("", before)
    suffix = _CURRENCY_SUFFIX.search(s)
    if suffix:
        s = s[:suffix.start()]
        s_before = s_before[:len(s)]
    if not _LIVE_ALLOWED.fullmatch(s):
        return text, cursor

    sign = s[0] if s[:1] in ("+", "-") else ""
    body = s[len(sign):]
    sign = "-" if sign == "-" else ""
    if decimal_comma and re.fullmatch(r"\d{1,3},\d{3}", body):
        # Chưa rõ là 125,000 (hàng nghìn) hay đang gõ phần lẻ 123,4567: giữ nguyên chữ người gõ.
        return text, cursor

    dec_index = _decimal_separator_index(body, decimal_comma)
    if dec_index is None:
        int_part, frac_part, has_decimal = body, "", False
    else:
        int_part, frac_part, has_decimal = body[:dec_index], body[dec_index + 1:], True
    int_digits = re.sub(r"\D", "", int_part)
    frac_digits = re.sub(r"\D", "", frac_part)

    stripped = int_digits.lstrip("0")
    removed_zeros = len(int_digits) - len(stripped)
    if not stripped and (int_digits or has_decimal):
        stripped, removed_zeros = "0", len(int_digits) - 1
    new_text = sign + _group_thousands(stripped) if stripped else sign
    if has_decimal:
        new_text += "," + frac_digits

    # Vị trí con trỏ: đếm số chữ số (và dấu phẩy thập phân) đứng trước con trỏ.
    if has_decimal:
        dec_pos = len(sign) + len(int_part)  # vị trí dấu thập phân trong s
        left = s_before
        count = len(re.sub(r"\D", "", left))
        passed_decimal = len(left) > dec_pos
    else:
        count = len(re.sub(r"\D", "", s_before))
        passed_decimal = False
    count = max(0, count - removed_zeros)
    new_cursor = len(sign) if sign and s_before.startswith("-") else 0
    seen = 0
    pos = len(sign)
    for pos in range(len(sign), len(new_text) + 1):
        if seen >= count and (not passed_decimal or "," in new_text[:pos]):
            break
        if pos < len(new_text):
            ch = new_text[pos]
            if ch.isdigit():
                seen += 1
    new_cursor = max(new_cursor, pos)
    if new_text in ("", "-") and not text.strip():
        return text, cursor
    return new_text, min(new_cursor, len(new_text))
