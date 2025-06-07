# /src/backend/common/database_base.py
import sqlite3
import datetime

DB_NAME = 'miniventory_sqlite.db'

def adapt_datetime_iso(val):
    """Chuyển đổi đối tượng datetime của Python thành chuỗi ISO 8601 để lưu trữ."""
    return val.isoformat()

def convert_datetime_iso(val):
    """Chuyển đổi chuỗi (dạng bytes) từ DB trở lại thành đối tượng datetime của Python."""
    try:
        return datetime.datetime.fromisoformat(val.decode())
    except ValueError:
        # Hỗ trợ định dạng cũ hơn nếu cần
        return datetime.datetime.strptime(val.decode(), '%Y-%m-%d %H:%M:%S.%f')

def get_db_connection(db_name=DB_NAME):
    """
    Tạo và trả về một đối tượng kết nối tới cơ sở dữ liệu SQLite.
    Hàm này tự động đăng ký các bộ chuyển đổi kiểu dữ liệu datetime và
    thiết lập row_factory để có thể truy cập các cột bằng tên.
    """
    # Đăng ký các hàm chuyển đổi để SQLite hiểu kiểu dữ liệu datetime của Python
    sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
    sqlite3.register_converter("timestamp", convert_datetime_iso)
    
    # Tạo kết nối
    conn = sqlite3.connect(db_name, detect_types=sqlite3.PARSE_DECLTYPES)
    
    # Thiết lập row_factory để kết quả trả về có thể được truy cập như dictionary (cho phép truy cập theo tên cột - ánh xạ tên cột )
    conn.row_factory = sqlite3.Row
    
    return conn
