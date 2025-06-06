# /src/backend/report/database.py
# Chứa các hàm truy vấn cơ sở dữ liệu dành riêng cho việc tạo báo cáo.
# Các hàm này thường phức tạp hơn, liên quan đến tổng hợp (aggregation),
# nhóm (grouping) và nối (joining) các bảng.

from ..common.database_base import get_db_connection

def db_get_low_stock_products(threshold): 
    """Lấy danh sách sản phẩm có tồn kho thấp hơn hoặc bằng ngưỡng cho trước."""
    conn = get_db_connection()
    try:
        # Đảm bảo ngưỡng là một số nguyên hợp lệ
        valid_threshold = int(threshold)
        if valid_threshold < 0: return []
    except (ValueError, TypeError): 
        return []
    
    query = "SELECT id, name, sku, unit_of_measure, current_stock, price, description FROM products WHERE current_stock <= ? ORDER BY current_stock ASC, name ASC"
    products = [dict(row) for row in conn.execute(query, (valid_threshold,)).fetchall()]
    conn.close()
    return products

def db_get_revenue_data(start_date_str, end_date_str, group_by='day'):
    """Lấy dữ liệu doanh thu (từ các giao dịch 'OUT') theo thời gian."""
    conn = get_db_connection()
    params = []
    # Xây dựng câu lệnh WHERE một cách linh hoạt dựa trên các bộ lọc được cung cấp
    query_conditions = ["transaction_type = 'OUT'"]
    if start_date_str:
        query_conditions.append("strftime('%Y-%m-%d', timestamp) >= ?")
        params.append(start_date_str)
    if end_date_str:
        query_conditions.append("strftime('%Y-%m-%d', timestamp) <= ?")
        params.append(end_date_str)
    
    where_clause = " AND ".join(query_conditions)
    # Định dạng ngày để nhóm (GROUP BY) theo ngày hoặc tháng
    date_format_sqlite = '%Y-%m-%d' if group_by == 'day' else '%Y-%m'
    query = f"SELECT strftime('{date_format_sqlite}', timestamp) as period, SUM(total_amount) as revenue FROM stock_transactions WHERE {where_clause} GROUP BY period ORDER BY period ASC"
    
    data = [dict(row) for row in conn.execute(query, tuple(params)).fetchall()]
    conn.close()
    return data

def db_get_product_flow_data(product_id, start_date_str, end_date_str, group_by='day'):
    """Lấy dữ liệu nhập/xuất của một sản phẩm cụ thể theo thời gian."""
    conn = get_db_connection()
    params = [product_id]
    query_conditions = ["st.product_id = ?"]
    if start_date_str:
        query_conditions.append("strftime('%Y-%m-%d', st.timestamp) >= ?")
        params.append(start_date_str)
    if end_date_str:
        query_conditions.append("strftime('%Y-%m-%d', st.timestamp) <= ?")
        params.append(end_date_str)
        
    where_clause = " AND ".join(query_conditions)
    date_format_sqlite = '%Y-%m-%d' if group_by == 'day' else '%Y-%m'
    query = f"SELECT strftime('{date_format_sqlite}', st.timestamp) as period, st.transaction_type, SUM(st.quantity) as total_quantity FROM stock_transactions st WHERE {where_clause} GROUP BY period, st.transaction_type ORDER BY period ASC"
    
    data = [dict(row) for row in conn.execute(query, tuple(params)).fetchall()]
    conn.close()
    return data

def db_get_revenue_by_product(start_date_str, end_date_str):
    """Lấy tổng doanh thu theo từng sản phẩm trong khoảng thời gian."""
    conn = get_db_connection()
    params = []
    query_conditions = ["st.transaction_type = 'OUT'"]

    if start_date_str:
        query_conditions.append("strftime('%Y-%m-%d', st.timestamp) >= ?")
        params.append(start_date_str)
    if end_date_str:
        query_conditions.append("strftime('%Y-%m-%d', st.timestamp) <= ?")
        params.append(end_date_str)
    
    where_clause = " AND ".join(query_conditions)
    
    query = f"""
        SELECT p.sku, p.name as product_name, SUM(st.total_amount) as total_revenue, SUM(st.quantity) as total_quantity_sold
        FROM stock_transactions st
        JOIN products p ON st.product_id = p.id
        WHERE {where_clause}
        GROUP BY p.id, p.sku, p.name
        HAVING SUM(st.total_amount) > 0
        ORDER BY total_revenue DESC
    """
    data = [dict(row) for row in conn.execute(query, tuple(params)).fetchall()]
    conn.close()
    return data

def db_get_dashboard_stats():
    """Lấy các thống kê chính cho trang chủ (dashboard)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    stats = {
        'total_products': 0,
        'total_in_transactions': 0,
        'total_out_transactions': 0,
        'current_warehouse_value': 0,
        'total_revenue': 0
    }
    try:
        # 1. Tổng số sản phẩm
        cursor.execute("SELECT COUNT(id) FROM products")
        stats['total_products'] = cursor.fetchone()[0]

        # 2. Tổng số giao dịch Nhập
        cursor.execute("SELECT COUNT(id) FROM stock_transactions WHERE transaction_type = 'IN'")
        stats['total_in_transactions'] = cursor.fetchone()[0]

        # 3. Tổng số giao dịch Xuất
        cursor.execute("SELECT COUNT(id) FROM stock_transactions WHERE transaction_type = 'OUT'")
        stats['total_out_transactions'] = cursor.fetchone()[0]

        # 4. Giá trị kho hiện tại (Tổng của (tồn kho * đơn giá) cho mỗi sản phẩm)
        cursor.execute("SELECT SUM(current_stock * price) FROM products")
        value = cursor.fetchone()[0]
        stats['current_warehouse_value'] = value if value is not None else 0

        # 5. Tổng doanh thu (Tổng tiền của các giao dịch xuất)
        cursor.execute("SELECT SUM(total_amount) FROM stock_transactions WHERE transaction_type = 'OUT'")
        revenue = cursor.fetchone()[0]
        stats['total_revenue'] = revenue if revenue is not None else 0

    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu thống kê cho trang chủ: {e}")
    finally:
        conn.close()

    return stats
