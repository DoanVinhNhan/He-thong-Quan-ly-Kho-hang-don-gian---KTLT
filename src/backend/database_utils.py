# src/backend/database_utils.py
from .common.database_base import DB_NAME
from .product import database as product_db
from .transaction import database as transaction_db

def init_db():
    """
    Khởi tạo tất cả các bảng cần thiết trong cơ sở dữ liệu (products, stock_transactions).
    """
    print(f"Bắt đầu khởi tạo cơ sở dữ liệu '{DB_NAME}'...")
    product_db.init_db(DB_NAME)
    transaction_db.init_db(DB_NAME)
    print(f"Cơ sở dữ liệu đã được khởi tạo thành công.")