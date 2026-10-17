"""Màu sắc và stylesheet chung của ứng dụng."""

PRIMARY = "#1A63D6"
TEXT = "#1F2937"
MUTED = "#6B7280"
SUCCESS = "#15803D"
WARNING = "#B45309"

FONT_FAMILY = "Segoe UI"

STYLESHEET = f"""
QMainWindow, QWidget#central, QScrollArea, QWidget#page {{
    background: #F3F5F9;
}}
QWidget {{
    color: {TEXT};
    font-family: "{FONT_FAMILY}";
    font-size: 10pt;
}}

/* Thanh điều khiển phía trên */
QWidget#header {{
    background: #FFFFFF;
    border-bottom: 1px solid #E3E8EF;
}}
QLabel#headerTitle {{
    font-size: 11pt;
    font-weight: 600;
}}
QPushButton#headerButton {{
    background: #FFFFFF;
    border: 1px solid #D5DCE6;
    border-radius: 6px;
    padding: 4px 10px;
    min-height: 22px;
}}
QPushButton#headerButton:hover {{
    background: #EEF3FB;
}}
QPushButton#headerButton:checked {{
    background: {PRIMARY};
    border-color: {PRIMARY};
    color: #FFFFFF;
    font-weight: 600;
}}

/* Màn hình lựa chọn */
QPushButton#homeChoice {{
    background: #FFFFFF;
    border: 1px solid #D5DCE6;
    border-radius: 12px;
}}
QLabel#homeChoiceTitle {{
    font-size: 15pt;
    font-weight: 700;
    color: {PRIMARY};
    background: transparent;
}}
QLabel#homeChoiceDesc {{
    color: {MUTED};
    background: transparent;
}}
QPushButton#homeChoice:hover {{
    border: 2px solid {PRIMARY};
    background: #F5F9FF;
}}
QLabel#homeHint {{
    color: {MUTED};
}}

/* Thẻ nội dung */
QFrame#card {{
    background: #FFFFFF;
    border: 1px solid #E3E8EF;
    border-radius: 10px;
}}
QFrame#mainCard {{
    background: #F2F7FF;
    border: 1px solid #BFD5F7;
    border-radius: 10px;
}}
QLabel#cardTitle {{
    color: {MUTED};
    font-size: 9pt;
    font-weight: 700;
}}
QLabel#mainTitle {{
    color: {PRIMARY};
    font-size: 9pt;
    font-weight: 700;
}}
QLabel#fieldLabel {{
    font-weight: 600;
}}
QLabel#hint {{
    color: {MUTED};
    font-size: 9pt;
}}

/* Ô nhập */
QLineEdit {{
    background: #FFFFFF;
    border: 1px solid #C9D2DE;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 11pt;
    selection-background-color: {PRIMARY};
}}
QLineEdit:focus {{
    border: 2px solid {PRIMARY};
    padding: 4px 7px;
}}
QLineEdit[invalid="true"] {{
    border: 2px solid #E08A3C;
    padding: 4px 7px;
    background: #FFF8F0;
}}

/* Kết quả */
QLabel#mainValue {{
    color: {PRIMARY};
    font-size: 26pt;
    font-weight: 700;
}}
QLabel#mainValue[compact="true"] {{
    font-size: 20pt;
}}
QLabel#mainValue[empty="true"] {{
    color: #A7B1BF;
}}
QLabel#money {{
    font-weight: 600;
}}
QLabel#leftover {{
    color: {WARNING};
    font-weight: 700;
    background: #FFF6E8;
    border: 1px solid #F4D3A4;
    border-radius: 6px;
    padding: 4px 8px;
}}
QLabel#money:hover, QLabel#mainValue:hover {{
    background: rgba(26, 99, 214, 0.08);
    border-radius: 4px;
}}
QLabel#message[kind="waiting"] {{
    color: {MUTED};
}}
QLabel#message[kind="warning"] {{
    color: {WARNING};
    background: #FFF6E8;
    border: 1px solid #F4D3A4;
    border-radius: 6px;
    padding: 6px 8px;
}}
QLabel#message[kind="success"] {{
    color: {SUCCESS};
    font-weight: 600;
}}
QLabel#message[kind="info"] {{
    color: {TEXT};
}}
QPushButton#linkButton {{
    background: transparent;
    border: none;
    color: {PRIMARY};
    padding: 2px 0;
    text-align: left;
}}

/* Thông báo nhỏ "Đã sao chép" */
QLabel#toast {{
    background: rgba(31, 41, 55, 0.92);
    color: #FFFFFF;
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 600;
}}
"""
