# /src/backend/report/logic.py
from . import database as db_report

def liet_ke_san_pham_sap_het_hang(nguong_ton_str):
    """Logic nghiệp vụ để lấy danh sách sản phẩm sắp hết hàng."""
    try:
        nguong = int(float(nguong_ton_str))
        if nguong < 0:
             return [], "Ngưỡng tồn kho không được là số âm."
    except ValueError:
        return [], "Ngưỡng tồn kho phải là một số."

    low_stock_products = db_report.db_get_low_stock_products(nguong)
    
    if low_stock_products:
        msg = f"Tìm thấy {len(low_stock_products)} sản phẩm có tồn kho &lt;= {nguong}."
        return low_stock_products, msg
    else:
        msg = f"Không có sản phẩm nào có tồn kho &lt;= {nguong}."
        return [], msg