# /src/backend/transaction/handlers.py
import datetime
import os
from . import database as db_transaction
from . import logic as logic_transaction
from ..product.database import db_get_all_products, db_get_product_by_sku
from ..common import html_templates as tmpl
from ..common import quan_ly_du_lieu as qldl

def handle_get_stock_in_out(handler, path):
    """
    Xử lý GET request cho trang nhập và xuất kho. 
    Tạo form cho phép người dùng nhập thủ công hoặc tải lên file CSV.
    """
    is_stock_in = path == '/stock/in'
    page_title = "Tạo Phiếu Nhập kho" if is_stock_in else "Tạo Phiếu Xuất kho"
    
    products_db = db_get_all_products(sort_by='name')
    options = "<option value=''>-- Chọn sản phẩm --</option>"
    if products_db:
        for p in products_db:
            options += f"<option value=\"{p['sku']}\">{p['name']} (SKU: {p['sku']}) - Tồn: {p.get('current_stock',0)} - Giá: {tmpl.format_currency(p.get('price',0))}</option>"
            
    body_content = f"""<h3>Giao dịch một sản phẩm (Thủ công):</h3>
    <form method="POST" action="{path}">
        <input type="hidden" name="form_action_type" value="manual_stock_transaction">
        <div><label for="sku_sp">Sản phẩm:</label><select id="sku_sp" name="sku_sp" required>{options}</select></div>
        <div><label for="soLuong">Số lượng (nguyên):</label><input type="number" id="soLuong" name="soLuong" min="1" step="1" required></div>
        <div><label for="ghiChu">Ghi chú:</label><textarea id="ghiChu" name="ghiChu" rows="3"></textarea></div>
        <input type="submit" value="{'Xác nhận Nhập' if is_stock_in else 'Xác nhận Xuất'}">
    </form><hr class="form-section-divider">
    <h3>Giao dịch hàng loạt từ file CSV:</h3>
    <p>File CSV: <strong>maSP, soLuong</strong>. Tùy chọn: <strong>donGia, ghiChu</strong>.</p>
    <form method="POST" action="{path}" enctype="multipart/form-data">
         <input type="hidden" name="form_action_type" value="csv_stock_transaction">
        <div><label for="csvfile">Chọn file CSV:</label><input type="file" id="csvfile" name="csvfile" accept=".csv"></div>
        <input type="submit" value="{'Tải lên và Nhập từ CSV' if is_stock_in else 'Tải lên và Xuất từ CSV'}">
    </form>"""
    return page_title, body_content

def handle_get_transactions_history(handler, query_params):
    """Xử lý GET request cho trang lịch sử giao dịch."""
    page_title = "Lịch sử Giao dịch"
    default_end_date = datetime.date.today()
    default_start_date = default_end_date - datetime.timedelta(days=30)
    start_date_filter = query_params.get('start_date', [default_start_date.isoformat()])[0]
    end_date_filter = query_params.get('end_date', [default_end_date.isoformat()])[0]
    
    transactions_data = db_transaction.db_get_transactions_by_date_range(start_date_filter, end_date_filter)
    
    table_rows = ""
    if transactions_data:
        for t in transactions_data:
            table_rows += f"""<tr><td>{t['timestamp']}</td><td>{t['product_sku']}</td>
                <td>{t['product_name']}</td><td>{t['transaction_type']}</td>
                <td>{t.get('quantity',0)}</td><td>{tmpl.format_currency(t.get('unit_price', 0))}</td>
                <td>{tmpl.format_currency(t.get('total_amount', 0))}</td>
                <td>{t.get('notes','')}</td><td>{t.get('user','')}</td></tr>"""
    else:
        table_rows = "<tr><td colspan='9'>Không có giao dịch nào trong khoảng thời gian đã chọn.</td></tr>"
    
    body_content = f"""
    <form method="GET" action="/transactions" style="display: flex; align-items: flex-end; gap: 10px; flex-wrap:wrap; margin-bottom:20px;">
        <div><label for="start_date">Từ ngày:</label><input type="date" id="start_date" name="start_date" value="{start_date_filter}"></div>
        <div><label for="end_date">Đến ngày:</label><input type="date" id="end_date" name="end_date" value="{end_date_filter}"></div>
        <input type="submit" value="Lọc" style="margin-top:0; height: 46px;">
        <a href="/transactions?start_date=&end_date=" class="btn btn-secondary" style='margin-top:0; height: 46px; line-height: 22px;'>Xem 30 ngày gần nhất</a>
    </form>
    <table><thead><tr><th>Thời gian</th><th>Mã SKU</th><th>Tên SP</th><th>Loại GD</th><th>Số lượng</th><th>Đơn giá</th><th>Tổng tiền</th><th>Ghi chú</th><th>User</th></tr></thead>
    <tbody>{table_rows}</tbody></table>"""
    return page_title, body_content

def handle_post_stock_transaction(handler, path, fields):
    """Xử lý POST request cho việc nhập và xuất kho."""
    transaction_type = 'IN' if path == '/stock/in' else 'OUT'
    form_action_type = handler.get_form_value(fields, 'form_action_type')
    message = ""
    msg_type = "error"

    if form_action_type == 'manual_stock_transaction':
        sku_sp = handler.get_form_value(fields, 'sku_sp') 
        so_luong_str = handler.get_form_value(fields, 'soLuong')
        ghi_chu = handler.get_form_value(fields, 'ghiChu')
        
        if sku_sp and so_luong_str:
            product = db_get_product_by_sku(sku_sp)
            if product:
                unit_price = product.get('price', 0)
                success, msg_result = db_transaction.db_add_stock_transaction(
                    product['id'], transaction_type, so_luong_str, str(unit_price), ghi_chu, user="web_manual"
                )
                message, msg_type = msg_result, "success" if success else "error"
            else:
                message = f"Lỗi: Không tìm thấy sản phẩm với SKU '{sku_sp}'."
        else:
            message = "Vui lòng chọn sản phẩm và nhập số lượng."

    elif form_action_type == 'csv_stock_transaction':
        file_content_bytes = handler.get_form_value(fields, 'csvfile')
        if file_content_bytes:
            temp_file_path = f"temp_uploaded_{datetime.datetime.now().timestamp()}.csv"
            try:
                with open(temp_file_path, 'wb') as f:
                    f.write(file_content_bytes)
                
                if transaction_type == 'IN':
                    processed_ok, result_msg = logic_transaction.nhap_kho_tu_file_csv(temp_file_path)
                else: # OUT
                    processed_ok, result_msg = logic_transaction.xuat_kho_tu_file_csv(temp_file_path)
                
                message = result_msg.replace('\n', '<br>')
                msg_type = "success" if processed_ok else "error"
            except Exception as e:
                message = f"Lỗi nghiêm trọng khi xử lý file: {e}"
                qldl.ghi_log_loi(f"Xử lý file CSV thất bại ({path}): {e}")
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        else:
            message = "Không có file CSV nào được tải lên."
    else:
        message = "Hành động không xác định."

    handler.send_redirect(path, message, msg_type)
