# calibration_tool.py - Công cụ hiệu chuẩn tham số HSV và LAB
import cv2
import numpy as np
import json


class CalibrationTool:
    def __init__(self):
        """
        Khởi tạo công cụ hiệu chuẩn

        Chức năng: Tạo giao diện trackbar để điều chỉnh ngưỡng màu sắc
        """
        self.current_image = None
        self.hsv_image = None
        self.lab_image = None
        self.window_name = "HSV LAB Calibration Tool"

        # Khởi tạo các giá trị mặc định
        self.hsv_values = {
            'H_min': 0, 'H_max': 180,
            'S_min': 0, 'S_max': 255,
            'V_min': 0, 'V_max': 255
        }

        self.lab_values = {
            'L_min': 0, 'L_max': 255,
            'A_min': 0, 'A_max': 255,
            'B_min': 0, 'B_max': 255
        }

    def create_trackbars(self):
        """
        Tạo các thanh trượt để điều chỉnh ngưỡng

        Chức năng: Giao diện người dùng để tinh chỉnh tham số thời gian thực
        """
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

        # Trackbars cho HSV
        cv2.createTrackbar('H_min', self.window_name, 0, 180, self.on_trackbar)
        cv2.createTrackbar('H_max', self.window_name, 180, 180, self.on_trackbar)
        cv2.createTrackbar('S_min', self.window_name, 0, 255, self.on_trackbar)
        cv2.createTrackbar('S_max', self.window_name, 255, 255, self.on_trackbar)
        cv2.createTrackbar('V_min', self.window_name, 0, 255, self.on_trackbar)
        cv2.createTrackbar('V_max', self.window_name, 255, 255, self.on_trackbar)

        # Trackbars cho LAB
        cv2.createTrackbar('A_min', self.window_name, 0, 255, self.on_trackbar)
        cv2.createTrackbar('A_max', self.window_name, 255, 255, self.on_trackbar)

        # Trackbars cho morphology
        cv2.createTrackbar('Open_kernel', self.window_name, 3, 15, self.on_trackbar)
        cv2.createTrackbar('Close_kernel', self.window_name, 5, 15, self.on_trackbar)
        cv2.createTrackbar('Min_area', self.window_name, 200, 2000, self.on_trackbar)

    def on_trackbar(self, val):
        """
        Callback khi trackbar thay đổi

        Chức năng: Cập nhật mask và hiển thị kết quả ngay lập tức
        """
        if self.current_image is None:
            return

        # Lấy giá trị từ trackbars
        self.hsv_values['H_min'] = cv2.getTrackbarPos('H_min', self.window_name)
        self.hsv_values['H_max'] = cv2.getTrackbarPos('H_max', self.window_name)
        self.hsv_values['S_min'] = cv2.getTrackbarPos('S_min', self.window_name)
        self.hsv_values['S_max'] = cv2.getTrackbarPos('S_max', self.window_name)
        self.hsv_values['V_min'] = cv2.getTrackbarPos('V_min', self.window_name)
        self.hsv_values['V_max'] = cv2.getTrackbarPos('V_max', self.window_name)

        self.lab_values['A_min'] = cv2.getTrackbarPos('A_min', self.window_name)
        self.lab_values['A_max'] = cv2.getTrackbarPos('A_max', self.window_name)

        open_k = cv2.getTrackbarPos('Open_kernel', self.window_name)
        close_k = cv2.getTrackbarPos('Close_kernel', self.window_name)
        min_area = cv2.getTrackbarPos('Min_area', self.window_name)

        # Tạo mask
        mask = self.create_mask(open_k, close_k, min_area)

        # Hiển thị kết quả
        self.display_results(mask)

    def create_mask(self, open_k, close_k, min_area):
        """
        Tạo mask dựa trên các ngưỡng hiện tại

        Chức năng: Áp dụng ngưỡng HSV và LAB để tạo mask
        """
        # Tạo mask HSV
        lower_hsv = np.array([self.hsv_values['H_min'],
                              self.hsv_values['S_min'],
                              self.hsv_values['V_min']])
        upper_hsv = np.array([self.hsv_values['H_max'],
                              self.hsv_values['S_max'],
                              self.hsv_values['V_max']])

        hsv_mask = cv2.inRange(self.hsv_image, lower_hsv, upper_hsv)

        # Tạo mask LAB (chỉ kênh a*)
        a_channel = self.lab_image[:, :, 1]
        lab_mask = cv2.inRange(a_channel, self.lab_values['A_min'], self.lab_values['A_max'])

        # Kết hợp masks
        combined_mask = cv2.bitwise_and(hsv_mask, lab_mask)

        # Áp dụng morphology
        if open_k > 0:
            open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_k, open_k))
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, open_kernel)

        if close_k > 0:
            close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k))
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, close_kernel)

        # Loại bỏ vùng nhỏ
        if min_area > 0:
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < min_area:
                    cv2.fillPoly(combined_mask, [contour], 0)

        return combined_mask

    def display_results(self, mask):
        """
        Hiển thị kết quả calibration

        Chức năng: Ghép ảnh gốc, mask và kết quả để so sánh
        """
        # Tạo ảnh kết quả
        result = cv2.bitwise_and(self.current_image, self.current_image, mask=mask)

        # Chuyển mask thành 3 kênh để ghép
        mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        # Ghép các ảnh
        h, w = self.current_image.shape[:2]

        # Resize để fit trong cửa sổ
        scale = min(400 / w, 300 / h)
        new_w, new_h = int(w * scale), int(h * scale)

        original_resized = cv2.resize(self.current_image, (new_w, new_h))
        mask_resized = cv2.resize(mask_colored, (new_w, new_h))
        result_resized = cv2.resize(result, (new_w, new_h))

        # Ghép 3 ảnh thành 1 hàng
        display = np.hstack([original_resized, mask_resized, result_resized])

        # Thêm text label
        cv2.putText(display, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display, "Mask", (new_w + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display, "Result", (new_w * 2 + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Hiển thị thông số hiện tại
        params_text = [
            f"HSV: H({self.hsv_values['H_min']}-{self.hsv_values['H_max']}) "
            f"S({self.hsv_values['S_min']}-{self.hsv_values['S_max']}) "
            f"V({self.hsv_values['V_min']}-{self.hsv_values['V_max']})",
            f"LAB: A({self.lab_values['A_min']}-{self.lab_values['A_max']})",
        ]

        for i, text in enumerate(params_text):
            cv2.putText(display, text, (10, new_h + 30 + i * 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        cv2.imshow(self.window_name, display)

    def load_image(self, image_path):
        """
        Tải ảnh để calibration

        Chức năng: Đọc ảnh và chuyển đổi không gian màu
        """
        self.current_image = cv2.imread(image_path)
        if self.current_image is None:
            print(f"Không thể tải ảnh: {image_path}")
            return False

        # Chuyển đổi không gian màu
        self.hsv_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2HSV)
        self.lab_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2LAB)

        return True

    def set_preset_values(self, color_type):
        """
        Thiết lập giá trị preset cho các loại màu

        Chức năng: Nhanh chóng áp dụng ngưỡng cho màu đỏ, xanh, vàng
        """
        presets = {
            'red': {
                'H_min': 0, 'H_max': 10, 'S_min': 80, 'S_max': 255, 'V_min': 70, 'V_max': 255,
                'A_min': 135, 'A_max': 255
            },
            'green': {
                'H_min': 35, 'H_max': 85, 'S_min': 60, 'S_max': 255, 'V_min': 60, 'V_max': 255,
                'A_min': 0, 'A_max': 120
            },
            'yellow': {
                'H_min': 15, 'H_max': 35, 'S_min': 50, 'S_max': 255, 'V_min': 50, 'V_max': 255,
                'A_min': 120, 'A_max': 140
            }
        }

        if color_type in presets:
            preset = presets[color_type]

            # Cập nhật trackbars
            cv2.setTrackbarPos('H_min', self.window_name, preset['H_min'])
            cv2.setTrackbarPos('H_max', self.window_name, preset['H_max'])
            cv2.setTrackbarPos('S_min', self.window_name, preset['S_min'])
            cv2.setTrackbarPos('S_max', self.window_name, preset['S_max'])
            cv2.setTrackbarPos('V_min', self.window_name, preset['V_min'])
            cv2.setTrackbarPos('V_max', self.window_name, preset['V_max'])
            cv2.setTrackbarPos('A_min', self.window_name, preset['A_min'])
            cv2.setTrackbarPos('A_max', self.window_name, preset['A_max'])

            print(f"Đã áp dụng preset cho màu: {color_type}")

    def save_config(self, filename="calibrated_config.json"):
        """
        Lưu cấu hình đã hiệu chuẩn

        Chức năng: Xuất các tham số đã tinh chỉnh ra file JSON
        """
        config = {
            "hsv_ranges": {
                "calibrated": [{
                    "H": [self.hsv_values['H_min'], self.hsv_values['H_max']],
                    "S": [self.hsv_values['S_min'], self.hsv_values['S_max']],
                    "V": [self.hsv_values['V_min'], self.hsv_values['V_max']]
                }]
            },
            "lab_thresholds": {
                "a_star_min": self.lab_values['A_min'],
                "a_star_max": self.lab_values['A_max']
            },
            "morphology": {
                "open_kernel": cv2.getTrackbarPos('Open_kernel', self.window_name),
                "close_kernel": cv2.getTrackbarPos('Close_kernel', self.window_name),
                "min_area": cv2.getTrackbarPos('Min_area', self.window_name)
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"Đã lưu cấu hình vào: {filename}")

    def run_calibration(self, image_path):
        """
        Chạy quá trình hiệu chuẩn

        Chức năng: Giao diện chính cho việc hiệu chuẩn tham số
        """
        if not self.load_image(image_path):
            return

        self.create_trackbars()
        self.on_trackbar(0)  # Khởi tạo hiển thị

        print("Hướng dẫn sử dụng:")
        print("- Điều chỉnh các thanh trượt để tối ưu mask")
        print("- Nhấn 'r' cho preset màu đỏ")
        print("- Nhấn 'g' cho preset màu xanh")
        print("- Nhấn 'y' cho preset màu vàng")
        print("- Nhấn 's' để lưu cấu hình")
        print("- Nhấn 'ESC' để thoát")

        while True:
            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                break
            elif key == ord('r'):  # Red preset
                self.set_preset_values('red')
            elif key == ord('g'):  # Green preset
                self.set_preset_values('green')
            elif key == ord('y'):  # Yellow preset
                self.set_preset_values('yellow')
            elif key == ord('s'):  # Save config
                self.save_config()

        cv2.destroyAllWindows()


# Chương trình chính
def main():
    import sys

    if len(sys.argv) != 2:
        print("Sử dụng: python calibration_tool.py <đường_dẫn_ảnh>")
        print("Ví dụ: python calibration_tool.py tomato_sample.jpg")
        return

    calibrator = CalibrationTool()
    calibrator.run_calibration(sys.argv[1])


if __name__ == "__main__":
    main()