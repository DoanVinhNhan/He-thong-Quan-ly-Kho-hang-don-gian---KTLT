# /src/backend/common/quan_ly_du_lieu.py
# File này chứa các hàm tiện ích dùng chung liên quan đến quản lý dữ liệu,
# cụ thể là ghi log và đọc/xử lý file CSV.

import csv
import os
from datetime import datetime

# Định nghĩa hằng số cho tên file log để dễ dàng thay đổi và quản lý.
FILE_LOG_LOI = 'log.txt'
FILE_LICH_SU_GIAO_DICH = 'lichsugiaodich.txt'

def ghi_log_loi(thong_bao_loi):
    """
    Ghi một thông báo lỗi (hoặc thông báo hệ thống) vào file log lỗi
    kèm theo timestamp hiện tại.

    Args:
        thong_bao_loi (str): Nội dung thông báo cần ghi.
    """
    try:
        with open(FILE_LOG_LOI, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {thong_bao_loi}\n")
    except IOError:
        # In ra console nếu không thể ghi file, đây là một lỗi nghiêm trọng.
        print(f"LỖI HỆ THỐNG NGHIÊM TRỌNG: Không thể ghi vào file log: {FILE_LOG_LOI}")

def ghi_log_giao_dich(thong_tin_giao_dich):
    """
    Ghi một thông tin tóm tắt về giao dịch vào file lịch sử giao dịch
    kèm theo timestamp.

    Args:
        thong_tin_giao_dich (str): Nội dung tóm tắt giao dịch.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(FILE_LICH_SU_GIAO_DICH, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {thong_tin_giao_dich}\n")
    except IOError:
        msg = f"Lỗi IO khi ghi log giao dịch vào file: {FILE_LICH_SU_GIAO_DICH}"
        print(msg)
        ghi_log_loi(f"Không thể ghi log giao dịch (text) vào file: {msg}")

def doc_file_csv_cho_nhap_xuat(ten_file):
    """
    Đọc và phân tích file CSV cho chức năng nhập/xuất kho hàng loạt.
    Hàm này được thiết kế linh hoạt để chấp nhận nhiều biến thể tên cột phổ biến
    (ví dụ: 'maSP', 'sku', 'soLuong', 'quantity').

    Args:
        ten_file (str): Đường dẫn đến file CSV.

    Returns:
        tuple: (list_dữ_liệu, thông_báo_trạng_thái)
               - list_dữ_liệu: List các dictionary đã được xử lý, sẵn sàng cho logic nghiệp vụ.
               - thông_báo_trạng_thái: String mô tả kết quả đọc file.
               Trả về (None, thông_báo_lỗi) nếu có lỗi nghiêm trọng không thể xử lý.
    """
    data_rows = []
    if not os.path.exists(ten_file):
        ghi_log_loi(f"Đọc file CSV: File '{ten_file}' không tồn tại.")
        return None, f"Lỗi: File '{ten_file}' không tồn tại."
    try:
        # Mở file với encoding 'utf-8-sig' để xử lý ký tự BOM (Byte Order Mark) nếu có.
        with open(ten_file, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                 return None, f"Lỗi: File '{ten_file}' trống hoặc không có header."

            # Chuẩn hóa tên cột: chuyển thành chữ thường và xóa khoảng trắng để so sánh.
            actual_cols = [col.strip().lower() for col in reader.fieldnames]

            # Tìm tên cột Mã Sản Phẩm thực tế trong file dựa trên danh sách các tên có thể có.
            sku_col_name = None
            possible_sku_cols = ['masp', 'mãsp', 'mã sp', 'sku']
            for col_name in possible_sku_cols:
                if col_name in actual_cols:
                    sku_col_name = reader.fieldnames[actual_cols.index(col_name)] 
                    break
            if not sku_col_name:
                return None, f"Lỗi: File '{ten_file}' thiếu cột Mã Sản Phẩm (ví dụ: maSP, SKU)."

            # Tương tự, tìm tên cột Số Lượng.
            qty_col_name = None
            possible_qty_cols = ['soluong', 'sốlượng', 'soluongnhap', 'soluongxuat', 'quantity']
            for col_name in possible_qty_cols:
                if col_name in actual_cols:
                    qty_col_name = reader.fieldnames[actual_cols.index(col_name)]
                    break
            if not qty_col_name:
                 return None, f"Lỗi: File '{ten_file}' thiếu cột Số Lượng (ví dụ: soLuong)."
            # Tìm các cột tùy chọn (ghi chú).
            notes_col_name = next((reader.fieldnames[actual_cols.index(col)] for col in ['ghichu', 'ghi chú', 'notes', 'note', 'diengiai'] if col in actual_cols), None)
            
            # Đọc và xử lý từng dòng trong file CSV.
            for row_dict_original in reader:
                # Làm sạch dữ liệu: xóa khoảng trắng thừa.
                cleaned_row = {key.strip(): str(value).strip() if value is not None else '' 
                               for key, value in row_dict_original.items()}

                # Tạo một dictionary mới với các key đã được chuẩn hóa.
                processed_entry = {
                    'maSP': cleaned_row.get(sku_col_name, ''),
                    'soLuongProcessed': cleaned_row.get(qty_col_name, '0'),
                    'ghiChu': cleaned_row.get(notes_col_name, '') if notes_col_name else ''
                }
                
                data_rows.append(processed_entry)
        
        if not data_rows:
            return [], "Thông báo: File CSV không có dữ liệu."
        return data_rows, f"Đọc thành công {len(data_rows)} dòng từ file '{os.path.basename(ten_file)}'."
    except csv.Error as e:
        msg = f"Lỗi định dạng CSV trong file '{os.path.basename(ten_file)}': {e}"
        ghi_log_loi(msg)
        return None, msg
    except Exception as e:
        msg = f"Lỗi không xác định khi đọc file '{os.path.basename(ten_file)}': {e}"
        ghi_log_loi(msg)
        return None, msg
