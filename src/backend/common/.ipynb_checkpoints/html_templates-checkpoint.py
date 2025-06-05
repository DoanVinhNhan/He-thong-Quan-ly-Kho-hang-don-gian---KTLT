# html_templates.py
import datetime
from urllib.parse import quote_plus 
import locale

STYLE_CSS_PATH = 'frontend/static/style.css'

try:
    locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        pass 

def format_currency(value):
    if value is None: return "0 VNĐ"
    try:
        num_int = int(value)
        if locale.getlocale(locale.LC_NUMERIC)[0] and \
           ('vi_VN' in locale.getlocale(locale.LC_NUMERIC)[0] or \
            'Vietnamese' in locale.getlocale(locale.LC_NUMERIC)[0]):
            formatted_num = locale.format_string("%d", num_int, grouping=True)
            return f"{formatted_num.replace('.', ' ')} VNĐ" 
        else: 
            s = str(num_int)
            groups = []
            while s and s[-1].isdigit():
                groups.append(s[-3:])
                s = s[:-3]
            return (s + ' '.join(reversed(groups))).strip() + " VNĐ"
    except (ValueError, TypeError):
        return "Không xác định"

def html_page_wrapper(title, body_content, message="", msg_type="info"):
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
    message_html = ""
    if message:
        escaped_message = message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        escaped_message = escaped_message.replace("\\n", "<br>")
        message_html = f"<div class='message {msg_type}'>{escaped_message}</div>"

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