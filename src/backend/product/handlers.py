# /src/backend/product/handlers.py
# File này chứa các hàm xử lý (handlers) cho các request HTTP liên quan đến sản phẩm.
# Các hàm này chịu trách nhiệm nhận request, gọi đến lớp logic/database để xử lý
# và tạo ra nội dung HTML để trả về cho người dùng.

from urllib.parse import quote_plus
from . import database as db_product
from . import logic as logic_product
from ..common import html_templates as tmpl

def handle_get_products_stock(handler, query_params):
    """
    Xử lý GET request cho trang danh sách sản phẩm và tồn kho.
    Hỗ trợ tìm kiếm và sắp xếp danh sách.

    Args:
        handler: Đối tượng request handler.
        query_params (dict): Dictionary chứa các tham số từ query string của URL.

    Returns:
        tuple: (str_tiêu_đề_trang, str_nội_dung_html)
    """
    page_title = "Quản lý Sản phẩm & Tồn kho"
    # Lấy các tham số tìm kiếm và sắp xếp từ URL
    search_term_query = query_params.get('search_term', [''])[0]
    sort_column = query_params.get('sort', ['name'])[0]
    sort_order = query_params.get('order', ['ASC'])[0]
    
    # Tạo form tìm kiếm
    body_content = f"""
    <h3>Tìm kiếm Sản phẩm</h3>
    <form method="GET" action="/products_stock">
        <label for="search_term">Nhập Mã SKU hoặc Tên sản phẩm:</label>
        <input type="text" id="search_term" name="search_term" value="{search_term_query}">
        <input type="submit" value="Tìm kiếm">
        {"<a href='/products_stock' class='btn btn-secondary'>Xem tất cả</a>" if search_term_query else ""}
    </form><hr>"""

    # Lấy dữ liệu sản phẩm dựa trên việc có tìm kiếm hay không
    if search_term_query:
        products_data = db_product.db_search_products_flexible(search_term_query)
        body_content += f"<h3>Kết quả tìm kiếm cho: '{search_term_query}'</h3>"
    else:
        products_data = db_product.db_get_all_products(sort_by=sort_column, order=sort_order)
        body_content += "<h3>Danh sách tất cả sản phẩm</h3>"

    # Hàm nội bộ để tạo link sắp xếp trên header của bảng
    def sort_link(column_key, display_name):
        new_order = 'DESC' if sort_column == column_key and sort_order == 'ASC' else 'ASC'
        arrow = ' &uarr;' if sort_column == column_key and sort_order == 'ASC' else ' &darr;' if sort_column == column_key else ''
        return f'<a href="/products_stock?sort={column_key}&order={new_order}">{display_name}{arrow}</a>'

    # Tạo các hàng của bảng sản phẩm
    table_rows = ""
    if products_data:
        for p in products_data:
            table_rows += f"""<tr><td>{p.get('sku','N/A')}</td><td>{p.get('name','N/A')}</td>
                <td>{p.get('unit_of_measure','N/A')}</td><td>{p.get('current_stock','N/A')}</td>
                <td>{tmpl.format_currency(p.get('price','N/A'))}</td><td>{p.get('description','')}</td></tr>"""
    else:
        table_rows = "<tr><td colspan='6'>Không tìm thấy sản phẩm nào.</td></tr>"
    
    # Hoàn thiện bảng và thêm nút "Thêm sản phẩm"
    body_content += f"""<p><a href="/products/add" class="btn">Thêm sản phẩm mới</a></p>
        <table><thead><tr><th>{sort_link('sku', 'Mã SKU')}</th><th>{sort_link('name', 'Tên SP')}</th>
            <th>{sort_link('unit_of_measure', 'ĐVT')}</th><th>{sort_link('current_stock', 'Tồn kho')}</th>
            <th>{sort_link('price', 'Đơn giá')}</th><th>Mô tả</th>
        </tr></thead><tbody>{table_rows}</tbody></table>"""

    return page_title, body_content

def handle_get_add_product(handler):
    """Xử lý GET request cho trang thêm sản phẩm, hiển thị form nhập liệu."""
    page_title = "Thêm Sản phẩm Mới"
    body_content = """<p>Mã SKU sẽ được tạo tự động.</p>
    <form method="POST" action="/products/add">
        <div><label for="name">Tên sản phẩm:</label><input type="text" id="name" name="name" required maxlength="100"></div>
        <div><label for="unit_of_measure">ĐVT:</label><input type="text" id="unit_of_measure" name="unit_of_measure" value="cái" maxlength="20"></div>
        <div><label for="current_stock">Tồn ban đầu:</label><input type="number" id="current_stock" name="current_stock" value="0" min="0" step="1" required></div>
        <div><label for="price">Đơn giá (VNĐ):</label><input type="number" id="price" name="price" value="0" min="0" step="1" required></div>
        <div><label for="description">Mô tả:</label><textarea id="description" name="description" rows="3"></textarea></div>
        <input type="submit" value="Thêm sản phẩm">
    </form>"""
    return page_title, body_content

def handle_post_add_product(handler, fields):
    """
    Xử lý POST request để thêm sản phẩm mới vào hệ thống.
    Lấy dữ liệu từ form, gọi lớp logic để xử lý và sau đó chuyển hướng người dùng.
    """
    # Lấy dữ liệu từ form
    name = handler.get_form_value(fields, 'name')
    dvt = handler.get_form_value(fields, 'unit_of_measure', 'cái')
    so_luong_ton_str = handler.get_form_value(fields, 'current_stock', '0')
    don_gia_str = handler.get_form_value(fields, 'price', '0')
    description = handler.get_form_value(fields, 'description')
    
    # Tạo SKU duy nhất tự động
    generated_sku = db_product.generate_unique_sku()
    
    if not generated_sku:
        message = "Lỗi: Không thể tạo mã SKU duy nhất. Vui lòng thử lại."
        msg_type = "error"
    else:
        # Gọi hàm logic để thực hiện việc thêm sản phẩm
        success, msg_result = logic_product.them_san_pham_moi(
            generated_sku, name, dvt, so_luong_ton_str, don_gia_str, description
        )
        message = msg_result
        msg_type = "success" if success else "error"
    
    # Chuyển hướng người dùng đến trang danh sách (nếu thành công) hoặc về lại form (nếu lỗi)
    redirect_url = "/products_stock" if msg_type == "success" else "/products/add"
    handler.send_redirect(redirect_url, message, msg_type)
