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
    cursor = conn.cursor()
    try:
        current_time = datetime.datetime.now()
        cursor.execute('''
        INSERT INTO products (name, sku, description, unit_of_measure, current_stock, price, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, sku, description, unit_of_measure, int(current_stock), int(price), current_time, current_time))
        conn.commit()
        return cursor.lastrowid, f"Thêm sản phẩm '{name}' (SKU: {sku}) thành công!"
    except sqlite3.IntegrityError:
        return None, f"Lỗi: Mã SKU '{sku}' đã tồn tại."
    except ValueError:
        return None, "Lỗi: Số lượng tồn hoặc đơn giá phải là số nguyên hợp lệ."
    except Exception as e:
        return None, f"Lỗi khi thêm sản phẩm: {e}"
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
    
    query = f"SELECT id, name, sku, description, unit_of_measure, current_stock, price, updated_at FROM products ORDER BY {sort_by} {order_direction}, id {order_direction}"
    products = [dict(row) for row in conn.execute(query).fetchall()]
    conn.close()
    return products

def db_get_product_by_id(product_id):
    """Lấy thông tin một sản phẩm dựa trên ID."""
    conn = get_db_connection()
    product_data = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(product_data) if product_data else None

def db_get_product_by_sku(sku):
    """Lấy thông tin một sản phẩm dựa trên SKU."""
    conn = get_db_connection()
    product_data = conn.execute("SELECT * FROM products WHERE sku = ?", (sku,)).fetchone()
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
    products = [dict(row) for row in conn.execute("SELECT id, name, sku, description, unit_of_measure, current_stock, price, updated_at FROM products WHERE sku LIKE ? OR name LIKE ? ORDER BY name ASC", (like_term, like_term)).fetchall()]
    conn.close()
    return products
