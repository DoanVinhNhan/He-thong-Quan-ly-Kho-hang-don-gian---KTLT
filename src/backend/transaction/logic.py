# /src/backend/transaction/logic.py
import os
from ..common import quan_ly_du_lieu as qldl
from . import database as db_transaction
from ..product.database import db_get_product_by_sku

def _process_stock_file(ten_file, transaction_type):
    """
    Xử lý logic nghiệp vụ cho việc nhập/xuất kho hàng loạt từ file CSV.
    Hàm này đọc file CSV, xác thực dữ liệu và gọi hàm trong database để thực hiện giao dịch.
    """
    data_rows, msg_read = qldl.doc_file_csv_cho_nhap_xuat(ten_file)

    if data_rows is None:
        qldl.ghi_log_loi(f"{transaction_type} kho từ file CSV thất bại (đọc file): {msg_read}")
        return False, msg_read
    if not data_rows and isinstance(data_rows, list):
        qldl.ghi_log_loi(f"{transaction_type} kho từ file CSV: File '{os.path.basename(ten_file)}' không có dữ liệu.")
        return True, f"Thông báo: File CSV '{os.path.basename(ten_file)}' không có dữ liệu để {transaction_type.lower()} kho."

    success_count = 0
    failure_count = 0
    processed_rows = 0
    error_messages_summary = []
    log_details_header = f"--- Bắt đầu Log chi tiết xử lý file {transaction_type.lower()} hàng DB: {os.path.basename(ten_file)} ---"
    qldl.ghi_log_loi(log_details_header)

    for i, row in enumerate(data_rows, start=1):
        processed_rows += 1
        ma_sp = row.get('maSP', '').strip()
        so_luong_str = row.get('soLuongProcessed', '').strip()
        ghi_chu_file = row.get('ghiChu', '').strip()
        don_gia_csv_str = row.get('donGiaCSV')

        current_row_log_prefix = f"Dòng {i}, File '{os.path.basename(ten_file)}', SKU '{ma_sp}'"

        if not ma_sp or not so_luong_str:
            err_msg = f"{current_row_log_prefix}: Bỏ qua do thiếu SKU hoặc số lượng."
            error_messages_summary.append(err_msg)
            qldl.ghi_log_loi(err_msg)
            failure_count +=1
            continue
        
        product = db_get_product_by_sku(ma_sp)
        if not product:
            err_msg = f"{current_row_log_prefix}: Sản phẩm không tồn tại trong DB."
            error_messages_summary.append(err_msg)
            qldl.ghi_log_loi(err_msg)
            failure_count +=1
            continue
        
        product_id = product['id']
        
        unit_price_for_transaction_str = "0"
        if don_gia_csv_str:
            try:
                unit_price_for_transaction_str = str(int(float(don_gia_csv_str)))
            except ValueError:
                qldl.ghi_log_loi(f"{current_row_log_prefix}: Đơn giá CSV '{don_gia_csv_str}' không hợp lệ, lấy giá từ DB.")
                unit_price_for_transaction_str = str(int(product.get('price', 0)))
        else:
            unit_price_for_transaction_str = str(int(product.get('price', 0)))

        notes_combined = f"{transaction_type} từ file {os.path.basename(ten_file)}, dòng {i}. Ghi chú file: {ghi_chu_file}"
        
        transaction_success, trans_msg = db_transaction.db_add_stock_transaction(
            product_id, transaction_type, so_luong_str, 
            unit_price_for_transaction_str, notes_combined, user="file_process_csv"
        )
        
        if transaction_success:
            qldl.ghi_log_loi(f"{current_row_log_prefix}: {transaction_type} thành công {so_luong_str}. {trans_msg}")
            success_count += 1
        else:
            err_msg = f"{current_row_log_prefix}: Lỗi DB khi {transaction_type.lower()} {so_luong_str}. {trans_msg}"
            error_messages_summary.append(err_msg)
            qldl.ghi_log_loi(err_msg)
            failure_count += 1
            
    qldl.ghi_log_loi(f"--- Kết thúc Log chi tiết xử lý file {transaction_type.lower()} hàng DB: {os.path.basename(ten_file)} ---")

    final_summary_msg = f"Hoàn tất {transaction_type.lower()} kho từ file '{os.path.basename(ten_file)}'.\nThành công: {success_count}/{processed_rows} dòng."
    if failure_count > 0:
        final_summary_msg += f"\nThất bại: {failure_count} dòng."
        if error_messages_summary:
             final_summary_msg += "\nChi tiết lỗi (tối đa 5 dòng đầu):\n" + "\n".join(error_messages_summary[:5])
    
    if processed_rows > 0 :
        qldl.ghi_log_giao_dich(f"{transaction_type}_KHO_FILE_DB: File '{os.path.basename(ten_file)}', TC: {success_count}/{processed_rows}, TB: {failure_count}.")

    return success_count > 0 or (processed_rows == 0 and success_count == 0), final_summary_msg

def nhap_kho_tu_file_csv(ten_file_nhap):
    """Logic xử lý nhập kho từ file CSV."""
    return _process_stock_file(ten_file_nhap, 'IN')

def xuat_kho_tu_file_csv(ten_file_xuat):
    """Logic xử lý xuất kho từ file CSV."""
    return _process_stock_file(ten_file_xuat, 'OUT')