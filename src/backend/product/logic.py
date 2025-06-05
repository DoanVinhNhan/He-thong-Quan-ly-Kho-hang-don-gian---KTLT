# /src/backend/product/logic.py
from ..common import quan_ly_du_lieu as qldl

def them_san_pham_moi(sku, name, unit_of_measure, current_stock_str, price_str, description):
    """Logic nghiệp vụ để thêm sản phẩm mới."""
    if not (sku and len(sku) <= 10):
        return False, f"Lỗi: Mã SKU tự động '{sku}' không hợp lệ."
    if not (name and len(name) <= 100): 
        return False, "Lỗi: Tên sản phẩm không hợp lệ (phải có, tối đa 100 ký tự)."
    if unit_of_measure and len(unit_of_measure) > 20: 
        return False, "Lỗi: Đơn vị tính tối đa 20 ký tự."

    try:
        current_stock = int(float(current_stock_str)) 
        price = int(float(price_str))
        if current_stock < 0 or price < 0:
            return False, "Lỗi: Số lượng tồn và đơn giá không được là số âm."
    except ValueError:
        return False, "Lỗi: Số lượng tồn và đơn giá phải là số hợp lệ."

    existing_product = db_product.db_get_product_by_sku(sku)
    if existing_product:
        msg = f"Lỗi: Mã SKU tự động '{sku}' đã tồn tại. Vui lòng thử lại."
        qldl.ghi_log_loi(f"Thêm sản phẩm thất bại (SKU tự động trùng): {msg}")
        return False, msg

    product_id, add_msg = db_product.db_add_product(name, sku, description, unit_of_measure, current_stock, price)
    
    if product_id:
        qldl.ghi_log_giao_dich(f"THEM_SP_DB_WEB: SKU '{sku}', Tên '{name}'. {add_msg}")
        qldl.ghi_log_loi(f"Thêm sản phẩm DB (web): SKU '{sku}'. Thành công.")
        return True, add_msg
    else:
        qldl.ghi_log_loi(f"Thêm sản phẩm DB thất bại cho SKU '{sku}' (web): {add_msg}")
        return False, add_msg