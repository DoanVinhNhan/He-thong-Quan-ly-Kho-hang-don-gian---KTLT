# /src/backend/common/html_templates.py
# File này chứa các hàm để tạo các chuỗi HTML.
# Việc tách riêng code tạo HTML giúp cho logic chính của ứng dụng
# (trong các file handlers) trở nên gọn gàng và dễ đọc hơn.

import datetime
from urllib.parse import quote_plus 
import locale

STYLE_CSS_PATH = 'frontend/static/style.css'

# Cố gắng thiết lập locale cho tiếng Việt để định dạng số và tiền tệ.
# Nếu không thành công, sẽ fallback về locale mặc định của hệ thống.
try:
    locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        pass # Bỏ qua nếu không thể thiết lập locale

def format_currency(value):
    """
    Định dạng một giá trị số thành chuỗi tiền tệ Việt Nam (VNĐ)
    với dấu phân cách hàng nghìn.

    Args:
        value: Giá trị số cần định dạng.

    Returns:
        str: Chuỗi đã được định dạng (ví dụ: "1 234 500 VNĐ").
    """
    if value is None: return "0 VNĐ"
    try:
        num_int = int(value)
        # Sử dụng locale để định dạng nếu là tiếng Việt
        if locale.getlocale(locale.LC_NUMERIC)[0] and \
           ('vi_VN' in locale.getlocale(locale.LC_NUMERIC)[0] or \
            'Vietnamese' in locale.getlocale(locale.LC_NUMERIC)[0]):
            formatted_num = locale.format_string("%d", num_int, grouping=True)
            # Thay dấu chấm bằng dấu cách cho phù hợp hơn
            return f"{formatted_num.replace('.', ' ')} VNĐ" 
        else: # Fallback cho các hệ thống không có locale tiếng Việt
            s = str(num_int)
            groups = []
            while s and s[-1].isdigit():
                groups.append(s[-3:])
                s = s[:-3]
            return (s + ' '.join(reversed(groups))).strip() + " VNĐ"
    except (ValueError, TypeError):
        return "Không xác định"

def html_page_wrapper(title, body_content, message="", msg_type="info"):
    """
    Tạo cấu trúc HTML hoàn chỉnh cho một trang web.
    Hàm này nhận tiêu đề và nội dung chính, sau đó bọc chúng trong một
    template chung bao gồm header, navigation, và footer.

    Args:
        title (str): Tiêu đề của trang.
        body_content (str): Nội dung HTML chính của trang.
        message (str, optional): Thông báo để hiển thị (thường sau khi redirect).
        msg_type (str, optional): Loại thông báo ('success', 'error', 'info').

    Returns:
        str: Một chuỗi HTML hoàn chỉnh sẵn sàng để gửi về client.
    """
    # Khối HTML cho thanh điều hướng
    nav_links = """
        <nav>
            <ul>
                <li><a href="/">Trang chủ</a></li>
                <li><a href="/products_stock">Sản phẩm & Kho</a></li>
                <li><a href="/products/add">Thêm Sản phẩm</a></li>
                <li><a href="/stock/in">Tạo Nhập kho</a></li>
                <li><a href="/stock/out">Tạo Xuất kho</a></li>
                <li><a href="/transactions">Lịch sử Giao dịch</a></li>
                <li><a href="/report/low_stock">Báo cáo sắp hết hàng</a></li>
                <li><a href="/reports_charts">Thống kê & Báo cáo</a></li>
            </ul>
        </nav>
    """
    # Khối HTML cho việc hiển thị thông báo (nếu có)
    message_html = ""
    if message:
        # Xử lý các ký tự đặc biệt và xuống dòng để hiển thị đúng trên HTML
        escaped_message = message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        escaped_message = escaped_message.replace("\\n", "<br>")
        message_html = f"<div class='message {msg_type}'>{escaped_message}</div>"

    # Trả về chuỗi HTML hoàn chỉnh
    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - MiniVentory Web</title>
        <link rel="stylesheet" type="text/css" href="/{STYLE_CSS_PATH}">
    </head>
    <body>
        <header><h1>Hệ Thống Quản Lý Kho MiniVentory</h1></header>
        {nav_links}
        <main class="container">
            <h2>{title}</h2>
            {message_html}
            {body_content}
        </main>
        <footer><p>&copy; {datetime.datetime.now().year} MiniVentory.</p></footer>
    </body>
    </html>"""
