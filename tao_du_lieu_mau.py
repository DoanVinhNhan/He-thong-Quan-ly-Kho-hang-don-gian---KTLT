# tao_du_lieu_mau.py
# Script để tạo một cơ sở dữ liệu SQLite với dữ liệu mẫu lớn,
# đã được cập nhật để hỗ trợ xóa mềm và tự động ghi nhận tồn kho ban đầu.
# Bao gồm 100 sản phẩm và 10,000 giao dịch kho.

import sqlite3
import datetime
import os
import random
import uuid
import time # Để theo dõi và in ra thời gian thực thi của các tác vụ

# --- Cấu hình Database ---
DB_NAME = 'miniventory_sqlite.db' # Đổi tên DB để không ghi đè file cũ

# --- Xử lý tương thích kiểu dữ liệu Datetime với SQLite ---
def adapt_datetime_iso(val):
    """Chuyển đối tượng datetime thành chuỗi ISO 8601."""
    return val.isoformat()

def convert_datetime_iso(val):
    """Chuyển chuỗi ISO 8601 (dạng bytes) từ DB về lại đối tượng datetime."""
    try:
        return datetime.datetime.fromisoformat(val.decode())
    except ValueError:
        return datetime.datetime.strptime(val.decode(), '%Y-%m-%d %H:%M:%S.%f')

sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
sqlite3.register_converter("timestamp", convert_datetime_iso)
# --- Kết thúc phần xử lý Datetime ---

def ghi_log(thong_bao, filename="tao_db_mau_lon.log"):
    """Hàm ghi log đơn giản để theo dõi quá trình tạo dữ liệu."""
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {thong_bao}\n")
    except IOError:
        print(f"Không thể ghi log: {thong_bao}")

# --- Các hàm thao tác với Database SQLite ---

def init_db():
    """Khởi tạo cấu trúc (schema) cho database, tạo các bảng nếu chưa tồn tại."""
    conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = conn.cursor()
    # Tạo bảng products với cột is_deleted
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT NOT NULL UNIQUE,
        description TEXT,
        unit_of_measure TEXT DEFAULT 'cái',
        current_stock INTEGER DEFAULT 0,
        price INTEGER DEFAULT 0,
        is_deleted INTEGER DEFAULT 0, -- THÊM MỚI: Cột để hỗ trợ xóa mềm (0=active, 1=deleted)
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # Tạo bảng stock_transactions (không đổi)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        transaction_type TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price INTEGER DEFAULT 0,
        total_amount INTEGER DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        user TEXT,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')
    conn.commit()
    conn.close()
    print(f"Khởi tạo/kiểm tra database SQLite '{DB_NAME}' thành công.")
    ghi_log(f"Database '{DB_NAME}' đã được khởi tạo/kiểm tra schema.")

def db_add_product_and_initial_transaction(conn, name, sku, description, unit_of_measure, current_stock=0, price=0):
    """
    SỬA ĐỔI: Thêm sản phẩm và tạo giao dịch nhập kho ban đầu nếu tồn kho > 0.
    Tất cả được thực hiện trong một DB transaction.
    """
    cursor = conn.cursor()
    try:
        stock_int = int(current_stock)
        price_int = int(price)
        current_time = datetime.datetime.now()

        # 1. Thêm sản phẩm vào bảng 'products'
        cursor.execute('''
        INSERT INTO products (name, sku, description, unit_of_measure, current_stock, price, created_at, updated_at, is_deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (name, sku, description, unit_of_measure, stock_int, price_int, current_time, current_time))

        product_id = cursor.lastrowid
        if not product_id:
            raise sqlite3.DatabaseError("Không thể lấy ID sản phẩm vừa tạo.")

        # 2. Nếu có tồn kho ban đầu, tạo một giao dịch 'IN' tương ứng
        if stock_int > 0:
            total_amount = stock_int * price_int
            cursor.execute('''
            INSERT INTO stock_transactions (product_id, transaction_type, quantity, unit_price, total_amount, notes, user, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (product_id, 'IN', stock_int, price_int, total_amount, 'Tồn kho ban đầu khi tạo sản phẩm', 'system_init', current_time))

        return product_id
    except sqlite3.IntegrityError:
        ghi_log(f"Lỗi Integrity (SKU '{sku}' có thể đã tồn tại): Không thể thêm sản phẩm '{name}'")
        return None
    except Exception as e:
        ghi_log(f"Lỗi khi thêm sản phẩm và GD ban đầu (SKU: {sku}): {e}")
        return None


def db_product_table_is_empty(conn):
    """Kiểm tra xem bảng products có dữ liệu hay không."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(id) FROM products")
    count = cursor.fetchone()[0]
    return count == 0

def db_update_product_stock(conn, product_id, new_stock):
    """Cập nhật số lượng tồn kho cho một sản phẩm."""
    cursor = conn.cursor()
    current_time = datetime.datetime.now()
    cursor.execute("UPDATE products SET current_stock = ?, updated_at = ? WHERE id = ?",
                      (new_stock, current_time, product_id))

def db_add_stock_transaction_batch(conn, transactions_data):
    """Thêm nhiều giao dịch kho cùng lúc (theo batch) để tăng hiệu năng."""
    cursor = conn.cursor()
    try:
        cursor.executemany('''
        INSERT INTO stock_transactions (product_id, transaction_type, quantity, unit_price, total_amount, notes, user, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', transactions_data)
        return True
    except Exception as e:
        ghi_log(f"Lỗi DB khi thêm batch giao dịch: {e}")
        return False

# --- Hàm tạo dữ liệu mẫu ---
def populate_large_sample_data():
    """
    Hàm chính để điền dữ liệu mẫu vào database.
    """
    conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES)

    if not db_product_table_is_empty(conn):
        print(f"Database '{DB_NAME}' đã có dữ liệu sản phẩm. Bỏ qua việc tạo dữ liệu mẫu.")
        ghi_log("Database đã có dữ liệu, không thêm dữ liệu mẫu.")
        conn.close()
        return

    # --- Giai đoạn 1: Tạo sản phẩm và giao dịch tồn kho ban đầu ---
    print("Đang thêm dữ liệu sản phẩm mẫu (100 sản phẩm) và ghi nhận tồn kho ban đầu...")
    start_time_products = time.time()

    # (Dữ liệu nguồn giữ nguyên như file gốc)
    base_names = ["Gạo Nàng Thơm", "Đường Cát Trắng", "Sữa Đặc Ngôi Sao", "Bánh Gạo An", "Kẹo Alpenliebe", "Nước Ngọt 7Up", "Bia Sài Gòn Special", "Dầu Hướng Dương", "Nước Mắm Liên Thành", "Hạt Nêm Knorr", "Mì Gói 3 Miền", "Phở Bò Cung Đình", "Bún Gạo Khô Safoco", "Miến Phú Hương", "Trà Xanh Không Độ", "Cà Phê G7", "Bột Giặt Tide", "Nước Rửa Chén Mỹ Hảo", "Kem Đánh Răng Closeup", "Bàn Chải Oral-B", "Xà Bông Lifebuoy Đỏ", "Dầu Gội Romano", "Sữa Tắm Enchanteur", "Khăn Ướt Bobby", "Giấy Vệ Sinh Bless You", "Tương Ớt Ông Chà Và", "Tương Cà Trung Thành", "Muối Tinh Khiết", "Tiêu Đen Phú Quốc", "Bánh Cosy Marie", "Bơ Tường An", "Phô Mai Con Bò Cười", "Xúc Xích Vissan", "Pate Cột Đèn", "Chà Bông Heo", "Cá Hộp Ba Cô Gái", "Rau Muống Vietgap", "Xoài Cát Hòa Lộc", "Thanh Long Chợ Gạo", "Thịt Ba Chỉ CP", "Thịt Bò Kobe", "Gà Ta Tam Hoàng", "Cá Hồi Na Uy", "Tôm Thẻ", "Mực Nang Đại Dương", "Trứng Gà Ba Huân", "Trứng Vịt Bắc Thảo", "Gia Vị Lẩu Nấm Ashima", "Snack Poca", "Bánh Tráng Cuốn", "Chả Giò Cầu Tre", "Giò Lụa Ước Lễ", "Nước Yến Song Yến", "Bánh Pía Sóc Trăng"]
    brands = ["", "Kinh Đô", "Vinamilk", "Lavie", "Hảo Hảo", "Coca-Cola", "Pepsi", "Heineken", "Tiger", "Simply", "Nam Ngư", "Ajinomoto", "Omachi", "VinaCafe", "Lipton", "Omo", "Sunlight", "PS", "Colgate", "Lifebuoy", "Clear", "Dove", "Pulppy", "An An", "Chinsu", "Cholimex", "Visalco", "Orion", "Nestle", "Dutch Lady", "TH True Milk", "Acecook", "Masan", "Vissan", "CP", "Bibica", "Đồng Nai", "Hapro"]
    units = ["Gói", "Chai", "Hộp", "Lon", "Thùng", "Bịch", "Tuýp", "Cây", "Cuộn", "Kg", "Lít", "Hũ", "Vỉ", "Combo", "Chục", "Bó"]
    descriptions_list = ["chất lượng cao", "thơm ngon hảo hạng", "tiện lợi cho gia đình", "sản xuất theo công nghệ mới", "an toàn cho sức khỏe", "được nhiều người tin dùng", "giá cả phải chăng", "hương vị truyền thống", "thiết kế bao bì đẹp mắt", "dinh dưỡng và tươi mát", "nhập khẩu chính hãng", "phiên bản giới hạn", "tiết kiệm hơn", "dành cho mọi nhà", "hỗ trợ tốt", "tăng cường năng lượng"]

    used_skus_local = set()
    target_products = 100

    conn.execute("BEGIN TRANSACTION")
    for i in range(target_products):
        sku = None
        for _ in range(20):
            random_hex = uuid.uuid4().hex[:5].upper()
            temp_sku = f"SP-{random_hex}"
            if temp_sku not in used_skus_local:
                sku = temp_sku
                break

        if not sku:
            ghi_log("Không thể tạo SKU duy nhất sau 20 lần thử, dừng thêm sản phẩm mẫu.")
            break

        name_part1 = random.choice(brands) if random.random() > 0.2 else ""
        name_part2 = base_names[i % len(base_names)]
        name = f"{name_part1} {name_part2}".strip()
        description = random.choice(descriptions_list)
        unit = random.choice(units)
        stock = random.randint(0, 500) # Tồn kho ban đầu
        price = random.randint(5, 1000) * 1000

        # SỬA ĐỔI: Gọi hàm mới
        p_id = db_add_product_and_initial_transaction(conn, name, sku, description, unit, stock, price)
        if p_id:
            print(f"  Đã thêm: {sku} - {name} (ID: {p_id}, Tồn đầu: {stock})")
            used_skus_local.add(sku)

    conn.commit()
    print(f"\nĐã thêm {len(used_skus_local)} sản phẩm vào DB và ghi nhận tồn kho ban đầu.")
    ghi_log(f"Đã thêm {len(used_skus_local)} sản phẩm mẫu vào DB.")
    end_time_products = time.time()
    print(f"Thời gian thêm sản phẩm: {end_time_products - start_time_products:.2f} giây.")

    if not used_skus_local:
        conn.close()
        return

    # --- Giai đoạn 2: Tạo giao dịch ngẫu nhiên (Nhập/Xuất) ---
    # Logic ở đây không thay đổi nhiều, chỉ cần lấy đúng tồn kho đã được cập nhật
    print("\nĐang thêm dữ liệu giao dịch mẫu (10,000 giao dịch)...")
    start_time_transactions = time.time()

    num_sample_transactions = 10000

    cursor = conn.cursor()
    # Lấy thông tin sản phẩm, không cần lấy is_deleted vì tất cả đều active
    cursor.execute("SELECT id, sku, price, current_stock FROM products WHERE is_deleted = 0")
    db_products_info = {row[1]: {'id': row[0], 'price': row[2], 'current_stock': row[3]} for row in cursor.fetchall()}

    if not db_products_info:
        conn.close()
        return

    available_skus_for_transaction = list(db_products_info.keys())
    now = datetime.datetime.now()
    transactions_batch = []
    batch_size = 500

    for i in range(num_sample_transactions):
        sku_to_transact = random.choice(available_skus_for_transaction)
        p_info = db_products_info.get(sku_to_transact)
        if not p_info: continue

        transaction_type = random.choices(['IN', 'OUT'], weights=[0.55, 0.45], k=1)[0]
        quantity = random.randint(1, 50)

        if transaction_type == 'OUT' and p_info['current_stock'] < quantity:
            continue

        transaction_datetime = now - datetime.timedelta(days=random.randint(0, 365))
        total_amount = quantity * p_info['price']
        transactions_batch.append((
            p_info['id'], transaction_type, quantity, p_info['price'], total_amount,
            f"GD tự động {i+1}", "script_10k", transaction_datetime
        ))

        if transaction_type == 'IN':
            db_products_info[sku_to_transact]['current_stock'] += quantity
        else:
            db_products_info[sku_to_transact]['current_stock'] -= quantity

        if len(transactions_batch) >= batch_size:
            conn.execute("BEGIN TRANSACTION")
            if db_add_stock_transaction_batch(conn, transactions_batch):
                conn.commit()
                print(f"  Đã ghi {len(transactions_batch)} giao dịch vào DB...")
            else:
                conn.rollback()
            transactions_batch = []

    if transactions_batch:
        conn.execute("BEGIN TRANSACTION")
        if db_add_stock_transaction_batch(conn, transactions_batch):
            conn.commit()
            print(f"  Đã ghi {len(transactions_batch)} giao dịch cuối cùng vào DB...")
        else:
            conn.rollback()

    # --- Giai đoạn 3: Cập nhật tồn kho cuối cùng ---
    print("\nĐang cập nhật tồn kho cuối cùng cho các sản phẩm...")
    conn.execute("BEGIN TRANSACTION")
    for sku, info in db_products_info.items():
        db_update_product_stock(conn, info['id'], info['current_stock'])
    conn.commit()
    print("Hoàn tất cập nhật tồn kho cuối cùng.")

    end_time_transactions = time.time()
    ghi_log(f"Đã tạo {num_sample_transactions} giao dịch mẫu.")
    print(f"Thời gian thêm giao dịch và cập nhật tồn kho: {end_time_transactions - start_time_transactions:.2f} giây.")
    conn.close()

# --- Chạy chương trình ---
if __name__ == '__main__':
    if os.path.exists(DB_NAME):
        response = input(f"File database '{DB_NAME}' đã tồn tại. Bạn có muốn XÓA và tạo lại dữ liệu mẫu không? (yes/no): ").lower()
        if response == 'yes':
            print(f"Đang xóa file '{DB_NAME}' cũ...")
            os.remove(DB_NAME)
            ghi_log(f"Người dùng đã chọn xóa và tạo lại DB '{DB_NAME}'.")
            init_db()
            populate_large_sample_data()
        else:
            print("Đã hủy bỏ thao tác. Giữ nguyên file DB hiện tại.")
    else:
        print(f"File database '{DB_NAME}' chưa tồn tại. Bắt đầu tạo mới...")
        init_db()
        populate_large_sample_data()

    print(f"\nQuá trình đã hoàn tất.")