import asyncio
import json
import os
import queue
import threading
import time
from datetime import datetime

import cv2
import gradio as gr
import numpy as np
from PIL import Image

from src import (
    OPENAI_CLIENT,
    SAVE_ANALYSIS_FRAMES,
    SAVE_FORMAT,
    TELEGRAM_BOT,
    USE_TELE_ALERT,
    alert_services,
)
from src.utils import frames_to_base64, prepare_messages, save_analysis_frames_to_temp


class FallDetectionWebUI:
    def __init__(self):
        # Camera and detection settings
        self.camera = None
        self.is_running = False
        self.analysis_interval = 5
        self.frame_buffer = []
        self.last_analysis_time = 0
        self.fall_detected_cooldown = 30
        self.last_fall_alert = 0
        self.frame_count = 0
        self.analysis_count = 0
        self.start_time = time.time()

        # UI specific
        self.current_frame = None
        self.alert_history = []
        self.system_logs = []
        self.status_data = {}
        self.ui_update_queue = queue.Queue()

        # Status tracking
        self.camera_status = "Không hoạt động"
        self.last_analysis_result = "Chưa có phân tích"

        # Video upload processing
        self.upload_processing = False
        self.upload_progress = 0
        self.uploaded_video_path = None

        # Evidence storage
        self.evidence_gifs = []  # Store paths to saved GIF evidence

    def initialize_camera(self, camera_index=0):
        """Initialize camera capture"""
        try:
            if self.camera:
                self.camera.release()

            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                raise Exception(f"Không thể mở camera {camera_index}")

            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)

            self.camera_status = "Hoạt động"
            self.add_log("✓ Camera đã được khởi tạo thành công", "success")
            return True

        except Exception as e:
            self.camera_status = "Lỗi"
            self.add_log(f"✗ Không thể khởi tạo camera: {e}", "error")
            return False

    def add_log(self, message, log_type="info"):
        """Add log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {"time": timestamp, "message": message, "type": log_type}
        self.system_logs.append(log_entry)
        # Keep only last 100 logs
        if len(self.system_logs) > 100:
            self.system_logs.pop(0)

    def capture_frames(self):
        """Continuously capture frames from camera"""
        while self.is_running and self.camera:
            ret, frame = self.camera.read()
            if not ret:
                self.add_log("⚠ Không thể chụp khung hình", "warning")
                continue

            # Add timestamp to frame
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Store frame with timestamp
            current_time = time.time()
            self.frame_count += 1
            self.frame_buffer.append({"frame": frame, "timestamp": current_time})

            # Keep only recent frames (last 10 seconds)
            self.frame_buffer = [f for f in self.frame_buffer if current_time - f["timestamp"] < 10]

            # Update current frame for UI
            self.current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Check for analysis trigger
            if current_time - self.last_analysis_time >= self.analysis_interval:
                threading.Thread(target=self.analyze_frames, daemon=True).start()
                self.last_analysis_time = current_time

            time.sleep(0.03)  # ~30 FPS

    def analyze_frames(self):
        """Analyze recent frames for fall detection using OpenAI"""
        if not self.frame_buffer:
            return

        try:
            self.analysis_count += 1
            self.add_log(f"🔍 Bắt đầu phân tích lần {self.analysis_count}...", "info")

            # Get recent frames
            recent_frames = self.frame_buffer.copy()

            # Save analysis frames if enabled
            if SAVE_ANALYSIS_FRAMES:
                threading.Thread(target=save_analysis_frames_to_temp, args=([recent_frames])).start()

            base64_frames = frames_to_base64(recent_frames)

            if not base64_frames:
                return

            # Call OpenAI API
            response = OPENAI_CLIENT.chat.completions.create(model="gpt-4o-mini", messages=prepare_messages(base64_frames), max_tokens=150)

            analysis_result = response.choices[0].message.content.strip()
            self.last_analysis_result = analysis_result
            self.add_log(f"📊 Kết quả phân tích: {analysis_result}", "info")

            # Check for fall detection (Vietnamese)
            if analysis_result.startswith("PHÁT_HIỆN_TÉ_NGÃ"):
                self.handle_fall_detection(analysis_result)

        except Exception as e:
            self.add_log(f"❌ Lỗi phân tích: {e}", "error")

    def handle_fall_detection(self, analysis_result):
        """Handle detected fall - send alerts"""
        current_time = time.time()

        # Check cooldown to prevent spam
        if current_time - self.last_fall_alert < self.fall_detected_cooldown:
            self.add_log("⏳ Phát hiện té ngã nhưng vẫn trong thời gian chờ", "warning")
            return

        self.last_fall_alert = current_time
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Add to alert history
        alert_data = {
            "timestamp": timestamp,
            "details": analysis_result,
            "frame_count": len(self.frame_buffer),
            "evidence_saved": SAVE_ANALYSIS_FRAMES,
            "source": "Live Camera",
        }
        self.alert_history.append(alert_data)

        # Log the alert
        self.add_log(f"🚨 PHÁT HIỆN TÉ NGÃ: {analysis_result}", "alert")

        # Save evidence as GIF
        try:
            gif_path = self.save_evidence_gif(self.frame_buffer, timestamp, "Live Camera")
            if gif_path:
                alert_data["gif_evidence"] = gif_path
                self.evidence_gifs.append({"path": gif_path, "timestamp": timestamp, "source": "Live Camera", "details": analysis_result})
                self.add_log(f"💾 Đã lưu bằng chứng GIF: {os.path.basename(gif_path)}", "success")
        except Exception as e:
            self.add_log(f"❌ Lỗi lưu GIF: {e}", "error")

        # Send Telegram notification only if enabled
        if TELEGRAM_BOT and USE_TELE_ALERT:
            asyncio.create_task(alert_services.send_telegram_alert(analysis_result, timestamp, self.frame_buffer))
            self.add_log("📱 Thông báo Telegram đã gửi", "success")
        else:
            self.add_log("ℹ Bỏ qua thông báo Telegram (đã tắt hoặc chưa cấu hình)", "info")

        # Save current frame as evidence (original format)
        if self.frame_buffer:
            threading.Thread(target=save_analysis_frames_to_temp, args=([self.frame_buffer])).start()

    def start_detection(self, camera_index):
        """Start the fall detection system"""
        if self.is_running:
            return "❌ Hệ thống đã đang chạy!", self.get_status_info()

        if not self.initialize_camera(camera_index):
            return "❌ Không thể khởi tạo camera!", self.get_status_info()

        self.is_running = True
        self.start_time = time.time()
        self.add_log("🚀 Hệ thống phát hiện té ngã đã khởi động", "success")

        # Start capture thread
        threading.Thread(target=self.capture_frames, daemon=True).start()

        return "✅ Hệ thống đã khởi động thành công!", self.get_status_info()

    def stop_detection(self):
        """Stop the fall detection system"""
        if not self.is_running:
            return "❌ Hệ thống chưa chạy!", self.get_status_info()

        self.is_running = False
        self.camera_status = "Đã dừng"

        if self.camera:
            self.camera.release()
            self.camera = None

        self.add_log("🛑 Hệ thống phát hiện té ngã đã dừng", "info")
        return "✅ Hệ thống đã dừng!", self.get_status_info()

    def get_current_frame(self):
        """Get current frame for display"""
        if self.current_frame is not None:
            return Image.fromarray(self.current_frame)
        else:
            # Return a placeholder image
            placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(placeholder, "Camera chua khoi dong", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            return Image.fromarray(placeholder)

    def get_status_info(self):
        """Get system status information"""
        uptime = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start_time))

        status_text = f"""
📊 **TRẠNG THÁI HỆ THỐNG**

🎥 **Camera:** {self.camera_status}\n
🔍 **Lần phân tích:** {self.analysis_count}\n
📱 **Gửi Tin Nhắn:** {'Bật' if USE_TELE_ALERT else 'Tắt'}\n
💾 **Lưu Frames:** {'Bật (' + SAVE_FORMAT.upper() + ')' if SAVE_ANALYSIS_FRAMES else 'Tắt'}\n
⏰ **Thời gian hoạt động:** {uptime}\n
🔄 **Chu kỳ:** {self.analysis_interval}s\n
📈 **Khung hình/Buffer Frames:** {self.frame_count} / {len(self.frame_buffer)}\n
🚨 **Cảnh báo:** {len(self.alert_history)}\n

📋 **Kết quả phân tích gần nhất:**
{self.last_analysis_result}
        """
        return status_text

    def get_logs_display(self):
        """Get formatted logs for display"""
        if not self.system_logs:
            return "Chưa có log nào..."

        log_text = ""
        for log in self.system_logs[-30:]:  # Show last 30 logs
            emoji = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "alert": "🚨"}
            icon = emoji.get(log["type"], "📝")
            log_text += f"[{log['time']}] {icon} {log['message']}\n"

        return log_text

    def get_alert_history_display(self):
        """Get formatted alert history for display"""
        if not self.alert_history:
            return "Chưa có cảnh báo nào..."

        alert_text = ""
        for i, alert in enumerate(reversed(self.alert_history[-10:])):  # Show last 10 alerts
            alert_text += f"""
**Cảnh báo #{len(self.alert_history) - i}**
🕐 Thời gian: {alert['timestamp']}
📝 Chi tiết: {alert['details']}
📊 Frames: {alert['frame_count']}
💾 Bằng chứng: {'Đã lưu' if alert['evidence_saved'] else 'Không lưu'}
---
            """

        return alert_text

    def process_uploaded_video(self, video_path):
        """Process uploaded video file for fall detection"""
        if not video_path:
            return "❌ Không có video được upload!", "Vui lòng chọn file video"

        if self.upload_processing:
            return "❌ Đang xử lý video khác!", "Vui lòng chờ hoàn thành"

        self.upload_processing = True
        self.upload_progress = 0
        self.uploaded_video_path = video_path

        try:
            self.add_log(f"📁 Bắt đầu xử lý video: {os.path.basename(video_path)}", "info")

            # Open video file
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("Không thể mở file video")

            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0

            self.add_log(f"📊 Video info: {total_frames} frames, {fps:.1f} FPS, {duration:.1f}s", "info")

            # Process video in chunks (analyze every 5 seconds)
            analysis_interval_frames = int(fps * 5) if fps > 0 else 150  # 5 seconds worth of frames

            frame_buffer = []
            frame_count = 0
            analysis_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                current_time = frame_count / fps if fps > 0 else frame_count * 0.033

                # Add frame to buffer
                frame_buffer.append({"frame": frame, "timestamp": current_time})

                # Update progress
                self.upload_progress = int((frame_count / total_frames) * 100) if total_frames > 0 else 0

                # Analyze when we have enough frames or at the end
                if len(frame_buffer) >= analysis_interval_frames or frame_count == total_frames:
                    analysis_count += 1

                    try:
                        # Analyze frames for fall detection
                        analysis_result = self.analyze_video_frames(frame_buffer, analysis_count, video_path)

                        # Check for fall detection
                        if analysis_result and analysis_result.startswith("PHÁT_HIỆN_TÉ_NGÃ"):
                            self.handle_video_fall_detection(analysis_result, frame_buffer, current_time, video_path)

                    except Exception as e:
                        self.add_log(f"❌ Lỗi phân tích chunk {analysis_count}: {e}", "error")

                    # Reset buffer
                    frame_buffer = []

            cap.release()
            self.upload_processing = False
            self.upload_progress = 100

            result_msg = f"✅ Hoàn thành xử lý video! Đã phân tích {analysis_count} đoạn video"
            self.add_log(result_msg, "success")

            return result_msg, f"Video: {os.path.basename(video_path)}\nFrames: {frame_count}\nPhân tích: {analysis_count} đoạn"

        except Exception as e:
            self.upload_processing = False
            error_msg = f"❌ Lỗi xử lý video: {e}"
            self.add_log(error_msg, "error")
            return error_msg, "Xử lý thất bại"

    def analyze_video_frames(self, frame_buffer, analysis_count, source_video):
        """Analyze frames from uploaded video"""
        if not frame_buffer:
            return None

        try:
            self.add_log(f"🔍 Phân tích đoạn video {analysis_count} ({len(frame_buffer)} frames)...", "info")

            # Convert frames to base64 (sample frames to avoid too many)
            sample_frames = frame_buffer[:: max(1, len(frame_buffer) // 5)]  # Sample max 5 frames
            base64_frames = frames_to_base64(sample_frames)

            if not base64_frames:
                return None

            # Call OpenAI API
            response = OPENAI_CLIENT.chat.completions.create(model="gpt-4o-mini", messages=prepare_messages(base64_frames), max_tokens=150)

            analysis_result = response.choices[0].message.content.strip()
            self.add_log(f"📊 Kết quả phân tích đoạn {analysis_count}: {analysis_result}", "info")

            return analysis_result

        except Exception as e:
            self.add_log(f"❌ Lỗi phân tích video frames: {e}", "error")
            return None

    def handle_video_fall_detection(self, analysis_result, frame_buffer, timestamp, source_video):
        """Handle fall detection from uploaded video"""
        detection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create alert data for video
        alert_data = {
            "timestamp": detection_time,
            "details": analysis_result,
            "frame_count": len(frame_buffer),
            "evidence_saved": True,
            "source": f"Video: {os.path.basename(source_video)}",
            "video_timestamp": f"{timestamp:.1f}s",
        }

        self.alert_history.append(alert_data)
        self.add_log(f"🚨 PHÁT HIỆN TÉ NGÃ TRONG VIDEO: {analysis_result} tại {timestamp:.1f}s", "alert")

        # Save evidence as GIF
        try:
            gif_path = self.save_evidence_gif(frame_buffer, detection_time, source_video)
            if gif_path:
                alert_data["gif_evidence"] = gif_path
                self.evidence_gifs.append({"path": gif_path, "timestamp": detection_time, "source": os.path.basename(source_video), "details": analysis_result})
                self.add_log(f"💾 Đã lưu bằng chứng GIF: {os.path.basename(gif_path)}", "success")
        except Exception as e:
            self.add_log(f"❌ Lỗi lưu GIF: {e}", "error")

        # Send Telegram notification if enabled
        if TELEGRAM_BOT and USE_TELE_ALERT:
            try:
                asyncio.create_task(
                    alert_services.send_telegram_alert(
                        f"🎬 {analysis_result} (Video: {os.path.basename(source_video)} tại {timestamp:.1f}s)", detection_time, frame_buffer
                    )
                )
                self.add_log("📱 Thông báo Telegram đã gửi", "success")
            except Exception as e:
                self.add_log(f"❌ Lỗi gửi Telegram: {e}", "error")

    def save_evidence_gif(self, frame_buffer, timestamp, source_info):
        """Save frame buffer as GIF evidence"""
        try:
            # Create evidence directory if not exists
            evidence_dir = "evidence_gifs"
            os.makedirs(evidence_dir, exist_ok=True)

            # Generate filename
            safe_timestamp = timestamp.replace(":", "-").replace(" ", "_")
            filename = f"fall_evidence_{safe_timestamp}.gif"
            gif_path = os.path.join(evidence_dir, filename)

            # Convert frames to PIL Images
            pil_frames = []
            for frame_data in frame_buffer[::2]:  # Skip every other frame for smaller GIF
                frame = frame_data["frame"]
                # Resize frame for smaller file size
                height, width = frame.shape[:2]
                new_width = min(320, width)
                new_height = int(height * (new_width / width))
                resized_frame = cv2.resize(frame, (new_width, new_height))
                pil_frame = Image.fromarray(cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB))
                pil_frames.append(pil_frame)

            # Save as GIF
            if pil_frames:
                pil_frames[0].save(gif_path, save_all=True, append_images=pil_frames[1:], duration=200, loop=0)  # 200ms per frame
                return gif_path

        except Exception as e:
            self.add_log(f"❌ Lỗi tạo GIF: {e}", "error")
            return None

    def get_evidence_gifs_display(self):
        """Get list of evidence GIFs for display"""
        if not self.evidence_gifs:
            return "Chưa có bằng chứng GIF nào...", []

        display_text = f"📁 **CÓ {len(self.evidence_gifs)} BẰNG CHỨNG GIF**\n\n"

        gif_paths = []
        for i, evidence in enumerate(reversed(self.evidence_gifs[-10:])):  # Show last 10
            display_text += f"""
**GIF #{len(self.evidence_gifs) - i}**
🕐 Thời gian: {evidence['timestamp']}
📁 Nguồn: {evidence['source']}
📝 Chi tiết: {evidence['details']}
📄 File: {os.path.basename(evidence['path'])}
---
            """
            gif_paths.append(evidence["path"])

        return display_text, gif_paths

    def get_upload_progress(self):
        """Get current upload processing progress"""
        if not self.upload_processing:
            return "Sẵn sàng upload video", 0
        return f"Đang xử lý video... {self.upload_progress}%", self.upload_progress


# Initialize the system
fall_system = FallDetectionWebUI()


def create_interface():
    """Create the Gradio interface"""

    with gr.Blocks(
        title="🏥 Hệ Thống Phát Hiện Té Ngã",
        theme=gr.themes.Soft(),
        css="""
        .alert-box { background-color: #ffebee; border-left: 4px solid #f44336; padding: 10px; }
        .success-box { background-color: #e8f5e8; border-left: 4px solid #4caf50; padding: 10px; }
        .info-box { background-color: #e3f2fd; border-left: 4px solid #2196f3; padding: 10px; }
        """,
    ) as demo:

        gr.HTML(
            """
        <div style="text-align: center; margin-bottom: 20px;">
            <h1>🏥 HỆ THỐNG PHÁT HIỆN TÉ NGÃ BỆNH VIỆN</h1>
            <p style="font-size: 16px; color: #666;">
                Hệ thống AI phát hiện té ngã thời gian thực sử dụng Vision Language Model
            </p>
        </div>
        """
        )

        with gr.Tab("🎥 Camera & Điều Khiển"):
            with gr.Row():
                with gr.Column(scale=2):
                    camera_feed = gr.Image(label="📹 Camera Feed", type="pil", height=400, show_label=True)

                    with gr.Row():
                        camera_index = gr.Number(label="Chỉ số Camera", value=0, precision=0, minimum=0, maximum=10)
                        start_btn = gr.Button("🚀 Khởi Động", variant="primary", size="lg")
                        stop_btn = gr.Button("🛑 Dừng", variant="secondary", size="lg")

                with gr.Column(scale=1):
                    status_display = gr.Markdown(label="📊 Trạng Thái Hệ Thống", value=fall_system.get_status_info())

                    control_output = gr.Textbox(label="📢 Thông Báo Hệ Thống", value="Sẵn sàng khởi động...", interactive=False)

        with gr.Tab("📋 Nhật Ký Hệ Thống"):
            logs_display = gr.Textbox(label="📝 System Logs (30 mục gần nhất)", value=fall_system.get_logs_display(), lines=30, interactive=False, max_lines=25)

            refresh_logs_btn = gr.Button("🔄 Cập Nhật Logs", size="sm")

        with gr.Tab("🚨 Lịch Sử Cảnh Báo"):
            alert_display = gr.Markdown(label="🚨 Lịch Sử Té Ngã (10 cảnh báo gần nhất)", value=fall_system.get_alert_history_display())

            refresh_alerts_btn = gr.Button("🔄 Cập Nhật Cảnh Báo", size="sm")

            with gr.Row():
                clear_alerts_btn = gr.Button("🗑️ Xóa Lịch Sử", variant="secondary")
                export_alerts_btn = gr.Button("📁 Xuất Báo Cáo", variant="primary")

        with gr.Tab("📁 Upload Video"):
            gr.HTML(
                """
            <div class="info-box">
                <h3>📁 Phân Tích Video Từ File</h3>
                <p>Upload video từ thiết bị để phân tích té ngã. Hỗ trợ các định dạng: MP4, AVI, MOV, MKV</p>
            </div>
            """
            )

            with gr.Row():
                with gr.Column(scale=2):
                    video_upload = gr.File(label="📹 Chọn File Video", file_types=["video"], type="filepath")

                    upload_btn = gr.Button("🔍 Phân Tích Video", variant="primary", size="lg")

                    gr.Progress()
                    upload_status = gr.Textbox(label="📊 Trạng Thái Xử Lý", value="Chưa có video được upload...", interactive=False)

                with gr.Column(scale=1):
                    upload_info = gr.Textbox(label="ℹ️ Thông Tin Video", value="Chưa chọn video...", interactive=False, lines=10)

            gr.HTML(
                """
            <div class="alert-box">
                <h4>⚠️ Lưu Ý Quan Trọng</h4>
                <ul>
                    <li>Video sẽ được phân tích từng đoạn 5 giây</li>
                    <li>Quá trình có thể mất thời gian tùy theo độ dài video</li>
                    <li>Kết quả sẽ hiển thị trong lịch sử cảnh báo</li>
                    <li>GIF bằng chứng sẽ được tự động tạo khi phát hiện té ngã</li>
                </ul>
            </div>
            """
            )

        with gr.Tab("🎬 Bằng Chứng GIF"):
            gr.HTML(
                """
            <div class="success-box">
                <h3>🎬 Bằng Chứng Té Ngã (GIF)</h3>
                <p>Xem các GIF bằng chứng đã được lưu khi phát hiện té ngã</p>
            </div>
            """
            )

            with gr.Row():
                with gr.Column(scale=1):
                    evidence_list = gr.Markdown(label="📋 Danh Sách Bằng Chứng", value=fall_system.get_evidence_gifs_display()[0])

                    with gr.Row():
                        refresh_evidence_btn = gr.Button("🔄 Cập Nhật", size="sm")
                        clear_evidence_btn = gr.Button("🗑️ Xóa Tất Cả", variant="secondary", size="sm")

                with gr.Column(scale=2):
                    evidence_gallery = gr.Gallery(label="🎬 GIF Bằng Chứng", show_label=True, elem_id="evidence_gallery", columns=2, rows=3, height="auto")

            gr.HTML(
                """
            <div class="info-box">
                <h4>📋 Hướng Dẫn Sử Dụng</h4>
                <ul>
                    <li>Click vào GIF trong gallery để xem chi tiết</li>
                    <li>GIF được tự động tạo khi phát hiện té ngã</li>
                    <li>Mỗi GIF chứa khoảnh khắc trước và sau khi té ngã</li>
                    <li>GIF được lưu trong thư mục <code>evidence_gifs/</code></li>
                </ul>
            </div>
            """
            )

        with gr.Tab("⚙️ Cấu Hình"):
            gr.HTML(
                """
            <div class="info-box">
                <h3>🔧 Cấu Hình Hệ Thống</h3>
                <p>Các cấu hình được đọc từ file <code>.env</code>. Sau khi thay đổi, vui lòng khởi động lại ứng dụng.</p>
            </div>
            """
            )

            with gr.Row():
                with gr.Column():
                    gr.Markdown(
                        """

                    ### 📱 Cấu Hình Telegram
                    - **USE_TELE_ALERT**: true/false (mặc định: false)
                    - **TELEGRAM_BOT_TOKEN**: Token bot Telegram
                    - **TELEGRAM_CHAT_ID**: ID chat nhận thông báo

                    ### 💾 Cấu Hình Lưu Trữ
                    - **SAVE_ANALYSIS_FRAMES**: true/false (mặc định: false)
                    - **SAVE_FORMAT**: images/gif/video/all (mặc định: images)
                    - **MAX_FRAMES**: Số frame tối đa gửi AI (mặc định: 5)
                    """
                    )

                with gr.Column():
                    current_config = f"""
### 📊 Cấu Hình Hiện Tại
- **Telegram**: {'✅ Bật' if USE_TELE_ALERT else '❌ Tắt'}
- **Lưu Frames**: {'✅ Bật' if SAVE_ANALYSIS_FRAMES else '❌ Tắt'}
- **Định Dạng**: {SAVE_FORMAT.upper()}
- **Max Frames**: {os.environ.get('MAX_FRAMES', 5)}
                    """
                    gr.Markdown(current_config)

        # Event handlers
        def start_system(camera_idx):
            message, status = fall_system.start_detection(int(camera_idx))
            return message, status

        def stop_system():
            message, status = fall_system.stop_detection()
            return message, status

        def clear_alert_history():
            fall_system.alert_history.clear()
            fall_system.add_log("🗑️ Đã xóa lịch sử cảnh báo", "info")
            return "✅ Đã xóa lịch sử cảnh báo!", fall_system.get_alert_history_display()

        def export_alert_report():
            if not fall_system.alert_history:
                return "❌ Không có dữ liệu để xuất!"

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"alert_report_{timestamp}.json"

            try:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(fall_system.alert_history, f, ensure_ascii=False, indent=2)
                return f"✅ Đã xuất báo cáo: {filename}"
            except Exception as e:
                return f"❌ Lỗi xuất báo cáo: {e}"

        # Bind events
        start_btn.click(start_system, inputs=[camera_index], outputs=[control_output, status_display])

        stop_btn.click(stop_system, outputs=[control_output, status_display])

        refresh_logs_btn.click(lambda: fall_system.get_logs_display(), outputs=[logs_display])

        refresh_alerts_btn.click(lambda: fall_system.get_alert_history_display(), outputs=[alert_display])

        clear_alerts_btn.click(clear_alert_history, outputs=[control_output, alert_display])

        export_alerts_btn.click(export_alert_report, outputs=[control_output])

        # Video upload event handlers
        def process_video(video_file):
            if not video_file:
                return "❌ Chưa chọn video!", "Vui lòng chọn file video"

            # Process video in a separate thread to avoid blocking UI
            def video_worker():
                return fall_system.process_uploaded_video(video_file)

            return video_worker()

        def refresh_evidence():
            display_text, gif_paths = fall_system.get_evidence_gifs_display()
            return display_text, gif_paths

        def clear_evidence():
            try:
                # Clear from memory
                fall_system.evidence_gifs.clear()

                # Optionally delete files (uncomment if needed)
                # import glob
                # gif_files = glob.glob("evidence_gifs/*.gif")
                # for gif_file in gif_files:
                #     os.remove(gif_file)

                fall_system.add_log("🗑️ Đã xóa danh sách bằng chứng GIF", "info")
                display_text, gif_paths = fall_system.get_evidence_gifs_display()
                return "✅ Đã xóa danh sách bằng chứng!", display_text, gif_paths
            except Exception as e:
                return f"❌ Lỗi xóa bằng chứng: {e}", "Lỗi", []

        # Bind new events
        upload_btn.click(process_video, inputs=[video_upload], outputs=[upload_status, upload_info])

        refresh_evidence_btn.click(refresh_evidence, outputs=[evidence_list, evidence_gallery])

        clear_evidence_btn.click(clear_evidence, outputs=[upload_status, evidence_list, evidence_gallery])

        # Fast refresh for camera feed (0.1s for real-time video)
        def update_camera():
            return fall_system.get_current_frame()

        # Slower refresh for status/logs/alerts/evidence (2s for text data)
        def update_status_and_logs():
            if fall_system.is_running:
                evidence_text, evidence_gifs = fall_system.get_evidence_gifs_display()
                return (fall_system.get_status_info(), fall_system.get_logs_display(), fall_system.get_alert_history_display(), evidence_text, evidence_gifs)
            else:
                evidence_text, evidence_gifs = fall_system.get_evidence_gifs_display()
                return (fall_system.get_status_info(), gr.update(), gr.update(), evidence_text, evidence_gifs)

        # Set up dual auto-refresh timers using gr.Timer (Gradio 5.x)
        try:
            # Fast timer for camera feed (0.1s = 10 FPS)
            camera_timer = gr.Timer(0.1)
            camera_timer.tick(update_camera, outputs=[camera_feed])

            # Slower timer for status and logs (2s)
            status_timer = gr.Timer(2.0)
            status_timer.tick(update_status_and_logs, outputs=[status_display, logs_display, alert_display, evidence_list, evidence_gallery])

            print("✅ Dual refresh timers set up: Camera 0.1s, Status/Logs 2s")

        except Exception as e:
            print(f"⚠️ Auto-refresh timers not available: {e}")
            # Fallback: single timer for everything at 1s
            try:
                fallback_timer = gr.Timer(1.0)

                def update_all():
                    if fall_system.is_running:
                        evidence_text, evidence_gifs = fall_system.get_evidence_gifs_display()
                        return (
                            fall_system.get_current_frame(),
                            fall_system.get_status_info(),
                            fall_system.get_logs_display(),
                            fall_system.get_alert_history_display(),
                            evidence_text,
                            evidence_gifs,
                        )
                    else:
                        evidence_text, evidence_gifs = fall_system.get_evidence_gifs_display()
                        return (fall_system.get_current_frame(), fall_system.get_status_info(), gr.update(), gr.update(), evidence_text, evidence_gifs)

                fallback_timer.tick(update_all, outputs=[camera_feed, status_display, logs_display, alert_display, evidence_list, evidence_gallery])
                print("⚠️ Using fallback timer: All components 1s")
            except:
                print("❌ No auto-refresh available - manual refresh only")

    return demo


if __name__ == "__main__":
    # Create and launch the interface
    demo = create_interface()

    print("🚀 Đang khởi động Gradio Web UI...")
    print("📱 Truy cập giao diện web tại: http://localhost:7860")
    print("🛑 Nhấn Ctrl+C để dừng server")

    try:
        demo.launch(server_name="127.0.0.1", server_port=7860, share=False, show_error=True, quiet=False, prevent_thread_lock=False)  # Use localhost first
    except Exception as e:
        print(f"❌ Localhost launch failed: {e}")
        print("🔄 Trying with network access...")
        try:
            demo.launch(server_name="0.0.0.0", server_port=7860, share=False, show_error=True, quiet=False, prevent_thread_lock=False)  # Allow external access
        except Exception as e2:
            print(f"❌ Network launch failed: {e2}")
            print("🌐 Creating shareable link...")
            demo.launch(share=True, show_error=True, quiet=False, prevent_thread_lock=False)  # Create public link as last resort
