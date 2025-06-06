# /src/backend/report/handlers.py
# Chứa các hàm xử lý request cho các trang báo cáo và thống kê.

import datetime
from . import logic as logic_report
from . import database as db_report
from ..product.database import db_get_all_products, db_get_product_by_sku
from ..common import html_templates as tmpl
from ..common import chart_utils as chart

def handle_get_low_stock_report(handler, query_params):
    """Xử lý GET request cho báo cáo sản phẩm sắp hết hàng."""
    page_title = "Báo cáo Sản phẩm Sắp hết hàng"
    # Lấy ngưỡng tìm kiếm từ URL, mặc định là 10.
    current_threshold_search = query_params.get('threshold_value', ['10'])[0] 
    
    # Tạo form để người dùng nhập ngưỡng.
    body_content = f"""
    <form method="GET" action="/report/low_stock">
        <div><label for="threshold_value">Ngưỡng tồn kho (nhỏ hơn hoặc bằng):</label>
        <input type="number" id="threshold_value" name="threshold_value" value="{current_threshold_search}" min="0" step="1" required></div>
        <input type="submit" name="search_submit" value="Xem báo cáo">
    </form><hr>"""

    # Chỉ xử lý và hiển thị kết quả khi người dùng nhấn nút "Xem báo cáo".
    if 'search_submit' in query_params:
        threshold_str = query_params.get('threshold_value', [''])[0]
        # Gọi lớp logic để lấy dữ liệu.
        low_stock_products, low_stock_msg = logic_report.liet_ke_san_pham_sap_het_hang(threshold_str)
        body_content += f"<div class='message { 'success' if low_stock_products else 'info' }'>{low_stock_msg}</div>"
        
        # Nếu có sản phẩm, hiển thị dưới dạng bảng.
        if low_stock_products:
            table_rows = ""
            for p_item in low_stock_products:
                table_rows += f"""<tr><td>{p_item.get('sku','N/A')}</td><td>{p_item.get('name','N/A')}</td>
                    <td>{p_item.get('current_stock','N/A')}</td>
                    <td>{tmpl.format_currency(p_item.get('price','N/A'))}</td></tr>"""
            body_content += f"""<h4>Kết quả:</h4>
                <table><thead><tr><th>Mã SKU</th><th>Tên SP</th><th>Tồn kho</th><th>Đơn giá</th></tr></thead>
                <tbody>{table_rows}</tbody></table>"""
    else:
        body_content += "<p>Nhập ngưỡng tồn kho và nhấn 'Xem báo cáo'.</p>"
    
    return page_title, body_content

def handle_get_charts_report(handler, query_params):
    """Xử lý GET request cho trang thống kê và biểu đồ."""
    page_title = "Thống kê & Báo cáo"
    # Lấy các tham số lọc từ URL
    report_type = query_params.get('report_type', ['revenue_by_time'])[0]
    default_end_date = datetime.date.today()
    default_start_date = default_end_date - datetime.timedelta(days=30)
    start_date_filter = query_params.get('start_date', [default_start_date.isoformat()])[0]
    end_date_filter = query_params.get('end_date', [default_end_date.isoformat()])[0]
    group_by = query_params.get('group_by', ['day'])[0]
    selected_sku_flow = query_params.get('product_sku_flow', [''])[0]

    # Tạo form bộ lọc
    body_content = f"""
    <form method="GET" action="/reports_charts">
        <h3>Tùy chọn báo cáo:</h3>
        <select name="report_type" onchange="this.form.submit()">
            <option value="revenue_by_time" {'selected' if report_type == 'revenue_by_time' else ''}>Doanh thu theo thời gian</option>
            <option value="product_flow" {'selected' if report_type == 'product_flow' else ''}>Xuất/Nhập theo sản phẩm</option>
            <option value="revenue_by_product" {'selected' if report_type == 'revenue_by_product' else ''}>Doanh thu theo sản phẩm</option>
        </select>
        <label>Từ:</label><input type="date" name="start_date" value="{start_date_filter}">
        <label>Đến:</label><input type="date" name="end_date" value="{end_date_filter}">"""
    
    # Thêm các bộ lọc phụ thuộc vào loại báo cáo
    if report_type in ['revenue_by_time', 'product_flow']:
        body_content += f"""<label>Nhóm theo:</label>
            <select name="group_by">
                <option value="day" {'selected' if group_by == 'day' else ''}>Ngày</option>
                <option value="month" {'selected' if group_by == 'month' else ''}>Tháng</option>
            </select>"""
    if report_type == 'product_flow':
        # ... (code tạo dropdown sản phẩm) ...
        pass
    
    body_content += '<input type="submit" value="Xem"></form><hr>'

    # Kiểm tra xem thư viện matplotlib có sẵn không
    if not chart.MATPLOTLIB_AVAILABLE:
        body_content += "<p class='error'>Chức năng biểu đồ không khả dụng: Thư viện 'matplotlib' chưa được cài đặt.</p>"
        return page_title, body_content
    
    # --- Logic tạo và hiển thị biểu đồ ---
    if report_type == 'revenue_by_time':
        body_content += "<h3>Biểu đồ Doanh thu theo thời gian</h3>"
        revenue_data = db_report.db_get_revenue_data(start_date_filter, end_date_filter, group_by)
        if revenue_data:
            # Chuẩn bị dữ liệu và gọi hàm vẽ biểu đồ
            periods = [row['period'] for row in revenue_data]
            revenues = [row['revenue'] for row in revenue_data]
            img_base64, err = chart.generate_chart_image_base64(periods, revenues, "Doanh thu", "VNĐ")
            if img_base64: body_content += f'<img src="{img_base64}">'
            else: body_content += f"<p class='error'>Lỗi tạo biểu đồ: {err}</p>"
        else: body_content += "<p>Không có dữ liệu.</p>"
    
    # ... (code cho các loại biểu đồ khác) ...
    
    return page_title, body_content
