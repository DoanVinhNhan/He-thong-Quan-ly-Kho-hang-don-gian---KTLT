# main.py
import os
import csv
import quan_ly_du_lieu as qldl
import xu_ly_kho as xlk

DANH_SACH_SAN_PHAM = []

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def hien_thi_menu_chinh():
    """Hiển thị menu chính của chương trình."""
    print("\n===== HỆ THỐNG QUẢN LÝ KHO HÀNG ĐƠN GIẢN =====")
    print("1. Quản lý Sản phẩm")
    print("2. Quản lý Nhập / Xuất kho")
    print("3. Tìm kiếm Sản phẩm")
    print("4. Liệt kê Sản phẩm sắp hết hàng")
    print("5. Lưu dữ liệu vào file")
    print("0. Thoát chương trình")
    print("==============================================")

def hien_thi_menu_quan_ly_san_pham():
    print("\n--- Menu Quản Lý Sản Phẩm ---")
    print("1. Thêm sản phẩm mới")
    print("2. Xem tất cả các sản phẩm trong kho")
    print("0. Quay lại menu chính")

def hien_thi_menu_quan_ly_nhap_xuat():
    print("\n--- Menu Quản Lý Nhập / Xuất Kho ---")
    print("1. Nhập hàng thủ công")
    print("2. Xuất hàng thủ công")
    print("3. Nhập hàng bằng file")
    print("4. Xuất hàng bằng file")
    print("5. Xem lịch sử giao dịch") # New option
    print("0. Quay lại menu chính")

def hien_thi_menu_tim_kiem_san_pham():
    print("\n--- Menu Tìm Kiếm Sản Phẩm ---")
    print("1. Tìm kiếm theo Mã sản phẩm")
    print("2. Tìm kiếm theo Tên sản phẩm")
    print("0. Quay lại menu chính")

def hien_thi_menu_liet_ke_dac_biet():
    print("\n--- Menu Liệt Kê Sản Phẩm Sắp Hết Hàng ---")
    print("1. Liệt kê sản phẩm sắp hết hàng theo ngưỡng")
    print("0. Quay lại menu chính")

def nhap_lua_chon(min_val, max_val, prompt="Nhập lựa chọn của bạn: "):
    """Nhận và xác thực lựa chọn của người dùng."""
    while True:
        try:
            lua_chon_str = input(prompt)
            lua_chon = int(lua_chon_str)
            if min_val <= lua_chon <= max_val:
                return lua_chon
            else:
                print(f"Lựa chọn không hợp lệ. Vui lòng chọn từ {min_val} đến {max_val}.")
        except ValueError:
            print("Đầu vào không phải là số. Vui lòng nhập lại.")

def chuong_trinh_chinh():
    """Hàm chính điều khiển luồng của ứng dụng."""
    global DANH_SACH_SAN_PHAM
    DANH_SACH_SAN_PHAM = qldl.tai_du_lieu_tu_file()

    while True:
        clear_screen()
        hien_thi_menu_chinh()
        lua_chon = nhap_lua_chon(0, 5)

        if lua_chon == 1:
            while True:
                clear_screen()
                hien_thi_menu_quan_ly_san_pham()
                lc_qlsp = nhap_lua_chon(0,2)
                if lc_qlsp == 1: xlk.them_san_pham_moi(DANH_SACH_SAN_PHAM)
                elif lc_qlsp == 2: xlk.liet_ke_tat_ca_san_pham(DANH_SACH_SAN_PHAM)
                elif lc_qlsp == 0: break
                input("\nNhấn Enter để tiếp tục...")
        elif lua_chon == 2:
            while True:
                clear_screen()
                hien_thi_menu_quan_ly_nhap_xuat()
                lc_qlnx = nhap_lua_chon(0,5) # Max value is now 5
                if lc_qlnx == 1: xlk.nhap_hang_cho_san_pham(DANH_SACH_SAN_PHAM)
                elif lc_qlnx == 2: xlk.xuat_hang_khoi_kho(DANH_SACH_SAN_PHAM)
                elif lc_qlnx == 3: xlk.nhap_hang_tu_file(DANH_SACH_SAN_PHAM)
                elif lc_qlnx == 4: xlk.xuat_hang_tu_file(DANH_SACH_SAN_PHAM)
                elif lc_qlnx == 5: xlk.doc_lich_su_giao_dich() # Call the new function
                elif lc_qlnx == 0: break
                input("\nNhấn Enter để tiếp tục...")
        elif lua_chon == 3:
            while True:
                clear_screen()
                hien_thi_menu_tim_kiem_san_pham()
                lc_tk = nhap_lua_chon(0,2)
                if lc_tk == 1: xlk.tim_kiem_san_pham_theo_ma(DANH_SACH_SAN_PHAM)
                elif lc_tk == 2: xlk.tim_kiem_san_pham_theo_ten(DANH_SACH_SAN_PHAM)
                elif lc_tk == 0: break
                input("\nNhấn Enter để tiếp tục...")
        elif lua_chon == 4:
            while True:
                clear_screen()
                hien_thi_menu_liet_ke_dac_biet()
                lc_lkdb = nhap_lua_chon(0,1)
                if lc_lkdb == 1: xlk.liet_ke_san_pham_sap_het_hang(DANH_SACH_SAN_PHAM)
                elif lc_lkdb == 0: break
                input("\nNhấn Enter để tiếp tục...")
        elif lua_chon == 5:
            qldl.luu_du_lieu_vao_file(DANH_SACH_SAN_PHAM)
            input("\nNhấn Enter để tiếp tục...")
        elif lua_chon == 0:
            print("\nBạn có muốn lưu dữ liệu trước khi thoát không?")
            luu_truoc_khi_thoat = input("Nhập 'c' hoặc 'C' để lưu, bất kỳ phím nào khác để thoát không lưu: ").strip().lower()
            if luu_truoc_khi_thoat == 'c':
                qldl.luu_du_lieu_vao_file(DANH_SACH_SAN_PHAM)
            print("Đang thoát chương trình. Tạm biệt!")
            break

if __name__ == "__main__":
    if not os.path.exists(xlk.DEFAULT_IMPORT_TRANSACTION_FILE):
        with open(xlk.DEFAULT_IMPORT_TRANSACTION_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['maSP', 'soLuongNhap'])
    
    if not os.path.exists(xlk.DEFAULT_EXPORT_TRANSACTION_FILE):
        with open(xlk.DEFAULT_EXPORT_TRANSACTION_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['maSP', 'soLuongXuat'])

    chuong_trinh_chinh()