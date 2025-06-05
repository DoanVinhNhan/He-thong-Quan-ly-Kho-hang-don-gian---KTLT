# chart_utils.py
import datetime
import io
import base64
import locale

try:
    import matplotlib
    matplotlib.use('Agg') 
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

def format_currency_for_chart(value): # Đảm bảo hàm này cũng xử lý INT
    if value is None: return "0"
    try:
        num_int = int(value)
        if locale.getlocale(locale.LC_NUMERIC)[0] and \
           ('vi_VN' in locale.getlocale(locale.LC_NUMERIC)[0] or \
            'Vietnamese' in locale.getlocale(locale.LC_NUMERIC)[0]):
            return locale.format_string("%d", num_int, grouping=True).replace('.', ' ')
        else: 
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
    if not MATPLOTLIB_AVAILABLE:
        return None, "Matplotlib chưa được cài đặt."
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_dates_objects = []
    is_monthly_data = False
    if dates:
        if all(len(d) == 7 and d.count('-') == 1 for d in dates): 
            is_monthly_data = True
            try: plot_dates_objects = [datetime.datetime.strptime(d + "-01", '%Y-%m-%d') for d in dates]
            except ValueError: plot_dates_objects = range(len(dates))
        elif all(len(d) == 10 and d.count('-') == 2 for d in dates):
            try: plot_dates_objects = [datetime.datetime.strptime(d, '%Y-%m-%d') for d in dates]
            except ValueError: plot_dates_objects = range(len(dates))
        else: 
            plot_dates_objects = range(len(dates))

    if not plot_dates_objects:
         ax.text(0.5, 0.5, 'Không có dữ liệu để hiển thị', ha='center', va='center', transform=ax.transAxes)
    elif chart_type == 'line':
        ax.plot(plot_dates_objects, values, marker='o', linestyle='-', color=color, label=ylabel if not y_values2 else ylabel.split('/')[0])
        if y_values2 is not None:
            ax.plot(plot_dates_objects, y_values2, marker='x', linestyle='-', color=color2, label=label2 if label2 else ylabel.split('/')[1] if '/' in ylabel else 'Dữ liệu 2')
        if y_values2 is not None: ax.legend()
    elif chart_type == 'bar':
        bar_width_val = 0.8
        if len(plot_dates_objects) > 0:
            if isinstance(plot_dates_objects[0], datetime.datetime):
                if is_monthly_data: bar_width_val = 20 
                else:
                    date_span_days = (max(plot_dates_objects) - min(plot_dates_objects)).days if len(plot_dates_objects) > 1 else 1
                    if date_span_days < 30 : bar_width_val = 0.8 
                    elif date_span_days < 90: bar_width_val = 1.5
                    else: bar_width_val = max(0.1, 250 / len(plot_dates_objects)) # Điều chỉnh độ rộng cột cho nhiều ngày
            ax.bar(plot_dates_objects, values, color=color, width=bar_width_val, label=ylabel)
            if y_values2 is not None: 
                ax.bar(plot_dates_objects, y_values2, bottom=values, color=color2, width=bar_width_val, label=label2)
                ax.legend()

    ax.set_title(title, fontsize=16)
    ax.set_ylabel(ylabel if not y_values2 else "Số lượng" if "Số lượng" in ylabel else ylabel, fontsize=12)
    ax.set_xlabel("Thời gian", fontsize=12)
    
    if all(isinstance(d, datetime.datetime) for d in plot_dates_objects) and len(plot_dates_objects) > 0 :
        num_ticks = min(12, len(plot_dates_objects)) # Giới hạn số lượng tick
        if is_monthly_data or ((max(plot_dates_objects) - min(plot_dates_objects)).days > 90 and len(plot_dates_objects) > 1):
             ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
             ax.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, len(plot_dates_objects)//num_ticks))) 
        else:
             ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))
             ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(plot_dates_objects)//num_ticks))) 
        fig.autofmt_xdate(rotation=30, ha='right') 
    elif x_labels_override: 
        ax.set_xticks(plot_dates_objects)
        ax.set_xticklabels(x_labels_override, rotation=30, ha='right')
    
    if "VNĐ" in ylabel:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency_for_chart(int(x))))
    else: 
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True, min_n_ticks=5)) # Đảm bảo có ít nhất 5 tick

    ax.grid(True, linestyle='--', alpha=0.6)
    fig.tight_layout() 
    
    img_stream = io.BytesIO()
    fig.savefig(img_stream, format='png', dpi=90)
    plt.close(fig) 
    img_stream.seek(0)
    
    img_base64 = base64.b64encode(img_stream.read()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}", None