# /src/backend/product/logic.py
# File này chứa logic nghiệp vụ (business logic) cho các hoạt động liên quan đến sản phẩm.
# Nó đóng vai trò trung gian giữa lớp handler (tiếp nhận request) và lớp database (truy cập dữ liệu).

from ..common import quan_ly_du_lieu as qldl
from . import database as db_product # Đổi tên để tránh nhầm lẫn

def them_san_pham_moi(sku, name, unit_of_measure, current_stock_str, price_str, description):
    """
    Logic nghiệp vụ để thêm một sản phẩm mới.
    Hàm này thực hiện các bước xác thực (validation) dữ liệu đầu vào
    trước khi gọi hàm của lớp database để thêm sản phẩm vào cơ sở dữ liệu.

    Args:
        sku (str): Mã SKU (đã được tạo tự động).
        name (str): Tên sản phẩm.
        unit_of_measure (str): Đơn vị tính.
        current_stock_str (str): Số lượng tồn kho ban đầu (dạng chuỗi).
        price_str (str): Đơn giá (dạng chuỗi).
        description (str): Mô tả sản phẩm.

    Returns:
        tuple: (bool_thành_công, str_thông_báo_kết_quả)
    """
    # --- Bước 1: Xác thực dữ liệu đầu vào ---
    if not (sku and len(sku) <= 10):
        return False, f"Lỗi: Mã SKU '{sku}' không hợp lệ."
    if not (name and len(name) <= 100): 
        return False, "Lỗi: Tên sản phẩm không hợp lệ (phải có, tối đa 100 ký tự)."
    if unit_of_measure and len(unit_of_measure) > 20: 
        return False, "Lỗi: Đơn vị tính tối đa 20 ký tự."

    # Xác thực và chuyển đổi các giá trị số
    try:
        current_stock = int(float(current_stock_str)) 
        price = int(float(price_str))
        if current_stock < 0 or price < 0:
            return False, "Lỗi: Số lượng tồn và đơn giá không được là số âm."
    except ValueError:
        return False, "Lỗi: Số lượng tồn và đơn giá phải là số hợp lệ."

    # --- Bước 2: Kiểm tra sự tồn tại của SKU ---
    # Mặc dù SKU được tạo duy nhất, vẫn kiểm tra lại để đảm bảo an toàn
    existing_product = db_product.db_get_product_by_sku(sku)
    if existing_product:
        msg = f"Lỗi: Mã SKU '{sku}' đã tồn tại. Vui lòng thử lại."
        qldl.ghi_log_loi(f"Thêm sản phẩm thất bại (SKU trùng): {msg}")
        return False, msg

    # --- Bước 3: Gọi lớp database để thực hiện thêm mới ---
    product_id, add_msg = db_product.db_add_product(name, sku, description, unit_of_measure, current_stock, price)
    
    # --- Bước 4: Xử lý kết quả và ghi log ---
    if product_id:
        # Ghi log thành công
        qldl.ghi_log_giao_dich(f"THEM_SP_WEB: SKU '{sku}', Tên '{name}'.")
        qldl.ghi_log_loi(f"Thêm sản phẩm (web): SKU '{sku}'. Thành công.")
        return True, add_msg
    else:
        # Ghi log thất bại
        qldl.ghi_log_loi(f"Thêm sản phẩm thất bại cho SKU '{sku}' (web): {add_msg}")
        return False, add_msg
