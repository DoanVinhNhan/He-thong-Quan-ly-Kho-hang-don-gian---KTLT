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
    current_threshold_search = query_params.get('threshold_value', ['10'])[0] 
    
    body_content = f"""
    <form method="GET" action="/report/low_stock">
        <div><label for="threshold_value">Ngưỡng tồn kho (nhỏ hơn hoặc bằng):</label>
        <input type="number" id="threshold_value" name="threshold_value" value="{current_threshold_search}" min="0" step="1" required></div>
        <input type="submit" name="search_submit" value="Xem báo cáo">
    </form><hr class="form-section-divider">"""

    if 'search_submit' in query_params:
        threshold_str = query_params.get('threshold_value', [''])[0]
        low_stock_products, low_stock_msg = logic_report.liet_ke_san_pham_sap_het_hang(threshold_str)
        body_content += f"<div class='message { 'success' if low_stock_products else 'info' }'>{low_stock_msg}</div>"
        
        if low_stock_products:
            table_rows = ""
            for p_item in low_stock_products:
                table_rows += f"""<tr><td>{p_item.get('sku','N/A')}</td><td>{p_item.get('name','N/A')}</td>
                    <td>{p_item.get('current_stock','N/A')}</td><td>{p_item.get('unit_of_measure','N/A')}</td>
                    <td>{tmpl.format_currency(p_item.get('price','N/A'))}</td></tr>"""
            body_content += f"""<h4>Kết quả: Sản phẩm có tồn kho &lt;= {threshold_str}</h4>
                <table><thead><tr><th>Mã SKU</th><th>Tên SP</th><th>Tồn kho</th><th>ĐVT</th><th>Đơn giá</th></tr></thead>
                <tbody>{table_rows}</tbody></table>"""
    else:
        body_content += "<p>Nhập ngưỡng tồn kho và nhấn 'Xem báo cáo'.</p>"
    
    return page_title, body_content

def handle_get_charts_report(handler, query_params):
    """Xử lý GET request cho trang thống kê và biểu đồ."""
    page_title = "Thống kê & Báo cáo"
    report_type = query_params.get('report_type', ['revenue_by_time'])[0]

    # Lấy các tham số filter thô từ URL
    group_by = query_params.get('group_by', ['day'])[0]
    raw_start_date = query_params.get('start_date', [''])[0]
    raw_end_date = query_params.get('end_date', [''])[0]
    selected_sku_flow = query_params.get('product_sku_flow', [''])[0]

    # --- SỬA LỖI: LOGIC MỚI CHO VIỆC XỬ LÝ NGÀY THÁNG ---
    start_date_for_query, end_date_for_query = raw_start_date, raw_end_date
    start_date_for_input, end_date_for_input = raw_start_date, raw_end_date

    # Nếu không có ngày nào được cung cấp, đặt mặc định là 30 ngày gần nhất
    if not raw_start_date or not raw_end_date:
        today = datetime.date.today()
        start_dt = today - datetime.timedelta(days=30)
        start_date_for_query = start_date_for_input = start_dt.isoformat()
        end_date_for_query = end_date_for_input = today.isoformat()
    else:
        # Nếu đang xem theo tháng, chuyển đổi YYYY-MM thành ngày đầy đủ YYYY-MM-DD
        if group_by == 'month':
            if len(raw_start_date) == 7: # Định dạng YYYY-MM
                start_date_for_query = raw_start_date + '-01'
                start_date_for_input = raw_start_date # Giữ nguyên YYYY-MM cho input type=month
            
            if len(raw_end_date) == 7:
                end_date_for_input = raw_end_date
                try:
                    year, month = map(int, raw_end_date.split('-'))
                    next_month_first_day = (datetime.date(year, month, 1).replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
                    last_day_of_month = next_month_first_day - datetime.timedelta(days=1)
                    end_date_for_query = last_day_of_month.isoformat()
                except (ValueError, TypeError):
                    end_date_for_query = raw_end_date + '-28'
        
    # --- PHẦN 2: TẠO GIAO DIỆN HTML VÀ JAVASCRIPT ---
    # Chuyển giá trị hiển thị trên form thành YYYY-MM-DD nếu nó đang là YYYY-MM,
    # JavaScript sẽ xử lý việc thay đổi type và format lại.
    display_start_date = start_date_for_input + '-01' if len(start_date_for_input) == 7 else start_date_for_input
    display_end_date = end_date_for_input + '-01' if len(end_date_for_input) == 7 else end_date_for_input

    body_content = f"""
    <form method="GET" action="/reports_charts" style="margin-bottom:30px; padding:15px; border:1px solid #ddd; border-radius:5px;">
        <h3>Tùy chọn báo cáo:</h3>
        <div style="margin-bottom:15px;">
            <label for="report_type_select">Loại báo cáo:</label>
            <select name="report_type" id="report_type_select" onchange="this.form.submit()">
                <option value="revenue_by_time" {'selected' if report_type == 'revenue_by_time' else ''}>Doanh thu theo thời gian</option>
                <option value="product_flow" {'selected' if report_type == 'product_flow' else ''}>Xuất/Nhập theo sản phẩm</option>
                <option value="revenue_by_product" {'selected' if report_type == 'revenue_by_product' else ''}>Doanh thu theo sản phẩm</option>
            </select>
        </div>
        <div style="display:flex; gap: 20px; flex-wrap:wrap; align-items:flex-end;">
            <div>
                <label for="start_date" id="start_date_label">Từ ngày:</label>
                <input type="date" id="start_date" name="start_date" value="{display_start_date}">
            </div>
            <div>
                <label for="end_date" id="end_date_label">Đến ngày:</label>
                <input type="date" id="end_date" name="end_date" value="{display_end_date}">
            </div>"""
    
    if report_type in ['revenue_by_time', 'product_flow']:
        body_content += f"""
            <div>
                <label for="group_by">Nhóm theo:</label>
                <select name="group_by" id="group_by">
                    <option value="day" {'selected' if group_by == 'day' else ''}>Ngày</option>
                    <option value="month" {'selected' if group_by == 'month' else ''}>Tháng</option>
                </select>
            </div>"""

    if report_type == 'product_flow':
        products_db = db_get_all_products(sort_by='name')
        product_options = "<option value=''>-- Chọn sản phẩm --</option>"
        for p in products_db:
            product_options += f"<option value='{p['sku']}' {'selected' if p['sku'] == selected_sku_flow else ''}>{p['name']} ({p['sku']})</option>"
        body_content += f"""
            <div>
                <label for="product_sku_flow">Sản phẩm:</label>
                <select name="product_sku_flow" id="product_sku_flow">{product_options}</select>
            </div>"""
    
    body_content += f'<input type="submit" value="Xem" style="margin-top:20px;"></div></form>'

    # --- JAVASCRIPT CHO GIAO DIỆN ĐỘNG ---
    body_content += """
    <script>
        const groupBySelect = document.getElementById('group_by');
        const startDateInput = document.getElementById('start_date');
        const endDateInput = document.getElementById('end_date');
        const startDateLabel = document.getElementById('start_date_label');
        const endDateLabel = document.getElementById('end_date_label');

        function updateDateInputs() {
            const originalStartDate = startDateInput.value;
            const originalEndDate = endDateInput.value;

            if (groupBySelect && groupBySelect.value === 'month') {
                startDateInput.type = 'month';
                endDateInput.type = 'month';
                startDateLabel.textContent = 'Từ tháng:';
                endDateLabel.textContent = 'Đến tháng:';
                if (originalStartDate) startDateInput.value = originalStartDate.substring(0, 7);
                if (originalEndDate) endDateInput.value = originalEndDate.substring(0, 7);
            } else {
                startDateInput.type = 'date';
                endDateInput.type = 'date';
                startDateLabel.textContent = 'Từ ngày:';
                endDateLabel.textContent = 'Đến ngày:';
                if (originalStartDate && originalStartDate.length === 7) startDateInput.value = originalStartDate + '-01';
                if (originalEndDate && originalEndDate.length === 7) endDateInput.value = originalEndDate + '-01';
            }
        }
        
        function validateDateRange() {
            if (startDateInput.value) {
                endDateInput.min = startDateInput.value;
            }
            if (endDateInput.value) {
                startDateInput.max = endDateInput.value;
            }
        }

        if (groupBySelect) {
            groupBySelect.addEventListener('change', updateDateInputs);
        }
        startDateInput.addEventListener('change', validateDateRange);
        endDateInput.addEventListener('change', validateDateRange);

        // Chạy ngay khi trang tải xong để đảm bảo giao diện đúng
        document.addEventListener('DOMContentLoaded', () => {
            if (groupBySelect) {
                updateDateInputs();
            }
            validateDateRange();
        });
    </script>
    <hr>
    """
    
    # --- PHẦN 3: LOGIC VẼ BIỂU ĐỒ ---
    if not chart.MATPLOTLIB_AVAILABLE:
        body_content += "<p class='error'>Chức năng biểu đồ không khả dụng: Thư viện 'matplotlib' chưa được cài đặt.</p>"
        return page_title, body_content
    
    if report_type == 'revenue_by_time':
        body_content += "<h3>Biểu đồ Doanh thu xuất kho theo thời gian</h3>"
        revenue_data_from_db = db_report.db_get_revenue_data(start_date_for_query, end_date_for_query, group_by)
        revenue_map = {row['period']: row['revenue'] for row in revenue_data_from_db}
        
        periods = []
        revenues = []

        try:
            start_dt = datetime.datetime.strptime(start_date_for_query, '%Y-%m-%d').date()
            end_dt = datetime.datetime.strptime(end_date_for_query, '%Y-%m-%d').date()

            if group_by == 'day':
                current_dt = start_dt
                while current_dt <= end_dt:
                    period_str = current_dt.strftime('%Y-%m-%d')
                    periods.append(period_str)
                    revenues.append(revenue_map.get(period_str, 0))
                    current_dt += datetime.timedelta(days=1)
            else: # group_by == 'month'
                unique_months = []
                current_dt = start_dt
                while current_dt <= end_dt:
                    month_str = current_dt.strftime('%Y-%m')
                    if not unique_months or unique_months[-1] != month_str:
                        unique_months.append(month_str)
                    
                    # Tăng tháng lên 1 cách an toàn
                    next_month_first_day = (current_dt.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
                    current_dt = next_month_first_day
                
                periods = unique_months
                revenues = [revenue_map.get(p, 0) for p in periods]

        except (ValueError, TypeError):
             # Fallback nếu ngày tháng không hợp lệ
             sorted_keys = sorted(revenue_map.keys())
             periods = sorted_keys
             revenues = [revenue_map[k] for k in sorted_keys]

        if periods:
            chart_title = f"Doanh thu từ {start_date_for_input} đến {end_date_for_input}"
            img_base64, err_msg = chart.generate_chart_image_base64(periods, revenues, chart_title, "Doanh thu (VNĐ)", chart_type='bar')
            if img_base64: body_content += f'<img src="{img_base64}" alt="Biểu đồ doanh thu">'
            else: body_content += f"<p class='error'>Lỗi tạo biểu đồ: {err_msg}</p>"
        else:
            body_content += "<p>Không có dữ liệu doanh thu cho bộ lọc này.</p>"
    
    elif report_type == 'product_flow' and selected_sku_flow:
        product = db_get_product_by_sku(selected_sku_flow)
        body_content += f"<h3>Biểu đồ Xuất/Nhập cho: {product['name']}</h3>"
        flow_data = db_report.db_get_product_flow_data(product['id'], start_date_for_query, end_date_for_query, group_by)
        if flow_data:
            periods = sorted(list(set(row['period'] for row in flow_data)))
            in_q = {p:0 for p in periods}; out_q = {p:0 for p in periods}
            for row in flow_data:
                if row['transaction_type'] == 'IN': in_q[row['period']] = row['total_quantity']
                else: out_q[row['period']] = row['total_quantity']
            val_in = [in_q[p] for p in periods]; val_out = [out_q[p] for p in periods]
            chart_title = f"Xuất/Nhập cho {selected_sku_flow}"
            img_base64, err_msg = chart.generate_chart_image_base64(periods, val_in, chart_title, "Số lượng Nhập", chart_type='line', y_values2=val_out, label2='Số lượng Xuất')
            if img_base64: body_content += f'<img src="{img_base64}" alt="Biểu đồ xuất nhập">'
            else: body_content += f"<p class='error'>Lỗi tạo biểu đồ: {err_msg}</p>"
        else: body_content += "<p>Không có dữ liệu cho sản phẩm và bộ lọc này.</p>"
    
    elif report_type == 'revenue_by_product':
        body_content += "<h3>Thống kê Doanh thu theo Sản phẩm</h3>"
        revenue_by_prod_data = db_report.db_get_revenue_by_product(start_date_for_query, end_date_for_query)
        if revenue_by_prod_data:
            table_rows, product_names, revenues = "", [], []
            for item in revenue_by_prod_data:
                table_rows += f"<tr><td>{item['sku']}</td><td>{item['product_name']}</td><td>{item['total_quantity_sold']}</td><td>{tmpl.format_currency(item['total_revenue'])}</td></tr>"
                product_names.append(f"{item['product_name']}")
                revenues.append(item['total_revenue'])
            body_content += f"<table><thead><tr><th>SKU</th><th>Tên Sản phẩm</th><th>Tổng SL Bán</th><th>Tổng Doanh thu</th></tr></thead><tbody>{table_rows}</tbody></table>"
            
            # Biểu đồ
            max_items = 15
            chart_title = f"Top {max_items} Sản phẩm theo Doanh thu"
            img_base64, err_msg = chart.generate_chart_image_base64(product_names[:max_items], revenues[:max_items], chart_title, "Doanh thu (VNĐ)", x_labels_override=product_names[:max_items], chart_type='bar')
            if img_base64: body_content += f'<h3>Biểu đồ Top Sản phẩm</h3><img src="{img_base64}" alt="Biểu đồ doanh thu theo sản phẩm">'
            else: body_content += f"<p class='error'>Lỗi tạo biểu đồ: {err_msg}</p>"
        else: body_content += "<p>Không có dữ liệu doanh thu theo sản phẩm cho bộ lọc này.</p>"

    return page_title, body_content
