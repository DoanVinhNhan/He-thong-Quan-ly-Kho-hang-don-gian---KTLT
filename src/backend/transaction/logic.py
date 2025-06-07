# /src/backend/transaction/logic.py
import os
from ..common import quan_ly_du_lieu as qldl
from . import database as db_transaction
from ..product.database import db_get_product_by_sku

def _process_stock_file(ten_file, transaction_type):
    """
    Logic nghiệp vụ cốt lõi để xử lý nhập/xuất kho hàng loạt từ file CSV.
    Hàm này điều phối việc đọc file, xác thực dữ liệu từng dòng, và gọi đến lớp
    database để thực hiện giao dịch cho các dòng hợp lệ.

    Args:
        ten_file (str): Đường dẫn đến file CSV.
        transaction_type (str): 'IN' cho nhập kho, 'OUT' cho xuất kho.

    Returns:
        tuple: (bool_thành_công, str_thông_báo_tổng_kết)
    """
    # Bước 1: Đọc và phân tích file CSV
    data_rows, msg_read = qldl.doc_file_csv_cho_nhap_xuat(ten_file)

    if data_rows is None:
        qldl.ghi_log_loi(f"{transaction_type} kho từ file CSV thất bại (đọc file): {msg_read}")
        return False, msg_read
    if not data_rows and isinstance(data_rows, list):
        return True, f"Thông báo: File CSV '{os.path.basename(ten_file)}' không có dữ liệu."

    # Bước 2: Khởi tạo các biến đếm và theo dõi kết quả
    success_count, failure_count, processed_rows = 0, 0, 0
    error_messages_summary = []
    log_header = f"--- Bắt đầu Log xử lý file {transaction_type}: {os.path.basename(ten_file)} ---"
    qldl.ghi_log_loi(log_header)

    # Bước 3: Lặp qua từng dòng dữ liệu đã đọc từ file
    for i, row in enumerate(data_rows, start=1):
        processed_rows += 1
        ma_sp = row.get('maSP', '').strip()
        so_luong_str = row.get('soLuongProcessed', '').strip()
        
        # Xác thực dữ liệu cơ bản
        if not ma_sp or not so_luong_str:
            err_msg = f"Dòng {i}: Bỏ qua do thiếu SKU hoặc số lượng."
            error_messages_summary.append(err_msg)
            failure_count += 1
            continue
        
        product = db_get_product_by_sku(ma_sp)
        if not product:
            err_msg = f"Dòng {i}, SKU '{ma_sp}': Sản phẩm không tồn tại."
            error_messages_summary.append(err_msg)
            failure_count += 1
            continue
        
        unit_price_str = str(product.get('price', 0))

        # Tạo ghi chú cho giao dịch
        ghi_chu_file = row.get('ghiChu', '').strip()
        notes_combined = f"Từ file {os.path.basename(ten_file)}, dòng {i}. Ghi chú: {ghi_chu_file}"
        
        # Bước 4: Gọi lớp database để thực hiện giao dịch
        success, trans_msg = db_transaction.db_add_stock_transaction(
            product['id'], transaction_type, so_luong_str, unit_price_str, notes_combined, user="file_csv"
        )
        
        # Bước 5: Cập nhật kết quả
        if success:
            success_count += 1
        else:
            err_msg = f"Dòng {i}, SKU '{ma_sp}': Lỗi khi xử lý - {trans_msg}"
            error_messages_summary.append(err_msg)
            failure_count += 1
            
    qldl.ghi_log_loi(f"--- Kết thúc Log xử lý file ---")

    # Bước 6: Tạo thông báo tổng kết cuối cùng
    final_msg = f"Hoàn tất xử lý file '{os.path.basename(ten_file)}'.\nThành công: {success_count}/{processed_rows}."
    if failure_count > 0:
        final_msg += f"\nThất bại: {failure_count} dòng."
        if error_messages_summary:
             final_msg += "\nChi tiết lỗi (tối đa 5):\n" + "\n".join(error_messages_summary[:5])
    
    if processed_rows > 0:
        qldl.ghi_log_giao_dich(f"{transaction_type}_FILE: '{os.path.basename(ten_file)}', TC: {success_count}/{processed_rows}.")

    return success_count > 0 or (processed_rows == 0), final_msg

def nhap_kho_tu_file_csv(ten_file_nhap):
    """
    Logic nghiệp vụ để điều phối việc nhập kho từ một file CSV.
    Đây là một hàm public, gọi đến hàm xử lý private `_process_stock_file`.
    """
    return _process_stock_file(ten_file_nhap, 'IN')

def xuat_kho_tu_file_csv(ten_file_xuat):
    """
    Logic nghiệp vụ để điều phối việc xuất kho từ một file CSV.
    Đây là một hàm public, gọi đến hàm xử lý private `_process_stock_file`.
    """
    return _process_stock_file(ten_file_xuat, 'OUT')