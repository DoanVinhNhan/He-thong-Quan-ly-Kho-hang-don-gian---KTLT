# /src/backend/report/logic.py
# Chứa logic nghiệp vụ cho việc tạo báo cáo.
from . import database as db_report

def liet_ke_san_pham_sap_het_hang(nguong_ton_str):
    """
    Logic nghiệp vụ để lấy danh sách sản phẩm sắp hết hàng.
    Xác thực đầu vào và gọi hàm database tương ứng.

    Args:
        nguong_ton_str (str): Ngưỡng tồn kho (dạng chuỗi) do người dùng nhập.

    Returns:
        tuple: (list_sản_phẩm, str_thông_báo)
    """
    # Xác thực ngưỡng tồn kho phải là số không âm.
    try:
        nguong = int(float(nguong_ton_str))
        if nguong < 0:
             return [], "Ngưỡng tồn kho không được là số âm."
    except ValueError:
        return [], "Ngưỡng tồn kho phải là một số."

    # Gọi hàm database để lấy dữ liệu.
    low_stock_products = db_report.db_get_low_stock_products(nguong)
    
    # Tạo thông báo kết quả.
    if low_stock_products:
        msg = f"Tìm thấy {len(low_stock_products)} sản phẩm có tồn kho &lt;= {nguong}."
        return low_stock_products, msg
    else:
        msg = f"Không có sản phẩm nào có tồn kho &lt;= {nguong}."
        return [], msg
