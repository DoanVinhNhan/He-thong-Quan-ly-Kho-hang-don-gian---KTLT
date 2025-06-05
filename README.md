# Hệ thống Quản lý Kho hàng MiniVentory

Một hệ thống quản lý kho hàng đơn giản được xây dựng bằng Python thuần, không sử dụng web framework. Dự án cho phép người dùng quản lý sản phẩm, theo dõi các giao dịch nhập/xuất kho, và xem các báo cáo, thống kê cơ bản qua giao diện web.

## Tính năng chính

-   **Dashboard trang chủ:** Cung cấp cái nhìn tổng quan về các chỉ số quan trọng: tổng số sản phẩm, số lượng giao dịch nhập/xuất, tổng giá trị tồn kho, và tổng doanh thu.
-   **Quản lý Sản phẩm:**
    -   Xem danh sách, tìm kiếm sản phẩm theo tên hoặc mã SKU.
    -   Thêm sản phẩm mới với mã SKU được tạo tự động và duy nhất.
-   **Quản lý Kho (Nhập/Xuất):**
    -   Thực hiện giao dịch Nhập kho và Xuất kho cho từng sản phẩm một cách thủ công.
    -   Nhập và Xuất kho hàng loạt thông qua việc tải lên file CSV.
-   **Báo cáo & Lịch sử:**
    -   Xem lịch sử tất cả các giao dịch đã thực hiện, có thể lọc theo khoảng thời gian.
    -   Tạo báo cáo các sản phẩm có số lượng tồn kho thấp, sắp hết hàng.
-   **Thống kê & Biểu đồ:**
    -   Trực quan hóa dữ liệu bằng biểu đồ: doanh thu theo thời gian, doanh thu theo sản phẩm, và luồng nhập/xuất của một sản phẩm cụ thể.

## Công nghệ sử dụng

-   **Backend:**
    -   **Ngôn ngữ:** Python 3
    -   **Web Server:** Module `http.server` có sẵn của Python.
-   **Cơ sở dữ liệu:**
    -   SQLite
-   **Frontend:**
    -   HTML5
    -   CSS3
-   **Thư viện Python:**
    -   `matplotlib` để vẽ các biểu đồ thống kê.

## Cài đặt và Chạy dự án

### Yêu cầu

-   Python 3.6+
-   Git (để clone repository)

### Hướng dẫn cài đặt

1.  **Clone repository về máy tính của bạn:**
    (Nếu bạn đã có mã nguồn, có thể bỏ qua bước này)
    ```bash
    git clone [https://github.com/DoanVinhNhan/He-thong-Quan-ly-Kho-hang-don-gian---KTLT.git](https://github.com/DoanVinhNhan/He-thong-Quan-ly-Kho-hang-don-gian---KTLT.git)
    ```

2.  **Di chuyển vào thư mục dự án:**
    ```bash
    cd He-thong-Quan-ly-Kho-hang-don-gian---KTLT
    ```
    *(Thay thế `He-thong-Quan-ly-Kho-hang-don-gian---KTLT` bằng tên thư mục dự án thực tế của bạn nếu khác)*

3.  **Cài đặt thư viện `matplotlib`:**
    Ứng dụng sử dụng `matplotlib` cho tính năng vẽ biểu đồ. Nếu chưa có, bạn cần cài đặt:
    ```bash
    pip install matplotlib
    ```
    Hoặc (nếu bạn dùng `pip3`):
    ```bash
    pip3 install matplotlib
    ```

4.  **(Tùy chọn) Tạo dữ liệu mẫu:**
    Nếu bạn muốn có sẵn dữ liệu để thử nghiệm các tính năng, hãy chạy script sau từ thư mục gốc của dự án:
    ```bash
    python tao_du_lieu_mau.py
    ```
    Script này sẽ tạo một file database `miniventory_sqlite.db` với sản phẩm và giao dịch mẫu. Nếu file database đã tồn tại, script sẽ hỏi bạn có muốn xóa và tạo lại không.

### Khởi chạy ứng dụng

Để chạy server web, hãy thực thi lệnh sau từ thư mục gốc của dự án:
```bash
python -m src.main
