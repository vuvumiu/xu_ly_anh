# main_gui.py — Giao diện chính với lựa chọn mode và loại quả (đã sửa lỗi và tối ưu hiển thị)
# Lưu file này là main_gui.py rồi chạy trực tiếp.

import os
import cv2
import json
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Thử import FruitClassificationSystem từ main.py, đưa ra thông báo rõ ràng nếu thiếu
try:
    from main import FruitClassificationSystem
except Exception:
    class FruitClassificationSystem:  # type: ignore
        def __init__(self, *_args, **_kwargs):
            raise ImportError(
                "Không import được FruitClassificationSystem từ main.py.\n"
                "• Hãy chắc chắn main.py tồn tại trong cùng thư mục.\n"
                "• Trong main.py phải có class FruitClassificationSystem(config_path: str)."
            )


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

        # Tuỳ chọn hiển thị/hiệu năng (sẽ tạo widget trong create_control_panel)
        self.hide_text_var = tk.BooleanVar(value=True)     # Chỉ vẽ khung, không vẽ chữ lên video
        self.fast_start_var = tk.BooleanVar(value=True)    # Mở nhanh: bỏ auto-calibrate khung đầu
        self.display_size_var = tk.StringVar(value="960x540")  # kích thước hiển thị camera
        self._display_wh = (960, 540)

        # Tải cấu hình các loại quả
        self.fruit_configs = self.load_all_fruit_configs()

        # Tạo giao diện
        self.create_interface()

    # ========================= CẤU HÌNH =========================
    def load_all_fruit_configs(self):
        """Tải cấu hình cho tất cả các loại quả (đã sửa lỗi JSON của orange)."""
        configs = {
            "tomato": {
                "name": "Cà chua",
                "product": "tomato",
                "size_thresholds_mm": {"S": [0, 55], "M": [55, 65], "L": [65, 75], "XL": [75, 999]},
                "hsv_ranges": {
                    "red": [
                        {"H": [0, 10], "S": [80, 255], "V": [70, 255]},
                        {"H": [160, 180], "S": [80, 255], "V": [70, 255]}
                    ],
                    "green": [{"H": [35, 85], "S": [60, 255], "V": [60, 255]}],
                    "yellow": [{"H": [15, 35], "S": [50, 255], "V": [50, 255]}]
                },
                "lab_thresholds": {"a_star_ripe_min": 25, "a_star_green_max": 10},
                "ripeness_logic": {
                    "green_if": {"ratio_red_max": 0.15, "a_star_max": 10},
                    "ripe_if": {"ratio_red_min": 0.35, "a_star_min": 20}
                },
                "defect": {"dark_delta_T": 25, "area_ratio_tau": 0.06},
                "morphology": {"open_kernel": 3, "close_kernel": 5, "min_area": 200},
                "watershed": {"distance_threshold_rel": 0.5}
            },

            "apple": {
                "name": "Táo",
                "product": "apple",
                "size_thresholds_mm": {"S": [0, 60], "M": [60, 70], "L": [70, 85], "XL": [85, 999]},
                "hsv_ranges": {
                    "red": [
                        {"H": [0, 15], "S": [100, 255], "V": [80, 255]},
                        {"H": [165, 180], "S": [100, 255], "V": [80, 255]}
                    ],
                    "green": [{"H": [40, 80], "S": [50, 255], "V": [60, 255]}],
                    "yellow": [{"H": [20, 40], "S": [60, 255], "V": [70, 255]}]
                },
                "lab_thresholds": {"a_star_ripe_min": 20, "a_star_green_max": 15},
                "ripeness_logic": {
                    "green_if": {"ratio_red_max": 0.20, "a_star_max": 15},
                    "ripe_if": {"ratio_red_min": 0.40, "a_star_min": 18}
                },
                "defect": {"dark_delta_T": 30, "area_ratio_tau": 0.08},
                "morphology": {"open_kernel": 4, "close_kernel": 6, "min_area": 300},
                "watershed": {"distance_threshold_rel": 0.45}
            },

            "banana": {
                "name": "Chuối",
                "product": "banana",
                "size_thresholds_mm": {"S": [0, 120], "M": [120, 150], "L": [150, 180], "XL": [180, 999]},
                "hsv_ranges": {
                    "yellow": [{"H": [15, 35], "S": [80, 255], "V": [80, 255]}],
                    "green": [{"H": [40, 80], "S": [60, 255], "V": [60, 255]}],
                    "brown": [{"H": [5, 25], "S": [50, 200], "V": [30, 100]}]
                },
                "lab_thresholds": {"b_star_yellow_min": 20, "a_star_green_max": 10},
                "ripeness_logic": {
                    "green_if": {"ratio_yellow_max": 0.30, "b_star_max": 15},
                    "ripe_if": {"ratio_yellow_min": 0.70, "b_star_min": 25}
                },
                "defect": {"dark_delta_T": 20, "area_ratio_tau": 0.05},
                "morphology": {"open_kernel": 3, "close_kernel": 4, "min_area": 400},
                "watershed": {"distance_threshold_rel": 0.3},
                "shape_analysis": {"min_aspect_ratio": 2.5}
            },

            "guava": {
                "name": "Ổi",
                "product": "guava",
                "size_thresholds_mm": {"S": [0, 50], "M": [50, 70], "L": [70, 90], "XL": [90, 999]},
                "hsv_ranges": {
                    "green": [{"H": [40, 90], "S": [30, 255], "V": [60, 255]}],
                    "white": [{"H": [0, 180], "S": [0, 50], "V": [150, 255]}],
                    "yellow": [{"H": [20, 40], "S": [40, 255], "V": [100, 255]}]
                },
                "lab_thresholds": {"a_star_ripe_min": 5, "l_star_min": 120},
                "ripeness_logic": {
                    "green_if": {"ratio_white_max": 0.20, "l_star_max": 140},
                    "ripe_if": {"ratio_white_min": 0.50, "l_star_min": 160}
                },
                "defect": {"dark_delta_T": 35, "area_ratio_tau": 0.04},
                "morphology": {"open_kernel": 4, "close_kernel": 6, "min_area": 250},
                "watershed": {"distance_threshold_rel": 0.55}
            },

            "orange": {
                "name": "Cam",
                "product": "orange",
                "size_thresholds_mm": {"S": [0, 65], "M": [65, 75], "L": [75, 90], "XL": [90, 999]},
                "hsv_ranges": {
                    "orange": [{"H": [5, 25], "S": [100, 255], "V": [100, 255]}],
                    "yellow": [{"H": [25, 40], "S": [80, 255], "V": [120, 255]}],
                    "green": [{"H": [40, 80], "S": [60, 255], "V": [80, 255]}]
                },
                "lab_thresholds": {"a_star_ripe_min": 15, "b_star_orange_min": 30},
                "ripeness_logic": {
                    "green_if": {"ratio_orange_max": 0.25, "b_star_max": 20},
                    "ripe_if": {"ratio_orange_min": 0.60, "b_star_min": 35}
                },
                "defect": {"dark_delta_T": 25, "area_ratio_tau": 0.06},
                "morphology": {"open_kernel": 3, "close_kernel": 5, "min_area": 300},
                "watershed": {"distance_threshold_rel": 0.5}
            },

            "mango": {
                "name": "Xoài",
                "product": "mango",
                "size_thresholds_mm": {"S": [0, 80], "M": [80, 120], "L": [120, 160], "XL": [160, 999]},
                "hsv_ranges": {
                    "yellow": [{"H": [15, 35], "S": [80, 255], "V": [100, 255]}],
                    "green": [{"H": [40, 80], "S": [60, 255], "V": [70, 255]}],
                    "red":   [{"H": [0, 15],  "S": [80, 255], "V": [80, 255]}]
                },
                "lab_thresholds": {"a_star_ripe_min": 10, "b_star_yellow_min": 25},
                "ripeness_logic": {
                    "green_if": {"ratio_yellow_max": 0.30, "b_star_max": 20},
                    "ripe_if": {"ratio_yellow_min": 0.60, "b_star_min": 30}
                },
                "defect": {"dark_delta_T": 28, "area_ratio_tau": 0.07},
                "morphology": {"open_kernel": 4, "close_kernel": 5, "min_area": 350},
                "watershed": {"distance_threshold_rel": 0.45}
            }
        }
        return configs

    # ========================= GIAO DIỆN =========================
    def create_interface(self):
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

        # Thống kê và kết quả (giữ như cũ)
        stats_frame = tk.LabelFrame(parent, text="THỐNG KÊ & KẾT QUẢ",
                                    bg='#fdf6e3', padx=10, pady=10)
        stats_frame.pack(fill=tk.BOTH, expand=True)

        self.results_text = tk.Text(stats_frame, height=8, font=('Consolas', 9),
                                    state=tk.DISABLED, bg='#ffffff')
        results_scroll = tk.Scrollbar(stats_frame, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scroll.set)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # BẢNG REAL-TIME: tránh chồng chữ, hiển thị đầy đủ dữ liệu đối tượng
        table_frame = tk.LabelFrame(parent, text="BẢNG REAL-TIME", bg='#fdf6e3')
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        cols = ("ID", "Size", "Ripeness", "Defect", "D(mm)")
        self.live_table = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)
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
            output_dir = os.path.join(
                folder_path, f"results_{fruit_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            os.makedirs(output_dir, exist_ok=True)

            batch_results = []
            processed_count = 0

            for i, image_path in enumerate(image_files):
                try:
                    progress = f"Xử lý {i+1}/{len(image_files)}: {os.path.basename(image_path)}"
                    self.root.after(0, lambda p=progress: self.update_status(p))

                    image = cv2.imread(image_path)
                    if image is None:
                        raise ValueError("Không thể đọc ảnh")

                    vis, results, mask = system.process_frame(image)

                    base_name = os.path.splitext(os.path.basename(image_path))[0]
                    result_path = os.path.join(output_dir, f"{base_name}_result.jpg")
                    mask_path = os.path.join(output_dir, f"{base_name}_mask.jpg")
                    cv2.imwrite(result_path, vis)
                    cv2.imwrite(mask_path, mask)

                    valid_results = [r for r in results if r is not None]
                    batch_results.extend(valid_results)

                    log_text = f"✓ {base_name}: {len(valid_results)} đối tượng"
                    self.root.after(0, lambda t=log_text: self.update_results(t))
                    processed_count += 1
                except Exception as e:
                    error_text = f"✗ {os.path.basename(image_path)}: {str(e)}"
                    self.root.after(0, lambda t=error_text: self.update_results(t))
                    continue

            # Báo cáo tổng hợp
            self.create_batch_report(batch_results, output_dir, processed_count, len(image_files))

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
            temp_config_file = f"temp_{fruit_key}_config.json"
            with open(temp_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.fruit_configs[fruit_key], f, indent=2, ensure_ascii=False)

            self.current_system = FruitClassificationSystem(temp_config_file)

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
        try:
            cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
        except Exception:
            cap = cv2.VideoCapture(camera_id)

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
        video_writer = None
        if self.recording_var.get():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            video_writer = cv2.VideoWriter(f"recording_{timestamp}.avi", fourcc, 20.0, (w, h))

        try:
            while self.is_camera_running:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1

                vis, results, mask = self.current_system.process_frame(frame)

                # đảm bảo kích thước hiển thị gọn
                if vis.shape[1] != w or vis.shape[0] != h:
                    vis = cv2.resize(vis, (w, h))
                if mask.shape[1] != int(w * 0.5) or mask.shape[0] != int(h * 0.5):
                    mask_disp = cv2.resize(mask, (int(w * 0.5), int(h * 0.5)))
                else:
                    mask_disp = mask

                # cập nhật bảng dữ liệu định kỳ (mỗi ~0.5s)
                if frame_count % 15 == 0:
                    valid_results = [r for r in results if r is not None]
                    self.root.after(0, lambda v=valid_results: self.update_live_table(v))
                    if valid_results:
                        self.update_camera_statistics(valid_results, frame_count)

                if video_writer is not None:
                    video_writer.write(vis)

                cv2.imshow("Camera - Phan loai san pham", vis)
                cv2.imshow("Segmentation Mask", mask_disp)

                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break
                elif key == ord('s'):
                    self.save_camera_frame(frame, vis, results, frame_count)
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"Lỗi camera processing: {str(e)}"))
        finally:
            cap.release()
            if video_writer is not None:
                video_writer.release()
            cv2.destroyAllWindows()
            self.is_camera_running = False
            self.root.after(0, lambda: self.camera_btn.config(text="BẮT ĐẦU CAMERA", bg='#3498db'))

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
        ripe_count = sum(1 for r in results if r.get('ripeness') == 'Ripe')
        defect_count = sum(1 for r in results if r.get('defect') == 'Defective')
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
            'files': { 'original': original_path, 'processed': result_path }
        }
        data_path = f"camera_data_{fruit_name}_{timestamp}.json"
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        self.update_results(f"Đã lưu frame: {timestamp}")

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
            f"- Trung bình: {total_objects/max(1, processed_count):.1f} đối tượng/ảnh",
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
            f"- Khuyết tật: {defect_count} ({100-quality_percent:.1f}%)"
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
                            msg = line[end_idx+2:]
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

    # ========================= VÒNG ĐỜI APP =========================
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
        self.root.destroy()


if __name__ == "__main__":
    app = MainGUIInterface()
    app.run()
