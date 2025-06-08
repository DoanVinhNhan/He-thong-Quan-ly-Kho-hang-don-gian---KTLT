# /src/backend/request_router.py
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote_plus
import cgi
import os

# Import các module handlers của từng chức năng.
from .product import handlers as product_handlers
from .transaction import handlers as transaction_handlers
from .report import handlers as report_handlers

# Import các module dùng chung và database.
from .report import database as report_db 
from .common import html_templates as tmpl

STYLE_CSS_PATH = 'frontend/static/style.css'

class MiniVentoryRequestHandler(BaseHTTPRequestHandler):
    """
    Bộ xử lý request chính của server.
    Tiếp nhận tất cả request HTTP, phân tích và điều hướng (route)
    đến các handler tương ứng với từng chức năng (sản phẩm, giao dịch, báo cáo).
    """

    def get_form_value(self, data_dict, key, default=''):
        """
        Trích xuất một giá trị từ dữ liệu form đã được parse.
        Hàm này giúp lấy dữ liệu an toàn, xử lý trường hợp key không tồn tại
        và tự động giải mã (decode) dữ liệu bytes.

        Args:
            data_dict (dict): Dictionary chứa dữ liệu form.
            key (str): Key của trường dữ liệu cần lấy.
            default: Giá trị mặc định nếu key không tồn tại.

        Returns:
            Giá trị của trường form hoặc giá trị mặc định.
        """
        value_list = data_dict.get(key)
        if value_list:
            val = value_list[0]
            # Xử lý decode cho dữ liệu dạng bytes (trừ file upload).
            if isinstance(val, bytes) and key != 'csvfile': 
                try: return val.decode('utf-8')
                except UnicodeDecodeError: return val.decode('latin-1', errors='ignore') 
            return val
        return default

    def _send_response_html(self, html_content, status_code=200, headers=None):
        """Gửi phản hồi HTML về cho client."""
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def _serve_static_file(self, file_path, content_type):
        """Phục vụ các file tĩnh như CSS."""
        try:
            full_path = os.path.join(os.path.dirname(__file__), '..', file_path)
            with open(full_path, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_error(404, f"File Not Found: {file_path}")

    def send_redirect(self, location, message="", msg_type="info"):
        """Gửi phản hồi chuyển hướng (303) về client, kèm theo thông báo."""
        redirect_url = f"{location}?message={quote_plus(message)}&msg_type={msg_type}"
        self.send_response(303)
        self.send_header('Location', redirect_url)
        self.end_headers()

    def do_GET(self):
        """Xử lý các request GET."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        # Lấy thông báo từ query string (dùng cho việc hiển thị sau khi redirect).
        message = query_params.get('message', [''])[0]
        msg_type = query_params.get('msg_type', ['info'])[0]

        page_title = "MiniVentory"
        body_content = ""

        # Phục vụ file CSS.
        if path == f'/{STYLE_CSS_PATH}':
            self._serve_static_file(STYLE_CSS_PATH, 'text/css')
            return

        # --- ROUTING ĐẾN CÁC HANDLERS ---
        if path == '/':
            page_title = "Trang chủ"
            stats = report_db.db_get_dashboard_stats()
            body_content = f"""
            <h3>Chào mừng bạn!</h3>
            <p>Dưới đây là tổng quan nhanh về hệ thống kho hàng của bạn:</p>
            <div class="dashboard-wrapper">
                <div class="dashboard-stats-row">
                    <div class="stat-card"><h4>Tổng số sản phẩm</h4><p>{stats['total_products']}</p></div>
                    <div class="stat-card"><h4>Giao dịch Nhập kho</h4><p>{stats['total_in_transactions']}</p></div>
                    <div class="stat-card"><h4>Giao dịch Xuất kho</h4><p>{stats['total_out_transactions']}</p></div>
                </div>
                <div class="dashboard-stats-row">
                    <div class="stat-card"><h4>Giá trị tồn kho</h4><p>{tmpl.format_currency(stats['current_warehouse_value'])}</p></div>
                    <div class="stat-card"><h4>Tổng doanh thu</h4><p>{tmpl.format_currency(stats['total_revenue'])}</p></div>
                </div>
            </div>
            """
        elif path == '/products_stock':
            page_title, body_content = product_handlers.handle_get_products_stock(self, query_params)
        elif path == '/products/add':
            page_title, body_content = product_handlers.handle_get_add_product(self)
        
        elif path.startswith('/products/edit/'):
            try:
                product_id = int(path.split('/')[-1])
                page_title, body_content = product_handlers.handle_get_edit_product(self, product_id)
            except (IndexError, ValueError):
                self.send_error(404, "Page Not Found")
                return

        elif path.startswith('/products/delete/'):
            try:
                product_id = int(path.split('/')[-1])
                page_title, body_content = product_handlers.handle_get_delete_product_confirmation(self, product_id)
            except (IndexError, ValueError):
                self.send_error(404, "Page Not Found")
                return
                
        elif path == '/products/hidden':
            page_title, body_content = product_handlers.handle_get_hidden_products_list(self)
        
        elif path in ['/stock/in', '/stock/out']:
            page_title, body_content = transaction_handlers.handle_get_stock_in_out(self, path)
        elif path == '/transactions':
            page_title, body_content = transaction_handlers.handle_get_transactions_history(self, query_params)
        elif path == '/report/low_stock':
            page_title, body_content = report_handlers.handle_get_low_stock_report(self, query_params)
        elif path == '/reports_charts':
            page_title, body_content = report_handlers.handle_get_charts_report(self, query_params)
        else:
            self.send_error(404, "Page Not Found")
            return
            
        # Gói nội dung vào template HTML chung và gửi về client.
        html_page = tmpl.html_page_wrapper(page_title, body_content, message, msg_type)
        self._send_response_html(html_page)

    def do_POST(self):
        """Xử lý các request POST."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Phân tích (parse) dữ liệu form từ request body.
        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
        fields = {}
        if ctype == 'multipart/form-data':
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            fields = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            fields = parse_qs(post_data.decode('utf-8'))

        # --- ROUTING POST REQUESTS ---
        if path.startswith('/products/edit/'):
            try:
                product_id = int(path.split('/')[-1])
                product_handlers.handle_post_edit_product(self, product_id, fields)
            except (IndexError, ValueError):
                self.send_error(400, "Bad Request")
                
        elif path.startswith('/products/delete/'):
            try:
                product_id = int(path.split('/')[-1])
                product_handlers.handle_post_delete_product(self, product_id)
            except (IndexError, ValueError):
                self.send_error(400, "Bad Request")
                
        elif path.startswith('/products/restore/'):
            try:
                product_id = int(path.split('/')[-1])
                product_handlers.handle_post_restore_product(self, product_id)
            except (IndexError, ValueError):
                self.send_error(400, "Bad Request")

        elif path == '/products/add':
            product_handlers.handle_post_add_product(self, fields)
            
        elif path in ['/stock/in', '/stock/out']:
            transaction_handlers.handle_post_stock_transaction(self, path, fields)
            
        else:
            self.send_error(405, "Method Not Allowed")
