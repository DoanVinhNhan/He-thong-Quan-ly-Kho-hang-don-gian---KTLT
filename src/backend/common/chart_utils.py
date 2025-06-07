# /src/backend/common/chart_utils.py
# File này chứa các hàm tiện ích để tạo biểu đồ bằng thư viện Matplotlib.
# Các hàm này sẽ tạo ra hình ảnh biểu đồ và chuyển đổi nó thành chuỗi base64
# để có thể nhúng trực tiếp vào file HTML.

import datetime
import io
import base64
import locale

# Cố gắng import matplotlib. Nếu không thành công, đặt cờ MATPLOTLIB_AVAILABLE = False.
# Cấu hình 'Agg' được sử dụng để matplotlib có thể chạy trên server mà không cần GUI.
try:
    import matplotlib
    matplotlib.use('Agg') 
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

def format_currency_for_chart(value):
    """Định dạng một giá trị số thành chuỗi tiền tệ ngắn gọn cho các trục của biểu đồ."""
    if value is None: return "0"
    try:
        num_int = int(value)
        # Sử dụng locale của hệ thống để định dạng số có dấu phân cách hàng nghìn.
        if locale.getlocale(locale.LC_NUMERIC)[0] and \
           ('vi_VN' in locale.getlocale(locale.LC_NUMERIC)[0] or \
            'Vietnamese' in locale.getlocale(locale.LC_NUMERIC)[0]):
            return locale.format_string("%d", num_int, grouping=True).replace('.', ' ')
        else: # Fallback nếu không có locale tiếng Việt
            s = str(num_int)
            groups = []
            while s and s[-1].isdigit():
                groups.append(s[-3:])
                s = s[:-3]
            return (s + ' '.join(reversed(groups))).strip()
    except (ValueError, TypeError):
        return "N/A"

def generate_chart_image_base64(dates, values, title, ylabel, 
                                 x_labels_override=None,
                                 color='skyblue', chart_type='bar',
                                 y_values2=None, label2=None, color2='red'):
    """
    Tạo một biểu đồ (dạng thanh hoặc đường), lưu nó dưới dạng hình ảnh PNG,
    và trả về dưới dạng chuỗi base64 để nhúng vào HTML.
    Hàm này rất linh hoạt, hỗ trợ nhiều loại dữ liệu và tùy chỉnh.

    Args:
        dates (list): Danh sách các nhãn cho trục X (thường là ngày tháng dạng chuỗi).
        values (list): Danh sách các giá trị cho chuỗi dữ liệu thứ nhất trên trục Y.
        title (str): Tiêu đề của biểu đồ.
        ylabel (str): Nhãn của trục Y.
        x_labels_override (list, optional): Dùng để ghi đè nhãn trên trục X khi không dùng ngày tháng.
        color (str, optional): Màu cho chuỗi dữ liệu thứ nhất.
        chart_type (str, optional): Loại biểu đồ, 'bar' hoặc 'line'.
        y_values2 (list, optional): Dữ liệu cho chuỗi thứ hai (dùng cho biểu đồ đường kép).
        label2 (str, optional): Nhãn cho chuỗi dữ liệu thứ hai.
        color2 (str, optional): Màu cho chuỗi dữ liệu thứ hai.

    Returns:
        tuple: (chuỗi_base64_hình_ảnh, thông_báo_lỗi)
               Nếu thành công, thông_báo_lỗi là None.
    """
    if not MATPLOTLIB_AVAILABLE:
        return None, "Thư viện 'matplotlib' chưa được cài đặt, chức năng biểu đồ không khả dụng."
    
    # Khởi tạo một figure và axes để vẽ
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # --- Xử lý dữ liệu cho trục X ---
    # Chuyển đổi chuỗi ngày tháng thành đối tượng datetime để vẽ đúng trên trục thời gian.
    plot_dates_objects = []
    is_monthly_data = False
    if dates:
        # Kiểm tra xem dữ liệu là theo tháng ('YYYY-MM') hay theo ngày ('YYYY-MM-DD')
        if all(len(d) == 7 and d.count('-') == 1 for d in dates): 
            is_monthly_data = True
            try: plot_dates_objects = [datetime.datetime.strptime(d + "-01", '%Y-%m-%d') for d in dates]
            except ValueError: plot_dates_objects = range(len(dates)) # Fallback nếu format sai
        elif all(len(d) == 10 and d.count('-') == 2 for d in dates):
            try: plot_dates_objects = [datetime.datetime.strptime(d, '%Y-%m-%d') for d in dates]
            except ValueError: plot_dates_objects = range(len(dates))
        else: # Nếu không phải định dạng ngày, coi như là danh mục (vd: tên sản phẩm)
            plot_dates_objects = range(len(dates))

    # --- Vẽ biểu đồ ---
    # Dựa vào tham số chart_type để quyết định vẽ biểu đồ đường hay cột.
    if not plot_dates_objects:
         ax.text(0.5, 0.5, 'Không có dữ liệu để hiển thị', ha='center', va='center', transform=ax.transAxes)
    elif chart_type == 'line':
        ax.plot(plot_dates_objects, values, marker='o', linestyle='-', color=color, label=ylabel if not y_values2 else ylabel.split('/')[0])
        # Vẽ chuỗi dữ liệu thứ hai nếu có
        if y_values2 is not None:
            ax.plot(plot_dates_objects, y_values2, marker='x', linestyle='-', color=color2, label=label2 if label2 else 'Dữ liệu 2')
        if y_values2 is not None: ax.legend()
    elif chart_type == 'bar':
        # Logic tự động điều chỉnh độ rộng của cột cho đẹp mắt
        bar_width_val = 0.8
        if len(plot_dates_objects) > 0 and isinstance(plot_dates_objects[0], datetime.datetime):
            if is_monthly_data: bar_width_val = 20 
            else: bar_width_val = 0.8
        ax.bar(plot_dates_objects, values, color=color, width=bar_width_val, label=ylabel)

    # --- Tùy chỉnh hiển thị cho biểu đồ ---
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_xlabel("Thời gian" if not x_labels_override else "Sản phẩm", fontsize=12)
    
    # Định dạng các nhãn trên trục X sao cho dễ đọc, đặc biệt với dữ liệu ngày tháng
    if all(isinstance(d, datetime.datetime) for d in plot_dates_objects) and len(plot_dates_objects) > 0:
        if is_monthly_data:
             ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
        else:
             ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))
        fig.autofmt_xdate(rotation=30, ha='right') # Tự động xoay nhãn cho dễ nhìn
    elif x_labels_override: # Ghi đè nhãn X nếu được cung cấp (dùng cho biểu đồ theo sản phẩm)
        ax.set_xticks(plot_dates_objects)
        ax.set_xticklabels(x_labels_override, rotation=30, ha='right')
    
    # Định dạng trục Y cho giá trị tiền tệ hoặc số nguyên
    if "VNĐ" in ylabel:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency_for_chart(int(x))))
    else: 
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True)) # Đảm bảo các mốc là số nguyên

    ax.grid(True, linestyle='--', alpha=0.6) # Thêm lưới mờ để dễ theo dõi
    fig.tight_layout() # Tự động căn chỉnh các thành phần cho vừa vặn
    
    # --- Chuyển đổi hình ảnh thành chuỗi Base64 ---
    # Lưu hình ảnh vào một buffer trong bộ nhớ thay vì lưu ra file vật lý
    img_stream = io.BytesIO()
    fig.savefig(img_stream, format='png', dpi=90)
    plt.close(fig) # Đóng figure để giải phóng bộ nhớ
    img_stream.seek(0)
    
    # Mã hóa buffer hình ảnh thành chuỗi base64
    img_base64 = base64.b64encode(img_stream.read()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}", None
