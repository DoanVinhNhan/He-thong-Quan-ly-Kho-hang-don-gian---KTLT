# /src/backend/product/logic.py
# File này chứa logic nghiệp vụ (business logic) cho các hoạt động liên quan đến sản phẩm.
# Nó đóng vai trò trung gian giữa lớp handler (tiếp nhận request) và lớp database (truy cập dữ liệu).

from ..common import quan_ly_du_lieu as qldl
from . import database as db_product # Đổi tên để tránh nhầm lẫn
from ..transaction.database import db_check_product_has_transactions

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

    # Gọi hàm DB mới để thực hiện thêm sản phẩm và giao dịch ban đầu
    product_id, add_msg = db_product.db_add_product(
        name, sku, description, unit_of_measure, current_stock, price
    )
    
    if product_id:
        qldl.ghi_log_giao_dich(f"THEM_SP_WEB: SKU '{sku}', Tên '{name}'.")
        qldl.ghi_log_loi(f"Thêm sản phẩm (web): SKU '{sku}'. Thành công.")
        return True, add_msg
    else:
        qldl.ghi_log_loi(f"Thêm sản phẩm thất bại cho SKU '{sku}' (web): {add_msg}")
        return False, add_msg
        
def sua_san_pham(product_id, name, unit_of_measure, price_str, description):
    """
    Logic nghiệp vụ để cập nhật thông tin sản phẩm.
    Xác thực dữ liệu đầu vào trước khi gọi lớp database.
    """
    # --- Bước 1: Xác thực dữ liệu đầu vào ---
    if not (name and len(name) <= 100): 
        return False, "Lỗi: Tên sản phẩm không hợp lệ (phải có, tối đa 100 ký tự)."
    if unit_of_measure and len(unit_of_measure) > 20: 
        return False, "Lỗi: Đơn vị tính tối đa 20 ký tự."

    try:
        price = int(float(price_str))
        if price < 0:
            return False, "Lỗi: Đơn giá không được là số âm."
    except ValueError:
        return False, "Lỗi: Đơn giá phải là số hợp lệ."

    # --- Bước 2: Gọi lớp database để thực hiện cập nhật ---
    success, message = db_product.db_update_product(product_id, name, description, unit_of_measure, price)
    
    # --- Bước 3: Ghi log ---
    if success:
        product = db_product.db_get_product_by_id(product_id)
        qldl.ghi_log_giao_dich(f"SUA_SP_WEB: SKU '{product['sku']}', Tên '{name}'.")
    
    return success, message
def xoa_san_pham(product_id):
    """
    Logic nghiệp vụ để xóa một sản phẩm.
    """
    # Bước 1: Kiểm tra sản phẩm có tồn tại không
    product = db_product.db_get_product_by_id(product_id)
    if not product:
        return False, "Sản phẩm không tồn tại."

    # Bước 3: Gọi lớp database để xóa
    success, message = db_product.db_delete_product_by_id(product_id)
    if success:
        qldl.ghi_log_giao_dich(f"XOA_MEM_SP_WEB: SKU '{product['sku']}', Tên '{product['name']}'.")
        qldl.ghi_log_loi(f"Xoá mềm sản phẩm (web): SKU '{product['sku']}'. Thành công.")

    return success, message