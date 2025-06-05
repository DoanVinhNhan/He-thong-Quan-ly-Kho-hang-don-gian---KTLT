# /src/backend/common/database_base.py
import sqlite3
import datetime

DB_NAME = 'miniventory_sqlite.db'

def adapt_datetime_iso(val):
    return val.isoformat()

def convert_datetime_iso(val):
    try:
        return datetime.datetime.fromisoformat(val.decode())
    except ValueError:
        # Hỗ trợ format cũ hơn nếu cần
        return datetime.datetime.strptime(val.decode(), '%Y-%m-%d %H:%M:%S.%f')

def get_db_connection(db_name=DB_NAME):
    """Tạo kết nối tới DB, đăng ký adapter và converter."""
    sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
    sqlite3.register_converter("timestamp", convert_datetime_iso)
    conn = sqlite3.connect(db_name, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn