# tao_db_mau_lon.py
import sqlite3
import datetime
import os
import random
import uuid
import time # Để theo dõi thời gian chạy

# --- Cấu hình Database ---
DB_NAME = 'miniventory_sqlite.db'

# --- Xử lý DeprecationWarning cho datetime với SQLite ---
def adapt_datetime_iso(val):
    return val.isoformat()

def convert_datetime_iso(val):
    try:
        return datetime.datetime.fromisoformat(val.decode())
    except ValueError:
        return datetime.datetime.strptime(val.decode(), '%Y-%m-%d %H:%M:%S.%f')

sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
sqlite3.register_converter("timestamp", convert_datetime_iso)
# --- Kết thúc phần xử lý DeprecationWarning ---

# --- Hàm ghi log đơn giản ---
def ghi_log(thong_bao, filename="tao_db_mau_lon.log"):
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {thong_bao}\n")
    except IOError:
        print(f"Không thể ghi log: {thong_bao}")

# --- Các hàm thao tác với Database SQLite ---
def init_db():
    conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = conn.cursor()
    # Bảng products
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT NOT NULL UNIQUE,
        description TEXT,
        unit_of_measure TEXT DEFAULT 'cái',
        current_stock INTEGER DEFAULT 0,
        price INTEGER DEFAULT 0, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # Bảng stock_transactions
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

def db_add_product(conn, name, sku, description, unit_of_measure, current_stock=0, price=0):
    cursor = conn.cursor()
    try:
        stock_int = int(current_stock)
        price_int = int(price)
        current_time = datetime.datetime.now()
        cursor.execute('''
        INSERT INTO products (name, sku, description, unit_of_measure, current_stock, price, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, sku, description, unit_of_measure, stock_int, price_int, current_time, current_time))
        return cursor.lastrowid 
    except sqlite3.IntegrityError:
        ghi_log(f"Lỗi Integrity (SKU '{sku}' có thể đã tồn tại): Không thể thêm sản phẩm '{name}'")
        return None 
    except Exception as e:
        ghi_log(f"Lỗi khi thêm sản phẩm (SKU: {sku}, Tên: {name}): {e}")
        return None

def db_get_product_info_for_transaction(conn, product_id):
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, sku, current_stock, price FROM products WHERE id = ?", (product_id,))
    return cursor.fetchone()

def db_product_table_is_empty(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(id) FROM products")
    count = cursor.fetchone()[0]
    return count == 0

def db_update_product_stock(conn, product_id, new_stock):
    cursor = conn.cursor()
    current_time = datetime.datetime.now()
    cursor.execute("UPDATE products SET current_stock = ?, updated_at = ? WHERE id = ?",
                      (new_stock, current_time, product_id))

def db_add_stock_transaction_batch(conn, transactions_data):
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
    conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES)

    if not db_product_table_is_empty(conn):
        print(f"Database '{DB_NAME}' đã có dữ liệu sản phẩm. Bỏ qua việc tạo dữ liệu mẫu.")
        ghi_log("Database đã có dữ liệu, không thêm dữ liệu mẫu.")
        conn.close()
        return

    print("Đang thêm dữ liệu sản phẩm mẫu (100 sản phẩm)...")
    start_time_products = time.time()
    
    base_names = ["Gạo Nàng Thơm", "Đường Cát Trắng", "Sữa Đặc Ngôi Sao", "Bánh Gạo An", "Kẹo Alpenliebe", 
                  "Nước Ngọt 7Up", "Bia Sài Gòn Special", "Dầu Hướng Dương", "Nước Mắm Liên Thành", 
                  "Hạt Nêm Knorr", "Mì Gói 3 Miền", "Phở Bò Cung Đình", "Bún Gạo Khô Safoco", "Miến Phú Hương", 
                  "Trà Xanh Không Độ", "Cà Phê G7", "Bột Giặt Tide", "Nước Rửa Chén Mỹ Hảo", 
                  "Kem Đánh Răng Closeup", "Bàn Chải Oral-B", "Xà Bông Lifebuoy Đỏ", "Dầu Gội Romano", 
                  "Sữa Tắm Enchanteur", "Khăn Ướt Bobby", "Giấy Vệ Sinh Bless You", "Tương Ớt Ông Chà Và", 
                  "Tương Cà Trung Thành", "Muối Tinh Khiết", "Tiêu Đen Phú Quốc", "Bánh Cosy Marie", 
                  "Bơ Tường An", "Phô Mai Con Bò Cười", "Xúc Xích Vissan", "Pate Cột Đèn", "Chà Bông Heo", 
                  "Cá Hộp Ba Cô Gái", "Rau Muống Vietgap", "Xoài Cát Hòa Lộc", "Thanh Long Chợ Gạo", 
                  "Thịt Ba Chỉ CP", "Thịt Bò Kobe", "Gà Ta Tam Hoàng", "Cá Hồi Na Uy", "Tôm Thẻ", 
                  "Mực Nang Đại Dương", "Trứng Gà Ba Huân", "Trứng Vịt Bắc Thảo", "Gia Vị Lẩu Nấm Ashima", "Snack Poca",
                  "Bánh Tráng Cuốn", "Chả Giò Cầu Tre", "Giò Lụa Ước Lễ", "Nước Yến Song Yến", "Bánh Pía Sóc Trăng"]
    
    brands = ["", "Kinh Đô", "Vinamilk", "Lavie", "Hảo Hảo", "Coca-Cola", "Pepsi", "Heineken", "Tiger", "Simply", 
              "Nam Ngư", "Ajinomoto", "Omachi", "VinaCafe", "Lipton", "Omo", "Sunlight", "PS", "Colgate", 
              "Lifebuoy", "Clear", "Dove", "Pulppy", "An An", "Chinsu", "Cholimex", "Visalco", "Orion", 
              "Nestle", "Dutch Lady", "TH True Milk", "Acecook", "Masan", "Vissan", "CP", "Bibica", "Đồng Nai", "Hapro"]
    
    units = ["Gói", "Chai", "Hộp", "Lon", "Thùng", "Bịch", "Tuýp", "Cây", "Cuộn", "Kg", "Lít", "Hũ", "Vỉ", "Combo", "Chục", "Bó"]
    
    descriptions_list = [
        "chất lượng cao", "thơm ngon hảo hạng", "tiện lợi cho gia đình", "sản xuất theo công nghệ mới",
        "an toàn cho sức khỏe", "được nhiều người tin dùng", "giá cả phải chăng", "hương vị truyền thống",
        "thiết kế bao bì đẹp mắt", "dinh dưỡng và tươi mát", "nhập khẩu chính hãng", "phiên bản giới hạn",
        "tiết kiệm hơn", "dành cho mọi nhà", "hỗ trợ tốt", "tăng cường năng lượng"
    ]

    used_skus_local = set()
    target_products = 100

    conn.execute("BEGIN TRANSACTION")
    for i in range(target_products):
        sku = None
        # *** SỬA ĐỔI: Tạo SKU duy nhất THEO ĐÚNG ĐỊNH DẠNG của ứng dụng chính (SP-XXXXX) ***
        for _ in range(20): # Thử tối đa 20 lần để tìm SKU chưa được dùng
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
        if random.random() < 0.2: name += " " + random.choice(["đặc biệt", "loại 1", ""])
        name = name.strip()[:100]

        description = random.choice(descriptions_list)
        if random.random() < 0.2: description += ", " + random.choice(descriptions_list)
        description = description[:200]
        
        unit = random.choice(units)
        stock = random.randint(0, 500)
        price = random.randint(5, 1000) * 1000

        p_id = db_add_product(conn, name, sku, description, unit, stock, price)
        if p_id:
            print(f"  Đã thêm: {sku} - {name} (ID: {p_id})")
            used_skus_local.add(sku)
        else:
            print(f"  Lỗi khi thêm {sku} - {name} (có thể SKU đã tồn tại hoặc lỗi khác).")

    conn.commit()
    print(f"\nĐã thêm {len(used_skus_local)} sản phẩm vào DB.")
    ghi_log(f"Đã thêm {len(used_skus_local)} sản phẩm mẫu vào DB.")
    end_time_products = time.time()
    print(f"Thời gian thêm sản phẩm: {end_time_products - start_time_products:.2f} giây.")

    if not used_skus_local:
        print("Không có sản phẩm nào được thêm, không thể tạo giao dịch mẫu.")
        conn.close()
        return

    print("\nĐang thêm dữ liệu giao dịch mẫu (10,000 giao dịch)...")
    start_time_transactions = time.time()
    
    num_sample_transactions = 10000
    created_transactions = 0
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, sku, price, current_stock FROM products")
    db_products_info = {row[1]: {'id': row[0], 'price': row[2], 'current_stock': row[3]} for row in cursor.fetchall()}
    
    if not db_products_info:
        print("Lỗi: Không thể lấy thông tin sản phẩm từ DB để tạo giao dịch.")
        conn.close()
        return

    available_skus_for_transaction = list(db_products_info.keys())
    
    now = datetime.datetime.now()
    transactions_batch = []
    batch_size = 500

    for i in range(num_sample_transactions):
        if not available_skus_for_transaction: break

        sku_to_transact = random.choice(available_skus_for_transaction)
        p_info = db_products_info.get(sku_to_transact)
        if not p_info: continue

        p_id = p_info['id']
        unit_price_for_transaction = p_info['price']
        current_stock_in_mem = p_info['current_stock']

        transaction_type = random.choices(['IN', 'OUT'], weights=[0.6, 0.4], k=1)[0]
        quantity = random.randint(1, int(current_stock_in_mem * 0.3) if transaction_type == 'OUT' and current_stock_in_mem > 3 else 50)
        if quantity == 0 and transaction_type == 'OUT' and current_stock_in_mem > 0: quantity = 1
        if quantity == 0 and transaction_type == 'IN': quantity = random.randint(1, 50)

        if transaction_type == 'OUT' and current_stock_in_mem < quantity:
            continue 

        notes = f"GD tự động {i+1}"
        
        days_ago = random.randint(0, 365)
        transaction_datetime = now - datetime.timedelta(days=days_ago, hours=random.randint(0,23), minutes=random.randint(0,59))
        
        if quantity > 0 :
            total_amount = quantity * unit_price_for_transaction
            transactions_batch.append((
                p_id, transaction_type, quantity, unit_price_for_transaction, total_amount,
                notes, "script_10k", transaction_datetime 
            ))

            if transaction_type == 'IN':
                db_products_info[sku_to_transact]['current_stock'] += quantity
            else:
                db_products_info[sku_to_transact]['current_stock'] -= quantity
            
            created_transactions += 1

            if len(transactions_batch) >= batch_size:
                conn.execute("BEGIN TRANSACTION")
                if db_add_stock_transaction_batch(conn, transactions_batch):
                    conn.commit()
                    print(f"  Đã ghi {len(transactions_batch)} giao dịch vào DB...")
                else:
                    conn.rollback()
                    print(f"  Lỗi khi ghi batch {len(transactions_batch)} giao dịch.")
                transactions_batch = []

        if (i + 1) % 1000 == 0:
            print(f"  Đã xử lý {i+1}/{num_sample_transactions} giao dịch...")

    if transactions_batch:
        conn.execute("BEGIN TRANSACTION")
        if db_add_stock_transaction_batch(conn, transactions_batch):
            conn.commit()
            print(f"  Đã ghi {len(transactions_batch)} giao dịch cuối cùng vào DB...")
        else:
            conn.rollback()
            print(f"  Lỗi khi ghi batch {len(transactions_batch)} giao dịch cuối cùng.")

    print("\nĐang cập nhật tồn kho cuối cùng cho các sản phẩm...")
    conn.execute("BEGIN TRANSACTION")
    for sku, info in db_products_info.items():
        db_update_product_stock(conn, info['id'], info['current_stock'])
    conn.commit()
    print("Hoàn tất cập nhật tồn kho cuối cùng.")

    end_time_transactions = time.time()
    print(f"\nHoàn tất thêm dữ liệu mẫu. Đã tạo {created_transactions} giao dịch.")
    print(f"Thời gian thêm giao dịch và cập nhật tồn kho: {end_time_transactions - start_time_transactions:.2f} giây.")
    ghi_log(f"Đã tạo {created_transactions} giao dịch mẫu.")
    conn.close()

# --- Chạy chương trình ---
if __name__ == '__main__':
    # Kiểm tra xem file DB có tồn tại không
    if os.path.exists(DB_NAME):
        response = input(f"File database '{DB_NAME}' đã tồn tại. Bạn có muốn XÓA và tạo lại dữ liệu mẫu không? (yes/no): ").lower()
        
        if response == 'yes':
            print(f"Đang xóa file '{DB_NAME}' cũ...")
            os.remove(DB_NAME)
            ghi_log(f"Người dùng đã chọn xóa và tạo lại DB '{DB_NAME}'.")
            
            # Chỉ khi người dùng đồng ý xóa, chúng ta mới khởi tạo và điền dữ liệu mới
            print("Bắt đầu tạo lại database và dữ liệu mẫu...")
            init_db()
            populate_large_sample_data()
        else:
            # Nếu người dùng nhập 'no' hoặc bất cứ gì khác, chỉ thông báo và thoát
            print("Đã hủy bỏ thao tác. Giữ nguyên file DB hiện tại.")
    else:
        # Nếu file DB không tồn tại, tự động tạo mới
        print(f"File database '{DB_NAME}' chưa tồn tại. Bắt đầu tạo mới...")
        init_db()
        populate_large_sample_data()

    print(f"\nQuá trình đã hoàn tất.")
    print(f"Bạn có thể kiểm tra file log 'tao_db_mau_lon.log' để xem chi tiết.")