"""Kiểm tra phiên bản mới trên GitHub Releases.

Chỉ chạy khi người dùng bấm "Kiểm tra cập nhật": không tự kết nối mạng khi mở app,
không tự tải hay cài đặt gì. Mọi phép tính của app vẫn hoạt động offline hoàn toàn.

Mỗi lần ra bản mới: tăng APP_VERSION, đóng gói EXE rồi tạo một Release trên GitHub
với tag dạng v1.1.0 và đính kèm file EXE.
"""

import json
import re
import urllib.request
from dataclasses import dataclass

from . import APP_VERSION

# Kho GitHub (công khai) chứa các bản phát hành, dạng "tài-khoản/tên-kho". Để trống = tắt.
UPDATE_REPO = "bmabongden/cong-cu-hoa-don-vat"

API_URL = "https://api.github.com/repos/{repo}/releases/latest"
TIMEOUT_SECONDS = 8


class UpdateError(Exception):
    """Lỗi khi kiểm tra cập nhật, thông điệp tiếng Việt để hiển thị."""


@dataclass(frozen=True)
class UpdateInfo:
    current: str
    latest: str
    has_update: bool
    url: str          # trang Release trên GitHub để tải bản mới
    notes: str


def parse_version(text: str) -> tuple[int, ...]:
    """'v0.10.2' -> (0, 10, 2). Bỏ qua tiền tố v và phần đuôi như -beta."""
    match = re.match(r"\s*[vV]?(\d+(?:\.\d+)*)", text or "")
    if not match:
        raise UpdateError(f"Không đọc được số phiên bản: {text!r}")
    return tuple(int(part) for part in match.group(1).split("."))


def is_newer(latest: str, current: str) -> bool:
    a, b = parse_version(latest), parse_version(current)
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) > b + (0,) * (width - len(b))


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "cong-cu-hoa-don-vat",
    })
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def check_for_update(repo: str = None, current: str = APP_VERSION, fetch=_fetch_json) -> UpdateInfo:
    """Hỏi GitHub bản phát hành mới nhất và so với phiên bản đang dùng."""
    repo = UPDATE_REPO if repo is None else repo
    if not repo:
        raise UpdateError("Chưa cấu hình kho GitHub để kiểm tra cập nhật.")
    try:
        data = fetch(API_URL.format(repo=repo))
    except UpdateError:
        raise
    except Exception as exc:
        status = getattr(exc, "code", None)
        if status == 404:
            raise UpdateError("Chưa có bản phát hành nào trên GitHub.") from None
        raise UpdateError("Không kết nối được GitHub. Vui lòng kiểm tra Internet.") from None
    latest = str(data.get("tag_name") or "").strip()
    if not latest:
        raise UpdateError("Không đọc được thông tin phiên bản từ GitHub.")
    # Chỉ mở trang trên github.com, tránh mở đường dẫn lạ nếu dữ liệu trả về bất thường.
    url = str(data.get("html_url") or "")
    if not url.startswith("https://github.com/"):
        url = f"https://github.com/{repo}/releases/latest"
    return UpdateInfo(
        current=current,
        latest=latest.lstrip("vV"),
        has_update=is_newer(latest, current),
        url=url,
        notes=str(data.get("body") or ""),
    )
