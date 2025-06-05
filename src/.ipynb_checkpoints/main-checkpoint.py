# src/main.py
from http.server import HTTPServer
from .backend.request_router import MiniVentoryRequestHandler
from .backend.common import quan_ly_du_lieu as qldl
from .backend import database_utils as db

# --- Cấu hình Server ---
HOST_NAME = 'localhost'
SERVER_PORT = 8001

def main():
    """Hàm chính để khởi tạo DB và chạy server."""
    try:
        db.init_db() 
        if hasattr(qldl, 'ghi_log_loi'):
            qldl.ghi_log_loi(f"Khởi động server web MiniVentory với SQLite DB '{db.DB_NAME}' tại cổng {HOST_NAME}:{SERVER_PORT}.")
        
        server_address = (HOST_NAME, SERVER_PORT)
        httpd = HTTPServer(server_address, MiniVentoryRequestHandler) 
        
        print(f"MiniVentory Web (tái cấu trúc) đang chạy tại http://{HOST_NAME}:{SERVER_PORT}/")
        print("Nhấn Ctrl+C để dừng server.")
        
        httpd.serve_forever()

    except KeyboardInterrupt:
        print("\nĐang dừng server...")
        if hasattr(qldl, 'ghi_log_loi'):
            qldl.ghi_log_loi("Dừng server web MiniVentory.")
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi khởi động server: {e}")
        if hasattr(qldl, 'ghi_log_loi'):
            qldl.ghi_log_loi(f"Lỗi nghiêm trọng khi khởi động server: {e}")
    finally:
        if 'httpd' in locals() and httpd: 
            httpd.server_close()
        print("Đã dừng server.")

if __name__ == '__main__':
    main()