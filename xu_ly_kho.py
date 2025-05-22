# xu_ly_kho.py
import csv
import os
from quan_ly_du_lieu import ghi_log_loi, FILE_LOG_LOI as LOG_FILE_PATH, ghi_log_giao_dich, FILE_LICH_SU_GIAO_DICH

DEFAULT_IMPORT_TRANSACTION_FILE = 'nhapHang.csv'
DEFAULT_EXPORT_TRANSACTION_FILE = 'xuatHang.csv'

def kiem_tra_ma_sp_ton_tai(ma_sp, danh_sach_san_pham):
    for sp in danh_sach_san_pham:
        if sp['maSP'] == ma_sp:
            return True
    return False

def tim_san_pham_theo_ma_sp(ma_sp, danh_sach_san_pham):
    for sp in danh_sach_san_pham:
        if sp['maSP'] == ma_sp:
            return sp
    return None

def them_san_pham_moi(danh_sach_san_pham):
    """Cho phép người dùng thêm một sản phẩm mới vào kho."""
    print("\n--- Thêm Sản Phẩm Mới ---")
    while True:
        ma_sp = input("Nhập mã sản phẩm (tối đa 10 ký tự, không để trống): ").strip()
        if not ma_sp:
            print("Lỗi: Mã sản phẩm không được để trống.")
        elif len(ma_sp) > 10:
            print("Lỗi: Mã sản phẩm không được vượt quá 10 ký tự.")
        elif kiem_tra_ma_sp_ton_tai(ma_sp, danh_sach_san_pham):
            print(f"Lỗi: Mã sản phẩm '{ma_sp}' đã tồn tại.")
        else:
            break

    while True:
        ten_sp = input("Nhập tên sản phẩm (tối đa 100 ký tự, không để trống): ").strip()
        if not ten_sp:
            print("Lỗi: Tên sản phẩm không được để trống.")
        elif len(ten_sp) > 100:
            print("Lỗi: Tên sản phẩm không được vượt quá 100 ký tự.")
        else:
            break

    while True:
        don_vi_tinh = input("Nhập đơn vị tính (tối đa 20 ký tự, không để trống): ").strip()
        if not don_vi_tinh :
             print("Lỗi: Đơn vị tính không được để trống.")
        elif len(don_vi_tinh) > 20:
            print("Lỗi: Đơn vị tính không được vượt quá 20 ký tự.")
        else:
            break

    while True:
        try:
            so_luong_ton = int(input("Nhập số lượng tồn ban đầu (số không âm): "))
            if so_luong_ton < 0:
                print("Lỗi: Số lượng tồn phải là số không âm.")
            else:
                break
        except ValueError:
            print("Lỗi: Số lượng tồn phải là một số nguyên.")

    while True:
        try:
            don_gia = int(input("Nhập đơn giá (số không âm): "))
            if don_gia < 0:
                print("Lỗi: Đơn giá phải là số không âm.")
            else:
                break
        except ValueError:
            print("Lỗi: Đơn giá phải là một số nguyên.")

    san_pham_moi = {
        'maSP': ma_sp,
        'tenSP': ten_sp,
        'donViTinh': don_vi_tinh,
        'soLuongTon': so_luong_ton,
        'donGia': don_gia
    }
    danh_sach_san_pham.append(san_pham_moi)
    print(f"Đã thêm thành công sản phẩm '{ten_sp}'.")
    return True

def liet_ke_tat_ca_san_pham(danh_sach_san_pham):
    """Hiển thị toàn bộ danh sách sản phẩm hiện có trong kho."""
    print("\n--- Danh Sách Sản Phẩm Trong Kho ---")
    if not danh_sach_san_pham:
        print("Kho chưa có sản phẩm nào.")
        return

    print(f"{'Mã SP':<12} | {'Tên Sản Phẩm':<30} | {'ĐVT':<10} | {'Số Lượng Tồn':>15} | {'Đơn Giá':>12}")
    print("-" * 85)
    for sp in danh_sach_san_pham:
        print(f"{sp['maSP']:<12} | {sp['tenSP']:<30} | {sp['donViTinh']:<10} | {sp['soLuongTon']:>15,} | {sp['donGia']:>12,}")
    print("-" * 85)
    print(f"Tổng số loại sản phẩm: {len(danh_sach_san_pham)}")


def nhap_hang_cho_san_pham(danh_sach_san_pham):
    """Tăng số lượng tồn kho cho một sản phẩm đã có qua nhập liệu từ bàn phím."""
    print("\n--- Nhập Hàng Thủ Công ---")
    ma_sp = input("Nhập mã sản phẩm cần nhập hàng: ").strip()
    san_pham = tim_san_pham_theo_ma_sp(ma_sp, danh_sach_san_pham)

    if not san_pham:
        print(f"Lỗi: Không tìm thấy sản phẩm với mã '{ma_sp}'.")
        return

    print(f"Thông tin sản phẩm: {san_pham['tenSP']} - Tồn kho hiện tại: {san_pham['soLuongTon']:,}")
    while True:
        try:
            so_luong_nhap = int(input("Nhập số lượng cần nhập (số dương): "))
            if so_luong_nhap <= 0:
                print("Lỗi: Số lượng nhập phải là số dương.")
            else:
                break
        except ValueError:
            print("Lỗi: Số lượng nhập phải là một số nguyên.")

    san_pham['soLuongTon'] += so_luong_nhap
    ghi_log_giao_dich(f"NHAP_THU_CONG: SP '{ma_sp}', Ten '{san_pham['tenSP']}', So luong nhap: {so_luong_nhap}, Ton moi: {san_pham['soLuongTon']}")
    print(f"Nhập hàng thành công. Số lượng tồn mới của '{san_pham['tenSP']}' là {san_pham['soLuongTon']:,}.")

def xuat_hang_khoi_kho(danh_sach_san_pham):
    """Giảm số lượng tồn kho cho một sản phẩm đã có, kiểm tra lượng tồn."""
    print("\n--- Xuất Hàng Thủ Công ---")
    ma_sp = input("Nhập mã sản phẩm cần xuất hàng: ").strip()
    san_pham = tim_san_pham_theo_ma_sp(ma_sp, danh_sach_san_pham)

    if not san_pham:
        print(f"Lỗi: Không tìm thấy sản phẩm với mã '{ma_sp}'.")
        return

    print(f"Thông tin sản phẩm: {san_pham['tenSP']} - Tồn kho hiện tại: {san_pham['soLuongTon']:,}")
    while True:
        try:
            so_luong_xuat = int(input("Nhập số lượng cần xuất (số dương): "))
            if so_luong_xuat <= 0:
                print("Lỗi: Số lượng xuất phải là số dương.")
            else:
                break
        except ValueError:
            print("Lỗi: Số lượng xuất phải là một số nguyên.")

    if so_luong_xuat > san_pham['soLuongTon']:
        print(f"Lỗi: Không đủ hàng tồn kho. Chỉ có {san_pham['soLuongTon']:,} sản phẩm '{san_pham['tenSP']}' trong kho.")
    else:
        san_pham['soLuongTon'] -= so_luong_xuat
        ghi_log_giao_dich(f"XUAT_THU_CONG: SP '{ma_sp}', Ten '{san_pham['tenSP']}', So luong xuat: {so_luong_xuat}, Ton moi: {san_pham['soLuongTon']}")
        print(f"Xuất hàng thành công. Số lượng tồn mới của '{san_pham['tenSP']}' là {san_pham['soLuongTon']:,}.")

def _xu_ly_giao_dich_tu_file_internal(danh_sach_san_pham, ten_file_giao_dich, loai_giao_dich, ten_cot_so_luong_expected):
    """Hàm nội bộ xử lý logic chung cho việc nhập/xuất hàng từ file."""
    if not os.path.exists(ten_file_giao_dich):
        msg = f"Lỗi: File giao dịch '{ten_file_giao_dich}' không tồn tại."
        ghi_log_loi(msg)
        return

    giao_dich_thanh_cong = 0
    giao_dich_that_bai = 0
    tong_giao_dich = 0
    log_entries = []

    print(f"\n--- Bắt đầu xử lý file {loai_giao_dich} hàng: {ten_file_giao_dich} ---")
    header = None

    try:
        with open(ten_file_giao_dich, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader, None)

            if header is None or len(header) < 2:
                msg = f"Lỗi định dạng file {ten_file_giao_dich}: File rỗng hoặc thiếu header."
                log_entries.append(msg)
                giao_dich_that_bai +=1
                tong_giao_dich +=1
            else:
                ma_sp_col_name_actual = header[0].strip().lower()
                so_luong_col_name_actual = header[1].strip().lower()
                
                accepted_qty_headers = [ten_cot_so_luong_expected.lower(), 'soluong', 'số lượng']
                if loai_giao_dich == 'nhap':
                    accepted_qty_headers.extend(['soluongnhap', 'số lượng nhập'])
                elif loai_giao_dich == 'xuat':
                    accepted_qty_headers.extend(['soluongxuat', 'số lượng xuất'])

                if ma_sp_col_name_actual != 'masp' or so_luong_col_name_actual not in accepted_qty_headers:
                    msg = (f"Lỗi định dạng header file {ten_file_giao_dich}: "
                           f"Cần cột đầu là 'maSP' và cột thứ hai là '{ten_cot_so_luong_expected}' (hoặc biến thể). "
                           f"Tìm thấy: '{header[0]}', '{header[1]}'")
                    log_entries.append(msg)
                    giao_dich_that_bai +=1
                    tong_giao_dich +=1
                else:
                    for i, row in enumerate(reader, start=2):
                        tong_giao_dich += 1
                        if len(row) < 2:
                            log_msg = f"Dòng {i} file '{ten_file_giao_dich}': Định dạng không hợp lệ (thiếu cột). Bỏ qua."
                            log_entries.append(log_msg)
                            giao_dich_that_bai += 1
                            continue

                        ma_sp_gd = row[0].strip()
                        try:
                            so_luong_gd = int(row[1].strip())
                            if so_luong_gd <= 0:
                                log_msg = f"Dòng {i} file '{ten_file_giao_dich}', Mã SP '{ma_sp_gd}': Số lượng '{so_luong_gd}' phải là số dương. Giao dịch thất bại."
                                log_entries.append(log_msg)
                                giao_dich_that_bai += 1
                                continue
                        except ValueError:
                            log_msg = f"Dòng {i} file '{ten_file_giao_dich}', Mã SP '{ma_sp_gd}': Số lượng '{row[1]}' không phải là số hợp lệ. Giao dịch thất bại."
                            log_entries.append(log_msg)
                            giao_dich_that_bai += 1
                            continue

                        san_pham = tim_san_pham_theo_ma_sp(ma_sp_gd, danh_sach_san_pham)
                        if not san_pham:
                            log_msg = f"Dòng {i} file '{ten_file_giao_dich}', Mã SP '{ma_sp_gd}': Không tìm thấy sản phẩm trong kho. Giao dịch thất bại."
                            log_entries.append(log_msg)
                            giao_dich_that_bai += 1
                            continue

                        if loai_giao_dich == 'nhap':
                            san_pham['soLuongTon'] += so_luong_gd
                            log_msg = f"Dòng {i} file '{ten_file_giao_dich}', Mã SP '{ma_sp_gd}': Nhập thành công {so_luong_gd}. Tồn mới: {san_pham['soLuongTon']:,}."
                            log_entries.append(log_msg)
                            ghi_log_giao_dich(f"NHAP_FILE: File '{os.path.basename(ten_file_giao_dich)}', SP '{ma_sp_gd}', Ten '{san_pham['tenSP']}', SL Nhap: {so_luong_gd}, Ton moi: {san_pham['soLuongTon']}")
                            giao_dich_thanh_cong += 1
                        elif loai_giao_dich == 'xuat':
                            if so_luong_gd > san_pham['soLuongTon']:
                                log_msg = f"Dòng {i} file '{ten_file_giao_dich}', Mã SP '{ma_sp_gd}': Không đủ hàng tồn kho (cần {so_luong_gd}, có {san_pham['soLuongTon']:,}). Giao dịch thất bại."
                                log_entries.append(log_msg)
                                giao_dich_that_bai += 1
                            else:
                                san_pham['soLuongTon'] -= so_luong_gd
                                log_msg = f"Dòng {i} file '{ten_file_giao_dich}', Mã SP '{ma_sp_gd}': Xuất thành công {so_luong_gd}. Tồn mới: {san_pham['soLuongTon']:,}."
                                log_entries.append(log_msg)
                                ghi_log_giao_dich(f"XUAT_FILE: File '{os.path.basename(ten_file_giao_dich)}', SP '{ma_sp_gd}', Ten '{san_pham['tenSP']}', SL Xuat: {so_luong_gd}, Ton moi: {san_pham['soLuongTon']}")
                                giao_dich_thanh_cong += 1
    except FileNotFoundError:
        msg = f"Lỗi: File giao dịch '{ten_file_giao_dich}' không tìm thấy trong quá trình xử lý."
        ghi_log_loi(msg)
        return
    except Exception as e:
        msg = f"Lỗi không xác định khi xử lý file {ten_file_giao_dich}: {e}"
        ghi_log_loi(msg)
        giao_dich_that_bai = tong_giao_dich - giao_dich_thanh_cong
    finally:
        log_header = f"--- KẾT THÚC Log xử lý file {loai_giao_dich} hàng: {os.path.basename(ten_file_giao_dich)} ---"
        ghi_log_loi(log_header)
        for entry in log_entries:
            ghi_log_loi(entry)
        
        summary_msg = f"Tổng kết xử lý file '{os.path.basename(ten_file_giao_dich)}': {tong_giao_dich} dòng được xem xét. {giao_dich_thanh_cong} thành công, {giao_dich_that_bai} thất bại."
        print(summary_msg)
        if giao_dich_that_bai > 0 or \
           (tong_giao_dich > 0 and giao_dich_thanh_cong == 0 and giao_dich_that_bai == 0 and not (header is None or len(header) < 2)) or \
           (tong_giao_dich == 0 and os.path.exists(ten_file_giao_dich) and (header is not None and len(header) >=2) ):
            print(f"Chi tiết xem tại file {LOG_FILE_PATH}.")


def nhap_hang_tu_file(danh_sach_san_pham):
    """Nhập hàng loạt sản phẩm vào kho bằng cách xử lý một file giao dịch nhập hàng."""
    print("\n--- Nhập Hàng Từ File ---")
    file_path = input(f"Nhập đường dẫn đến file giao dịch nhập hàng (mặc định: {DEFAULT_IMPORT_TRANSACTION_FILE}): ").strip()
    if not file_path:
        file_path = DEFAULT_IMPORT_TRANSACTION_FILE
    _xu_ly_giao_dich_tu_file_internal(danh_sach_san_pham, file_path, 'nhap', 'soLuongNhap')


def xuat_hang_tu_file(danh_sach_san_pham):
    """Xuất hàng loạt sản phẩm khỏi kho bằng cách xử lý một file giao dịch xuất hàng."""
    print("\n--- Xuất Hàng Từ File ---")
    file_path = input(f"Nhập đường dẫn đến file giao dịch xuất hàng (mặc định: {DEFAULT_EXPORT_TRANSACTION_FILE}): ").strip()
    if not file_path:
        file_path = DEFAULT_EXPORT_TRANSACTION_FILE
    _xu_ly_giao_dich_tu_file_internal(danh_sach_san_pham, file_path, 'xuat', 'soLuongXuat')


def tim_kiem_san_pham_theo_ma(danh_sach_san_pham):
    """Cho phép người dùng tìm kiếm một sản phẩm dựa trên mã sản phẩm."""
    print("\n--- Tìm Kiếm Sản Phẩm Theo Mã SP ---")
    ma_sp_can_tim = input("Nhập mã sản phẩm cần tìm: ").strip()
    san_pham = tim_san_pham_theo_ma_sp(ma_sp_can_tim, danh_sach_san_pham)

    if san_pham:
        print("Thông tin sản phẩm tìm thấy:")
        print(f"  Mã SP        : {san_pham['maSP']}")
        print(f"  Tên Sản Phẩm : {san_pham['tenSP']}")
        print(f"  Đơn Vị Tính  : {san_pham['donViTinh']}")
        print(f"  Số Lượng Tồn : {san_pham['soLuongTon']:,}")
        print(f"  Đơn Giá      : {san_pham['donGia']:,}")
    else:
        print(f"Không tìm thấy sản phẩm với mã '{ma_sp_can_tim}'.")

def tim_kiem_san_pham_theo_ten(danh_sach_san_pham):
    """Cho phép người dùng tìm kiếm sản phẩm dựa trên tên sản phẩm."""
    print("\n--- Tìm Kiếm Sản Phẩm Theo Tên SP ---")
    ten_can_tim = input("Nhập tên hoặc một phần tên sản phẩm cần tìm: ").strip()
    
    if not ten_can_tim:
        print("Vui lòng nhập tên cần tìm.")
        return

    ket_qua_tim_kiem = []
    for sp in danh_sach_san_pham:
        if ten_can_tim.lower() in sp['tenSP'].lower():
            ket_qua_tim_kiem.append(sp)

    if ket_qua_tim_kiem:
        print(f"\n--- Kết Quả Tìm Kiếm cho '{ten_can_tim}' ---")
        print(f"{'Mã SP':<12} | {'Tên Sản Phẩm':<30} | {'ĐVT':<10} | {'Số Lượng Tồn':>15} | {'Đơn Giá':>12}")
        print("-" * 85)
        for sp in ket_qua_tim_kiem:
            print(f"{sp['maSP']:<12} | {sp['tenSP']:<30} | {sp['donViTinh']:<10} | {sp['soLuongTon']:>15,} | {sp['donGia']:>12,}")
        print("-" * 85)
    else:
        print(f"Không tìm thấy sản phẩm nào có tên chứa '{ten_can_tim}'.")


def liet_ke_san_pham_sap_het_hang(danh_sach_san_pham):
    """Liệt kê các sản phẩm có số lượng tồn kho dưới một ngưỡng nhất định."""
    print("\n--- Liệt Kê Sản Phẩm Sắp Hết Hàng ---")
    
    try:
        nguong_str = input("Nhập ngưỡng số lượng tồn để cảnh báo (số không âm): ")
        nguong_so_luong_ton = int(nguong_str)
        if nguong_so_luong_ton < 0:
            print("Lỗi: Ngưỡng số lượng tồn phải là số không âm.")
            return
    except ValueError:
        print("Lỗi: Ngưỡng số lượng tồn không hợp lệ. Vui lòng nhập số.")
        return

    san_pham_can_canh_bao = []
    for sp in danh_sach_san_pham:
        if sp['soLuongTon'] <= nguong_so_luong_ton:
            san_pham_can_canh_bao.append(sp)
    
    if san_pham_can_canh_bao:
        print(f"\n--- Danh Sách Sản Phẩm Sắp Hết Hàng (Ngưỡng <= {nguong_so_luong_ton:,}) ---")
        print(f"{'Mã SP':<12} | {'Tên Sản Phẩm':<30} | {'ĐVT':<10} | {'Số Lượng Tồn':>15} | {'Đơn Giá':>12}")
        print("-" * 85)
        for sp in san_pham_can_canh_bao:
            print(f"{sp['maSP']:<12} | {sp['tenSP']:<30} | {sp['donViTinh']:<10} | {sp['soLuongTon']:>15,} | {sp['donGia']:>12,}")
        print("-" * 85)
    else:
        print(f"Không có sản phẩm nào sắp hết hàng với ngưỡng <= {nguong_so_luong_ton:,}.")

def doc_lich_su_giao_dich():
    """Đọc và hiển thị lịch sử giao dịch từ file lichsugiaodich.txt."""
    print("\n--- Lịch Sử Giao Dịch ---")
    try:
        if not os.path.exists(FILE_LICH_SU_GIAO_DICH) or os.path.getsize(FILE_LICH_SU_GIAO_DICH) == 0:
            print("Lịch sử giao dịch trống.")
            ghi_log_loi(f"Truy cập lịch sử giao dịch: {FILE_LICH_SU_GIAO_DICH} trống hoặc không tồn tại.")
            return

        with open(FILE_LICH_SU_GIAO_DICH, 'r', encoding='utf-8') as f:
            history_content = f.read()
            if not history_content.strip():
                 print("Lịch sử giao dịch trống.")
                 ghi_log_loi(f"Truy cập lịch sử giao dịch: {FILE_LICH_SU_GIAO_DICH} chỉ chứa khoảng trắng.")
                 return
            print(history_content)
        ghi_log_loi(f"Truy cập lịch sử giao dịch: Hiển thị thành công từ {FILE_LICH_SU_GIAO_DICH}.")
    except IOError:
        msg = f"Lỗi: Không thể đọc file lịch sử giao dịch: {FILE_LICH_SU_GIAO_DICH}"
        print(msg)
        ghi_log_loi(msg)
    except Exception as e:
        msg = f"Lỗi không xác định khi đọc lịch sử giao dịch: {e}"
        print(msg)
        ghi_log_loi(msg)