# /src/backend/transaction/database.py
import sqlite3
import datetime
from ..common.database_base import get_db_connection

def init_db(db_name):
    conn = get_db_connection(db_name)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL,
        transaction_type TEXT NOT NULL, quantity INTEGER NOT NULL,
        unit_price INTEGER DEFAULT 0, total_amount INTEGER DEFAULT 0, 
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, notes TEXT, user TEXT, 
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')
    conn.commit()
    conn.close()

def db_add_stock_transaction(product_id, transaction_type, quantity_str, unit_price_at_transaction_str, notes="", user="system"):
    conn = get_db_connection()
    try:
        quantity = int(quantity_str)
        if quantity <= 0: return False, "Số lượng giao dịch phải là số nguyên dương."
        unit_price = int(unit_price_at_transaction_str)
        if unit_price < 0: return False, "Đơn giá không được âm."
    except ValueError:
        return False, "Số lượng hoặc đơn giá không hợp lệ (phải là số nguyên)."
    
    total_amount = quantity * unit_price
    
    try:
        conn.execute("BEGIN TRANSACTION")
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, sku, current_stock FROM products WHERE id = ?", (product_id,))
        product_row = cursor.fetchone()
        
        if not product_row:
            conn.rollback()
            return False, f"Sản phẩm ID {product_id} không tồn tại."
        
        product_name, product_sku, current_stock = product_row['name'], product_row['sku'], product_row['current_stock']
        new_stock = current_stock
        current_time = datetime.datetime.now()

        if transaction_type == 'IN':
            new_stock += quantity
        elif transaction_type == 'OUT':
            if current_stock < quantity:
                conn.rollback()
                return False, f"Không đủ '{product_name}' tồn kho (hiện có {current_stock}, cần {quantity})."
            new_stock -= quantity
        
        cursor.execute("UPDATE products SET current_stock = ?, updated_at = ? WHERE id = ?", (new_stock, current_time, product_id))
        cursor.execute('''
        INSERT INTO stock_transactions (product_id, transaction_type, quantity, unit_price, total_amount, notes, user, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (product_id, transaction_type, quantity, unit_price, total_amount, notes, user, current_time))
        
        conn.commit()
        return True, f"Giao dịch {transaction_type} cho '{product_name}' (SKU: {product_sku}) thành công. Tồn kho mới: {new_stock}"
    except Exception as e:
        conn.rollback()
        return False, f"Lỗi DB khi xử lý giao dịch: {e}"
    finally:
        conn.close()

def db_get_transactions_by_date_range(start_date_str, end_date_str):
    conn = get_db_connection()
    params = []
    query_conditions = []
    if start_date_str:
        query_conditions.append("strftime('%Y-%m-%d', st.timestamp) >= ?")
        params.append(start_date_str)
    if end_date_str:
        query_conditions.append("strftime('%Y-%m-%d', st.timestamp) <= ?")
        params.append(end_date_str)
    where_clause = " AND ".join(query_conditions) if query_conditions else "1=1"
    
    query = f'''
    SELECT st.id, p.name as product_name, p.sku as product_sku, st.transaction_type, 
           st.quantity, st.unit_price, st.total_amount, st.notes, st.user, 
           strftime('%Y-%m-%d %H:%M:%S', st.timestamp) as timestamp 
    FROM stock_transactions st JOIN products p ON st.product_id = p.id
    WHERE {where_clause} ORDER BY st.timestamp DESC'''
    
    transactions = [dict(row) for row in conn.execute(query, tuple(params)).fetchall()]
    conn.close()
    return transactions