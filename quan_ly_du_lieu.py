# quan_ly_du_lieu.py
import csv
import os
from datetime import datetime # Added for timestamp

FILE_KHO = 'kho.csv'
FILE_LOG_LOI = 'log.txt'
FILE_LICH_SU_GIAO_DICH = 'lichsugiaodich.txt'

def ghi_log_loi(thong_bao_loi):
    """Ghi một thông báo lỗi vào file log.txt."""
    try:
        with open(FILE_LOG_LOI, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {thong_bao_loi}\n")
    except IOError:
        print(f"LỖI HỆ THỐNG: Không thể ghi vào file log: {FILE_LOG_LOI}")

def ghi_log_giao_dich(thong_tin_giao_dich):
    """Ghi một thông tin giao dịch vào file lichsugiaodich.txt."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(FILE_LICH_SU_GIAO_DICH, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {thong_tin_giao_dich}\n")
    except IOError:
        ghi_log_loi(f"LỖI HỆ THỐNG: Không thể ghi vào file lịch sử giao dịch: {FILE_LICH_SU_GIAO_DICH}")
    except Exception as e:
        ghi_log_loi(f"LỖI KHÔNG XÁC ĐỊNH khi ghi lịch sử giao dịch: {e}")

def tai_du_lieu_tu_file(ten_file=FILE_KHO):
    """
    Tải dữ liệu sản phẩm từ file CSV khi khởi động.
    Định dạng file: maSP,tenSP,donViTinh,soLuongTon,donGia
    """
    danh_sach_san_pham_tam = []
    if not os.path.exists(ten_file):
        print(f"Thông báo: File dữ liệu '{ten_file}' không tồn tại. Khởi tạo kho rỗng.")
        return danh_sach_san_pham_tam

    try:
        with open(ten_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            expected_headers = ['maSP', 'tenSP', 'donViTinh', 'soLuongTon', 'donGia']

            if not reader.fieldnames or not all(col in reader.fieldnames for col in expected_headers):
                msg = f"Lỗi: File '{ten_file}' có định dạng cột không đúng. Cần: {','.join(expected_headers)}."
                print(msg)
                ghi_log_loi(msg)
                return danh_sach_san_pham_tam

            file_had_data_rows = False
            for i, row in enumerate(reader, start=2):
                file_had_data_rows = True
                try:
                    if not all(key in row and row[key] is not None for key in expected_headers):
                        error_msg = f"Lỗi tải dòng {i} file '{ten_file}': Thiếu cột dữ liệu hoặc giá trị rỗng không mong muốn."
                        ghi_log_loi(error_msg)
                        continue

                    ma_sp = row['maSP'].strip()
                    ten_sp = row['tenSP'].strip()
                    dvt = row['donViTinh'].strip()
                    so_luong_str = row['soLuongTon'].strip()
                    don_gia_str = row['donGia'].strip()

                    if not (ma_sp and len(ma_sp) <= 10):
                        error_msg = f"Lỗi tải dòng {i} file '{ten_file}': Mã SP '{ma_sp}' không hợp lệ (rỗng hoặc >10 ký tự)."
                        ghi_log_loi(error_msg)
                        continue
                    if not (ten_sp and len(ten_sp) <= 100):
                        error_msg = f"Lỗi tải dòng {i} file '{ten_file}': Tên SP cho mã '{ma_sp}' không hợp lệ (rỗng hoặc >100 ký tự)."
                        ghi_log_loi(error_msg)
                        continue
                    if not (dvt and len(dvt) <= 20):
                        error_msg = f"Lỗi tải dòng {i} file '{ten_file}': ĐVT cho mã '{ma_sp}' không hợp lệ (rỗng hoặc >20 ký tự)."
                        ghi_log_loi(error_msg)
                        continue

                    so_luong = int(so_luong_str)
                    don_gia = int(don_gia_str)

                    if so_luong < 0:
                        error_msg = f"Lỗi tải dòng {i} file '{ten_file}': Số lượng tồn của '{ma_sp}' là số âm ({so_luong})."
                        ghi_log_loi(error_msg)
                        continue
                    if don_gia < 0:
                        error_msg = f"Lỗi tải dòng {i} file '{ten_file}': Đơn giá của '{ma_sp}' là số âm ({don_gia})."
                        ghi_log_loi(error_msg)
                        continue

                    if any(sp_temp['maSP'] == ma_sp for sp_temp in danh_sach_san_pham_tam):
                        error_msg = f"Lỗi tải dòng {i} file '{ten_file}': Mã SP '{ma_sp}' bị trùng trong file."
                        ghi_log_loi(error_msg)
                        continue

                    danh_sach_san_pham_tam.append({
                        'maSP': ma_sp,
                        'tenSP': ten_sp,
                        'donViTinh': dvt,
                        'soLuongTon': so_luong,
                        'donGia': don_gia
                    })
                except ValueError:
                    error_msg = f"Lỗi tải dòng {i} file '{ten_file}': Số lượng hoặc đơn giá không phải là số nguyên hợp lệ."
                    ghi_log_loi(error_msg)
                except Exception as e_row:
                    error_msg = f"Lỗi không xác định khi xử lý dòng {i} file '{ten_file}': {e_row}"
                    ghi_log_loi(error_msg)

            if not file_had_data_rows and reader.fieldnames:
                 print(f"Thông báo: File dữ liệu '{ten_file}' rỗng (chỉ có header). Khởi tạo kho rỗng.")

        if danh_sach_san_pham_tam:
            print(f"Đã tải thành công {len(danh_sach_san_pham_tam)} sản phẩm từ file '{ten_file}'.")
        elif file_had_data_rows:
             print(f"Thông báo: Không có sản phẩm hợp lệ nào được tải từ file '{ten_file}'. Xem chi tiết trong {FILE_LOG_LOI} (nếu có lỗi).")

    except FileNotFoundError:
        print(f"Thông báo: File dữ liệu '{ten_file}' không tìm thấy. Khởi tạo kho rỗng.")
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tải dữ liệu từ file '{ten_file}': {e}. Khởi tạo kho rỗng.")
        ghi_log_loi(f"Lỗi nghiêm trọng khi đọc file {ten_file}: {e}")
        danh_sach_san_pham_tam = []
    return danh_sach_san_pham_tam

def luu_du_lieu_vao_file(danh_sach_san_pham, ten_file=FILE_KHO):
    """Lưu toàn bộ danh sách sản phẩm hiện tại vào file CSV."""
    if not danh_sach_san_pham:
        print("Thông báo: Không có dữ liệu sản phẩm để lưu.")
        return

    try:
        with open(ten_file, mode='w', newline='', encoding='utf-8') as file:
            fieldnames = ['maSP', 'tenSP', 'donViTinh', 'soLuongTon', 'donGia']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(danh_sach_san_pham)
        print(f"Đã lưu thành công dữ liệu vào file '{ten_file}'.")
    except IOError as e:
        error_msg = f"Lỗi: Không thể lưu dữ liệu vào file '{ten_file}'. Chi tiết: {e}"
        print(error_msg)
        ghi_log_loi(error_msg)
    except Exception as e:
        error_msg = f"Lỗi không xác định khi lưu file: {e}"
        print(error_msg)
        ghi_log_loi(error_msg)