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
    # Lấy các tham số tìm kiếm và sắp xếp từ URL
    page_title = "Quản lý Sản phẩm & Tồn kho"
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
            # Tạo HTML cho mỗi nút
            edit_button_html = f'<a href="/products/edit/{p["id"]}" class="btn btn-edit">Sửa</a>'
            # SỬA ĐỔI: Thêm class 'btn' cho nút Xóa để đảm bảo nó nằm cùng hàng
            delete_button_html = f'<a href="/products/delete/{p["id"]}" class="btn btn-delete">Ẩn</a>'
            
            # Gộp 2 nút vào chung một ô <td>
            table_rows += f"""<tr><td>{p.get('sku','N/A')}</td><td>{p.get('name','N/A')}</td>
                <td>{p.get('unit_of_measure','N/A')}</td><td>{p.get('current_stock','N/A')}</td>
                <td>{tmpl.format_currency(p.get('price','N/A'))}</td><td>{p.get('description','')}</td>
                <td class="cell-center">{edit_button_html} {delete_button_html}</td></tr>"""
    else:
        # Cập nhật colspan thành 7
        table_rows = "<tr><td colspan='7'>Không tìm thấy sản phẩm nào.</td></tr>"

    # Hoàn thiện bảng và thêm nút "Thêm sản phẩm"
    body_content += f"""
        <div style="margin-bottom: 20px; display: flex; gap: 10px;">
            <a href="/products/add" class="btn">Thêm sản phẩm mới</a>
            <a href="/products/hidden" class="btn btn-secondary">Xem danh sách đã ẩn</a>
        </div>
    """
    body_content +=f"""
        <table>
            <thead>
                <tr>
                    <th>{sort_link('sku', 'Mã SKU')}</th>
                    <th>{sort_link('name', 'Tên SP')}</th>
                    <th>{sort_link('unit_of_measure', 'ĐVT')}</th>
                    <th>{sort_link('current_stock', 'Tồn kho')}</th>
                    <th>{sort_link('price', 'Đơn giá')}</th>
                    <th>Mô tả</th>
                    <th style="width: 15%;">Hành động</th>
                </tr>
            </thead>
            <tbody>{table_rows}</tbody>
        </table>"""

    return page_title, body_content

def handle_get_add_product(handler):
    """Xử lý GET request cho trang thêm sản phẩm, hiển thị form nhập liệu."""
    page_title = "Thêm Sản phẩm Mới"
    body_content = """<p>Mã SKU sẽ được tạo tự động.</p>
    <form method="POST" action="/products/add">
        <div>
            <label for="name">Tên sản phẩm:</label>
            <input type="text" id="name" name="name" required maxlength="100">
            <div id="name-validation-msg" class="validation-message">Tên sản phẩm tối đa 100 ký tự.</div>
        </div>
        <div>
            <label for="unit_of_measure">ĐVT:</label>
            <input type="text" id="unit_of_measure" name="unit_of_measure" value="cái" maxlength="20">
            <div id="unit-validation-msg" class="validation-message">Đơn vị tính tối đa 20 ký tự.</div>
        </div>
        <div>
            <label for="current_stock">Tồn ban đầu:</label>
            <input type="number" id="current_stock" name="current_stock" value="0" min="0" step="1" required>
        </div>
        <div>
            <label for="price">Đơn giá (VNĐ):</label>
            <input type="number" id="price" name="price" value="0" min="0" step="1" required>
        </div>
        <div>
            <label for="description">Mô tả:</label>
            <textarea id="description" name="description" rows="3" maxlength="255"></textarea>
            <div id="description-validation-msg" class="validation-message">Mô tả tối đa 255 ký tự.</div>
        </div>
        <input type="submit" value="Thêm sản phẩm">
    </form>
    <script>
        function setupValidation(inputId, msgId) {
            const input = document.getElementById(inputId);
            const msg = document.getElementById(msgId);
            if (!input || !msg) return;

            // Lắng nghe sự kiện 'input' để kiểm tra mỗi khi người dùng nhập liệu
            input.addEventListener('input', () => {
                if (input.value.length >= input.maxLength) {
                    msg.style.display = 'block'; // Hiện thông báo khi đạt giới hạn
                } else {
                    msg.style.display = 'none'; // Ẩn thông báo nếu chưa đạt giới hạn
                }
            });
        }

        // Chờ DOM tải xong rồi mới gắn các sự kiện
        document.addEventListener('DOMContentLoaded', () => {
            setupValidation('name', 'name-validation-msg');
            setupValidation('unit_of_measure', 'unit-validation-msg');
            setupValidation('description', 'description-validation-msg');
        });
    </script>
    """
    return page_title, body_content

def handle_get_delete_product_confirmation(handler, product_id):
    """
    Xử lý GET request cho trang xác nhận xóa sản phẩm.
    Hàm này lấy thông tin sản phẩm từ DB và hiển thị một trang yêu cầu
    người dùng xác nhận trước khi thực hiện hành động xóa vĩnh viễn.

    Args:
        handler: Đối tượng request handler, dùng để gửi phản hồi Ẩn
        product_id (int): ID của sản phẩm cần xóa.

    Returns:
        tuple: (str_tiêu_đề_trang, str_nội_dung_html) để hiển thị cho người dùng.
               Trả về thông báo lỗi nếu không tìm thấy sản phẩm.
    """
    page_title = "Xác nhận Ẩn Sản phẩm"
    product = db_product.db_get_product_by_id(product_id)
    
    # Kiểm tra xem sản phẩm có tồn tại không
    if not product:
        # Trả về thông báo lỗi nếu không tìm thấy sản phẩm, tránh lỗi ở dưới
        return "Lỗi", "<p>Không tìm thấy sản phẩm.</p>"

    # Nội dung đã được cập nhật cho chức năng "ẩn" sản phẩm
    body_content = f"""
    <p class="warning-text">Bạn có chắc chắn muốn ẩn sản phẩm này không?</p>
    <div class='product-info-box'>
        <strong>Tên sản phẩm:</strong> {product['name']}<br>
        <strong>SKU:</strong> {product['sku']}<br>
        <strong>Tồn kho hiện tại:</strong> {product['current_stock']}
    </div>
    <p><strong>Lưu ý:</strong> Sản phẩm sẽ bị ẩn khỏi tất cả các danh sách và không thể thực hiện giao dịch mới. Lịch sử giao dịch cũ vẫn được giữ lại.</p>
    <form method="POST" action="/products/delete/{product_id}" style="display:inline-block; margin-right: 10px;">
        <input type="submit" value="Đồng ý Ẩn" class="btn-danger">
    </form>
    <a href="/products_stock" class="btn btn-secondary">Hủy bỏ</a>
    """
    return page_title, body_content

def handle_get_edit_product(handler, product_id):
    """
    Xử lý GET request cho trang sửa sản phẩm.
    Hàm này lấy thông tin sản phẩm từ DB dựa trên ID, sau đó hiển thị
    một form cho phép người dùng chỉnh sửa thông tin. Các ô nhập liệu
    sẽ được điền sẵn giá trị hiện tại của sản phẩm.

    Args:
        handler: Đối tượng request handler.
        product_id (int): ID của sản phẩm cần sửa.

    Returns:
        tuple: (str_tiêu_đề_trang, str_nội_dung_html) để hiển thị.
    """
    page_title = "Tùy chỉnh Sản phẩm"
    product = db_product.db_get_product_by_id(product_id)
    if not product:
        return "Lỗi", "<p>Không tìm thấy sản phẩm.</p>"

    body_content = f"""
    <form method="POST" action="/products/edit/{product_id}">
        <div>
            <label for="sku">Mã SKU (Không thể thay đổi):</label>
            <input type="text" id="sku" name="sku" value="{product['sku']}" readonly>
        </div>
        <div>
            <label for="current_stock">Tồn kho (Không thể thay đổi):</label>
            <input type="text" id="current_stock" name="current_stock" value="{product['current_stock']}" readonly>
        </div>
        <div>
            <label for="name">Tên sản phẩm:</label>
            <input type="text" id="name" name="name" value="{product['name']}" required maxlength="100">
            <div id="name-validation-msg" class="validation-message">Tên sản phẩm tối đa 100 ký tự.</div>
        </div>
        <div>
            <label for="unit_of_measure">ĐVT:</label>
            <input type="text" id="unit_of_measure" name="unit_of_measure" value="{product.get('unit_of_measure', 'cái')}" maxlength="20">
            <div id="unit-validation-msg" class="validation-message">Đơn vị tính tối đa 20 ký tự.</div>
        </div>
        <div>
            <label for="price">Đơn giá (VNĐ):</label>
            <input type="number" id="price" name="price" value="{product.get('price', 0)}" min="0" step="1" required>
        </div>
        <div>
            <label for="description">Mô tả:</label>
            <textarea id="description" name="description" rows="3" maxlength="255">{product.get('description', '')}</textarea>
            <div id="description-validation-msg" class="validation-message">Mô tả tối đa 255 ký tự.</div>
        </div>
        <input type="submit" value="Lưu thay đổi">
        <a href="/products_stock" class="btn btn-secondary">Hủy bỏ</a>
    </form>
    <script>
        function setupValidation(inputId, msgId) {{
            const input = document.getElementById(inputId);
            const msg = document.getElementById(msgId);
            if (!input || !msg) return;

            // Lắng nghe sự kiện 'input' để kiểm tra mỗi khi người dùng nhập liệu
            input.addEventListener('input', () => {{
                if (input.value.length >= input.maxLength) {{
                    msg.style.display = 'block'; 
                }} else {{
                    msg.style.display = 'none';
                }}
            }});
        }}

        // Chờ DOM tải xong rồi mới gắn các sự kiện
        document.addEventListener('DOMContentLoaded', () => {{
            setupValidation('name', 'name-validation-msg');
            setupValidation('unit_of_measure', 'unit-validation-msg');
            setupValidation('description', 'description-validation-msg');
        }});
    </script>
    """
    return page_title, body_content

def handle_post_edit_product(handler, product_id, fields):
    """
    Xử lý POST request để cập nhật thông tin sản phẩm sau khi người dùng
    nhấn "Lưu thay đổi" từ form sửa.
    Hàm này nhận dữ liệu từ form, gọi lớp logic để xử lý và sau đó
    chuyển hướng người dùng về trang danh sách sản phẩm.

    Args:
        handler: Đối tượng request handler, dùng để chuyển hướng.
        product_id (int): ID của sản phẩm đang được sửa.
        fields (dict): Dictionary chứa dữ liệu từ form đã được gửi lên.
    """
    
    name = handler.get_form_value(fields, 'name')
    unit_of_measure = handler.get_form_value(fields, 'unit_of_measure')
    price_str = handler.get_form_value(fields, 'price')
    description = handler.get_form_value(fields, 'description')
    
    success, message = logic_product.sua_san_pham(
        product_id, name, unit_of_measure, price_str, description
    )
    msg_type = "success" if success else "error"
    handler.send_redirect("/products_stock", message, msg_type)

def handle_post_delete_product(handler, product_id):
    """
    Xử lý POST request để thực hiện việc xóa sản phẩm.
    Hàm này gọi đến lớp logic để kiểm tra các quy tắc nghiệp vụ và xóa
    sản phẩm. Sau khi hoàn tất, nó chuyển hướng người dùng trở lại
    trang danh sách sản phẩm với một thông báo kết quả.

    Args:
        handler: Đối tượng request handler, dùng để chuyển hướng.
        product_id (int): ID của sản phẩm cần xóa.
    """
    success, message = logic_product.xoa_san_pham(product_id)
    msg_type = "success" if success else "error"
    handler.send_redirect("/products_stock", message, msg_type)

def handle_post_add_product(handler, fields):
    """
    Xử lý POST request để thêm sản phẩm mới vào hệ thống.
    Lấy dữ liệu từ form, gọi lớp logic để xử lý và sau đó chuyển hướng người dùng.
    """
    
    # Tạo SKU duy nhất tự động
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

# /src/backend/product/handlers.py

def handle_get_hidden_products_list(handler):
    """
    Xử lý GET request cho trang danh sách các sản phẩm đã bị ẩn.
    Hàm này lấy danh sách các sản phẩm có cờ is_deleted = 1 từ DB,
    sau đó tạo ra một trang HTML hiển thị chúng trong một bảng.
    Mỗi hàng trong bảng sẽ có nút "Hiển thị lại".

    Args:
        handler: Đối tượng request handler.

    Returns:
        tuple: (str_tiêu_đề_trang, str_nội_dung_html) để hiển thị cho người dùng.
    """
    page_title = "Danh sách Sản phẩm đã ẩn"
    products_data = db_product.db_get_all_hidden_products()
    
    table_rows = ""
    if products_data:
        for p in products_data:
            # Nút khôi phục sẽ là một form POST
            restore_button_html = f"""
            <form method="POST" action="/products/restore/{p['id']}" style="display:inline;">
                <button type="submit" class="btn btn-restore" title="Hiển thị lại sản phẩm này">Hiển thị lại</button>
            </form>
            """
            table_rows += f"""<tr><td>{p.get('sku','N/A')}</td><td>{p.get('name','N/A')}</td>
                <td>{p.get('unit_of_measure','N/A')}</td><td>{p.get('current_stock','N/A')}</td>
                <td>{tmpl.format_currency(p.get('price','N/A'))}</td><td>{p.get('description','')}</td>
                <td class="cell-center">{restore_button_html}</td></tr>"""
    else:
        table_rows = "<tr><td colspan='7'>Không có sản phẩm nào đang bị ẩn.</td></tr>"

    body_content = f"""
        <p><a href="/products_stock" class="btn btn-secondary">Quay lại danh sách chính</a></p>
        <table>
            <thead>
                <tr>
                    <th>Mã SKU</th><th>Tên SP</th><th>ĐVT</th><th>Tồn kho</th>
                    <th>Đơn giá</th><th>Mô tả</th><th>Hành động</th>
                </tr>
            </thead>
            <tbody>{table_rows}</tbody>
        </table>
    """
    return page_title, body_content
    
def handle_post_restore_product(handler, product_id):
    """
    Xử lý POST request để khôi phục (hiển thị lại) một sản phẩm đã bị ẩn.
    Hàm này nhận ID sản phẩm, gọi đến lớp logic để cập nhật trạng thái
    sản phẩm trong DB, và sau đó chuyển hướng người dùng về lại trang
    danh sách các sản phẩm đã ẩn kèm theo một thông báo kết quả.

    Args:
        handler: Đối tượng request handler, dùng để chuyển hướng.
        product_id (int): ID của sản phẩm cần khôi phục.
    """
    success, message = logic_product.khoi_phuc_san_pham(product_id)
    msg_type = "success" if success else "error"
    # Chuyển hướng về lại trang danh sách ẩn với thông báo
    handler.send_redirect("/products/hidden", message, msg_type)