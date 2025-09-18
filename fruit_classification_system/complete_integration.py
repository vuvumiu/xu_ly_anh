# complete_integration.py - Tích hợp đầy đủ tất cả các tính năng
import cv2
import numpy as np
import json
import argparse
from datetime import datetime
import os

# Import các modules đã tạo
from main import FruitClassificationSystem
from advanced_features import AdvancedFeatures, ObjectTracker, StatisticsManager, ConveyorBeltHandler


class CompleteIntegratedSystem:
    def __init__(self, config_file="config.json"):
        """
        Hệ thống tích hợp hoàn chỉnh

        Chức năng: Kết hợp tất cả các tính năng trong một hệ thống thống nhất
        """
        # Khởi tạo các thành phần chính
        self.classification_system = FruitClassificationSystem(config_file)
        self.object_tracker = ObjectTracker(max_disappeared=15, max_distance=80)
        self.statistics_manager = StatisticsManager()
        self.conveyor_handler = ConveyorBeltHandler(belt_speed_px_per_frame=12)

        # Cấu hình mode hoạt động
        self.mode = "camera"  # "camera", "batch", "conveyor"
        self.output_dir = "results"
        self.enable_tracking = True
        self.enable_quality_analysis = True

        # Tạo thư mục output
        os.makedirs(self.output_dir, exist_ok=True)

        print("Đã khởi tạo hệ thống tích hợp hoàn chỉnh")

    def run_camera_mode(self, camera_id=0, enable_recording=False):
        """
        Chế độ camera thời gian thực với đầy đủ tính năng

        Chức năng: Xử lý video stream với tracking, thống kê, ghi hình
        """
        print("=== CHẠY CHE ĐỘ CAMERA THỜI GIAN THỰC ===")

        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print("Không thể mở camera!")
            return

        # Thiết lập camera
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)

        # Khởi tạo ghi video nếu cần
        video_writer = None
        if enable_recording:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_path = os.path.join(self.output_dir, f"recording_{timestamp}.avi")
            video_writer = cv2.VideoWriter(video_path, fourcc, 30.0, (1280, 720))
            print(f"Đang ghi video: {video_path}")

        frame_count = 0
        fps_counter = 0
        fps_timer = cv2.getTickCount()

        print("Điều khiển:")
        print("- SPACE: Chụp ảnh và lưu kết quả")
        print("- 'r': Bắt đầu/dừng ghi video")
        print("- 's': Xuất báo cáo thống kê")
        print("- 'c': Reset bộ đếm")
        print("- ESC: Thoát")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                # Xử lý frame
                processed_frame, current_results = self.process_single_frame(
                    frame, frame_count, enable_tracking=self.enable_tracking
                )

                # Tính FPS
                fps_counter += 1
                if fps_counter >= 30:
                    current_time = cv2.getTickCount()
                    fps = 30.0 / ((current_time - fps_timer) / cv2.getTickFrequency())
                    fps_timer = current_time
                    fps_counter = 0

                    # Hiển thị FPS trên frame
                    cv2.putText(processed_frame, f"FPS: {fps:.1f}",
                                (processed_frame.shape[1] - 150, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Ghi video nếu đang recording
                if video_writer is not None:
                    video_writer.write(processed_frame)
                    cv2.circle(processed_frame, (50, 50), 10, (0, 0, 255), -1)  # Đèn đỏ ghi hình

                # Hiển thị
                cv2.imshow("Hệ thống phân loại tích hợp", processed_frame)

                # Xử lý phím nhấn
                key = cv2.waitKey(1) & 0xFF

                if key == 27:  # ESC - Thoát
                    break
                elif key == ord(' '):  # SPACE - Chụp ảnh
                    self.save_frame_result(frame, processed_frame, current_results)
                elif key == ord('r'):  # R - Toggle recording
                    if video_writer is None and enable_recording:
                        # Bắt đầu ghi
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        video_path = os.path.join(self.output_dir, f"recording_{timestamp}.avi")
                        video_writer = cv2.VideoWriter(video_path, fourcc, 30.0, (1280, 720))
                        print(f"Bắt đầu ghi: {video_path}")
                    elif video_writer is not None:
                        # Dừng ghi
                        video_writer.release()
                        video_writer = None
                        print("Đã dừng ghi video")
                elif key == ord('s'):  # S - Xuất thống kê
                    self.export_statistics()
                elif key == ord('c'):  # C - Reset counter
                    self.reset_counters()
                    print("Đã reset bộ đếm")

        except KeyboardInterrupt:
            print("Người dùng dừng chương trình")

        finally:
            # Cleanup
            cap.release()
            if video_writer is not None:
                video_writer.release()
            cv2.destroyAllWindows()

            # Xuất báo cáo cuối session
            self.export_final_report()

    def process_single_frame(self, frame, frame_number, enable_tracking=True):
        """
        Xử lý một frame với đầy đủ tính năng

        Chức năng: Pipeline xử lý frame tích hợp tracking và phân tích
        """
        # 1. Phân loại cơ bản
        vis, results, mask = self.classification_system.process_frame(frame)

        # 2. Object tracking (nếu bật)
        tracked_results = results
        if enable_tracking and results:
            object_mapping = self.object_tracker.update(results)

            # Cập nhật ID tracking cho results
            for result in tracked_results:
                if result:
                    # Tìm tracked ID tương ứng
                    for tracked_id, detection_idx in object_mapping.items():
                        if detection_idx < len(results) and results[detection_idx] == result:
                            result['tracked_id'] = tracked_id
                            break

                    # Kiểm tra xem có nên đếm object này không (cho conveyor belt)
                    if self.mode == "conveyor":
                        tracked_id = result.get('tracked_id')
                        if tracked_id and self.conveyor_handler.should_count_object(tracked_id, result['bbox']):
                            result['should_count'] = True

        # 3. Cập nhật thống kê
        valid_results = [r for r in tracked_results if r is not None]
        if valid_results:
            self.statistics_manager.update_stats(valid_results)

        # 4. Vẽ thông tin bổ sung lên frame
        enhanced_vis = self.enhance_visualization(vis, tracked_results, frame_number)

        return enhanced_vis, valid_results

    def enhance_visualization(self, vis, results, frame_number):
        """
        Cải thiện hiển thị với thông tin bổ sung

        Chức năng: Thêm tracking ID, thống kê realtime, trạng thái hệ thống
        """
        enhanced = vis.copy()

        # Vẽ tracking information
        for result in results:
            if result and 'tracked_id' in result:
                x, y, w, h = result['bbox']
                tracked_id = result['tracked_id']

                # Vẽ tracking ID
                cv2.putText(enhanced, f"ID:{tracked_id}", (x, y - 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                # Đánh dấu nếu được đếm (conveyor mode)
                if result.get('should_count', False):
                    cv2.rectangle(enhanced, (x - 2, y - 2), (x + w + 2, y + h + 2), (0, 255, 255), 3)

        # Panel thông tin hệ thống
        info_panel = self.create_info_panel(frame_number)

        # Ghép info panel vào góc phải
        panel_h, panel_w = info_panel.shape[:2]
        vis_h, vis_w = enhanced.shape[:2]

        if vis_w >= panel_w and vis_h >= panel_h:
            # Tạo vùng semi-transparent
            overlay = enhanced.copy()
            cv2.rectangle(overlay, (vis_w - panel_w, 0), (vis_w, panel_h), (0, 0, 0), -1)
            enhanced = cv2.addWeighted(enhanced, 0.7, overlay, 0.3, 0)

            # Đặt info panel
            enhanced[0:panel_h, vis_w - panel_w:vis_w] = info_panel

        return enhanced

    def create_info_panel(self, frame_number):
        """
        Tạo panel thông tin hệ thống

        Chức năng: Hiển thị thống kê realtime và trạng thái
        """
        panel_width, panel_height = 250, 200
        panel = np.zeros((panel_height, panel_width, 3), dtype=np.uint8)

        # Lấy thống kê hiện tại
        today = datetime.now().strftime("%Y-%m-%d")
        stats = self.statistics_manager.daily_stats.get(today, {})

        # Tính tổng số
        total_processed = sum(v for k, v in stats.items() if k.startswith('size_'))
        ripe_count = stats.get('ripeness_Ripe', 0)
        defective_count = stats.get('defect_Defective', 0)

        # Vẽ thông tin
        info_lines = [
            f"Frame: {frame_number}",
            f"Mode: {self.mode}",
            f"Total: {total_processed}",
            f"Ripe: {ripe_count}",
            f"Defects: {defective_count}",
            f"Quality: {((total_processed - defective_count) / max(1, total_processed) * 100):.1f}%",
            f"Tracking: {'ON' if self.enable_tracking else 'OFF'}",
            "",
            "Controls:",
            "SPACE: Save",
            "S: Stats",
            "ESC: Exit"
        ]

        for i, line in enumerate(info_lines):
            color = (255, 255, 255)
            if line.startswith("Quality:"):
                # Màu theo chất lượng
                quality = ((total_processed - defective_count) / max(1, total_processed) * 100)
                if quality >= 90:
                    color = (0, 255, 0)  # Xanh lá - tốt
                elif quality >= 75:
                    color = (0, 255, 255)  # Vàng - trung bình
                else:
                    color = (0, 0, 255)  # Đỏ - kém
            elif line.startswith("Tracking:"):
                color = (0, 255, 0) if self.enable_tracking else (128, 128, 128)

            cv2.putText(panel, line, (10, 20 + i * 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        return panel

    def save_frame_result(self, original_frame, processed_frame, results):
        """
        Lưu kết quả frame hiện tại

        Chức năng: Chụp ảnh và lưu thông tin chi tiết
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

        # Lưu ảnh
        original_path = os.path.join(self.output_dir, f"original_{timestamp}.jpg")
        result_path = os.path.join(self.output_dir, f"result_{timestamp}.jpg")

        cv2.imwrite(original_path, original_frame)
        cv2.imwrite(result_path, processed_frame)

        # Lưu dữ liệu JSON
        data_path = os.path.join(self.output_dir, f"data_{timestamp}.json")
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'results': results,
                'total_objects': len([r for r in results if r is not None]),
                'frame_info': {
                    'original_image': original_path,
                    'processed_image': result_path
                }
            }, f, indent=2, ensure_ascii=False, default=str)

        print(f"Đã lưu kết quả: {timestamp}")
        return timestamp

    def run_batch_mode(self, input_dir, file_pattern="*.jpg"):
        """
        Chế độ xử lý hàng loạt

        Chức năng: Xử lý nhiều ảnh cùng lúc và tạo báo cáo tổng hợp
        """
        import glob

        print("=== CHẠY CHE ĐỘ XỬ LÝ HÀNG LOẠT ===")

        # Tìm tất cả files
        search_pattern = os.path.join(input_dir, file_pattern)
        image_files = glob.glob(search_pattern)

        if not image_files:
            print(f"Không tìm thấy ảnh nào trong: {search_pattern}")
            return

        print(f"Tìm thấy {len(image_files)} ảnh để xử lý")

        # Tạo thư mục output cho batch
        batch_output = os.path.join(self.output_dir, f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(batch_output, exist_ok=True)

        batch_results = []
        processed_count = 0

        for i, image_path in enumerate(image_files):
            print(f"Xử lý {i + 1}/{len(image_files)}: {os.path.basename(image_path)}")

            # Đọc ảnh
            image = cv2.imread(image_path)
            if image is None:
                print(f"  Không thể đọc ảnh: {image_path}")
                continue

            try:
                # Xử lý ảnh
                vis, results, mask = self.classification_system.process_frame(image)

                # Lưu kết quả
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                result_path = os.path.join(batch_output, f"{base_name}_result.jpg")
                mask_path = os.path.join(batch_output, f"{base_name}_mask.jpg")

                cv2.imwrite(result_path, vis)
                cv2.imwrite(mask_path, mask)

                # Thu thập kết quả
                valid_results = [r for r in results if r is not None]
                batch_results.extend(valid_results)

                # Cập nhật thống kê
                if valid_results:
                    self.statistics_manager.update_stats(valid_results)

                processed_count += 1
                print(f"  Tìm thấy {len(valid_results)} đối tượng")

            except Exception as e:
                print(f"  Lỗi xử lý {image_path}: {e}")
                continue

        # Tạo báo cáo batch
        self.create_batch_report(batch_results, batch_output, processed_count)

        print(f"Hoàn thành! Xử lý {processed_count}/{len(image_files)} ảnh")
        print(f"Kết quả lưu trong: {batch_output}")

    def create_batch_report(self, results, output_dir, image_count):
        """
        Tạo báo cáo chi tiết cho batch processing

        Chức năng: Phân tích tổng thể và tạo biểu đồ
        """
        from collections import Counter

        # Thống kê cơ bản
        total_objects = len(results)

        size_counts = Counter(r.get('size', 'Unknown') for r in results)
        ripeness_counts = Counter(r.get('ripeness', 'Unknown') for r in results)
        defect_counts = Counter(r.get('defect', 'Unknown') for r in results)

        # Tạo báo cáo text
        report = f"""
=== BÁO CÁO XỬ LÝ HÀNG LOẠT ===
Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

TỔNG QUAN:
- Số ảnh xử lý: {image_count}
- Tổng số đối tượng: {total_objects}
- Trung bình: {total_objects / max(1, image_count):.1f} đối tượng/ảnh

PHÂN LOẠI KÍCH THƯỚC:
"""
        for size, count in size_counts.most_common():
            percent = count / total_objects * 100 if total_objects > 0 else 0
            report += f"- {size}: {count} ({percent:.1f}%)\n"

        report += "\nPHÂN LOẠI ĐỘ CHÍN:\n"
        for ripeness, count in ripeness_counts.most_common():
            percent = count / total_objects * 100 if total_objects > 0 else 0
            report += f"- {ripeness}: {count} ({percent:.1f}%)\n"

        report += "\nCHẤT LƯỢNG:\n"
        for defect, count in defect_counts.most_common():
            percent = count / total_objects * 100 if total_objects > 0 else 0
            report += f"- {defect}: {count} ({percent:.1f}%)\n"

        # Phân tích chi tiết
        if results:
            diameters = [r.get('d_eq_mm', 0) for r in results if r.get('d_eq_mm', 0) > 0]
            defect_ratios = [r.get('defect_ratio', 0) for r in results]

            if diameters:
                report += f"\nPHÂN TÍCH KÍCH THƯỚC:\n"
                report += f"- Đường kính TB: {np.mean(diameters):.1f}mm\n"
                report += f"- Đường kính min: {np.min(diameters):.1f}mm\n"
                report += f"- Đường kính max: {np.max(diameters):.1f}mm\n"
                report += f"- Độ lệch chuẩn: {np.std(diameters):.1f}mm\n"

            if defect_ratios:
                report += f"\nPHÂN TÍCH KHUYẾT TẬT:\n"
                report += f"- Tỷ lệ khuyết tật TB: {np.mean(defect_ratios) * 100:.2f}%\n"
                report += f"- Số lượng không khuyết tật: {sum(1 for r in defect_ratios if r < 0.05)}\n"
                report += f"- Số lượng khuyết tật nhẹ: {sum(1 for r in defect_ratios if 0.05 <= r < 0.1)}\n"
                report += f"- Số lượng khuyết tật nặng: {sum(1 for r in defect_ratios if r >= 0.1)}\n"

        # Lưu báo cáo
        report_path = os.path.join(output_dir, "batch_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        # Xuất dữ liệu CSV
        csv_path = os.path.join(output_dir, "batch_data.csv")
        self.export_results_to_csv(results, csv_path)

        print(f"Đã tạo báo cáo: {report_path}")
        print(f"Đã xuất dữ liệu: {csv_path}")

    def export_results_to_csv(self, results, filename):
        """
        Xuất kết quả ra file CSV

        Chức năng: Lưu dữ liệu chi tiết để phân tích thêm
        """
        import csv

        fieldnames = [
            'id', 'tracked_id', 'size', 'ripeness', 'defect',
            'd_eq_mm', 'area_px', 'circularity', 'aspect_ratio',
            'h_mean', 's_mean', 'v_mean', 'a_mean', 'b_mean',
            'ratio_red', 'ratio_green', 'defect_ratio'
        ]

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                if result:
                    row = {field: result.get(field, '') for field in fieldnames}
                    writer.writerow(row)

    def run_conveyor_mode(self, camera_id=0):
        """
        Chế độ băng tải với tracking và đếm chính xác

        Chức năng: Theo dõi sản phẩm trên băng tải, tránh đếm trùng
        """
        print("=== CHẠY CHE ĐỘ BĂNG TẢI ===")
        self.mode = "conveyor"

        # Reset counters
        self.reset_counters()

        # Chạy camera mode với conveyor handling
        self.run_camera_mode(camera_id, enable_recording=True)

    def reset_counters(self):
        """
        Reset tất cả bộ đếm

        Chức năng: Bắt đầu session đếm mới
        """
        self.statistics_manager = StatisticsManager()
        self.conveyor_handler.reset_counting()
        self.object_tracker = ObjectTracker(max_disappeared=15, max_distance=80)
        print("Đã reset tất cả bộ đếm")

    def export_statistics(self):
        """
        Xuất thống kê hiện tại

        Chức năng: Tạo báo cáo và xuất file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Xuất báo cáo hàng ngày
        daily_report = self.statistics_manager.generate_daily_report()
        report_path = os.path.join(self.output_dir, f"daily_report_{timestamp}.txt")

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(daily_report)

        # Xuất CSV
        csv_path = self.statistics_manager.export_to_csv(
            os.path.join(self.output_dir, f"statistics_{timestamp}.csv")
        )

        print(f"Đã xuất báo cáo: {report_path}")
        print("Thống kê hiện tại:")
        print(daily_report)

    def export_final_report(self):
        """
        Xuất báo cáo cuối session

        Chức năng: Tổng kết toàn bộ session làm việc
        """
        print("=== XUẤT BÁO CÁO CUỐI SESSION ===")

        # Phân tích xu hướng chất lượng
        quality_trends = self.statistics_manager.analyze_quality_trends()

        final_report = f"""
=== BÁO CÁO CUỐI SESSION ===
Thời gian kết thúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Mode hoạt động: {self.mode}

{self.statistics_manager.generate_daily_report()}

XU HƯỚNG CHẤT LƯỢNG:
Hướng: {quality_trends.get('direction', 'N/A')}
Tỷ lệ khuyết tật hiện tại: {quality_trends.get('current_avg', 0) * 100:.2f}%

CẤU HÌNH HỆ THỐNG:
- Tracking: {'Bật' if self.enable_tracking else 'Tắt'}
- Phân tích chất lượng: {'Bật' if self.enable_quality_analysis else 'Tắt'}
- Thư mục output: {self.output_dir}
"""

        # Lưu báo cáo cuối
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_report_path = os.path.join(self.output_dir, f"final_report_{timestamp}.txt")

        with open(final_report_path, 'w', encoding='utf-8') as f:
            f.write(final_report)

        print(f"Đã lưu báo cáo cuối: {final_report_path}")
        print("Cảm ơn bạn đã sử dụng hệ thống!")


def main():
    """
    Hàm main với command line interface

    Chức năng: Giao diện dòng lệnh để chọn mode và cấu hình
    """
    parser = argparse.ArgumentParser(description="Hệ thống phân loại sản phẩm tích hợp")

    parser.add_argument("--mode", choices=["camera", "batch", "conveyor"],
                        default="camera", help="Chế độ hoạt động")
    parser.add_argument("--config", default="config.json",
                        help="File cấu hình")
    parser.add_argument("--camera-id", type=int, default=0,
                        help="ID camera")
    parser.add_argument("--input-dir", default="input_images",
                        help="Thư mục ảnh đầu vào (batch mode)")
    parser.add_argument("--output-dir", default="results",
                        help="Thư mục kết quả")
    parser.add_argument("--enable-recording", action="store_true",
                        help="Bật ghi video")
    parser.add_argument("--disable-tracking", action="store_true",
                        help="Tắt object tracking")

    args = parser.parse_args()

    # Khởi tạo hệ thống
    system = CompleteIntegratedSystem(args.config)
    system.output_dir = args.output_dir
    system.enable_tracking = not args.disable_tracking

    print(f"Khởi động hệ thống với mode: {args.mode}")
    print(f"Cấu hình: {args.config}")
    print(f"Output: {args.output_dir}")
    print(f"Tracking: {'Bật' if system.enable_tracking else 'Tắt'}")

    try:
        if args.mode == "camera":
            system.run_camera_mode(args.camera_id, args.enable_recording)
        elif args.mode == "batch":
            system.run_batch_mode(args.input_dir)
        elif args.mode == "conveyor":
            system.run_conveyor_mode(args.camera_id)
    except KeyboardInterrupt:
        print("\nNgười dùng dừng chương trình")
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Chương trình kết thúc")


if __name__ == "__main__":
    main()

# Ví dụ sử dụng:
# python complete_integration.py --mode camera --camera-id 0 --enable-recording
# python complete_integration.py --mode batch --input-dir ./test_images
# python complete_integration.py --mode conveyor --camera-id 1 --disable-tracking