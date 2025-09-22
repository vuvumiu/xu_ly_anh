# main_gui.py — Giao diện chính với lựa chọn mode và loại quả (đã sửa lỗi và tối ưu hiển thị)
# Lưu file này là main_gui.py rồi chạy trực tiếp.

import os
import cv2
import json
import time
import threading
import tkinter as tk
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from PIL import Image, ImageTk
from tkinter import ttk, filedialog, messagebox


# Style cho giao diện
class CustomStyle:
    """Custom styles cho các widget."""

    COLORS = {
        'primary': '#2c3e50',
        'secondary': '#34495e',
        'success': '#27ae60',
        'warning': '#f39c12',
        'danger': '#c0392b',
        'info': '#3498db',
        'light': '#ecf0f1',
        'dark': '#2c3e50',
        'white': '#ffffff',
        'muted': '#95a5a6',

        # Màu cho tiêu đề bảng
        'header_bg': '#1a1a1a',  # Đen đậm cho nền (tương phản cao)
        'header_fg': '#ffffff',  # Trắng cho chữ

        # Màu cho nội dung bảng
        'row_bg': '#f8f9fa',  # Xám rất nhạt cho nền
        'row_fg': '#000000',  # Đen cho chữ
        'row_alt_bg': '#edf2f7',  # Xám nhạt hơn cho hàng xen kẽ

        # Màu khi chọn dòng
        'selected_bg': '#3498db',  # Xanh dương cho nền
        'selected_fg': '#ffffff'  # Trắng cho chữ
    }

    @staticmethod
    def setup():
        """Thiết lập style cho toàn bộ ứng dụng"""
        CustomStyle.setup_table_style()

    @staticmethod
    def setup_table_style():
        """Thiết lập style cho các bảng (Treeview)"""
        style = ttk.Style()
        # BẮT BUỘC: dùng 'clam' để cho phép đổi màu header trên mọi OS
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        # Style cơ bản cho Treeview
        style.configure(
            "Custom.Treeview",
            background=CustomStyle.COLORS['row_bg'],
            foreground=CustomStyle.COLORS['row_fg'],
            rowheight=25,
            fieldbackground=CustomStyle.COLORS['row_bg']
        )

        # Style cho tiêu đề (heading) với màu sắc rõ ràng và tương phản cao
        # Heading của Treeview phải dùng đúng key: "Treeview.Heading"
        style.configure(
            "Treeview.Heading",
            background=CustomStyle.COLORS['header_bg'],
            foreground=CustomStyle.COLORS['header_fg'],
            relief='raised',
            font=('Arial', 10, 'bold'),
            padding=(5, 8)
        )
        # Đảm bảo hover/pressed không đổi sang màu “tàng hình”
        style.map(
            "Treeview.Heading",
            background=[('active', CustomStyle.COLORS['secondary']),
                        ('pressed', CustomStyle.COLORS['secondary'])],
            foreground=[('active', CustomStyle.COLORS['header_fg']),
                        ('pressed', CustomStyle.COLORS['header_fg'])]
        )

        # Style cho trạng thái được chọn
        style.map(
            "Custom.Treeview",
            background=[('selected', CustomStyle.COLORS['selected_bg'])],
            foreground=[('selected', CustomStyle.COLORS['selected_fg'])]
        )

        # Fix cho Windows để hiển thị màu nền đúng
        style.layout("Custom.Treeview", style.layout("Treeview"))


    @staticmethod
    def apply_to_tree(tree):
        """Áp dụng style cho một Treeview cụ thể"""
        # Áp dụng style chính
        tree.configure(style="Custom.Treeview")

        # Tạo tag cho màu xen kẽ
        tree.tag_configure('oddrow', background=CustomStyle.COLORS['row_alt_bg'])

        # Áp dụng màu xen kẽ cho các hàng
        def alternate_rows():
            for i, item in enumerate(tree.get_children()):
                if i % 2:
                    tree.item(item, tags=('oddrow',))

        # Thêm callback để cập nhật màu khi dữ liệu thay đổi
        tree.bind('<<TreeviewOpen>>', lambda _: alternate_rows())
        tree.bind('<<TreeviewClose>>', lambda _: alternate_rows())
        alternate_rows()


import os
import cv2
import json
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

# DB helper (tùy chọn): chỉ dùng khi bật lưu DB. Sẽ lazy-import để tránh lỗi che khuất.
try:
    from db_helper import (
        load_config as load_app_config,
        MySQLConnectionManager,
        ensure_product_exists,
        insert_capture,
        insert_classification,
        fetch_recent_classifications,
        fetch_captures_with_counts,
        fetch_classifications_by_capture,
    )
except Exception:
    load_app_config = None  # type: ignore
    MySQLConnectionManager = None  # type: ignore
    ensure_product_exists = None  # type: ignore
    insert_capture = None  # type: ignore
    insert_classification = None  # type: ignore
    fetch_recent_classifications = None  # type: ignore
    fetch_captures_with_counts = None  # type: ignore
    fetch_classifications_by_capture = None  # type: ignore

# Thử import FruitClassificationSystem từ main.py, đưa ra thông báo rõ ràng nếu thiếu
try:
    from main import FruitClassificationSystem
except Exception:
    class FruitClassificationSystem:  # type: ignore
        def __init__(self, *_args, **_kwargs):
            messagebox.showerror(
                "Lỗi Import",
                "Không thể import FruitClassificationSystem từ main.py.\n"
                "• Hãy chắc chắn main.py tồn tại trong cùng thư mục.\n"
                "• Trong main.py phải có class FruitClassificationSystem(config_path: str)."
            )
            raise ImportError("Không thể khởi tạo hệ thống")


class MainGUIInterface:
    def __init__(self):
        """
        Khởi tạo giao diện chính với các lựa chọn
        Chức năng: Tạo GUI để lựa chọn mode xử lý và loại sản phẩm
        """
        self.root = tk.Tk()
        self.root.title("Hệ thống Phân loại Sản phẩm Nông nghiệp")
        self.root.geometry("1000x720")
        self.root.configure(bg='#f0f0f0')

        # Biến trạng thái
        self.current_system = None
        self.camera_thread = None
        self.is_camera_running = False
        self.selected_fruit = tk.StringVar(value="tomato")
        self.save_to_db_var = tk.BooleanVar(value=False)
        self._db = None  # type: ignore
        self._product_id = None
        self.last_results = None
        self.last_image_path = None

        # Tuỳ chọn hiển thị/hiệu năng (sẽ tạo widget trong create_control_panel)
        self.hide_text_var = tk.BooleanVar(value=True)  # Chỉ vẽ khung, không vẽ chữ lên video
        self.fast_start_var = tk.BooleanVar(value=True)  # Mở nhanh: bỏ auto-calibrate khung đầu
        self.display_size_var = tk.StringVar(value="960x540")  # kích thước hiển thị camera
        self._display_wh = (960, 540)

        # Tải cấu hình các loại quả
        self.fruit_configs = self.load_all_fruit_configs()

        # Tạo giao diện
        self.create_interface()

    # ========================= CẤU HÌNH =========================
    def load_all_fruit_configs(self):
        """Tải cấu hình cho tất cả các loại quả từ fruit_configs.FruitConfigManager."""
        try:
            from fruit_configs import FruitConfigManager
            mgr = FruitConfigManager()
            return mgr.configs
        except Exception:
            # Fallback: nếu import lỗi, giữ lại tối thiểu một loại để app chạy được
            return {
                "tomato": {
                    "name": "Cà chua",
                    "product": "tomato",
                    "size_thresholds_mm": {"S": [0, 55], "M": [55, 65], "L": [65, 75], "XL": [75, 999]},
                    "hsv_ranges": {
                        "red": [
                            {"H": [0, 10], "S": [80, 255], "V": [70, 255]},
                            {"H": [160, 180], "S": [80, 255], "V": [70, 255]}
                        ]
                    },
                    "lab_thresholds": {"a_star_ripe_min": 25, "a_star_green_max": 10},
                    "ripeness_logic": {
                        "green_if": {"ratio_red_max": 0.15, "a_star_max": 10},
                        "ripe_if": {"ratio_red_min": 0.35, "a_star_min": 20}
                    },
                    "defect": {"dark_delta_T": 25, "area_ratio_tau": 0.06},
                    "morphology": {"open_kernel": 3, "close_kernel": 5, "min_area": 200},
                    "watershed": {"distance_threshold_rel": 0.5}
                }
            }

    # ========================= GIAO DIỆN =========================
    def create_interface(self):
        # Áp dụng custom style cho toàn bộ ứng dụng
        CustomStyle.setup()

        # Title
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        title_frame.pack(fill=tk.X, padx=10, pady=(10, 20))
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="HỆ THỐNG PHÂN LOẠI SẢN PHẨM NÔNG NGHIỆP",
            font=('Arial', 18, 'bold'), fg='white', bg='#2c3e50'
        ).pack(expand=True)

        tk.Label(
            title_frame,
            text="Sử dụng Computer Vision và OpenCV",
            font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50'
        ).pack()

        # Main content frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left panel - Cấu hình
        left_frame = tk.LabelFrame(main_frame, text="CẤU HÌNH HỆ THỐNG",
                                   font=('Arial', 12, 'bold'),
                                   bg='#f0f0f0', padx=15, pady=15)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.create_config_panel(left_frame)

        # Right panel - Điều khiển
        right_frame = tk.LabelFrame(main_frame, text="ĐIỀU KHIỂN",
                                    font=('Arial', 12, 'bold'),
                                    bg='#f0f0f0', padx=15, pady=15)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.create_control_panel(right_frame)

        # Status bar
        self.create_status_bar()

    def create_config_panel(self, parent):
        # Chọn loại quả
        fruit_frame = tk.Frame(parent, bg='#f0f0f0')
        fruit_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(fruit_frame, text="Loại sản phẩm:",
                 font=('Arial', 11, 'bold'), bg='#f0f0f0').pack(anchor=tk.W)

        fruit_combo = ttk.Combobox(
            fruit_frame, textvariable=self.selected_fruit,
            values=list(self.fruit_configs.keys()), state="readonly", width=25
        )
        fruit_combo.pack(fill=tk.X, pady=(5, 0))
        fruit_combo.bind('<<ComboboxSelected>>', self.on_fruit_changed)

        # Hiển thị tên tiếng Việt
        self.fruit_name_label = tk.Label(
            fruit_frame,
            text=f"({self.fruit_configs[self.selected_fruit.get()]['name']})",
            font=('Arial', 10, 'italic'), fg='#7f8c8d', bg='#f0f0f0'
        )
        self.fruit_name_label.pack(anchor=tk.W, pady=(2, 0))

        # Thông số kỹ thuật
        specs_frame = tk.LabelFrame(parent, text="Thông số kỹ thuật", bg='#f0f0f0')
        specs_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.specs_text = tk.Text(specs_frame, height=18, width=38,
                                  font=('Consolas', 9), state=tk.DISABLED,
                                  bg='#ffffff', wrap=tk.WORD)
        scrollbar = tk.Scrollbar(specs_frame, command=self.specs_text.yview)
        self.specs_text.configure(yscrollcommand=scrollbar.set)
        self.specs_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        button_frame = tk.Frame(parent, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(button_frame, text="Hiệu chuẩn tham số",
                  command=self.open_calibration, bg='#3498db', fg='white',
                  font=('Arial', 10)).pack(fill=tk.X, pady=(0, 5))

        tk.Button(button_frame, text="Lưu cấu hình",
                  command=self.save_current_config, bg='#27ae60', fg='white',
                  font=('Arial', 10)).pack(fill=tk.X)

        # Cập nhật hiển thị ban đầu
        self.update_specs_display()

    def create_control_panel(self, parent):
        # Mode 1: Xử lý ảnh tĩnh
        mode1_frame = tk.LabelFrame(parent, text="MODE 1: XỬ LÝ ẢNH TĨNH",
                                    bg='#e8f5e8', padx=10, pady=10)
        mode1_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(mode1_frame, text="Tải ảnh từ máy tính để phân tích",
                 font=('Arial', 10), bg='#e8f5e8').pack(anchor=tk.W, pady=(0, 10))

        btn_frame1 = tk.Frame(mode1_frame, bg='#e8f5e8')
        btn_frame1.pack(fill=tk.X)

        tk.Button(btn_frame1, text="Tải ảnh đơn lẻ", command=self.load_single_image,
                  bg='#2ecc71', fg='white', font=('Arial', 11, 'bold'), height=2
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        tk.Button(btn_frame1, text="Tải hàng loạt", command=self.load_batch_images,
                  bg='#27ae60', fg='white', font=('Arial', 11, 'bold'), height=2
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

        # Mode 2: Camera trực tiếp
        mode2_frame = tk.LabelFrame(parent, text="MODE 2: CAMERA TRỰC TIẾP",
                                    bg='#e8f4fd', padx=10, pady=10)
        mode2_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(mode2_frame, text="Quét và phân loại thời gian thực",
                 font=('Arial', 10), bg='#e8f4fd').pack(anchor=tk.W, pady=(0, 10))

        camera_frame = tk.Frame(mode2_frame, bg='#e8f4fd')
        camera_frame.pack(fill=tk.X)

        self.camera_btn = tk.Button(camera_frame, text="BẮT ĐẦU CAMERA",
                                    command=self.toggle_camera,
                                    bg='#3498db', fg='white',
                                    font=('Arial', 11, 'bold'), height=2)
        self.camera_btn.pack(fill=tk.X, pady=(0, 10))

        # Camera controls
        camera_controls = tk.Frame(mode2_frame, bg='#e8f4fd')
        camera_controls.pack(fill=tk.X)

        tk.Label(camera_controls, text="Camera ID:", bg='#e8f4fd').pack(side=tk.LEFT)
        self.camera_id_var = tk.StringVar(value="0")
        tk.Entry(camera_controls, textvariable=self.camera_id_var, width=5
                 ).pack(side=tk.LEFT, padx=(5, 15))

        self.recording_var = tk.BooleanVar(value=False)
        tk.Checkbutton(camera_controls, text="Ghi video",
                       variable=self.recording_var, bg='#e8f4fd').pack(side=tk.LEFT)

        # --- tuỳ chọn hiển thị & hiệu năng ---
        opts_frame = tk.Frame(mode2_frame, bg='#e8f4fd')
        opts_frame.pack(fill=tk.X, pady=(6, 0))

        tk.Label(opts_frame, text="Hiển thị:", bg='#e8f4fd').pack(side=tk.LEFT)
        tk.Checkbutton(opts_frame, text="Chỉ khung (không chữ)",
                       variable=self.hide_text_var, bg='#e8f4fd').pack(side=tk.LEFT, padx=(6, 15))

        tk.Checkbutton(opts_frame, text="Mở nhanh (bỏ hiệu chuẩn khung đầu)",
                       variable=self.fast_start_var, bg='#e8f4fd').pack(side=tk.LEFT)

        # --- chọn kích thước hiển thị/capture ---
        size_frame = tk.Frame(mode2_frame, bg='#e8f4fd')
        size_frame.pack(fill=tk.X, pady=(8, 0))
        tk.Label(size_frame, text="Kích thước:", bg='#e8f4fd').pack(side=tk.LEFT)
        ttk.Combobox(size_frame, textvariable=self.display_size_var, width=10, state="readonly",
                     values=["640x360", "800x450", "960x540", "1280x720"]).pack(side=tk.LEFT, padx=(6, 10))

        # Thống kê và kết quả
        stats_frame = tk.LabelFrame(parent, text="THỐNG KÊ & KẾT QUẢ",
                                    bg='#fdf6e3', padx=10, pady=10)
        stats_frame.pack(fill=tk.BOTH, expand=True)

        # Gói phần text + scrollbar vào một frame con để tránh chồng lấp với thanh công cụ bên dưới
        results_area = tk.Frame(stats_frame, bg='#fdf6e3')
        # Không expand để không che mất thanh nút bên dưới
        results_area.pack(fill=tk.X, expand=False)

        self.results_text = tk.Text(results_area, height=10, font=('Consolas', 9),
                                    state=tk.DISABLED, bg='#ffffff')
        results_scroll = tk.Scrollbar(results_area, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scroll.set)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # BẢNG REAL-TIME: tránh chồng chữ, hiển thị đầy đủ dữ liệu đối tượng
        table_frame = tk.LabelFrame(parent, text="BẢNG REAL-TIME", bg='#fdf6e3')
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        cols = ("Mã", "Kích thước", "Độ chín", "Tình trạng", "ĐK (mm)")
        self.live_table = ttk.Treeview(table_frame, columns=cols, show="headings", height=8, style="Custom.Treeview")
        for c, w in zip(cols, (60, 80, 100, 100, 80)):
            self.live_table.heading(c, text=c)
            self.live_table.column(c, width=w, anchor=tk.CENTER)
        self.live_table.pack(fill=tk.BOTH, expand=True)

        # Export buttons
        export_frame = tk.Frame(stats_frame, bg='#fdf6e3')
        export_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(export_frame, text="Xuất CSV", command=self.export_csv,
                  bg='#f39c12', fg='white', font=('Arial', 9)
                  ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(export_frame, text="Báo cáo", command=self.export_report,
                  bg='#e67e22', fg='white', font=('Arial', 9)
                  ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Checkbutton(export_frame, text="Lưu vào DB", variable=self.save_to_db_var,
                       bg='#fdf6e3').pack(side=tk.LEFT, padx=(10, 5))

        # Nhập tên phiên để dễ xem lại
        tk.Label(export_frame, text="Tên phiên:", bg='#fdf6e3').pack(side=tk.LEFT, padx=(10, 4))
        self.session_name_var = tk.StringVar(value="")
        tk.Entry(export_frame, textvariable=self.session_name_var, width=18).pack(side=tk.LEFT)

        tk.Button(export_frame, text="Lưu DB", command=self.manual_save_db,
                  bg='#27ae60', fg='white', font=('Arial', 9)
                  ).pack(side=tk.LEFT)

        tk.Button(export_frame, text="Xem DB", command=self.open_db_viewer,
                  bg='#2980b9', fg='white', font=('Arial', 9)
                  ).pack(side=tk.LEFT, padx=(5, 0))

        tk.Button(export_frame, text="Xóa", command=self.clear_results,
                  bg='#95a5a6', fg='white', font=('Arial', 9)
                  ).pack(side=tk.RIGHT)

    def create_status_bar(self):
        status_frame = tk.Frame(self.root, bg='#34495e', height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(status_frame, text="Sẵn sàng",
                                     bg='#34495e', fg='white', font=('Arial', 10))
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

        self.time_label = tk.Label(status_frame,
                                   text=datetime.now().strftime("%H:%M:%S"),
                                   bg='#34495e', fg='#bdc3c7', font=('Arial', 9))
        self.time_label.pack(side=tk.RIGHT, padx=10, pady=5)

        self.update_time()

    def update_time(self):
        self.time_label.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self.update_time)

    # ========================= SỰ KIỆN & HIỂN THỊ =========================
    def on_fruit_changed(self, _event=None):
        fruit_key = self.selected_fruit.get()
        fruit_name = self.fruit_configs[fruit_key]['name']
        self.fruit_name_label.config(text=f"({fruit_name})")
        self.update_specs_display()
        self.update_status(f"Đã chọn {fruit_name}")

        # Nếu hệ thống đang chạy, cập nhật config trực tiếp nếu có thuộc tính đó
        if self.current_system is not None:
            if hasattr(self.current_system, 'set_config'):
                self.current_system.set_config(self.fruit_configs[fruit_key])  # type: ignore
            else:
                self.current_system.config = self.fruit_configs[fruit_key]

    def _detect_ratio_key(self, ripeness_logic: dict) -> str | None:
        """Tìm ratio_* key để hiển thị ngưỡng (tương thích mọi loại quả)."""
        for branch in (ripeness_logic.get('green_if', {}), ripeness_logic.get('ripe_if', {})):
            for k in branch.keys():
                if k.startswith('ratio_') and (k.endswith('_max') or k.endswith('_min')):
                    core = k.rsplit('_', 1)[0]
                    return core
        return None

    def update_specs_display(self):
        fruit_key = self.selected_fruit.get()
        config = self.fruit_configs[fruit_key]

        lines = [f"THÔNG SỐ {config['name'].upper()}", "", "KÍCH THƯỚC (mm):"]
        for size, rng in config['size_thresholds_mm'].items():
            min_val, max_val = rng[0], rng[1]
            lines.append(f"  {size}: {min_val}-{max_val}mm")

        lines.append("\nDẢI MÀU HSV:")
        for color, ranges in config['hsv_ranges'].items():
            lines.append(f"  {color.upper()}:")
            for r in ranges:
                lines.append(
                    f"    H:{r['H'][0]}-{r['H'][1]} S:{r['S'][0]}-{r['S'][1]} V:{r['V'][0]}-{r['V'][1]}"
                )

        lines.append("\nTHÔNG SỐ PHÂN LOẠI:")
        ripeness = config.get('ripeness_logic', {})
        ratio_core = self._detect_ratio_key(ripeness)  # ví dụ: ratio_red / ratio_yellow / ratio_white
        green_if = ripeness.get('green_if', {})
        ripe_if = ripeness.get('ripe_if', {})
        if ratio_core:
            green_key = f"{ratio_core}_max"
            ripe_key = f"{ratio_core}_min"
            if green_key in green_if:
                lines.append(f"  Xanh: {ratio_core} ≤ {green_if[green_key]}")
            if ripe_key in ripe_if:
                lines.append(f"  Chín: {ratio_core} ≥ {ripe_if[ripe_key]}")
        for k, v in green_if.items():
            if not k.startswith('ratio_'):
                lines.append(f"  (green_if) {k}: {v}")
        for k, v in ripe_if.items():
            if not k.startswith('ratio_'):
                lines.append(f"  (ripe_if) {k}: {v}")

        lines.append("\nPHÁT HIỆN KHUYẾT TẬT:")
        defect = config['defect']
        lines.append(f"  Ngưỡng tối: {defect['dark_delta_T']}")
        lines.append(f"  Tỷ lệ tối đa: {defect['area_ratio_tau']}")

        lines.append("\nHÌNH THÁI HỌC:")
        morph = config['morphology']
        lines.append(f"  Open kernel: {morph['open_kernel']}")
        lines.append(f"  Close kernel: {morph['close_kernel']}")
        lines.append(f"  Min area: {morph['min_area']}")

        # Cập nhật text widget
        self.specs_text.config(state=tk.NORMAL)
        self.specs_text.delete(1.0, tk.END)
        self.specs_text.insert(1.0, "\n".join(lines))
        self.specs_text.config(state=tk.DISABLED)

    def update_status(self, message: str):
        self.status_label.config(text=message)

    def update_results(self, text: str):
        self.results_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results_text.insert(tk.END, f"[{timestamp}] {text}\n")
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)

    def update_live_table(self, results):
        # Làm mới bảng với dữ liệu mới
        for r in self.live_table.get_children():
            self.live_table.delete(r)
        for r in results:
            self.live_table.insert("", tk.END, values=(
                r.get("id", ""),
                r.get("size", ""),
                r.get("ripeness", ""),
                r.get("defect", ""),
                f"{r.get('d_eq_mm', 0):.1f}"
            ))

    # ========================= XỬ LÝ ẢNH =========================
    def load_single_image(self):
        self.update_status("Đang chọn ảnh...")
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("All files", "*.*")
        ]
        file_path = filedialog.askopenfilename(title="Chọn ảnh để phân loại", filetypes=filetypes)
        if not file_path:
            self.update_status("Hủy chọn ảnh")
            return

        try:
            self.update_status("Đang xử lý ảnh...")

            # Khởi tạo hệ thống với config hiện tại (tạo file tạm)
            fruit_key = self.selected_fruit.get()
            temp_config_file = f"temp_{fruit_key}_config.json"
            with open(temp_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.fruit_configs[fruit_key], f, indent=2, ensure_ascii=False)

            system = FruitClassificationSystem(temp_config_file)
            # Áp dụng chế độ render để không chồng chữ
            system.set_render_mode("boxes_only" if self.hide_text_var.get() else "full")

            # Đọc ảnh
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError("Không thể đọc ảnh")

            # Xử lý
            vis, results, mask = system.process_frame(image)

            # Hiển thị kết quả
            self.display_image_results(vis, mask, results, file_path)
            self.update_live_table([r for r in results if r is not None])

            # Cập nhật thống kê
            valid_results = [r for r in results if r is not None]
            self.update_image_statistics(valid_results, file_path)
            self.update_status(f"Xử lý thành công: {len(valid_results)} đối tượng")

            # Lưu trạng thái gần nhất và auto lưu DB nếu bật
            self.last_results = valid_results
            self.last_image_path = file_path
            if self.save_to_db_var.get():
                try:
                    self.save_results_to_db(valid_results, source="single_image", image_path=file_path)
                    self.update_results("→ Đã lưu DB cho ảnh đơn lẻ")
                except Exception as db_e:
                    self.update_results(f"DB lỗi: {db_e}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xử lý ảnh:\n{str(e)}")
            self.update_status("Lỗi xử lý ảnh")
        finally:
            # Cleanup file tạm
            if 'temp_config_file' in locals() and os.path.exists(temp_config_file):
                try:
                    os.remove(temp_config_file)
                except Exception:
                    pass

    def load_batch_images(self):
        """Chọn thư mục và xử lý tất cả ảnh trong đó (chạy trên thread riêng)."""
        self.update_status("Đang chọn thư mục...")
        folder_path = filedialog.askdirectory(title="Chọn thư mục chứa ảnh")
        if not folder_path:
            self.update_status("Hủy chọn thư mục")
            return

        try:
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            image_files = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if any(f.lower().endswith(ext) for ext in image_extensions)
            ]
            if not image_files:
                messagebox.showwarning("Cảnh báo", "Không tìm thấy ảnh nào trong thư mục!")
                return

            self.update_status(f"Tìm thấy {len(image_files)} ảnh. Đang xử lý...")
            thread = threading.Thread(target=self.process_batch_images, args=(image_files, folder_path), daemon=True)
            thread.start()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xử lý thư mục:\n{str(e)}")
            self.update_status("Lỗi xử lý thư mục")

    def process_batch_images(self, image_files, folder_path):
        try:
            fruit_key = self.selected_fruit.get()
            temp_config_file = f"temp_{fruit_key}_config.json"
            with open(temp_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.fruit_configs[fruit_key], f, indent=2, ensure_ascii=False)
            system = FruitClassificationSystem(temp_config_file)
            system.set_render_mode("boxes_only" if self.hide_text_var.get() else "full")

            # Thư mục kết quả
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.join(
                folder_path, f"results_{fruit_key}_{timestamp}"
            )
            os.makedirs(output_dir, exist_ok=True)

            # Lưu chi tiết cho mỗi ảnh
            self.batch_details = {
                'timestamp': timestamp,
                'output_dir': output_dir,
                'fruit_type': fruit_key,
                'images': {}  # Sẽ chứa thông tin chi tiết của từng ảnh
            }

            batch_results = []
            processed_count = 0

            for i, image_path in enumerate(image_files):
                try:
                    progress = f"Xử lý {i + 1}/{len(image_files)}: {os.path.basename(image_path)}"
                    self.root.after(0, lambda p=progress: self.update_status(p))

                    image = cv2.imread(image_path)
                    if image is None:
                        raise ValueError("Không thể đọc ảnh")

                    start_time = time.time()
                    vis, results, mask = system.process_frame(image)
                    process_time = time.time() - start_time

                    base_name = os.path.splitext(os.path.basename(image_path))[0]
                    result_path = os.path.join(output_dir, f"{base_name}_result.jpg")
                    mask_path = os.path.join(output_dir, f"{base_name}_mask.jpg")
                    cv2.imwrite(result_path, vis)
                    cv2.imwrite(mask_path, mask)

                    valid_results = [r for r in results if r is not None]
                    batch_results.extend(valid_results)

                    # Lưu thông tin chi tiết cho ảnh này
                    self.batch_details['images'][image_path] = {
                        'base_name': base_name,
                        'result_path': result_path,
                        'mask_path': mask_path,
                        'results': valid_results,
                        'process_time': process_time,
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'original_size': f"{image.shape[1]}x{image.shape[0]}"
                    }

                    # Tùy chọn: lưu DB theo từng ảnh nếu bật
                    if self.save_to_db_var.get() and valid_results:
                        try:
                            self.save_results_to_db(valid_results, source="batch", image_path=image_path)
                            self.root.after(0, lambda: self.update_results("→ Đã lưu DB ảnh batch"))
                        except Exception as db_e:
                            self.root.after(0, lambda e=str(db_e): self.update_results(f"DB lỗi: {e}"))

                    log_text = f"✓ {base_name}: {len(valid_results)} đối tượng"
                    self.root.after(0, lambda t=log_text: self.update_results(t))
                    processed_count += 1
                except Exception as e:
                    error_text = f"✗ {os.path.basename(image_path)}: {str(e)}"
                    self.root.after(0, lambda t=error_text: self.update_results(t))
                    continue

            # Báo cáo tổng hợp
            self.create_batch_report(batch_results, output_dir, processed_count, len(image_files))

            # Hiển thị bảng tổng hợp chi tiết
            self.root.after(0, self.show_batch_summary_window)

            summary = (
                f"Hoàn thành! Xử lý {processed_count}/{len(image_files)} ảnh, "
                f"tìm thấy {len(batch_results)} đối tượng"
            )
            self.root.after(0, lambda s=summary: self.update_status(s))
            self.root.after(0, lambda s=summary: self.update_results(s))
        except Exception as e:
            error_msg = f"• Lỗi batch processing: {str(e)}"
            self.root.after(0, lambda e=error_msg: self.update_status(e))
        finally:
            if 'temp_config_file' in locals() and os.path.exists(temp_config_file):
                try:
                    os.remove(temp_config_file)
                except Exception:
                    pass

    # ========================= CAMERA =========================
    def toggle_camera(self):
        if not self.is_camera_running:
            try:
                camera_id = int(self.camera_id_var.get())
                self.start_camera(camera_id)
            except ValueError:
                messagebox.showerror("Lỗi", "Camera ID phải là số nguyên")
        else:
            self.stop_camera()

    def start_camera(self, camera_id: int):
        try:
            self.update_status("Đang khởi động camera...")

            # Chọn kích thước từ combobox
            w, h = map(int, self.display_size_var.get().split("x"))
            self._display_wh = (w, h)

            # Khởi tạo hệ thống với config hiện tại
            fruit_key = self.selected_fruit.get()
            if fruit_key not in self.fruit_configs:
                raise Exception(f"Không tìm thấy cấu hình cho loại quả: {fruit_key}")

            temp_config_file = f"temp_{fruit_key}_config.json"
            with open(temp_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.fruit_configs[fruit_key], f, indent=2, ensure_ascii=False)

            # Khởi tạo hệ thống với error handling
            try:
                self.current_system = FruitClassificationSystem(temp_config_file)
            except Exception as e:
                raise Exception(f"Lỗi khởi tạo hệ thống xử lý: {str(e)}")

            # Áp dụng chế độ render (tránh chồng chữ trên video)
            if hasattr(self.current_system, "set_render_mode"):
                self.current_system.set_render_mode("boxes_only" if self.hide_text_var.get() else "full")

            # Mở nhanh: bỏ auto-calibrate ở khung đầu để khởi động nhanh
            if self.fast_start_var.get():
                self.current_system.scale_state["mm_per_px"] = 1.0  # không None => bỏ calibrate tự động

            # Test mở camera (ưu tiên CAP_DSHOW trên Windows) + giảm buffer + set kích thước
            try:
                cap_test = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            except Exception:
                cap_test = cv2.VideoCapture(camera_id)
            if not cap_test.isOpened():
                raise Exception(f"Không thể mở camera ID {camera_id}")
            cap_test.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap_test.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            cap_test.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            cap_test.release()

            self.is_camera_running = True
            self.camera_btn.config(text="DỪNG CAMERA", bg='#e74c3c')

            self.camera_thread = threading.Thread(
                target=self.camera_processing_loop, args=(camera_id,), daemon=True
            )
            self.camera_thread.start()

            self.update_status(f"Camera {camera_id} đang chạy ({w}x{h})")
        except Exception as e:
            messagebox.showerror("Lỗi Camera", f"Không thể khởi động camera:\n{str(e)}")
            self.update_status("Lỗi khởi động camera")
            # Cleanup nếu có lỗi
            if hasattr(self, 'current_system') and self.current_system is not None:
                self.current_system = None

    def stop_camera(self):
        self.is_camera_running = False
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=2.0)
        self.camera_btn.config(text="BẮT ĐẦU CAMERA", bg='#3498db')
        self.current_system = None

        # Cleanup temp file
        fruit_key = self.selected_fruit.get()
        temp_config_file = f"temp_{fruit_key}_config.json"
        if os.path.exists(temp_config_file):
            try:
                os.remove(temp_config_file)
            except Exception:
                pass
        self.update_status("Đã dừng camera")

    def camera_processing_loop(self, camera_id: int):
        # mở cam theo backend nhanh hơn
        w, h = getattr(self, "_display_wh", (960, 540))
        cap = None
        video_writer = None

        try:
            # Khởi tạo camera với error handling tốt hơn
            try:
                cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            except Exception:
                cap = cv2.VideoCapture(camera_id)

            if not cap.isOpened():
                raise Exception(f"Không thể mở camera {camera_id}")

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # ép kích thước cửa sổ hiển thị
            cv2.namedWindow("Camera - Phan loai san pham", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Camera - Phan loai san pham", w, h)

            cv2.namedWindow("Segmentation Mask", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Segmentation Mask", int(w * 0.5), int(h * 0.5))

            frame_count = 0

            # Ghi video nếu cần
            if hasattr(self, 'recording_var') and self.recording_var.get():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                video_writer = cv2.VideoWriter(f"recording_{timestamp}.avi", fourcc, 20.0, (w, h))

            # Kiểm tra hệ thống xử lý
            if self.current_system is None:
                raise Exception("Hệ thống xử lý chưa được khởi tạo")

            while self.is_camera_running:
                ret, frame = cap.read()
                if not ret:
                    self.root.after(0, lambda: self.update_status("Không thể đọc frame từ camera"))
                    break
                frame_count += 1

                try:
                    # Xử lý frame với error handling
                    vis, results, mask = self.current_system.process_frame(frame)

                    # Kiểm tra kết quả xử lý
                    if vis is None or mask is None:
                        self.root.after(0, lambda: self.update_status("Lỗi xử lý frame"))
                        continue

                except Exception as e:
                    self.root.after(0, lambda: self.update_status(f"Lỗi xử lý frame: {str(e)}"))
                    continue

                # đảm bảo kích thước hiển thị gọn
                if vis.shape[1] != w or vis.shape[0] != h:
                    vis = cv2.resize(vis, (w, h))

                # Xử lý mask display
                if mask is not None:
                    if mask.shape[1] != int(w * 0.5) or mask.shape[0] != int(h * 0.5):
                        mask_disp = cv2.resize(mask, (int(w * 0.5), int(h * 0.5)))
                    else:
                        mask_disp = mask
                else:
                    mask_disp = None

                # cập nhật bảng dữ liệu định kỳ (mỗi ~0.5s)
                if frame_count % 15 == 0:
                    valid_results = [r for r in results if r is not None]
                    self.root.after(0, lambda v=valid_results: self.update_live_table(v))
                    if valid_results:
                        self.update_camera_statistics(valid_results, frame_count)

                # Ghi video nếu cần
                if video_writer is not None:
                    video_writer.write(vis)

                # Hiển thị kết quả
                cv2.imshow("Camera - Phan loai san pham", vis)
                if mask_disp is not None:
                    cv2.imshow("Segmentation Mask", mask_disp)

                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break
                elif key == ord('s'):
                    self.save_camera_frame(frame, vis, results, frame_count)

        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"Lỗi camera processing: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Lỗi Camera", f"Lỗi xử lý camera:\n{str(e)}"))
        finally:
            # Cleanup resources
            if cap is not None:
                cap.release()
            if video_writer is not None:
                video_writer.release()
            cv2.destroyAllWindows()
            self.is_camera_running = False
            self.root.after(0, lambda: self.camera_btn.config(text="BẮT ĐẦU CAMERA", bg='#3498db'))
            self.root.after(0, lambda: self.update_status("Camera đã dừng"))

    # ========================= HIỂN THỊ & BÁO CÁO =========================
    def display_image_results(self, vis, mask, results, image_path: str):
        # Resize để fit màn hình
        h, w = vis.shape[:2]
        max_size = 900
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            vis = cv2.resize(vis, (new_w, new_h))
            mask = cv2.resize(mask, (new_w, new_h))

        window_name = f"Ket qua - {os.path.basename(image_path)}"
        cv2.imshow(window_name, vis)
        cv2.imshow("Mask - " + os.path.basename(image_path), mask)
        try:
            cv2.moveWindow(window_name, 100, 100)
            cv2.moveWindow("Mask - " + os.path.basename(image_path), 600, 100)
        except Exception:
            pass

    def update_image_statistics(self, results, image_path: str):
        if not results:
            self.update_results("Không tìm thấy đối tượng nào")
            return
        total = len(results)
        size_count = {}
        ripeness_count = {}
        defect_count = 0
        for r in results:
            size = r.get('size', 'Unknown')
            size_count[size] = size_count.get(size, 0) + 1
            ripeness = r.get('ripeness', 'Unknown')
            ripeness_count[ripeness] = ripeness_count.get(ripeness, 0) + 1
            if r.get('defect', 'OK') == 'Defective':
                defect_count += 1

        quality_percent = (total - defect_count) / total * 100 if total > 0 else 0
        lines = [
            f"\n=== {os.path.basename(image_path)} ===",
            f"Tổng số: {total} đối tượng",
            "Kích thước: " + ", ".join(f"{k}:{v}" for k, v in size_count.items()),
            "Độ chín: " + ", ".join(f"{k}:{v}" for k, v in ripeness_count.items()),
            f"Chất lượng: {quality_percent:.1f}% ({total - defect_count}/{total})"
        ]
        self.update_results("\n".join(lines))

    def update_camera_statistics(self, results, frame_count: int):
        if not results:
            return
        total = len(results)
        # Sửa lỗi so sánh chuỗi - sử dụng giá trị tiếng Việt
        ripe_count = sum(1 for r in results if r.get('ripeness') == 'Chín')
        defect_count = sum(1 for r in results if r.get('defect_status') == 'Khuyết tật')
        self.update_results(f"Frame {frame_count}: {total} đối tượng, {ripe_count} chín, {defect_count} lỗi")

    def save_camera_frame(self, original, processed, results, frame_count: int):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fruit_name = self.selected_fruit.get()
        original_path = f"camera_original_{fruit_name}_{timestamp}.jpg"
        result_path = f"camera_result_{fruit_name}_{timestamp}.jpg"
        cv2.imwrite(original_path, original)
        cv2.imwrite(result_path, processed)

        data = {
            'timestamp': timestamp,
            'frame_number': frame_count,
            'fruit_type': fruit_name,
            'results': results,
            'files': {'original': original_path, 'processed': result_path}
        }
        data_path = f"camera_data_{fruit_name}_{timestamp}.json"
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        self.update_results(f"Đã lưu frame: {timestamp}")

        # Cập nhật last_* và lưu DB nếu bật
        valid_results = [r for r in results if r is not None]
        self.last_results = valid_results
        self.last_image_path = original_path
        if self.save_to_db_var.get() and valid_results:
            try:
                self.save_results_to_db(valid_results, source="camera", image_path=original_path)
                self.update_results("→ Đã lưu DB cho frame camera")
            except Exception as db_e:
                self.update_results(f"DB lỗi: {db_e}")

    def create_batch_report(self, results, output_dir: str, processed_count: int, total_files: int):
        from collections import Counter
        if not results:
            self.update_results("Không có kết quả để báo cáo.")
            return
        total_objects = len(results)
        size_counts = Counter(r.get('size', 'Unknown') for r in results)
        ripeness_counts = Counter(r.get('ripeness', 'Unknown') for r in results)
        defect_count = sum(1 for r in results if r.get('defect') == 'Defective')
        quality_percent = (total_objects - defect_count) / total_objects * 100 if total_objects > 0 else 0

        lines = [
            "BÁO CÁO XỬ LÝ HÀNG LOẠT",
            "============================",
            f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Loại sản phẩm: {self.fruit_configs[self.selected_fruit.get()]['name']}",
            "",
            "TỔNG QUAN:",
            f"- Số file xử lý: {processed_count}/{total_files}",
            f"- Tổng đối tượng: {total_objects}",
            f"- Trung bình: {total_objects / max(1, processed_count):.1f} đối tượng/ảnh",
            "",
            "KÍCH THƯỚC:"
        ]
        for size, count in size_counts.most_common():
            percent = count / total_objects * 100 if total_objects > 0 else 0
            lines.append(f"- {size}: {count} ({percent:.1f}%)")
        lines.append("")
        lines.append("ĐỘ CHÍN:")
        for ripeness, count in ripeness_counts.most_common():
            percent = count / total_objects * 100 if total_objects > 0 else 0
            lines.append(f"- {ripeness}: {count} ({percent:.1f}%)")
        lines.extend([
            "",
            "CHẤT LƯỢNG:",
            f"- Tốt: {total_objects - defect_count} ({quality_percent:.1f}%)",
            f"- Khuyết tật: {defect_count} ({100 - quality_percent:.1f}%)"
        ])

        report_path = os.path.join(output_dir, "batch_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        csv_path = os.path.join(output_dir, "batch_data.csv")
        self.export_results_to_csv(results, csv_path)
        self.update_results(f"Báo cáo lưu tại: {report_path}")

    def export_results_to_csv(self, results, filename: str):
        import csv
        fieldnames = ['id', 'size', 'ripeness', 'defect', 'd_eq_mm', 'area_px', 'circularity', 'defect_ratio']
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                if r:
                    row = {field: r.get(field, '') for field in fieldnames}
                    writer.writerow(row)

    # ========================= TIỆN ÍCH =========================
    def open_calibration(self):
        try:
            filetypes = [("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
            file_path = filedialog.askopenfilename(title="Chọn ảnh mẫu để hiệu chuẩn", filetypes=filetypes)
            if not file_path:
                return
            self.update_status("Đang mở công cụ hiệu chuẩn...")
            from calibration_tool import CalibrationTool  # yêu cầu file calibration_tool.py
            calibrator = CalibrationTool()

            def run_calibration():
                calibrator.run_calibration(file_path)
                self.root.after(0, lambda: self.update_status("Hoàn thành hiệu chuẩn"))

            threading.Thread(target=run_calibration, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở công cụ hiệu chuẩn:\n{str(e)}")

    def save_current_config(self):
        try:
            fruit_key = self.selected_fruit.get()
            config = self.fruit_configs[fruit_key]
            filename = filedialog.asksaveasfilename(
                title="Lưu cấu hình", defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"config_{fruit_key}.json"
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                self.update_status(f"Đã lưu cấu hình: {filename}")
                messagebox.showinfo("Thành công", f"Đã lưu cấu hình vào:\n{filename}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu cấu hình:\n{str(e)}")

    def export_csv(self):
        """Xuất nội dung kết quả hiện tại ra CSV (Time, Message)."""
        try:
            filename = filedialog.asksaveasfilename(
                title="Xuất CSV", defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            if filename:
                content = self.results_text.get(1.0, tk.END).strip().splitlines()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Time,Message\n")
                    for line in content:
                        line = line.strip()
                        if not line:
                            continue
                        time_val, msg = "", line
                        if line.startswith('[') and ']' in line:
                            end_idx = line.find(']')
                            time_val = line[1:end_idx]
                            msg = line[end_idx + 2:]
                        # escape quotes
                        msg = msg.replace('"', "'")
                        f.write(f"\"{time_val}\",\"{msg}\"\n")
                self.update_status(f"Đã xuất CSV: {filename}")
                messagebox.showinfo("Thành công", f"Đã xuất CSV vào:\n{filename}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất CSV:\n{str(e)}")

    def export_report(self):
        try:
            filename = filedialog.asksaveasfilename(
                title="Xuất báo cáo", defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            if filename:
                fruit_key = self.selected_fruit.get()
                report_content = (
                    "BÁO CÁO HỆ THỐNG PHÂN LOẠI SẢN PHẨM\n"
                    "=====================================\n"
                    f"Thời gian tạo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Loại sản phẩm: {self.fruit_configs[fruit_key]['name']}\n\n"
                    f"KẾT QUẢ XỬ LÝ:\n{self.results_text.get(1.0, tk.END)}\n"
                    f"CẤU HÌNH HỆ THỐNG:\n{json.dumps(self.fruit_configs[fruit_key], indent=2, ensure_ascii=False)}\n"
                )
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                self.update_status(f"Đã xuất báo cáo: {filename}")
                messagebox.showinfo("Thành công", f"Đã xuất báo cáo vào:\n{filename}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo:\n{str(e)}")

    def clear_results(self):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state=tk.DISABLED)
        self.update_status("Đã xóa kết quả")

    # ========================= LƯU DỮ LIỆU VÀO DB =========================
    def _init_db_if_needed(self):
        if getattr(self, "_db", None) is not None:
            return
        # Nếu chưa có symbols do import lúc khởi động thất bại, thử import lại và báo lỗi chi tiết
        global load_app_config, MySQLConnectionManager, ensure_product_exists, insert_capture, insert_classification
        if MySQLConnectionManager is None or load_app_config is None:
            try:
                from db_helper import (
                    load_config as _load_app_config,
                    MySQLConnectionManager as _MySQLConnectionManager,
                    ensure_product_exists as _ensure_product_exists,
                    insert_capture as _insert_capture,
                    insert_classification as _insert_classification,
                )
                load_app_config = _load_app_config
                MySQLConnectionManager = _MySQLConnectionManager
                ensure_product_exists = _ensure_product_exists
                insert_capture = _insert_capture
                insert_classification = _insert_classification
            except Exception as e:
                raise RuntimeError(f"Lỗi import db_helper: {e}")
        cfg = load_app_config()
        self._db = MySQLConnectionManager(cfg)

    def _ensure_product_id(self) -> int:
        self._init_db_if_needed()
        fruit_key = self.selected_fruit.get()
        cfg = self.fruit_configs.get(fruit_key, {})
        product_name = cfg.get('product', fruit_key)
        description = cfg.get('name', fruit_key)
        pid = ensure_product_exists(self._db, product_name, description)
        self._product_id = pid
        return pid

    def save_results_to_db(self, results, source: str, image_path: Optional[str]):
        if not results:
            return
        product_id = self._ensure_product_id()
        # Nếu người dùng nhập tên phiên, lưu kèm theo để dễ tìm kiếm
        session_suffix = self.session_name_var.get().strip() if hasattr(self, 'session_name_var') else ""
        source_with_session = f"{source}{' | ' + session_suffix if session_suffix else ''}"
        capture_id = insert_capture(self._db, product_id, source=source_with_session, image_path=image_path)
        for r in results:
            if not r:
                continue
            size_label = r.get('size')
            ripeness_label = r.get('ripeness')
            defect_detected = r.get('defect') == 'Defective'
            defect_area_ratio = r.get('defect_ratio')
            color_ratio_red = r.get('ratio_red') or r.get('red_ratio')
            color_ratio_green = r.get('ratio_green') or r.get('green_ratio')
            a_star_value = r.get('a_star')
            b_star_value = r.get('b_star')
            confidence = r.get('confidence')
            extra = {
                'd_eq_mm': r.get('d_eq_mm'),
                'area_px': r.get('area_px'),
                'circularity': r.get('circularity'),
                'raw': r,
            }
            insert_classification(
                self._db,
                capture_id=capture_id,
                product_id=product_id,
                size_label=size_label,
                ripeness_label=ripeness_label,
                defect_detected=defect_detected,
                defect_area_ratio=defect_area_ratio,
                color_ratio_red=color_ratio_red,
                color_ratio_green=color_ratio_green,
                a_star_value=a_star_value,
                b_star_value=b_star_value,
                confidence=confidence,
                extra=extra,
            )

    def manual_save_db(self):
        try:
            if not self.last_results:
                messagebox.showwarning("Chú ý", "Chưa có kết quả nào để lưu.")
                return
            self.save_results_to_db(self.last_results, source="manual", image_path=self.last_image_path)
            messagebox.showinfo("Thành công", "Đã lưu dữ liệu vào DB")
        except Exception as e:
            messagebox.showerror("DB lỗi", str(e))

    # ========================= XEM DỮ LIỆU DB =========================
    def open_db_viewer(self):
        """Mở cửa sổ xem dữ liệu đã lưu trong DB với giao diện cải tiến."""
        try:
            self._init_db_if_needed()

            # Lazy import fallback nếu cần
            global fetch_captures_with_counts, fetch_classifications_by_capture
            if fetch_captures_with_counts is None or fetch_classifications_by_capture is None:
                try:
                    from db_helper import (
                        fetch_captures_with_counts as _fetch_captures,
                        fetch_classifications_by_capture as _fetch_class
                    )
                    fetch_captures_with_counts = _fetch_captures
                    fetch_classifications_by_capture = _fetch_class
                except Exception as e:
                    raise RuntimeError(f"Lỗi import db_helper: {e}")

            # Tạo cửa sổ mới với style
            db_window = tk.Toplevel(self.root)
            db_window.title("🗄️ Quản lý dữ liệu - Hệ thống phân loại sản phẩm")
            db_window.geometry("1600x900")
            db_window.configure(bg='#f8f9fa')

            # Áp dụng custom style
            CustomStyle.setup()

            # Header với tiêu đề đẹp
            header_frame = tk.Frame(db_window, bg='#2c3e50', height=80)
            header_frame.pack(fill=tk.X, padx=0, pady=0)
            header_frame.pack_propagate(False)

            tk.Label(
                header_frame,
                text="🗄️ QUẢN LÝ DỮ LIỆU PHÂN LOẠI",
                font=('Arial', 18, 'bold'), fg='white', bg='#2c3e50'
            ).pack(expand=True, pady=10)

            tk.Label(
                header_frame,
                text="Xem và quản lý dữ liệu đã lưu trong cơ sở dữ liệu",
                font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50'
            ).pack()

            # Frame chính
            main_frame = tk.Frame(db_window, bg='#f8f9fa')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

            # Frame tìm kiếm và lọc với style đẹp
            filter_frame = tk.LabelFrame(
                main_frame,
                text="🔍 TÌM KIẾM & LỌC DỮ LIỆU",
                font=('Arial', 12, 'bold'),
                bg='#ffffff', fg='#2c3e50',
                relief=tk.RAISED, bd=2,
                padx=15, pady=15
            )
            filter_frame.pack(fill=tk.X, pady=(0, 15))

            # Grid layout cho các điều khiển lọc với spacing đẹp
            tk.Label(filter_frame, text="🔍 Tìm kiếm phiên:",
                     font=('Arial', 10, 'bold'), bg='#ffffff').grid(row=0, column=0, padx=(0, 5), pady=8, sticky='w')
            session_filter = tk.Entry(filter_frame, width=25, font=('Arial', 10), relief=tk.SUNKEN, bd=2)
            session_filter.grid(row=0, column=1, padx=(0, 20), pady=8, sticky='w')

            tk.Label(filter_frame, text="🍎 Loại sản phẩm:",
                     font=('Arial', 10, 'bold'), bg='#ffffff').grid(row=0, column=2, padx=(0, 5), pady=8, sticky='w')
            product_filter = ttk.Combobox(
                filter_frame,
                values=["Tất cả"] + [name for _, name in self.fruit_configs.items()],
                width=18, font=('Arial', 10), state="readonly"
            )
            product_filter.set("Tất cả")
            product_filter.grid(row=0, column=3, padx=(0, 20), pady=8, sticky='w')

            tk.Label(filter_frame, text="📅 Thời gian:",
                     font=('Arial', 10, 'bold'), bg='#ffffff').grid(row=0, column=4, padx=(0, 5), pady=8, sticky='w')
            time_filter = ttk.Combobox(
                filter_frame,
                values=["Tất cả", "Hôm nay", "7 ngày", "30 ngày"],
                width=12, font=('Arial', 10), state="readonly"
            )
            time_filter.set("Tất cả")
            time_filter.grid(row=0, column=5, padx=(0, 20), pady=8, sticky='w')

            # Nút làm mới với icon
            refresh_btn = tk.Button(
                filter_frame,
                text="🔄 Làm mới",
                command=lambda: refresh_captures(),
                bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                relief=tk.RAISED, bd=2, padx=15, pady=5
            )
            refresh_btn.grid(row=0, column=6, padx=10, pady=8)

            # Container cho 2 cột chính
            content_container = tk.Frame(main_frame, bg='#f8f9fa')
            content_container.pack(fill=tk.BOTH, expand=True)

            # Cột trái: Danh sách captures
            left_panel = tk.LabelFrame(
                content_container,
                text="📋 DANH SÁCH PHIÊN CHỤP",
                font=('Arial', 12, 'bold'),
                bg='#ffffff', fg='#2c3e50',
                relief=tk.RAISED, bd=2,
                padx=10, pady=10
            )
            left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

            # Treeview cho captures với style mới
            cap_columns = ('id', 'timestamp', 'source', 'product', 'items', 'path')
            tree_cap = ttk.Treeview(
                left_panel,
                columns=cap_columns,
                show='headings',
                style="Custom.Treeview",
                height=12
            )

            # Định nghĩa các cột với width phù hợp
            headings_cap = {
                'id': ('ID', 60),
                'timestamp': ('Thời gian', 140),
                'source': ('Nguồn', 180),
                'product': ('Sản phẩm', 120),
                'items': ('Số lượng', 80),
                'path': ('Đường dẫn ảnh', 250)
            }

            for col, (text, width) in headings_cap.items():
                tree_cap.heading(col, text=text, anchor=tk.CENTER)
                tree_cap.column(col, width=width, anchor=tk.CENTER)

            # Thêm scrollbar cho captures
            scrollbar_cap = ttk.Scrollbar(left_panel, orient=tk.VERTICAL, command=tree_cap.yview)
            scrollbar_cap.pack(side=tk.RIGHT, fill=tk.Y)
            tree_cap.configure(yscrollcommand=scrollbar_cap.set)
            tree_cap.pack(fill=tk.BOTH, expand=True)

            # Cột phải: Chi tiết và ảnh
            right_panel = tk.Frame(content_container, bg='#f8f9fa')
            right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

            # Frame chi tiết classifications
            detail_frame = tk.LabelFrame(
                right_panel,
                text="📊 CHI TIẾT PHÂN LOẠI",
                font=('Arial', 12, 'bold'),
                bg='#ffffff', fg='#2c3e50',
                relief=tk.RAISED, bd=2,
                padx=10, pady=10
            )
            detail_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            # Treeview cho classifications
            cls_columns = ('id', 'size', 'ripeness', 'defect', 'confidence', 'timestamp')
            tree_cls = ttk.Treeview(
                detail_frame,
                columns=cls_columns,
                show='headings',
                style="Custom.Treeview",
                height=8
            )

            # Định nghĩa các cột
            headings_cls = {
                'id': ('ID', 50),
                'size': ('Kích thước', 80),
                'ripeness': ('Độ chín', 80),
                'defect': ('Khuyết tật', 80),
                'confidence': ('Độ tin cậy', 90),
                'timestamp': ('Thời gian', 120)
            }

            for col, (text, width) in headings_cls.items():
                tree_cls.heading(col, text=text, anchor=tk.CENTER)
                tree_cls.column(col, width=width, anchor=tk.CENTER)

            # Thêm scrollbar cho classifications
            scrollbar_cls = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=tree_cls.yview)
            scrollbar_cls.pack(side=tk.RIGHT, fill=tk.Y)
            tree_cls.configure(yscrollcommand=scrollbar_cls.set)
            tree_cls.pack(fill=tk.BOTH, expand=True)

            # Frame hiển thị ảnh
            image_frame = tk.LabelFrame(
                right_panel,
                text="🖼️ XEM ẢNH",
                font=('Arial', 12, 'bold'),
                bg='#ffffff', fg='#2c3e50',
                relief=tk.RAISED, bd=2,
                padx=10, pady=10
            )
            image_frame.pack(fill=tk.BOTH, expand=True)

            # Label hiển thị ảnh với border
            image_label = tk.Label(
                image_frame,
                bg='#f8f9fa',
                relief=tk.SUNKEN,
                bd=2,
                text="Chọn một phiên để xem ảnh",
                font=('Arial', 10, 'italic'),
                fg='#6c757d'
            )
            image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            def show_image(path):
                if not path or not os.path.exists(path):
                    image_label.config(
                        text="❌ Không có ảnh hoặc đường dẫn không hợp lệ",
                        image=''
                    )
                    image_label.image = None
                    return
                try:
                    img = Image.open(path)
                    # Resize để vừa với frame
                    img.thumbnail((400, 300), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    image_label.configure(image=photo, text="")
                    image_label.image = photo
                except Exception as e:
                    image_label.config(
                        text=f"❌ Lỗi hiển thị ảnh: {str(e)}",
                        image=''
                    )
                    image_label.image = None

            def on_select_capture(event):
                """Xử lý khi chọn một phiên chụp."""
                selection = tree_cap.selection()
                if not selection:
                    return

                # Lấy thông tin phiên được chọn
                item = tree_cap.item(selection[0])
                cap_id = item['values'][0]
                img_path = item['values'][5]

                # Hiển thị ảnh nếu có
                if img_path:
                    show_image(img_path)

                # Cập nhật bảng classifications
                try:
                    rows = fetch_classifications_by_capture(self._db, cap_id)

                    # Xóa dữ liệu cũ
                    for r in tree_cls.get_children():
                        tree_cls.delete(r)

                    # Thêm dữ liệu mới với màu sắc và định dạng
                    for r in rows:
                        confidence = r.get('confidence')
                        conf_str = f"{confidence:.1%}" if confidence is not None else 'N/A'
                        defect = "Có" if r.get('defect_detected') else "Không"

                        # Thêm tags để đánh dấu màu
                        tags = []
                        if r.get('defect_detected'):
                            tags.append('defect')
                        if confidence and confidence < 0.7:
                            tags.append('low_confidence')

                        tree_cls.insert(
                            "", tk.END,
                            values=(
                                r.get('id'),
                                r.get('size_label', 'N/A'),
                                r.get('ripeness_label', 'N/A'),
                                defect,
                                conf_str,
                                str(r.get('created_at'))[:19] if r.get('created_at') else 'N/A'
                            ),
                            tags=tags
                        )
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể tải chi tiết: {str(e)}")

            def refresh_captures():
                """Cập nhật danh sách captures theo bộ lọc."""
                try:
                    # Xóa dữ liệu cũ
                    for r in tree_cap.get_children():
                        tree_cap.delete(r)

                    # Áp dụng các bộ lọc
                    session_filter_text = session_filter.get().strip()
                    product_filter_text = product_filter.get()
                    time_filter_text = time_filter.get()

                    # Tải dữ liệu mới
                    rows = fetch_captures_with_counts(
                        self._db,
                        session_like=session_filter_text if session_filter_text else None,
                        limit=500
                    )

                    # Lọc theo sản phẩm
                    if product_filter_text != "Tất cả":
                        rows = [r for r in rows if r.get('product') == product_filter_text]

                    # Lọc theo thời gian
                    now = datetime.now()
                    if time_filter_text == "Hôm nay":
                        rows = [r for r in rows if r.get('captured_at').date() == now.date()]
                    elif time_filter_text == "7 ngày":
                        cutoff = now - timedelta(days=7)
                        rows = [r for r in rows if r.get('captured_at') >= cutoff]
                    elif time_filter_text == "30 ngày":
                        cutoff = now - timedelta(days=30)
                        rows = [r for r in rows if r.get('captured_at') >= cutoff]

                    # Thêm dữ liệu mới với định dạng đẹp
                    for r in rows:
                        timestamp = str(r.get('captured_at'))[:19] if r.get('captured_at') else 'N/A'
                        source = r.get('source') or 'N/A'
                        product = r.get('product') or 'N/A'
                        items = r.get('num_items') or 0
                        path = r.get('image_path') or 'N/A'

                        tree_cap.insert("", tk.END, values=(
                            r.get('id'),
                            timestamp,
                            source,
                            product,
                            items,
                            path
                        ))

                    # Cập nhật status
                    self.update_status(f"Đã tải {len(rows)} phiên chụp")

                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể cập nhật dữ liệu: {str(e)}")

            # Gắn sự kiện
            tree_cap.bind('<<TreeviewSelect>>', on_select_capture)

            # Gắn sự kiện cho các bộ lọc
            def on_filter_change(*args):
                refresh_captures()

            session_filter.bind('<Return>', on_filter_change)
            product_filter.bind('<<ComboboxSelected>>', on_filter_change)
            time_filter.bind('<<ComboboxSelected>>', on_filter_change)

            # Tải dữ liệu ban đầu
            refresh_captures()

        except Exception as e:
            messagebox.showerror("Lỗi DB", f"Không thể mở cửa sổ quản lý dữ liệu:\n{str(e)}")

    # ========================= VÒNG ĐỜI APP =========================
    def show_batch_summary_window(self):
        """Hiển thị cửa sổ tổng hợp chi tiết xử lý hàng loạt với giao diện đẹp mắt."""
        if not hasattr(self, 'batch_details'):
            return

        # Tạo cửa sổ mới với style đẹp
        summary_window = tk.Toplevel(self.root)
        summary_window.title(f"📊 Kết quả xử lý hàng loạt - {self.batch_details['fruit_type'].upper()}")
        # Kích thước tự co để không vượt màn hình
        sw = summary_window.winfo_screenwidth()
        sh = summary_window.winfo_screenheight()
        win_w = min(1200, sw - 80)  # chừa viền
        win_h = min(720, sh - 120)  # luôn fit 768p
        summary_window.geometry(f"{win_w}x{win_h}+20+20")

        summary_window.configure(bg='#f8f9fa')

        # Áp dụng custom style
        CustomStyle.setup()

        # Header với tiêu đề đẹp
        header_frame = tk.Frame(summary_window, bg='#27ae60', height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="📊 KẾT QUẢ XỬ LÝ HÀNG LOẠT",
            font=('Arial', 18, 'bold'), fg='white', bg='#27ae60'
        ).pack(expand=True, pady=10)

        tk.Label(
            header_frame,
            text=f"Loại sản phẩm: {self.batch_details['fruit_type'].upper()} | Thời gian: {self.batch_details['timestamp']}",
            font=('Arial', 12), fg='#ecf0f1', bg='#27ae60'
        ).pack()

        # Frame chính
        # --- Khung cuộn dọc ---
        scroll_container = tk.Frame(summary_window, bg='#f8f9fa')
        scroll_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(scroll_container, bg='#f8f9fa', highlightthickness=0)
        vbar = ttk.Scrollbar(scroll_container, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)

        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tạo frame nội dung bên trong canvas
        main_frame = tk.Frame(canvas, bg='#f8f9fa')

        # LƯU LẠI window id để còn chỉnh width
        win_id = canvas.create_window((0, 0), window=main_frame, anchor='nw')

        # Cập nhật vùng cuộn khi nội dung đổi
        def _update_scrollregion(_=None):
            canvas.configure(scrollregion=canvas.bbox('all'))

        main_frame.bind('<Configure>', _update_scrollregion)

        # QUAN TRỌNG: ép main_frame giãn đúng bằng bề rộng Canvas => hết trắng bên phải
        def _sync_width(event):
            canvas.itemconfigure(win_id, width=event.width)

        canvas.bind('<Configure>', _sync_width)

        # Mouse wheel
        def _on_mousewheel(e):
            canvas.yview_scroll(-int(e.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        # --- Hết khung cuộn ---

        # Frame chứa thông tin tổng quan với style đẹp
        overview_frame = tk.LabelFrame(
            main_frame,
            text="📈 THỐNG KÊ TỔNG QUAN",
            font=('Arial', 12, 'bold'),
            bg='#ffffff', fg='#2c3e50',
            relief=tk.RAISED, bd=2,
            padx=15, pady=15
        )
        overview_frame.pack(fill=tk.X, pady=(0, 15))

        # Tính toán thống kê
        total_images = len(self.batch_details['images'])
        successful_images = sum(1 for d in self.batch_details['images'].values() if len(d['results']) > 0)
        error_images = sum(1 for d in self.batch_details['images'].values() if 'error' in d)
        total_objects = sum(len(d['results']) for d in self.batch_details['images'].values())
        avg_time = sum(
            d['process_time'] for d in self.batch_details['images'].values()) / total_images if total_images > 0 else 0

        # Grid layout cho thông tin tổng quan với icons
        stats_data = [
            ("📁 Tổng số ảnh:", str(total_images)),
            ("✅ Thành công:", str(successful_images)),
            ("❌ Lỗi:", str(error_images)),
            ("🎯 Tổng đối tượng:", str(total_objects)),
            ("⏱️ Thời gian TB/ảnh:", f"{avg_time:.2f}s"),
            ("📂 Thư mục kết quả:", self.batch_details['output_dir'])
        ]

        for i, (label, value) in enumerate(stats_data):
            row = i // 3
            col = (i % 3) * 2

            tk.Label(
                overview_frame,
                text=label,
                font=('Arial', 10, 'bold'),
                bg='#ffffff',
                fg='#2c3e50'
            ).grid(row=row, column=col, padx=(0, 5), pady=8, sticky='w')

            tk.Label(
                overview_frame,
                text=value,
                font=('Arial', 10),
                bg='#ffffff',
                fg='#34495e'
            ).grid(row=row, column=col + 1, padx=(0, 20), pady=8, sticky='w')

        # Frame chứa bảng và công cụ
        content_frame = tk.LabelFrame(
            main_frame,
            text="📋 CHI TIẾT TỪNG ẢNH",
            font=('Arial', 12, 'bold'),
            bg='#ffffff', fg='#2c3e50',
            relief=tk.RAISED, bd=2,
            padx=10, pady=10
        )
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Frame công cụ với style đẹp
        tools_frame = tk.Frame(content_frame, bg='#ffffff')
        tools_frame.pack(fill=tk.X, padx=5, pady=(0, 10))

        # Thêm công cụ lọc và tìm kiếm với icons
        tk.Label(tools_frame, text="🔍 Tìm kiếm:",
                 font=('Arial', 10, 'bold'), bg='#ffffff').pack(side=tk.LEFT, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = tk.Entry(tools_frame, textvariable=search_var, width=25,
                                font=('Arial', 10), relief=tk.SUNKEN, bd=2)
        search_entry.pack(side=tk.LEFT, padx=(0, 20))

        # Thêm combobox lọc theo trạng thái
        tk.Label(tools_frame, text="🔧 Lọc:",
                 font=('Arial', 10, 'bold'), bg='#ffffff').pack(side=tk.LEFT, padx=(0, 5))
        filter_var = tk.StringVar()
        filter_combo = ttk.Combobox(
            tools_frame,
            textvariable=filter_var,
            values=["Tất cả", "✅ Thành công", "⚠️ Cảnh báo", "❌ Lỗi"],
            width=15,
            font=('Arial', 10),
            state="readonly"
        )
        filter_combo.set("Tất cả")
        filter_combo.pack(side=tk.LEFT, padx=(0, 20))

        # Nút làm mới
        refresh_btn = tk.Button(
            tools_frame,
            text="🔄 Làm mới",
            command=lambda: refresh_table(),
            bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
            relief=tk.RAISED, bd=2, padx=10, pady=3
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Frame chứa bảng chi tiết
        table_frame = tk.Frame(content_frame, bg='#ffffff')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tạo Treeview với style mới
        columns = ('status', 'file_name', 'objects', 'size', 'process_time', 'timestamp', 'details')
        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            style="Custom.Treeview",
            height=15
        )

        # Định nghĩa các cột với heading style mới
        headings = {
            'status': ('Trạng thái', 80),
            'file_name': ('Tên file', 200),
            'objects': ('Số đối tượng', 100),
            'size': ('Kích thước ảnh', 120),
            'process_time': ('Thời gian XL (s)', 120),
            'timestamp': ('Thời điểm', 100),
            'details': ('Chi tiết phân loại', 400)
        }

        for col, (text, width) in headings.items():
            tree.heading(col, text=text, anchor=tk.CENTER)
            tree.column(col, width=width, anchor=tk.CENTER)

        # Thêm scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(fill=tk.BOTH, expand=True)

        def add_data_to_table():
            """Thêm dữ liệu vào bảng với màu sắc và icons"""
            # Xóa dữ liệu cũ
            for item in tree.get_children():
                tree.delete(item)

            # Thêm dữ liệu mới
            for image_path, details in self.batch_details['images'].items():
                results = details['results']
                objects_count = len(results)

                # Xác định trạng thái và icon
                if 'error' in details:
                    status = '❌ Lỗi'
                    tags = ['error']
                elif objects_count == 0:
                    status = '⚠️ Cảnh báo'
                    tags = ['warning']
                else:
                    status = '✅ Thành công'
                    tags = ['success']

                # Tạo chuỗi chi tiết với format đẹp hơn
                if results:
                    # Thống kê nhanh
                    sizes = {}
                    ripeness = {}
                    defects = 0

                    for r in results:
                        size = r.get('size', r.get('size_label', 'N/A'))
                        ripe = r.get('ripeness', r.get('ripeness_label', 'N/A'))
                        sizes[size] = sizes.get(size, 0) + 1
                        ripeness[ripe] = ripeness.get(ripe, 0) + 1
                        if r.get('defect', r.get('defect_detected', False)) == 'Defective' or r.get('defect_detected',
                                                                                                    False):
                            defects += 1

                    # Format thông tin
                    size_str = ", ".join(f"{size}:{count}" for size, count in sizes.items())
                    ripe_str = ", ".join(f"{state}:{count}" for state, count in ripeness.items())
                    details_str = f"Kích cỡ: {size_str} | Độ chín: {ripe_str} | Khuyết tật: {defects}/{objects_count}"
                else:
                    details_str = "Không phát hiện đối tượng"

                tree.insert('', tk.END, values=(
                    status,
                    details['base_name'],
                    objects_count,
                    details['original_size'],
                    f"{details['process_time']:.2f}",
                    details['timestamp'],
                    details_str
                ), tags=tags)

        def refresh_table():
            """Làm mới bảng dữ liệu"""
            add_data_to_table()

        def filter_table(*args):
            """Lọc bảng theo tìm kiếm và trạng thái"""
            search_text = search_var.get().lower()
            filter_value = filter_var.get()

            # Xóa dữ liệu cũ
            for item in tree.get_children():
                tree.delete(item)

            # Thêm dữ liệu đã lọc
            for image_path, details in self.batch_details['images'].items():
                # Lọc theo tìm kiếm
                if search_text and search_text not in details['base_name'].lower():
                    continue

                results = details['results']
                objects_count = len(results)

                # Xác định trạng thái
                if 'error' in details:
                    status = '❌ Lỗi'
                    tags = ['error']
                elif objects_count == 0:
                    status = '⚠️ Cảnh báo'
                    tags = ['warning']
                else:
                    status = '✅ Thành công'
                    tags = ['success']

                # Lọc theo trạng thái
                if filter_value == "✅ Thành công" and status != '✅ Thành công':
                    continue
                if filter_value == "⚠️ Cảnh báo" and status != '⚠️ Cảnh báo':
                    continue
                if filter_value == "❌ Lỗi" and status != '❌ Lỗi':
                    continue

                # Tạo chuỗi chi tiết
                if results:
                    sizes = {}
                    ripeness = {}
                    defects = 0

                    for r in results:
                        size = r.get('size', r.get('size_label', 'N/A'))
                        ripe = r.get('ripeness', r.get('ripeness_label', 'N/A'))
                        sizes[size] = sizes.get(size, 0) + 1
                        ripeness[ripe] = ripeness.get(ripe, 0) + 1
                        if r.get('defect', r.get('defect_detected', False)) == 'Defective' or r.get('defect_detected',
                                                                                                    False):
                            defects += 1

                    size_str = ", ".join(f"{size}:{count}" for size, count in sizes.items())
                    ripe_str = ", ".join(f"{state}:{count}" for state, count in ripeness.items())
                    details_str = f"Kích cỡ: {size_str} | Độ chín: {ripe_str} | Khuyết tật: {defects}/{objects_count}"
                else:
                    details_str = "Không phát hiện đối tượng"

                tree.insert('', tk.END, values=(
                    status,
                    details['base_name'],
                    objects_count,
                    details['original_size'],
                    f"{details['process_time']:.2f}",
                    details['timestamp'],
                    details_str
                ), tags=tags)

        # Gắn sự kiện tìm kiếm và lọc
        search_var.trace('w', filter_table)
        filter_var.trace('w', filter_table)

        def on_tree_select(event):
            """Xử lý sự kiện khi chọn một dòng trong bảng."""
            selection = tree.selection()
            if not selection:
                return

            item = tree.item(selection[0])
            file_name = item['values'][1]  # Tên file ở cột thứ 2

            # Tìm đường dẫn ảnh từ tên file
            selected_details = None
            selected_path = None
            for image_path, details in self.batch_details['images'].items():
                if details['base_name'] == file_name:
                    selected_details = details
                    selected_path = image_path
                    break

            if selected_details and selected_path:
                try:
                    # Hiển thị kết quả chi tiết như khi xử lý đơn lẻ
                    image = cv2.imread(selected_path)
                    result_image = cv2.imread(selected_details['result_path'])
                    mask_image = cv2.imread(selected_details['mask_path'])

                    if image is not None and result_image is not None and mask_image is not None:
                        # Sử dụng hàm hiển thị có sẵn
                        self.display_image_results(
                            result_image,
                            mask_image,
                            selected_details['results'],
                            selected_path
                        )
                    else:
                        messagebox.showwarning("Cảnh báo", "Không thể tải ảnh để hiển thị")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể hiển thị ảnh: {str(e)}")

        # Gắn sự kiện click vào dòng trong bảng
        tree.bind('<Double-1>', on_tree_select)

        # Thêm dữ liệu ban đầu
        add_data_to_table()

        # Frame chứa các nút điều khiển
        control_frame = tk.Frame(content_frame, bg='#ffffff')
        control_frame.pack(fill=tk.X, padx=5, pady=(10, 0))

        # Thêm các nút với style mới
        tk.Button(
            control_frame,
            text="📊 Xuất Excel",
            bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
            relief=tk.RAISED, bd=2, padx=15, pady=5,
            command=lambda: self.export_batch_to_excel()
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            control_frame,
            text="📈 Xem thống kê",
            bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
            relief=tk.RAISED, bd=2, padx=15, pady=5,
            command=lambda: self.show_batch_statistics()
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            control_frame,
            text="🖼️ Xem ảnh gốc",
            bg='#9b59b6', fg='white', font=('Arial', 10, 'bold'),
            relief=tk.RAISED, bd=2, padx=15, pady=5,
            command=lambda: self.open_result_folder()
        ).pack(side=tk.LEFT, padx=5)

        # Thêm label thống kê nhanh
        stats_text = f"📊 Tổng: {total_images} ảnh | ✅ Thành công: {successful_images} | ❌ Lỗi: {error_images} | 🎯 Đối tượng: {total_objects}"
        tk.Label(
            control_frame,
            text=stats_text,
            font=('Arial', 10, 'bold'),
            bg='#ffffff',
            fg='#2c3e50'
        ).pack(side=tk.RIGHT, padx=5)

    def open_result_folder(self):
        """Mở thư mục kết quả trong file explorer."""
        if not hasattr(self, 'batch_details'):
            messagebox.showwarning("Cảnh báo", "Chưa có dữ liệu xử lý hàng loạt")
            return

        output_dir = self.batch_details.get('output_dir')
        if not output_dir or not os.path.exists(output_dir):
            messagebox.showerror("Lỗi", "Thư mục kết quả không tồn tại")
            return

        try:
            import subprocess
            import platform

            if platform.system() == "Windows":
                subprocess.run(["explorer", output_dir], check=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", output_dir], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", output_dir], check=True)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở thư mục: {str(e)}")

    def show_batch_statistics(self):
        """Hiển thị cửa sổ thống kê chi tiết cho xử lý hàng loạt với giao diện đẹp mắt."""
        if not hasattr(self, 'batch_details'):
            return

        stats_window = tk.Toplevel(self.root)
        stats_window.title("📈 Thống kê chi tiết - Xử lý hàng loạt")
        stats_window.geometry("800x600")
        stats_window.configure(bg='#f8f9fa')

        # Header với tiêu đề đẹp
        header_frame = tk.Frame(stats_window, bg='#3498db', height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="📈 THỐNG KÊ CHI TIẾT",
            font=('Arial', 16, 'bold'), fg='white', bg='#3498db'
        ).pack(expand=True, pady=15)

        # Frame chính
        main_frame = tk.Frame(stats_window, bg='#f8f9fa')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Tính toán thống kê
        total_images = len(self.batch_details['images'])
        total_objects = 0
        size_stats = {}
        ripeness_stats = {}
        defect_count = 0
        total_time = 0
        error_count = 0
        successful_count = 0

        for details in self.batch_details['images'].values():
            results = details['results']
            total_objects += len(results)
            total_time += details['process_time']

            if 'error' in details:
                error_count += 1
            elif len(results) > 0:
                successful_count += 1

            for r in results:
                size = r.get('size', r.get('size_label', 'N/A'))
                ripe = r.get('ripeness', r.get('ripeness_label', 'N/A'))
                size_stats[size] = size_stats.get(size, 0) + 1
                ripeness_stats[ripe] = ripeness_stats.get(ripe, 0) + 1
                if r.get('defect', r.get('defect_detected', False)) == 'Defective' or r.get('defect_detected', False):
                    defect_count += 1

        # Frame cho thống kê cơ bản với style đẹp
        basic_frame = tk.LabelFrame(
            main_frame,
            text="📊 THỐNG KÊ CƠ BẢN",
            font=('Arial', 12, 'bold'),
            bg='#ffffff', fg='#2c3e50',
            relief=tk.RAISED, bd=2,
            padx=15, pady=15
        )
        basic_frame.pack(fill=tk.X, padx=5, pady=5)

        # Hiển thị thống kê với icons
        stats_data = [
            ("📁 Tổng số ảnh:", str(total_images)),
            ("✅ Thành công:", str(successful_count)),
            ("❌ Lỗi:", str(error_count)),
            ("🎯 Tổng đối tượng:", str(total_objects)),
            ("⏱️ Thời gian TB/ảnh:", f"{total_time / total_images:.2f}s" if total_images > 0 else "0s"),
            ("🔍 Đối tượng có khuyết tật:", str(defect_count)),
            ("📈 Tỷ lệ thành công:", f"{successful_count / total_images * 100:.1f}%" if total_images > 0 else "0%"),
            ("🎯 Đối tượng/ảnh TB:", f"{total_objects / total_images:.1f}" if total_images > 0 else "0")
        ]

        for i, (label, value) in enumerate(stats_data):
            row = i // 2
            col = (i % 2) * 2

            tk.Label(
                basic_frame,
                text=label,
                font=('Arial', 10, 'bold'),
                bg='#ffffff',
                fg='#2c3e50'
            ).grid(row=row, column=col, padx=(0, 5), pady=8, sticky='w')
            tk.Label(
                basic_frame,
                text=value,
                font=('Arial', 10),
                bg='#ffffff',
                fg='#34495e'
            ).grid(row=row, column=col + 1, padx=(0, 20), pady=8, sticky='w')

        # Container cho 2 cột thống kê
        stats_container = tk.Frame(main_frame, bg='#f8f9fa')
        stats_container.pack(fill=tk.BOTH, expand=True, pady=10)

        # Frame cho phân phối kích thước
        size_frame = tk.LabelFrame(
            stats_container,
            text="📏 PHÂN PHỐI KÍCH THƯỚC",
            font=('Arial', 12, 'bold'),
            bg='#ffffff', fg='#2c3e50',
            relief=tk.RAISED, bd=2,
            padx=15, pady=15
        )
        size_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        if size_stats:
            for i, (size, count) in enumerate(sorted(size_stats.items())):
                percent = count / total_objects * 100 if total_objects > 0 else 0
                tk.Label(
                    size_frame,
                    text=f"📐 {size}:",
                    font=('Arial', 10, 'bold'),
                    bg='#ffffff',
                    fg='#2c3e50'
                ).grid(row=i, column=0, padx=5, pady=5, sticky='w')
                tk.Label(
                    size_frame,
                    text=f"{count} ({percent:.1f}%)",
                    font=('Arial', 10),
                    bg='#ffffff',
                    fg='#34495e'
                ).grid(row=i, column=1, padx=5, pady=5, sticky='w')
        else:
            tk.Label(
                size_frame,
                text="Không có dữ liệu",
                font=('Arial', 10, 'italic'),
                bg='#ffffff',
                fg='#6c757d'
            ).pack(pady=20)

        # Frame cho phân phối độ chín
        ripe_frame = tk.LabelFrame(
            stats_container,
            text="🍎 PHÂN PHỐI ĐỘ CHÍN",
            font=('Arial', 12, 'bold'),
            bg='#ffffff', fg='#2c3e50',
            relief=tk.RAISED, bd=2,
            padx=15, pady=15
        )
        ripe_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        if ripeness_stats:
            for i, (ripe, count) in enumerate(sorted(ripeness_stats.items())):
                percent = count / total_objects * 100 if total_objects > 0 else 0
                # Chọn icon phù hợp
                icon = "🟢" if "Xanh" in ripe or "Green" in ripe else "🔴" if "Chín" in ripe or "Ripe" in ripe else "🟡"
                tk.Label(
                    ripe_frame,
                    text=f"{icon} {ripe}:",
                    font=('Arial', 10, 'bold'),
                    bg='#ffffff',
                    fg='#2c3e50'
                ).grid(row=i, column=0, padx=5, pady=5, sticky='w')
                tk.Label(
                    ripe_frame,
                    text=f"{count} ({percent:.1f}%)",
                    font=('Arial', 10),
                    bg='#ffffff',
                    fg='#34495e'
                ).grid(row=i, column=1, padx=5, pady=5, sticky='w')
        else:
            tk.Label(
                ripe_frame,
                text="Không có dữ liệu",
                font=('Arial', 10, 'italic'),
                bg='#ffffff',
                fg='#6c757d'
            ).pack(pady=20)

        # Frame chứa nút đóng
        button_frame = tk.Frame(main_frame, bg='#f8f9fa')
        button_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(
            button_frame,
            text="❌ Đóng",
            command=stats_window.destroy,
            bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'),
            relief=tk.RAISED, bd=2, padx=20, pady=5
        ).pack(side=tk.RIGHT, padx=5)

    def export_batch_to_excel(self):
        """Xuất kết quả xử lý hàng loạt ra file Excel."""
        if not hasattr(self, 'batch_details'):
            return

        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=f"batch_results_{self.batch_details['timestamp']}.xlsx"
            )
            if not filename:
                return

            # Tạo DataFrame từ dữ liệu
            rows = []
            for image_path, details in self.batch_details['images'].items():
                base_row = {
                    'Tên file': details['base_name'],
                    'Kích thước': details['original_size'],
                    'Thời gian xử lý (s)': f"{details['process_time']:.2f}",
                    'Thời điểm': details['timestamp'],
                    'Số đối tượng': len(details['results'])
                }

                if not details['results']:
                    rows.append({**base_row, 'STT đối tượng': 'N/A', 'Kích cỡ': 'N/A',
                                 'Độ chín': 'N/A', 'Khuyết tật': 'N/A'})
                else:
                    for idx, result in enumerate(details['results'], 1):
                        rows.append({
                            **base_row,
                            'STT đối tượng': idx,
                            'Kích cỡ': result.get('size_label', 'N/A'),
                            'Độ chín': result.get('ripeness_label', 'N/A'),
                            'Khuyết tật': "Có" if result.get('defect_detected', False) else "Không"
                        })

            df = pd.DataFrame(rows)
            df.to_excel(filename, index=False, engine='openpyxl')
            messagebox.showinfo("Thành công", f"Đã xuất báo cáo chi tiết ra file:\n{filename}")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất file Excel:\n{str(e)}")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        if self.is_camera_running:
            self.stop_camera()
        # Cleanup tất cả file tạm
        for fruit_key in self.fruit_configs.keys():
            temp_file = f"temp_{fruit_key}_config.json"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        # Đóng DB nếu có
        try:
            if getattr(self, "_db", None) is not None:
                self._db.close()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    app = MainGUIInterface()
    app.run()
