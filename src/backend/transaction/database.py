# /src/backend/transaction/database.py
import sqlite3
import datetime
from ..common.database_base import get_db_connection

def init_db(db_name):
    """Tạo bảng 'stock_transactions' nếu nó chưa tồn tại."""
    conn = get_db_connection(db_name)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL,
        transaction_type TEXT NOT NULL, quantity INTEGER NOT NULL,
        unit_price INTEGER DEFAULT 0, total_amount INTEGER DEFAULT 0, 
        timestamp TIMESTAMP, notes TEXT, user TEXT, 
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')
    conn.commit()
    conn.close()

def db_add_stock_transaction(product_id, transaction_type, quantity_str, unit_price_str, notes="", user="system"):
    """
    Thêm một giao dịch kho (IN/OUT) và cập nhật tồn kho của sản phẩm tương ứng.
    Toàn bộ hoạt động được bọc trong một transaction của SQLite để đảm bảo tính toàn vẹn dữ liệu:
    hoặc tất cả cùng thành công, hoặc không có gì thay đổi.

    Returns:
        tuple: (bool_thành_công, str_thông_báo)
    """
    conn = get_db_connection()
    try:
        # Xác thực và chuyển đổi kiểu dữ liệu đầu vào
        quantity = int(quantity_str)
        if quantity <= 0: return False, "Số lượng phải là số nguyên dương."
        unit_price = int(unit_price_str)
    except ValueError:
        return False, "Số lượng hoặc đơn giá không hợp lệ."
    
    total_amount = quantity * unit_price
    
    try:
        # Bắt đầu một DB transaction
        conn.execute("BEGIN TRANSACTION")
        cursor = conn.cursor()
        
        # Lấy thông tin sản phẩm hiện tại để kiểm tra và cập nhật
        cursor.execute("SELECT id, name, sku, current_stock FROM products WHERE id = ?", (product_id,))
        product_row = cursor.fetchone()
        
        if not product_row:
            conn.rollback() # Hoàn tác transaction
            return False, f"Sản phẩm ID {product_id} không tồn tại."
        
        product_name, current_stock = product_row['name'], product_row['current_stock']
        new_stock = current_stock

        # Tính toán tồn kho mới dựa trên loại giao dịch
        if transaction_type == 'IN':
            new_stock += quantity
        elif transaction_type == 'OUT':
            # Kiểm tra điều kiện xuất kho
            if current_stock < quantity:
                conn.rollback()
                return False, f"Không đủ '{product_name}' tồn kho (cần {quantity}, có {current_stock})."
            new_stock -= quantity
        
        # Cập nhật tồn kho mới cho sản phẩm
        cursor.execute("UPDATE products SET current_stock = ?, updated_at = ? WHERE id = ?", (new_stock, datetime.datetime.now(), product_id))
        
        # Chèn bản ghi giao dịch mới
        cursor.execute('''
        INSERT INTO stock_transactions (product_id, transaction_type, quantity, unit_price, total_amount, notes, user, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (product_id, transaction_type, quantity, unit_price, total_amount, notes, user, datetime.datetime.now()))
        
        conn.commit() # Chấp nhận tất cả thay đổi
        return True, f"Giao dịch {transaction_type} thành công. Tồn kho mới: {new_stock}"
    except Exception as e:
        conn.rollback() # Hoàn tác nếu có bất kỳ lỗi nào
        return False, f"Lỗi DB khi xử lý giao dịch: {e}"
    finally:
        conn.close()

def db_get_transactions_by_date_range(start_date_str, end_date_str):
    """Lấy danh sách các giao dịch trong một khoảng thời gian cho trước."""
    conn = get_db_connection()
    params = []
    query_conditions = []
    # Xây dựng câu lệnh WHERE một cách linh hoạt
    if start_date_str:
        query_conditions.append("strftime('%Y-%m-%d', st.timestamp) >= ?")
        params.append(start_date_str)
    if end_date_str:
        query_conditions.append("strftime('%Y-%m-%d', st.timestamp) <= ?")
        params.append(end_date_str)
    where_clause = " AND ".join(query_conditions) if query_conditions else "1=1"
    
    # Truy vấn dữ liệu, join với bảng products để lấy tên và SKU
    query = f'''
    SELECT st.id, p.name as product_name, p.sku as product_sku, st.transaction_type, 
           st.quantity, st.unit_price, st.total_amount, st.notes, st.user, 
           strftime('%Y-%m-%d %H:%M:%S', st.timestamp) as timestamp 
    FROM stock_transactions st JOIN products p ON st.product_id = p.id
    WHERE {where_clause} ORDER BY st.timestamp DESC'''
    
    transactions = [dict(row) for row in conn.execute(query, tuple(params)).fetchall()]
    conn.close()
    return transactions

def db_check_product_has_transactions(product_id):
    """Kiểm tra xem một sản phẩm có bất kỳ giao dịch nào không. Trả về True nếu có."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM stock_transactions WHERE product_id = ? LIMIT 1", (product_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists
