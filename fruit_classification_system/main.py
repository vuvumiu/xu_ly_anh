# main.py - Ứng dụng chính xử lý video/camera thời gian thực
import cv2
import numpy as np
import json
import time
from datetime import datetime
import os


class FruitClassificationSystem:
    def __init__(self, config_file="config.json"):
        """
        Khởi tạo hệ thống phân loại sản phẩm

        Tham số:
        - config_file: tệp cấu hình chứa ngưỡng và tham số cho từng loại quả
        """
        self.config = self.load_config(config_file)
        self.scale_state = {"mm_per_px": None}
        self.results_log = []
        # ---- MỚI: chế độ render để kiểm soát chữ vẽ lên frame ----
        # "full": vẽ khung + text từng đối tượng + panel tổng
        # "minimal": vẽ khung + panel tổng (không text từng đối tượng)
        # "boxes_only": chỉ vẽ khung (mặc định dùng trong GUI để tránh chồng chữ)
        # "off": không vẽ gì thêm
        self.render_mode = "boxes_only"

    def set_render_mode(self, mode: str):
        """
        Đặt chế độ render cho hình hiển thị:
        - "full" | "minimal" | "boxes_only" | "off"
        """
        self.render_mode = mode

    def load_config(self, config_file):
        """Tải cấu hình từ tệp JSON"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.default_config()

    def default_config(self):
        """Cấu hình mặc định cho cà chua"""
        return {
            "product": "tomato",
            "size_thresholds_mm": {"S": [0, 55], "M": [55, 65], "L": [65, 75], "XL": [75, 999]},
            "hsv_ranges": {
                "red": [{"H": [0, 10], "S": [80, 255], "V": [70, 255]},
                        {"H": [160, 180], "S": [80, 255], "V": [70, 255]}],
                "green": [{"H": [35, 85], "S": [60, 255], "V": [60, 255]}]
            },
            "lab_thresholds": {
                "a_star_ripe_min": 25,
                "a_star_green_max": 10
            },
            "ripeness_logic": {
                "green_if": {"ratio_red_max": 0.15, "a_star_max": 10},
                "ripe_if": {"ratio_red_min": 0.35, "a_star_min": 20}
            },
            "defect": {"dark_delta_T": 25, "area_ratio_tau": 0.06},
            "morphology": {"open_kernel": 3, "close_kernel": 5, "min_area": 200},
            "watershed": {"distance_threshold_rel": 0.5}
        }

    def color_correction_lab_clahe(self, bgr):
        """
        Hiệu chỉnh màu sắc và độ sáng bằng CLAHE trong không gian màu LAB

        Chức năng: Cân bằng độ tương phản địa phương để xử lý ánh sáng không đều
        """
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Áp dụng CLAHE (Contrast Limited Adaptive Histogram Equalization) cho kênh L
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_corrected = clahe.apply(l)

        # Ghép các kênh lại và chuyển về BGR
        lab_corrected = cv2.merge([l_corrected, a, b])
        return cv2.cvtColor(lab_corrected, cv2.COLOR_LAB2BGR)

    def denoise(self, img, method="median", k=3):
        """
        Giảm nhiễu cho ảnh

        Chức năng: Loại bỏ nhiễu muối tiêu và nhiễu Gaussian
        """
        if method == "median":
            return cv2.medianBlur(img, k)
        elif method == "gaussian":
            return cv2.GaussianBlur(img, (k, k), 1.0)
        return img

    def segment_by_color_hsv_lab(self, bgr):
        """
        Phân đoạn vật thể dựa trên màu sắc trong không gian HSV và LAB

        Chức năng: Tách foreground (quả) khỏi background bằng ngưỡng màu
        """
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)

        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)

        # Kết hợp mask từ các dải màu HSV
        for color_name, ranges in self.config["hsv_ranges"].items():
            for range_dict in ranges:
                lower_hsv = np.array([range_dict["H"][0], range_dict["S"][0], range_dict["V"][0]])
                upper_hsv = np.array([range_dict["H"][1], range_dict["S"][1], range_dict["V"][1]])
                color_mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
                mask = cv2.bitwise_or(mask, color_mask)

        # Kết hợp với điều kiện a* trong LAB để tăng độ chính xác
        a_channel = lab[:, :, 1]
        if "lab_thresholds" in self.config:
            lab_mask = np.ones(a_channel.shape, dtype=np.uint8) * 255
            mask = cv2.bitwise_and(mask, lab_mask)

        return mask

    def clean_mask(self, mask):
        """
        Làm sạch mask bằng các phép hình thái học

        Chức năng: Loại bỏ nhiễu nhỏ, lấp lỗ, làm mượt biên
        """
        morph_config = self.config["morphology"]

        # Opening: loại bỏ nhiễu nhỏ
        open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                (morph_config["open_kernel"], morph_config["open_kernel"]))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, open_kernel)

        # Closing: lấp lỗ
        close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                 (morph_config["close_kernel"], morph_config["close_kernel"]))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_kernel)

        # Loại bỏ các vùng nhỏ
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < morph_config["min_area"]:
                cv2.fillPoly(mask, [contour], 0)

        return mask

    def watershed_separation(self, mask):
        """
        Tách các vật thể dính nhau bằng thuật toán Watershed

        Chức năng: Phân tách các quả chồng lên nhau thành các đối tượng riêng biệt
        """
        # Tính Distance Transform
        dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, 5)

        # Tìm local maxima làm markers
        threshold_rel = self.config["watershed"]["distance_threshold_rel"]
        _, sure_fg = cv2.threshold(dist_transform, threshold_rel * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)

        # Tìm markers
        _, markers = cv2.connectedComponents(sure_fg)

        # Áp dụng Watershed
        markers = markers + 1  # Đảm bảo background không phải 0
        markers[mask == 0] = 0  # Đánh dấu background

        # Chuyển mask sang 3 kênh cho watershed
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        markers = cv2.watershed(mask_3ch, markers)

        return markers, markers.max()

    def extract_features(self, bgr, obj_mask, object_id):
        """
        Trích xuất đặc trưng từ một đối tượng

        Chức năng: Tính toán các thông số hình học, màu sắc và khuyết tật
        """
        # Tìm contour
        contours, _ = cv2.findContours(obj_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        contour = max(contours, key=cv2.contourArea)

        # Đặc trưng hình học
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        # Đường kính tương đương
        d_eq_px = np.sqrt(4 * area / np.pi)
        d_eq_mm = d_eq_px * (self.scale_state["mm_per_px"] or 1.0)

        # Độ tròn
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0

        # Bounding box
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / h if h > 0 else 0

        # Đặc trưng màu sắc
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)

        # Tính màu trung bình trong vùng mask
        h_mean = cv2.mean(hsv[:, :, 0], obj_mask)[0]
        s_mean = cv2.mean(hsv[:, :, 1], obj_mask)[0]
        v_mean = cv2.mean(hsv[:, :, 2], obj_mask)[0]

        a_mean = cv2.mean(lab[:, :, 1], obj_mask)[0]
        b_mean = cv2.mean(lab[:, :, 2], obj_mask)[0]

        # Tính tỷ lệ pixel màu đỏ và xanh
        ratio_red = self.calculate_color_ratio(hsv, obj_mask, "red")
        ratio_green = self.calculate_color_ratio(hsv, obj_mask, "green")

        # Phát hiện khuyết tật
        defect_ratio = self.detect_defects(lab[:, :, 0], obj_mask)

        return {
            "id": object_id,
            "area_px": area,
            "perimeter": perimeter,
            "d_eq_px": d_eq_px,
            "d_eq_mm": d_eq_mm,
            "circularity": circularity,
            "aspect_ratio": aspect_ratio,
            "h_mean": h_mean,
            "s_mean": s_mean,
            "v_mean": v_mean,
            "a_mean": a_mean,
            "b_mean": b_mean,
            "ratio_red": ratio_red,
            "ratio_green": ratio_green,
            "defect_ratio": defect_ratio,
            "bbox": (x, y, w, h)
        }

    def calculate_color_ratio(self, hsv, obj_mask, color):
        """
        Tính tỷ lệ pixel có màu cụ thể trong đối tượng

        Chức năng: Đánh giá độ chín dựa trên tỷ lệ màu đỏ/xanh
        """
        if color not in self.config["hsv_ranges"]:
            return 0.0

        total_pixels = np.sum(obj_mask > 0)
        if total_pixels == 0:
            return 0.0

        color_pixels = 0
        for range_dict in self.config["hsv_ranges"][color]:
            lower = np.array([range_dict["H"][0], range_dict["S"][0], range_dict["V"][0]])
            upper = np.array([range_dict["H"][1], range_dict["S"][1], range_dict["V"][1]])
            color_mask = cv2.inRange(hsv, lower, upper)
            combined_mask = cv2.bitwise_and(color_mask, obj_mask)
            color_pixels += np.sum(combined_mask > 0)

        return color_pixels / total_pixels

    def detect_defects(self, l_channel, obj_mask):
        """
        Phát hiện các vùng khuyết tật (đốm thâm, hỏng)

        Chức năng: Tìm các vùng tối bất thường so với độ sáng trung bình
        """
        if np.sum(obj_mask) == 0:
            return 0.0

        # Tính độ sáng trung bình của đối tượng
        mean_brightness = cv2.mean(l_channel, obj_mask)[0]

        # Ngưỡng để xác định vùng tối
        dark_threshold = mean_brightness - self.config["defect"]["dark_delta_T"]

        # Tạo mask cho vùng tối
        dark_mask = (l_channel < dark_threshold).astype(np.uint8) * 255
        dark_mask = cv2.bitwise_and(dark_mask, obj_mask)

        # Tính tỷ lệ diện tích khuyết tật
        defect_area = np.sum(dark_mask > 0)
        total_area = np.sum(obj_mask > 0)

        return defect_area / total_area if total_area > 0 else 0.0

    def classify_object(self, features):
        """
        Phân loại đối tượng dựa trên các đặc trưng

        Chức năng: Xác định kích thước, độ chín và trạng thái khuyết tật
        """
        # Phân loại kích thước
        size_class = "Unknown"
        d_mm = features["d_eq_mm"]
        for size, (min_val, max_val) in self.config["size_thresholds_mm"].items():
            if min_val <= d_mm < max_val:
                size_class = size
                break

        # Phân loại độ chín
        ripeness_class = "Medium"
        ratio_red = features["ratio_red"]
        a_mean = features["a_mean"]

        green_conditions = self.config["ripeness_logic"]["green_if"]
        ripe_conditions = self.config["ripeness_logic"]["ripe_if"]

        if (ratio_red <= green_conditions.get("ratio_red_max", 1.0) or
                a_mean <= green_conditions.get("a_star_max", 255)):
            ripeness_class = "Green"
        elif (ratio_red >= ripe_conditions.get("ratio_red_min", 0.0) or
              a_mean >= ripe_conditions.get("a_star_min", 0.0)):
            ripeness_class = "Ripe"

        # Phân loại khuyết tật
        defect_status = "OK"
        if features["defect_ratio"] >= self.config["defect"]["area_ratio_tau"]:
            defect_status = "Defective"

        return {
            "size": size_class,
            "ripeness": ripeness_class,
            "defect": defect_status
        }

    def calibrate_scale_from_reference(self, bgr):
        """
        Hiệu chuẩn tỷ lệ pixel/mm từ vật tham chiếu

        Chức năng: Xác định tỷ lệ chuyển đổi từ pixel sang mm thực tế
        """
        # Tìm đồng xu hoặc vật tham chiếu có kích thước biết trước
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 50,
                                   param1=50, param2=30, minRadius=20, maxRadius=100)

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            if len(circles) > 0:
                # Giả sử đồng xu có đường kính 24mm
                reference_diameter_mm = 24.0
                reference_diameter_px = circles[0][2] * 2
                return reference_diameter_mm / reference_diameter_px

        return None

    def draw_results(self, bgr, labels, results):
        """
        Vẽ kết quả phân loại lên ảnh

        Chức năng: Hiển thị thông tin phân loại và đếm cho người dùng
        (đã chỉnh để tránh chồng chữ; có các chế độ hiển thị)
        """
        vis = bgr.copy()
        mode = getattr(self, "render_mode", "boxes_only")

        draw_boxes = mode in ("full", "minimal", "boxes_only")
        draw_text_per_object = mode == "full"
        draw_global_stats = mode in ("full", "minimal")

        for result in results:
            if result is None:
                continue

            # Lấy thông tin
            x, y, w, h = result["bbox"]
            size = result.get("size", "Unknown")
            ripeness = result.get("ripeness", "Unknown")
            defect = result.get("defect", "OK")

            # Chọn màu khung dựa trên trạng thái
            if defect == "Defective":
                color = (0, 0, 255)  # Đỏ cho hỏng
            elif ripeness == "Ripe":
                color = (0, 255, 0)  # Xanh lá cho chín
            elif ripeness == "Green":
                color = (0, 255, 255)  # Vàng cho xanh
            else:
                color = (255, 0, 0)  # Xanh dương cho trung bình

            if draw_boxes:
                cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)

            if draw_text_per_object and h > 22:
                # Chỉ vẽ text chi tiết khi ở chế độ "full"
                text_lines = [
                    f"ID:{result['id']}",
                    f"Size:{size}",
                    f"Ripeness:{ripeness}",
                    f"Status:{defect}",
                    f"D:{result['d_eq_mm']:.1f}mm"
                ]
                for i, line in enumerate(text_lines):
                    yy = max(0, y - 6 - i * 15)
                    cv2.putText(vis, line, (x, yy),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

        if draw_global_stats:
            # Thống kê tổng quan nhỏ gọn ở góc trái, có nền mờ
            total_count = len([r for r in results if r is not None])
            ripe_count = len([r for r in results if r and r.get("ripeness") == "Ripe"])
            green_count = len([r for r in results if r and r.get("ripeness") == "Green"])
            defective_count = len([r for r in results if r and r.get("defect") == "Defective"])
            stats_text = [
                f"Total: {total_count}",
                f"Ripe: {ripe_count}",
                f"Green: {green_count}",
                f"Defective: {defective_count}"
            ]

            overlay = vis.copy()
            # hộp nền mờ
            cv2.rectangle(overlay, (8, 8), (8 + 210, 8 + 24 * (len(stats_text) + 1)), (0, 0, 0), -1)
            vis = cv2.addWeighted(overlay, 0.35, vis, 0.65, 0)

            for i, line in enumerate(stats_text):
                cv2.putText(vis, line, (18, 34 + i * 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

        return vis

    def process_frame(self, bgr):
        """
        Xử lý một khung hình hoàn chỉnh

        Chức năng: Pipeline chính thực hiện tất cả các bước xử lý
        """
        # 1. Tiền xử lý ảnh
        bgr_corrected = self.color_correction_lab_clahe(bgr)
        denoised = self.denoise(bgr_corrected, method="median", k=3)

        # 2. Phân đoạn
        mask = self.segment_by_color_hsv_lab(denoised)
        mask_clean = self.clean_mask(mask)

        # 3. Tách vật thể dính
        labels, n_objects = self.watershed_separation(mask_clean)

        # 4. Hiệu chuẩn tỷ lệ (chỉ thực hiện một lần)
        if self.scale_state["mm_per_px"] is None:
            mm_per_px = self.calibrate_scale_from_reference(bgr)
            if mm_per_px is not None:
                self.scale_state["mm_per_px"] = mm_per_px

        # 5. Trích xuất đặc trưng và phân loại
        results = []
        for obj_id in range(1, n_objects + 1):
            obj_mask = (labels == obj_id).astype(np.uint8) * 255
            features = self.extract_features(denoised, obj_mask, obj_id)

            if features is not None:
                classification = self.classify_object(features)
                features.update(classification)
                results.append(features)

        # 6. Vẽ kết quả
        vis = self.draw_results(denoised, labels, results)

        return vis, results, mask_clean

    def run_camera(self, camera_id=0):
        """
        Chạy hệ thống với camera thời gian thực

        Chức năng: Xử lý video stream từ camera và hiển thị kết quả
        """
        cap = cv2.VideoCapture(camera_id)

        if not cap.isOpened():
            print("Không thể mở camera!")
            return

        print("Nhấn 's' để lưu kết quả, 'ESC' để thoát")

        frame_count = 0
        start_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Xử lý khung hình
            vis, results, mask = self.process_frame(frame)

            # Tính FPS
            frame_count += 1
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                fps = 30 / elapsed
                print(f"FPS: {fps:.1f}")
                start_time = time.time()

            # Hiển thị
            cv2.imshow("Fruit Classification System", vis)
            cv2.imshow("Segmentation Mask", mask)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('s'):  # Save results
                self.save_results(results)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                cv2.imwrite(f"result_{timestamp}.jpg", vis)
                print(f"Đã lưu kết quả: result_{timestamp}.jpg")

        cap.release()
        cv2.destroyAllWindows()

    def save_results(self, results):
        """Lưu kết quả phân loại ra file CSV"""
        import csv

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"classification_results_{timestamp}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'size', 'ripeness', 'defect', 'd_eq_mm',
                          'area_px', 'circularity', 'defect_ratio']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for result in results:
                if result:
                    writer.writerow({k: result.get(k, '') for k in fieldnames})

        print(f"Đã lưu kết quả vào: {filename}")


# Chạy ứng dụng
if __name__ == "__main__":
    # Khởi tạo hệ thống
    system = FruitClassificationSystem()

    # Chạy với camera (ID 0 là camera mặc định)
    system.run_camera(camera_id=0)

    # Hoặc xử lý ảnh tĩnh:
    # image = cv2.imread("fruit_image.jpg")
    # vis, results, mask = system.process_frame(image)
    # cv2.imshow("Result", vis)
    # cv2.waitKey(0)
