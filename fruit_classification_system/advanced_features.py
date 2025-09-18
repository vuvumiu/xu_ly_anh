# advanced_features.py - Các tính năng nâng cao của hệ thống
import cv2
import numpy as np
from collections import defaultdict
import csv
from datetime import datetime


class AdvancedFeatures:
    def __init__(self):
        """
        Khởi tạo các tính năng nâng cao

        Chức năng: Tracking, thống kê, KNN tự cài đặt
        """
        self.object_tracker = ObjectTracker()
        self.quality_analyzer = QualityAnalyzer()
        self.custom_knn = CustomKNN()
        self.statistics = StatisticsManager()


class ObjectTracker:
    def __init__(self, max_disappeared=10, max_distance=50):
        """
        Theo dõi đối tượng qua các frame

        Chức năng: Gán ID persistent cho các đối tượng, đếm chính xác
        """
        self.next_object_id = 0
        self.objects = {}  # {id: centroid}
        self.disappeared = {}  # {id: số frame biến mất}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid):
        """Đăng ký đối tượng mới"""
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1

    def deregister(self, object_id):
        """Hủy đăng ký đối tượng"""
        del self.objects[object_id]
        del self.disappeared[object_id]

    def update(self, detections):
        """
        Cập nhật tracker với detections mới

        Chức năng: Liên kết detections với các đối tượng đã biết
        """
        if len(detections) == 0:
            # Tăng counter cho các objects bị mất
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return {}

        # Nếu chưa có object nào được track
        if len(self.objects) == 0:
            for detection in detections:
                centroid = self.compute_centroid(detection)
                self.register(centroid)
        else:
            # Tính khoảng cách giữa objects hiện tại và detections
            object_centroids = list(self.objects.values())
            object_ids = list(self.objects.keys())

            detection_centroids = [self.compute_centroid(d) for d in detections]

            # Tính ma trận khoảng cách
            D = self.compute_distance_matrix(object_centroids, detection_centroids)

            # Gán objects tới detections gần nhất
            used_detection_indices = set()
            used_object_ids = set()

            # Sắp xếp theo khoảng cách tăng dần
            rows, cols = D.shape
            for _ in range(min(rows, cols)):
                (min_row, min_col) = np.unravel_index(D.argmin(), D.shape)

                if D[min_row, min_col] > self.max_distance:
                    break

                object_id = object_ids[min_row]
                self.objects[object_id] = detection_centroids[min_col]
                self.disappeared[object_id] = 0

                used_object_ids.add(object_id)
                used_detection_indices.add(min_col)

                # Đặt giá trị lớn để không chọn lại
                D[min_row, :] = np.inf
                D[:, min_col] = np.inf

            # Xử lý objects không được gán
            unused_object_ids = set(object_ids) - used_object_ids
            for object_id in unused_object_ids:
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)

            # Đăng ký detections mới
            unused_detection_indices = set(range(len(detections))) - used_detection_indices
            for i in unused_detection_indices:
                self.register(detection_centroids[i])

        # Trả về mapping {object_id: detection_index}
        result = {}
        for i, detection in enumerate(detections):
            detection_centroid = self.compute_centroid(detection)
            for object_id, object_centroid in self.objects.items():
                if np.linalg.norm(np.array(detection_centroid) - np.array(object_centroid)) < 5:
                    result[object_id] = i
                    break

        return result

    def compute_centroid(self, detection):
        """Tính centroid của detection"""
        if 'bbox' in detection:
            x, y, w, h = detection['bbox']
            return (x + w // 2, y + h // 2)
        return (0, 0)

    def compute_distance_matrix(self, object_centroids, detection_centroids):
        """Tính ma trận khoảng cách Euclidean"""
        D = np.zeros((len(object_centroids), len(detection_centroids)))
        for i, obj_centroid in enumerate(object_centroids):
            for j, det_centroid in enumerate(detection_centroids):
                D[i, j] = np.linalg.norm(np.array(obj_centroid) - np.array(det_centroid))
        return D


class QualityAnalyzer:
    def __init__(self):
        """
        Phân tích chất lượng chi tiết

        Chức năng: Đánh giá độ tươi, bề mặt, hình dạng
        """
        pass

    def analyze_freshness(self, bgr_image, mask):
        """
        Phân tích độ tươi dựa trên màu sắc và texture

        Chức năng: Tính chỉ số tươi từ độ bão hòa và độ đồng nhất
        """
        hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)

        # Tính độ bão hòa trung bình
        saturation = cv2.mean(hsv[:, :, 1], mask)[0]

        # Tính độ đồng nhất texture (GLCM approximation)
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        masked_gray = cv2.bitwise_and(gray, gray, mask=mask)

        # Tính gradient để đánh giá texture
        grad_x = cv2.Sobel(masked_gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(masked_gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

        texture_score = cv2.mean(gradient_magnitude, mask)[0]

        # Chỉ số tươi (0-100)
        freshness_score = min(100, saturation * 0.6 + (255 - texture_score) * 0.4)

        return {
            'freshness_score': freshness_score,
            'saturation': saturation,
            'texture_score': texture_score
        }

    def analyze_surface_defects(self, bgr_image, mask):
        """
        Phân tích chi tiết các khuyết tật bề mặt

        Chức năng: Phát hiện vết nứt, đốm đen, vùng thâm
        """
        lab = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]

        # Tính độ sáng trung bình
        mean_brightness = cv2.mean(l_channel, mask)[0]
        std_brightness = np.std(l_channel[mask > 0])

        # Phát hiện vùng tối bất thường
        dark_threshold = mean_brightness - 2 * std_brightness
        dark_mask = (l_channel < dark_threshold).astype(np.uint8) * 255
        dark_mask = cv2.bitwise_and(dark_mask, mask)

        # Phân tích các vùng tối
        contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        defects = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 10:  # Lọc nhiễu
                # Phân loại khuyết tật
                aspect_ratio = self.get_contour_aspect_ratio(contour)
                circularity = 4 * np.pi * area / (cv2.arcLength(contour, True) ** 2)

                defect_type = "spot"
                if aspect_ratio > 3:
                    defect_type = "crack"
                elif circularity > 0.7:
                    defect_type = "bruise"

                defects.append({
                    'type': defect_type,
                    'area': area,
                    'circularity': circularity,
                    'aspect_ratio': aspect_ratio
                })

        total_defect_area = sum(d['area'] for d in defects)
        total_area = np.sum(mask > 0)
        defect_ratio = total_defect_area / total_area if total_area > 0 else 0

        return {
            'defects': defects,
            'total_defect_ratio': defect_ratio,
            'defect_count': len(defects)
        }

    def get_contour_aspect_ratio(self, contour):
        """Tính tỷ lệ khung hình của contour"""
        x, y, w, h = cv2.boundingRect(contour)
        return w / h if h > 0 else 0


class CustomKNN:
    def __init__(self, k=5):
        """
        KNN classifier tự cài đặt (không dùng sklearn)

        Chức năng: Phân loại dựa trên k láng giềng gần nhất
        """
        self.k = k
        self.X_train = None
        self.y_train = None
        self.feature_names = []

    def fit(self, X, y, feature_names=None):
        """
        Huấn luyện mô hình

        X: ma trận đặc trưng (n_samples x n_features)
        y: nhãn (n_samples,)
        """
        self.X_train = np.array(X)
        self.y_train = np.array(y)
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]

    def predict(self, X):
        """
        Dự đoán cho dữ liệu mới

        Chức năng: Tìm k láng giềng gần nhất và voting
        """
        X = np.array(X)
        predictions = []

        for sample in X:
            # Tính khoảng cách tới tất cả training samples
            distances = np.sqrt(np.sum((self.X_train - sample) ** 2, axis=1))

            # Tìm k láng giềng gần nhất
            k_nearest_indices = np.argsort(distances)[:self.k]
            k_nearest_labels = self.y_train[k_nearest_indices]

            # Voting
            unique_labels, counts = np.unique(k_nearest_labels, return_counts=True)
            predicted_label = unique_labels[np.argmax(counts)]
            predictions.append(predicted_label)

        return np.array(predictions)

    def predict_proba(self, X):
        """
        Dự đoán xác suất cho các lớp

        Chức năng: Trả về phân phối xác suất dựa trên voting của k neighbors
        """
        X = np.array(X)
        probabilities = []

        # Lấy tất cả các lớp unique
        unique_classes = np.unique(self.y_train)

        for sample in X:
            distances = np.sqrt(np.sum((self.X_train - sample) ** 2, axis=1))
            k_nearest_indices = np.argsort(distances)[:self.k]
            k_nearest_labels = self.y_train[k_nearest_indices]

            # Tính xác suất cho mỗi lớp
            class_probs = []
            for cls in unique_classes:
                prob = np.sum(k_nearest_labels == cls) / self.k
                class_probs.append(prob)

            probabilities.append(class_probs)

        return np.array(probabilities)

    def score(self, X, y):
        """Tính accuracy trên tập test"""
        predictions = self.predict(X)
        return np.mean(predictions == y)


class StatisticsManager:
    def __init__(self):
        """
        Quản lý thống kê và báo cáo

        Chức năng: Thu thập, phân tích và xuất báo cáo
        """
        self.daily_stats = defaultdict(lambda: defaultdict(int))
        self.session_data = []
        self.quality_trends = []

    def update_stats(self, results, timestamp=None):
        """
        Cập nhật thống kê từ kết quả phân loại

        Chức năng: Ghi nhận số lượng theo từng loại
        """
        if timestamp is None:
            timestamp = datetime.now()

        date_key = timestamp.strftime("%Y-%m-%d")

        for result in results:
            if result is None:
                continue

            # Thống kê theo kích thước
            size = result.get('size', 'Unknown')
            self.daily_stats[date_key][f'size_{size}'] += 1

            # Thống kê theo độ chín
            ripeness = result.get('ripeness', 'Unknown')
            self.daily_stats[date_key][f'ripeness_{ripeness}'] += 1

            # Thống kê khuyết tật
            defect = result.get('defect', 'OK')
            self.daily_stats[date_key][f'defect_{defect}'] += 1

            # Lưu dữ liệu chi tiết
            self.session_data.append({
                'timestamp': timestamp,
                'size': size,
                'ripeness': ripeness,
                'defect': defect,
                'diameter_mm': result.get('d_eq_mm', 0),
                'defect_ratio': result.get('defect_ratio', 0)
            })

    def generate_daily_report(self, date=None):
        """
        Tạo báo cáo hàng ngày

        Chức năng: Tổng hợp thống kê theo ngày
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if date not in self.daily_stats:
            return "Không có dữ liệu cho ngày này"

        stats = self.daily_stats[date]

        report = f"=== BÁO CÁO NGÀY {date} ===\n\n"

        # Tổng quan
        total = sum(v for k, v in stats.items() if k.startswith('size_'))
        report += f"Tổng số sản phẩm: {total}\n\n"

        # Thống kê kích thước
        report += "PHÂN LOẠI KÍCH THƯỚC:\n"
        for size in ['S', 'M', 'L', 'XL']:
            count = stats.get(f'size_{size}', 0)
            percent = (count / total * 100) if total > 0 else 0
            report += f"  {size}: {count} ({percent:.1f}%)\n"

        # Thống kê độ chín
        report += "\nPHÂN LOẠI ĐỘ CHÍN:\n"
        for ripeness in ['Green', 'Medium', 'Ripe']:
            count = stats.get(f'ripeness_{ripeness}', 0)
            percent = (count / total * 100) if total > 0 else 0
            report += f"  {ripeness}: {count} ({percent:.1f}%)\n"

        # Thống kê chất lượng
        report += "\nCHẤT LƯỢNG:\n"
        ok_count = stats.get('defect_OK', 0)
        defective_count = stats.get('defect_Defective', 0)
        ok_percent = (ok_count / total * 100) if total > 0 else 0
        defect_percent = (defective_count / total * 100) if total > 0 else 0

        report += f"  Tốt: {ok_count} ({ok_percent:.1f}%)\n"
        report += f"  Khuyết tật: {defective_count} ({defect_percent:.1f}%)\n"

        return report

    def export_to_csv(self, filename=None):
        """
        Xuất dữ liệu ra file CSV

        Chức năng: Lưu trữ dữ liệu chi tiết để phân tích
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fruit_classification_data_{timestamp}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'size', 'ripeness', 'defect',
                          'diameter_mm', 'defect_ratio']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for data in self.session_data:
                writer.writerow(data)

        print(f"Đã xuất dữ liệu ra: {filename}")
        return filename

    def analyze_quality_trends(self, days=7):
        """
        Phân tích xu hướng chất lượng

        Chức năng: Theo dõi thay đổi chất lượng theo thời gian
        """
        if len(self.session_data) < 10:
            return "Không đủ dữ liệu để phân tích xu hướng"

        # Nhóm dữ liệu theo ngày
        daily_quality = defaultdict(list)
        for data in self.session_data:
            date_key = data['timestamp'].strftime("%Y-%m-%d")
            daily_quality[date_key].append(data['defect_ratio'])

        # Tính trung bình defect ratio theo ngày
        trends = []
        for date in sorted(daily_quality.keys())[-days:]:
            avg_defect = np.mean(daily_quality[date])
            trends.append({'date': date, 'avg_defect_ratio': avg_defect})

        # Phân tích xu hướng
        if len(trends) >= 3:
            recent_trend = np.mean([t['avg_defect_ratio'] for t in trends[-3:]])
            earlier_trend = np.mean([t['avg_defect_ratio'] for t in trends[:-3]])

            if recent_trend > earlier_trend * 1.1:
                trend_direction = "xấu đi"
            elif recent_trend < earlier_trend * 0.9:
                trend_direction = "cải thiện"
            else:
                trend_direction = "ổn định"
        else:
            trend_direction = "chưa đủ dữ liệu"

        return {
            'trends': trends,
            'direction': trend_direction,
            'current_avg': trends[-1]['avg_defect_ratio'] if trends else 0
        }


class ConveyorBeltHandler:
    def __init__(self, belt_speed_px_per_frame=10):
        """
        Xử lý băng tải di chuyển

        Chức năng: Theo dõi đối tượng trên băng tải, tránh đếm trùng
        """
        self.belt_speed = belt_speed_px_per_frame
        self.processing_zones = {
            'entry': (0, 200),  # Vùng vào
            'analysis': (200, 600),  # Vùng phân tích chính
            'exit': (600, 800)  # Vùng ra
        }
        self.counted_objects = set()  # IDs đã được đếm

    def is_in_analysis_zone(self, bbox):
        """
        Kiểm tra đối tượng có trong vùng phân tích không

        Chức năng: Chỉ phân loại khi đối tượng ở vùng tối ưu
        """
        x, y, w, h = bbox
        center_x = x + w // 2

        analysis_start, analysis_end = self.processing_zones['analysis']
        return analysis_start <= center_x <= analysis_end

    def should_count_object(self, object_id, bbox):
        """
        Quyết định có nên đếm đối tượng này không

        Chức năng: Tránh đếm trùng khi đối tượng di chuyển qua khung hình
        """
        if object_id in self.counted_objects:
            return False

        # Chỉ đếm khi đối tượng ở giữa vùng phân tích
        if self.is_in_analysis_zone(bbox):
            self.counted_objects.add(object_id)
            return True

        return False

    def reset_counting(self):
        """Reset bộ đếm cho session mới"""
        self.counted_objects.clear()


class BatchProcessor:
    def __init__(self, system):
        """
        Xử lý hàng loạt ảnh/video

        Chức năng: Xử lý nhiều file cùng lúc, xuất báo cáo tổng hợp
        """
        self.system = system
        self.batch_results = []

    def process_image_batch(self, image_paths, output_dir="batch_results"):
        """
        Xử lý hàng loạt ảnh

        Chức năng: Phân loại nhiều ảnh và tạo báo cáo
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        batch_stats = defaultdict(int)

        for i, image_path in enumerate(image_paths):
            print(f"Đang xử lý {i + 1}/{len(image_paths)}: {image_path}")

            image = cv2.imread(image_path)
            if image is None:
                print(f"Không thể đọc ảnh: {image_path}")
                continue

            # Xử lý ảnh
            vis, results, mask = self.system.process_frame(image)

            # Lưu kết quả
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_result.jpg")
            cv2.imwrite(output_path, vis)

            # Cập nhật thống kê
            for result in results:
                if result:
                    batch_stats[f"size_{result.get('size', 'Unknown')}"] += 1
                    batch_stats[f"ripeness_{result.get('ripeness', 'Unknown')}"] += 1
                    batch_stats[f"defect_{result.get('defect', 'OK')}"] += 1

            self.batch_results.extend(results)

        # Tạo báo cáo
        self.generate_batch_report(batch_stats, output_dir)
        return batch_stats

    def generate_batch_report(self, stats, output_dir):
        """Tạo báo cáo cho batch processing"""
        total = sum(v for k, v in stats.items() if k.startswith('size_'))

        report = "=== BÁO CÁO XỬ LÝ HÀNG LOẠT ===\n\n"
        report += f"Tổng số sản phẩm: {total}\n\n"

        # Chi tiết thống kê
        for category in ['size', 'ripeness', 'defect']:
            report += f"\n{category.upper()}:\n"
            category_items = [k for k in stats.keys() if k.startswith(f'{category}_')]
            for item in category_items:
                count = stats[item]
                percent = (count / total * 100) if total > 0 else 0
                label = item.split('_')[1]
                report += f"  {label}: {count} ({percent:.1f}%)\n"

        # Lưu báo cáo
        report_path = os.path.join(output_dir, "batch_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"Đã tạo báo cáo: {report_path}")


# Ví dụ sử dụng các tính năng nâng cao
def demo_advanced_features():
    """
    Demo các tính năng nâng cao

    Chức năng: Hướng dẫn sử dụng tracking, KNN, thống kê
    """

    # 1. Object Tracking
    print("=== DEMO OBJECT TRACKING ===")
    tracker = ObjectTracker()

    # Giả lập detections qua các frame
    frame_detections = [
        [{'bbox': (100, 100, 50, 50)}, {'bbox': (200, 150, 45, 45)}],
        [{'bbox': (110, 105, 50, 50)}, {'bbox': (210, 155, 45, 45)}],
        [{'bbox': (120, 110, 50, 50)}, {'bbox': (220, 160, 45, 45)}]
    ]

    for frame_idx, detections in enumerate(frame_detections):
        object_map = tracker.update(detections)
        print(f"Frame {frame_idx}: {len(tracker.objects)} objects tracked")
        print(f"Mapping: {object_map}")

    # 2. Custom KNN
    print("\n=== DEMO CUSTOM KNN ===")
    knn = CustomKNN(k=3)

    # Dữ liệu huấn luyện mẫu (features: [diameter, red_ratio, defect_ratio])
    X_train = [
        [45, 0.1, 0.02],  # Green S
        [50, 0.15, 0.03],  # Green S
        [60, 0.8, 0.01],  # Ripe M
        [65, 0.9, 0.02],  # Ripe M
        [70, 0.85, 0.1],  # Ripe L with defect
    ]
    y_train = ['Green_S', 'Green_S', 'Ripe_M', 'Ripe_M', 'Defective_L']

    knn.fit(X_train, y_train)

    # Test
    X_test = [[55, 0.7, 0.02], [48, 0.12, 0.01]]
    predictions = knn.predict(X_test)
    probabilities = knn.predict_proba(X_test)

    print(f"Predictions: {predictions}")
    print(f"Probabilities: {probabilities}")

    # 3. Statistics Manager
    print("\n=== DEMO STATISTICS ===")
    stats_manager = StatisticsManager()

    # Giả lập kết quả
    sample_results = [
        {'size': 'M', 'ripeness': 'Ripe', 'defect': 'OK', 'd_eq_mm': 62, 'defect_ratio': 0.02},
        {'size': 'L', 'ripeness': 'Green', 'defect': 'OK', 'd_eq_mm': 68, 'defect_ratio': 0.01},
        {'size': 'S', 'ripeness': 'Ripe', 'defect': 'Defective', 'd_eq_mm': 45, 'defect_ratio': 0.08}
    ]

    stats_manager.update_stats(sample_results)
    report = stats_manager.generate_daily_report()
    print(report)


if __name__ == "__main__":
    demo_advanced_features()