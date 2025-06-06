# src/main.py
from http.server import HTTPServer
from .backend.request_router import MiniVentoryRequestHandler
from .backend.common import quan_ly_du_lieu as qldl
from .backend import database_utils as db

# --- Cấu hình Server ---
HOST_NAME = 'localhost'
SERVER_PORT = 8001

def main():
    """
    Điểm khởi đầu của ứng dụng (entry point).
    Hàm này khởi tạo cơ sở dữ liệu và bắt đầu chạy HTTP server.
    """
    try:
        # Khởi tạo các bảng trong cơ sở dữ liệu nếu chưa tồn tại.
        db.init_db() 
        if hasattr(qldl, 'ghi_log_loi'):
            qldl.ghi_log_loi(f"Khởi động server web MiniVentory với SQLite DB '{db.DB_NAME}' tại cổng {HOST_NAME}:{SERVER_PORT}.")
        
        # Thiết lập địa chỉ và khởi tạo server với Request Handler đã định nghĩa.
        server_address = (HOST_NAME, SERVER_PORT)
        httpd = HTTPServer(server_address, MiniVentoryRequestHandler) 
        
        print(f"MiniVentory Web (tái cấu trúc) đang chạy tại http://{HOST_NAME}:{SERVER_PORT}/")
        print("Nhấn Ctrl+C để dừng server.")
        
        # Bắt đầu vòng lặp chính của server để lắng nghe các request.
        httpd.serve_forever()

    except KeyboardInterrupt:
        # Xử lý khi người dùng nhấn Ctrl+C để dừng server một cách an toàn.
        print("\nĐang dừng server...")
        if hasattr(qldl, 'ghi_log_loi'):
            qldl.ghi_log_loi("Dừng server web MiniVentory.")
    except Exception as e:
        # Ghi lại bất kỳ lỗi nghiêm trọng nào xảy ra trong quá trình khởi động.
        print(f"Lỗi nghiêm trọng khi khởi động server: {e}")
        if hasattr(qldl, 'ghi_log_loi'):
            qldl.ghi_log_loi(f"Lỗi nghiêm trọng khi khởi động server: {e}")
    finally:
        # Đảm bảo server được đóng lại đúng cách khi kết thúc.
        if 'httpd' in locals() and httpd: 
            httpd.server_close()
        print("Đã dừng server.")

if __name__ == '__main__':
    main()
