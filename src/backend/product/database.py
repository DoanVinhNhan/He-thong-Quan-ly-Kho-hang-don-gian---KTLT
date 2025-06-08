# /src/backend/product/database.py
# File này chứa tất cả các hàm để tương tác trực tiếp với bảng 'products'
# trong cơ sở dữ liệu SQLite. Mỗi hàm thực hiện một thao tác CRUD
# (Create, Read, Update, Delete) hoặc truy vấn cụ thể.

import sqlite3
import uuid
import datetime
from ..common.database_base import get_db_connection

def init_db(db_name):
    """Tạo bảng 'products' trong database nếu nó chưa tồn tại."""
    conn = get_db_connection(db_name)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, sku TEXT NOT NULL UNIQUE,
        description TEXT, unit_of_measure TEXT DEFAULT 'cái',
        current_stock INTEGER DEFAULT 0, price INTEGER DEFAULT 0,
        is_deleted INTEGER DEFAULT 0, -- Thêm cột này
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def generate_unique_sku():
    """
    Tạo một mã SKU duy nhất theo định dạng 'SP-XXXXX'.
    Hàm sẽ thử tạo và kiểm tra với DB tối đa 10 lần để đảm bảo tính duy nhất.

    Returns:
        str: Một mã SKU duy nhất hoặc None nếu không thể tạo được.
    """
    for _ in range(10):
        random_hex = uuid.uuid4().hex[:5].upper() 
        sku = f"SP-{random_hex}"
        # Kiểm tra xem SKU đã tồn tại trong DB chưa
        if not db_get_product_by_sku(sku): 
            return sku
    return None 
        
def db_add_product(name, sku, description, unit_of_measure, current_stock=0, price=0):
    """
    Thêm một sản phẩm mới vào bảng 'products'.
    Thêm một giao dịch mới vào bảng 'stock_transactions' nếu tồn kho ban đầu lớn hơn 0

    Args:
        name (str): Tên sản phẩm.
        sku (str): Mã SKU duy nhất của sản phẩm.
        description (str): Mô tả chi tiết.
        unit_of_measure (str): Đơn vị tính.
        current_stock (int): Số lượng tồn kho ban đầu.
        price (int): Đơn giá của sản phẩm.

    Returns:
        tuple: (ID_sản_phẩm_mới, thông_báo_kết_quả)
               Trả về (None, thông_báo_lỗi) nếu có lỗi xảy ra.
    """
    conn = get_db_connection()
    try:
        conn.execute("BEGIN TRANSACTION")
        cursor = conn.cursor()
        current_time = datetime.datetime.now()

        # 1. Thêm sản phẩm vào bảng 'products'
        cursor.execute('''
        INSERT INTO products (name, sku, description, unit_of_measure, current_stock, price, created_at, updated_at, is_deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (name, sku, description, unit_of_measure, int(current_stock), int(price), current_time, current_time))
        
        product_id = cursor.lastrowid
        if not product_id:
            raise Exception("Không thể lấy ID sản phẩm vừa tạo.")

        # 2. Nếu có tồn kho ban đầu, tạo một giao dịch 'IN'
        if int(current_stock) > 0:
            total_amount = int(current_stock) * int(price)
            cursor.execute('''
            INSERT INTO stock_transactions (product_id, transaction_type, quantity, unit_price, total_amount, notes, user, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (product_id, 'IN', int(current_stock), int(price), total_amount, 'Tồn kho ban đầu khi tạo sản phẩm', 'system_init', current_time))
        
        conn.commit()
        return product_id, f"Thêm sản phẩm '{name}' (SKU: {sku}) thành công!"

    except sqlite3.IntegrityError:
        conn.rollback()
        return None, f"Lỗi: Mã SKU '{sku}' đã tồn tại."
    except ValueError:
        conn.rollback()
        return None, "Lỗi: Số lượng tồn hoặc đơn giá phải là số nguyên hợp lệ."
    except Exception as e:
        conn.rollback()
        return None, f"Lỗi khi thêm sản phẩm và giao dịch ban đầu: {e}"
    finally:
        conn.close()
        
def db_get_all_products(sort_by='name', order='ASC'):
    """
    Lấy tất cả sản phẩm từ cơ sở dữ liệu, có hỗ trợ sắp xếp.

    Args:
        sort_by (str): Tên cột để sắp xếp.
        order (str): 'ASC' (tăng dần) hoặc 'DESC' (giảm dần).

    Returns:
        list: Danh sách các sản phẩm, mỗi sản phẩm là một dictionary.
    """
    conn = get_db_connection()
    # Danh sách các cột hợp lệ để tránh lỗi SQL Injection
    valid_sort_columns = ['name', 'sku', 'current_stock', 'price', 'updated_at', 'id', 'unit_of_measure']
    if sort_by not in valid_sort_columns: sort_by = 'name'
    order_direction = 'ASC' if order.upper() == 'ASC' else 'DESC'
    
    query = f"SELECT id, name, sku, description, unit_of_measure, current_stock, price, updated_at FROM products WHERE is_deleted = 0 ORDER BY {sort_by} {order_direction}, id {order_direction}"
    products = [dict(row) for row in conn.execute(query).fetchall()]
    conn.close()
    return products

def db_get_product_by_id(product_id):
    """Lấy thông tin một sản phẩm dựa trên ID."""
    conn = get_db_connection()
    product_data = conn.execute("SELECT * FROM products WHERE id = ? AND is_deleted = 0", (product_id,)).fetchone()
    conn.close()
    return dict(product_data) if product_data else None

def db_get_product_by_sku(sku):
    """Lấy thông tin một sản phẩm dựa trên SKU."""
    conn = get_db_connection()
    product_data = conn.execute("SELECT * FROM products WHERE sku = ? AND is_deleted = 0", (sku,)).fetchone()
    conn.close()
    return dict(product_data) if product_data else None

def db_search_products_flexible(search_term):
    """
    Tìm kiếm sản phẩm trong DB một cách linh hoạt theo SKU hoặc Tên.
    Sử dụng toán tử LIKE để tìm kiếm gần đúng.

    Args:
        search_term (str): Từ khóa tìm kiếm.

    Returns:
        list: Danh sách các sản phẩm khớp với từ khóa.
    """
    conn = get_db_connection()
    like_term = f"%{search_term}%"
    products = [dict(row) for row in conn.execute("SELECT id, name, sku, description, unit_of_measure, current_stock, price, updated_at FROM products WHERE (sku LIKE ? OR name LIKE ?) AND is_deleted = 0 ORDER BY name ASC", (like_term, like_term)).fetchall()]
    conn.close()
    return products
    
def db_update_product(product_id, name, description, unit_of_measure, price):
    """Cập nhật thông tin chi tiết của một sản phẩm đã có."""
    conn = get_db_connection()
    try:
        current_time = datetime.datetime.now()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products 
            SET name = ?, description = ?, unit_of_measure = ?, price = ?, updated_at = ?
            WHERE id = ?
        ''', (name, description, unit_of_measure, int(price), current_time, product_id))
        conn.commit()
        return True, f"Cập nhật sản phẩm '{name}' thành công!"
    except ValueError:
        return False, "Lỗi: Đơn giá phải là số nguyên hợp lệ."
    except Exception as e:
        return False, f"Lỗi khi cập nhật sản phẩm: {e}"
    finally:
        conn.close()

def db_delete_product_by_id(product_id):
    """Xóa mềm một sản phẩm: cập nhật cờ is_deleted = 1 và trả về thông báo chi tiết."""
    conn = get_db_connection()
    try:
        # BƯỚC 1: Lấy thông tin sản phẩm (SKU, Tên) TRƯỚC khi xóa.
        product_info = conn.execute("SELECT sku, name FROM products WHERE id = ?", (product_id,)).fetchone()

        # Kiểm tra nếu không tìm thấy sản phẩm
        if not product_info:
            return False, f"Lỗi: Không tìm thấy sản phẩm với ID {product_id} để xóa."

        # BƯỚC 2: Thực hiện xóa mềm (UPDATE)
        current_time = datetime.datetime.now()
        conn.execute("UPDATE products SET is_deleted = 1, updated_at = ? WHERE id = ?", (current_time, product_id))
        conn.commit()

        # BƯỚC 3: Tạo thông báo thành công với thông tin vừa lấy được
        sku = product_info['sku']
        product_name = product_info['name']
        success_message = f"Ẩn sản phẩm {sku} - {product_name} thành công"
        
        return True, success_message
        
    except Exception as e:
        # Trong trường hợp có lỗi, rollback để đảm bảo an toàn
        conn.rollback()
        return False, f"Lỗi cơ sở dữ liệu khi xóa sản phẩm: {e}"
    finally:
        conn.close()

