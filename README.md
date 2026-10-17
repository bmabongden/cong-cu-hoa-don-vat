# Công cụ hóa đơn VAT (phiên bản 1.0.0)

Ứng dụng Windows nhỏ gọn, chạy offline hoàn toàn, gồm hai công cụ:

1. **Cân hóa đơn VAT**: tính giá chưa VAT mới của một mặt hàng để tổng hóa đơn khớp (hoặc gần nhất) với tiền khách chuyển.
2. **Tính giá trước VAT**: tính giá chưa VAT từ giá đã bao gồm VAT.

**Tải bản EXE (không cần cài Python):** https://github.com/bmabongden/cong-cu-hoa-don-vat/releases/latest
→ tải file `CongCuHoaDonVAT.exe` rồi nhấp đúp để chạy. Lần đầu Windows có thể hiện cảnh báo SmartScreen
vì file chưa được ký số: bấm **More info → Run anyway**.

Phần dưới đây dành cho việc chạy từ mã nguồn và tự đóng gói.

## 1. Cài đặt (một lần)

1. Cài **Python 3.10 trở lên** (khuyên dùng 3.12 hoặc 3.13) từ https://www.python.org/downloads/windows/
   Khi cài, nhớ tick **"Add python.exe to PATH"**.
2. Mở thư mục `cong-cu-hoa-don-vat`, bấm vào thanh địa chỉ của File Explorer, gõ `cmd` rồi Enter.
3. Cài thư viện:

   ```
   python -m pip install -r requirements.txt
   ```

   Thư viện duy nhất cần cài là PySide6 (gói gọn `PySide6-Essentials`).

## 2. Chạy ứng dụng

Cách nhanh nhất: **nhấp đúp file `chay_ung_dung.bat`** (lần đầu sẽ tự cài PySide6 nếu chưa có).

Hoặc trong cửa sổ cmd tại thư mục này:

```
python main.py
```

## 3. Chạy kiểm thử tự động

```
python -m unittest -v
```

Gồm kiểm thử công thức (`tests/test_calculations.py`), đọc/định dạng số tiền (`tests/test_money.py`)
và kiểm thử giao diện cơ bản (`tests/test_ui.py`: nhập liệu, nhấp đúp sao chép, ghim, mini, làm mới,
dữ liệu bất thường, đổi kích thước). Khi chạy kiểm thử giao diện có thể thấy cửa sổ chớp lên rồi tắt, đó là bình thường.

## 4. Cách dùng nhanh

- Nhập số là kết quả tự tính lại, không cần nút Tính hay phím Enter.
- Số tiền nhập được dạng `1000000`, `1.000.000` hoặc `1,000,000`. Dấu chấm hàng nghìn tự hiện ngay khi gõ (gõ `1500000` thấy `1.500.000`).
- Số tiền tối đa 999.999.999.999.999đ. Có thể nhập phần lẻ sau dấu phẩy (ví dụ `126.851,5`).
- Thuế suất mặc định 8%, gõ số khác vào ô thuế suất khi cần (ví dụ `10` hoặc `8,5`).
- **Nhấp đúp vào bất kỳ số tiền kết quả nào** để sao chép, clipboard chỉ chứa chữ số (ví dụ `126852`, hoặc `-1851` nếu âm).
- **📌 Ghim**: bật thì cửa sổ luôn nổi trên các cửa sổ khác (nút chuyển màu xanh, chữ "Đang ghim"). Bấm lần nữa để tắt.
- **Mini / Mở rộng**: chuyển sang cửa sổ nhỏ gọn và trở lại kích thước cũ. Ở chế độ mini, phần chi tiết kiểm tra
  được thu gọn (bấm "Xem chi tiết kiểm tra" để mở), kết quả chính luôn hiển thị; nếu còn chênh lệch
  sau khi làm tròn thì dòng "Chênh lệch còn lại" cũng luôn hiện.
- **↻ Làm mới**: xóa dữ liệu của công cụ đang mở, đưa thuế suất về 8%.
- **← Quay lại**: trở về màn hình chọn công cụ (dữ liệu đã nhập của từng công cụ được giữ lại).

## 5. Quy tắc tính toán

Toàn bộ dùng `Decimal`, không dùng `float`.

**Cân hóa đơn** (A: tiền khách chuyển, B: tổng hóa đơn hiện tại, C: giá cũ chưa VAT, T: thuế suất):

- `D = A − B`
- `Giá mới = C + D / (1 + T/100)`, **luôn làm tròn lên** đến đồng (`ROUND_CEILING`). Nếu A = B thì giữ nguyên giá.
- Tiền VAT = giá × T/100, làm tròn `ROUND_HALF_UP` đến đồng.
- `Tổng hóa đơn dự kiến = B − (giá cũ sau VAT) + (giá mới sau VAT)`, tính bằng giá mới **đã làm tròn**.
- `Sai lệch còn lại = Tổng hóa đơn dự kiến − A`, hiển thị đúng như tính được (không che giấu).
- Nếu giá mới nhỏ hơn 0: báo không thể điều chỉnh, không đưa ra giá âm.

Ví dụ: A = 1.000.000, B = 998.000, C = 125.000, VAT 8% → giá mới **126.852đ**, VAT mới 10.148đ,
giá sau VAT 137.000đ, tổng dự kiến 1.000.000đ, sai lệch 0đ.

**Giá trước VAT**: `Giá trước VAT = Giá sau VAT / (1 + T/100)`, làm tròn lên đến đồng;
`Tiền VAT = Giá sau VAT − Giá trước VAT đã làm tròn`. Ví dụ 108.000đ, 8% → 100.000đ, VAT 8.000đ.

Lưu ý: đây là phép kiểm tra dự kiến theo cách làm tròn của ứng dụng; phần mềm xuất hóa đơn có thể làm tròn khác.

## 6. Đóng gói EXE

Trên Windows, nhấp đúp `dong_goi_exe.bat` (hoặc chạy trong cmd). Script cài PyInstaller, chạy kiểm thử rồi tạo
`dist\CongCuHoaDonVAT.exe` (một file duy nhất, kèm biểu tượng app).

## 7. Cấu trúc mã nguồn

```
main.py                  Khởi chạy ứng dụng
chay_ung_dung.bat        Chạy nhanh trên Windows (từ mã nguồn)
dong_goi_exe.bat         Đóng gói EXE bằng PyInstaller
assets/                  Biểu tượng app
vat_app/
  __init__.py            Tên và số phiên bản (dùng cho kiểm tra cập nhật sau này)
  calculations.py        Công thức của hai công cụ (tách khỏi giao diện)
  money.py               Đọc số tiền/thuế suất người dùng nhập, định dạng hiển thị và sao chép
  ui/
    main_window.py       Cửa sổ chính: thanh điều khiển, Ghim, Mini, chuyển màn hình
    home_page.py         Màn hình chọn công cụ
    balance_page.py      Công cụ Cân hóa đơn VAT
    prevat_page.py       Công cụ Tính giá trước VAT
    tool_page.py         Phần bố cục dùng chung của hai công cụ
    widgets.py           Ô nhập tiền, chọn thuế suất, nhãn tiền nhấp đúp để sao chép, thông báo nhỏ
    styles.py            Màu sắc, phông chữ
  updater.py             Kiểm tra bản mới trên GitHub Releases (chỉ khi bấm nút)
tests/                   Kiểm thử tự động
```

## 8. Offline và kiểm tra cập nhật

Mọi phép tính chạy offline, không gửi dữ liệu đi đâu, không lưu dữ liệu ra file.

Ở màn hình chọn công cụ có dòng **Phiên bản x.y.z · Kiểm tra cập nhật**. App chỉ kết nối Internet khi bấm nút này
(không tự kiểm tra khi mở, không tự tải hay cài gì). App hỏi GitHub bản phát hành mới nhất; nếu có bản mới sẽ hiện
đường dẫn mở trang tải.

Kho đang dùng: `bmabongden/cong-cu-hoa-don-vat` (khai báo ở `UPDATE_REPO` trong `vat_app/updater.py`).

Ra bản mới:

1. Tăng `APP_VERSION` trong `vat_app/__init__.py` (ví dụ `1.1.0`).
2. Chạy `dong_goi_exe.bat` để tạo EXE mới.
3. Tạo Release trên GitHub với tag `v1.1.0` và đính kèm `dist\CongCuHoaDonVAT.exe`.

Người dùng bản cũ bấm "Kiểm tra cập nhật" sẽ thấy bản mới và đường dẫn tải. Bước tự tải và cài bản mới có thể
bổ sung sau, dựa trên chính phần kiểm tra này.
