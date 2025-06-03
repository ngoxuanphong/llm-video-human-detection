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
from src.audio_warning import AudioWarningSystem
from src.utils import frames_to_base64, prepare_messages, save_analysis_frames_to_temp
from src.videollama_detector import VideoLLamaFallDetector


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

        # Detection method: "openai" or "videollama3"
        self.detection_method = "openai"

        # Initialize VideoLLaMA3 detector
        self.videollama_detector = VideoLLamaFallDetector()

        # Initialize audio warning system
        self.audio_warning = AudioWarningSystem()

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
        """Analyze recent frames for fall detection using selected method"""
        if not self.frame_buffer:
            return

        try:
            self.analysis_count += 1
            self.add_log(f"🔍 Bắt đầu phân tích lần {self.analysis_count} ({self.detection_method.upper()})...", "info")

            # Get recent frames
            recent_frames = self.frame_buffer.copy()

            # Save analysis frames if enabled
            if SAVE_ANALYSIS_FRAMES:
                threading.Thread(target=save_analysis_frames_to_temp, args=([recent_frames])).start()

            # Choose analysis method
            if self.detection_method == "videollama3":
                analysis_result = self.analyze_frames_videollama3(recent_frames)
            else:  # Default to OpenAI
                analysis_result = self.analyze_frames_openai(recent_frames)

            if analysis_result:
                self.last_analysis_result = analysis_result
                self.add_log(f"📊 Kết quả phân tích: {analysis_result}", "info")

                # Check for fall detection (Vietnamese)
                if analysis_result.startswith("PHÁT_HIỆN_TÉ_NGÃ"):
                    self.handle_fall_detection(analysis_result)

        except Exception as e:
            self.add_log(f"❌ Lỗi phân tích: {e}", "error")

    def analyze_frames_openai(self, recent_frames):
        """Analyze frames using OpenAI GPT-4V"""
        try:
            base64_frames = frames_to_base64(recent_frames)
            if not base64_frames:
                return None

            # Call OpenAI API
            response = OPENAI_CLIENT.chat.completions.create(model="gpt-4o-mini", messages=prepare_messages(base64_frames), max_tokens=150)

            return response.choices[0].message.content.strip()
        except Exception as e:
            self.add_log(f"❌ Lỗi OpenAI API: {e}", "error")
            return None

    def analyze_frames_videollama3(self, recent_frames):
        """Analyze frames using local VideoLLaMA3 model"""
        try:
            if not self.videollama_detector.is_loaded:
                self.add_log("⚠️ VideoLLaMA3 model chưa được tải", "warning")
                return None

            return self.videollama_detector.analyze_frames(recent_frames)
        except Exception as e:
            self.add_log(f"❌ Lỗi VideoLLaMA3: {e}", "error")
            return None

    def handle_fall_detection(self, analysis_result):
        """Handle detected fall - send alerts and play audio warning"""
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
            "detection_method": self.detection_method.upper(),
        }
        self.alert_history.append(alert_data)

        # Log the alert
        self.add_log(f"🚨 PHÁT HIỆN TÉ NGÃ: {analysis_result}", "alert")

        # Play audio warning (async to avoid blocking)
        self.audio_warning.play_warning_async(analysis_result)
        self.add_log("🔊 Đã phát cảnh báo âm thanh", "success")

        # Save evidence as GIF
        try:
            gif_folder = self.save_evidence_gif(self.frame_buffer, timestamp, "Live Camera")
            if gif_folder:
                alert_data["gif_evidence"] = gif_folder
                self.evidence_gifs.append(
                    {"path": gif_folder, "timestamp": timestamp, "source": "Live Camera", "details": analysis_result, "detection_method": self.detection_method.upper()}
                )
                self.add_log(f"💾 Đã lưu bằng chứng GIF: {os.path.basename(gif_folder)}", "success")
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

        # Get VideoLLaMA3 status
        llama_status = self.videollama_detector.get_model_status()
        audio_status = self.audio_warning.get_status()

        status_text = f"""
📊 **TRẠNG THÁI HỆ THỐNG**

🎥 **Camera:** {self.camera_status}
🤖 **Phương thức phát hiện:** {self.detection_method.upper()}
🔍 **Lần phân tích:** {self.analysis_count}
📱 **Gửi Tin Nhắn:** {'Bật' if USE_TELE_ALERT else 'Tắt'}
💾 **Lưu Frames:** {'Bật (' + SAVE_FORMAT.upper() + ')' if SAVE_ANALYSIS_FRAMES else 'Tắt'}
⏰ **Thời gian hoạt động:** {uptime}
🔄 **Chu kỳ:** {self.analysis_interval}s
📈 **Khung hình/Buffer Frames:** {self.frame_count} / {len(self.frame_buffer)}
🚨 **Cảnh báo:** {len(self.alert_history)}

🧠 **VideoLLaMA3:** {'✅ Loaded' if llama_status['loaded'] else '❌ Not Loaded'}
🔊 **Audio Warning:** {'✅ Enabled' if audio_status['enabled'] else '❌ Disabled'} ({audio_status['tts_method']})

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
            self.add_log(f"🔍 Phân tích đoạn video {analysis_count} ({len(frame_buffer)} frames) - {self.detection_method.upper()}...", "info")

            # Choose analysis method
            if self.detection_method == "videollama3":
                if not self.videollama_detector.is_loaded:
                    self.add_log("⚠️ VideoLLaMA3 model chưa được tải, chuyển về OpenAI", "warning")
                    return self.analyze_video_frames_openai(frame_buffer)
                else:
                    return self.videollama_detector.analyze_frames(frame_buffer)
            else:
                return self.analyze_video_frames_openai(frame_buffer)

        except Exception as e:
            self.add_log(f"❌ Lỗi phân tích video frames: {e}", "error")
            return None

    def analyze_video_frames_openai(self, frame_buffer):
        """Analyze video frames using OpenAI"""
        # Sample frames to avoid too many
        sample_frames = frame_buffer[:: max(1, len(frame_buffer) // 5)]  # Sample max 5 frames
        base64_frames = frames_to_base64(sample_frames)

        if not base64_frames:
            return None

        # Call OpenAI API
        response = OPENAI_CLIENT.chat.completions.create(model="gpt-4o-mini", messages=prepare_messages(base64_frames), max_tokens=150)

        analysis_result = response.choices[0].message.content.strip()
        self.add_log(f"📊 Kết quả phân tích OpenAI: {analysis_result}", "info")
        return analysis_result

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
            "detection_method": self.detection_method.upper(),
        }

        self.alert_history.append(alert_data)
        self.add_log(f"🚨 PHÁT HIỆN TÉ NGÃ TRONG VIDEO: {analysis_result} tại {timestamp:.1f}s", "alert")

        # Play audio warning for video detection too
        self.audio_warning.play_warning_async(analysis_result)
        self.add_log("🔊 Đã phát cảnh báo âm thanh cho video", "success")

        # Save evidence as GIF
        try:
            gif_folder = self.save_evidence_gif(frame_buffer, detection_time, source_video)
            if gif_folder:
                alert_data["gif_evidence"] = gif_folder
                self.evidence_gifs.append(
                    {
                        "path": gif_folder,
                        "timestamp": detection_time,
                        "source": os.path.basename(source_video),
                        "details": analysis_result,
                        "detection_method": self.detection_method.upper(),
                    }
                )
                self.add_log(f"💾 Đã lưu bằng chứng GIF: {os.path.basename(gif_folder)}", "success")
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
        """Save frame buffer as GIF evidence with same format as temp folder"""
        try:
            # Create evidence directory if not exists
            evidence_dir = "evidence_gifs"
            os.makedirs(evidence_dir, exist_ok=True)

            # Create timestamp folder (matching temp folder format)
            safe_timestamp = timestamp.replace(":", "").replace(" ", "_").replace("-", "")
            timestamp_folder = os.path.join(evidence_dir, f"fall_{safe_timestamp}")
            os.makedirs(timestamp_folder, exist_ok=True)

            # Generate GIF filename
            gif_filename = "fall_evidence.gif"
            gif_path = os.path.join(timestamp_folder, gif_filename)

            # Generate info filename
            info_filename = "fall_info.txt"
            info_path = os.path.join(timestamp_folder, info_filename)

            # Convert frames to PIL Images with proper timing
            pil_frames = []
            frame_timestamps = []

            for i, frame_data in enumerate(frame_buffer):
                frame = frame_data["frame"]
                # Resize frame for consistent size (matching temp folder)
                height, width = frame.shape[:2]
                new_width = min(640, width)  # Max width 640px
                new_height = int(height * (new_width / width))
                resized_frame = cv2.resize(frame, (new_width, new_height))

                # Convert BGR to RGB
                pil_frame = Image.fromarray(cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB))
                pil_frames.append(pil_frame)
                frame_timestamps.append(frame_data.get("timestamp", i * 0.1))

            # Save as GIF with proper timing (10 FPS like temp folder)
            if pil_frames:
                duration_ms = 100  # 100ms per frame = 10 FPS
                pil_frames[0].save(gif_path, save_all=True, append_images=pil_frames[1:], duration=duration_ms, loop=0)

                # Create info file (matching temp folder format)
                gif_duration = len(pil_frames) * 0.1  # 10 FPS
                info_content = f"""Fall Detection Evidence
========================================
Timestamp: {timestamp}
Source: {source_info}
Detection Method: {self.detection_method.upper()}
Total frames: {len(pil_frames)}
Save format: gif
GIF duration: {gif_duration:.1f}s (10 FPS)

Files saved:
- {gif_filename}

Analysis Result:
{self.last_analysis_result}
"""

                with open(info_path, "w", encoding="utf-8") as f:
                    f.write(info_content)

                # Return the folder path (not just GIF path) for consistency
                return timestamp_folder

        except Exception as e:
            self.add_log(f"❌ Lỗi tạo GIF evidence: {e}", "error")
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
🤖 Phương thức: {evidence.get('detection_method', 'UNKNOWN')}
📝 Chi tiết: {evidence['details']}
📄 Folder: {os.path.basename(evidence['path'])}
---
            """
            # Look for GIF file in the evidence folder
            evidence_folder = evidence["path"]
            if os.path.isdir(evidence_folder):
                # Look for the GIF file inside the folder
                gif_file = os.path.join(evidence_folder, "fall_evidence.gif")
                if os.path.exists(gif_file):
                    gif_paths.append(gif_file)
            elif evidence_folder.endswith(".gif") and os.path.exists(evidence_folder):
                # Legacy: direct GIF path
                gif_paths.append(evidence_folder)

        return display_text, gif_paths

    def get_upload_progress(self):
        """Get current upload processing progress"""
        if not self.upload_processing:
            return "Sẵn sàng upload video", 0
        return f"Đang xử lý video... {self.upload_progress}%", self.upload_progress

    def set_detection_method(self, method):
        """Set detection method (openai or videollama3)"""
        if method in ["openai", "videollama3"]:
            self.detection_method = method
            self.add_log(f"🔧 Đã chuyển phương thức phát hiện: {method.upper()}", "info")
            return f"✅ Đã chuyển sang {method.upper()}"
        else:
            return "❌ Phương thức không hợp lệ"

    def load_videollama3_model(self):
        """Load VideoLLaMA3 model"""
        if self.videollama_detector.is_loaded:
            return "⚠️ Model đã được tải rồi"

        self.add_log("🚀 Đang tải VideoLLaMA3 model...", "info")

        def load_worker():
            success = self.videollama_detector.load_model()
            if success:
                self.add_log("✅ VideoLLaMA3 model đã tải thành công", "success")
                # Force UI update by updating the queue
                self.ui_update_queue.put(("model_loaded", "✅ VideoLLaMA3 model đã tải thành công"))
            else:
                self.add_log("❌ Không thể tải VideoLLaMA3 model", "error")
                self.ui_update_queue.put(("model_error", "❌ Không thể tải VideoLLaMA3 model"))

        threading.Thread(target=load_worker, daemon=True).start()
        return "⏳ Đang tải model, vui lòng chờ..."

    def unload_videollama3_model(self):
        """Unload VideoLLaMA3 model"""
        if not self.videollama_detector.is_loaded:
            return "⚠️ Model chưa được tải"

        self.videollama_detector.unload_model()
        self.add_log("🗑️ Đã gỡ VideoLLaMA3 model", "info")
        self.ui_update_queue.put(("model_unloaded", "✅ Đã gỡ model khỏi bộ nhớ"))
        return "✅ Đã gỡ model khỏi bộ nhớ"

    def get_model_status_message(self):
        """Get current model status for UI display"""
        if self.videollama_detector.is_loaded:
            return "✅ VideoLLaMA3 model đã sẵn sàng"
        else:
            return "❌ VideoLLaMA3 model chưa được tải"

    def test_audio_warning(self):
        """Test audio warning system"""
        result = self.audio_warning.test_audio_system()
        self.add_log(f"🔊 Test audio: {result}", "info")
        return result

    def set_audio_enabled(self, enabled):
        """Enable/disable audio warnings"""
        self.audio_warning.set_enabled(enabled)
        status = "bật" if enabled else "tắt"
        self.add_log(f"🔊 Cảnh báo âm thanh đã {status}", "info")
        return f"✅ Cảnh báo âm thanh đã {status}"

    def set_audio_volume(self, volume):
        """Set audio volume"""
        self.audio_warning.set_volume(volume / 100.0)  # Convert from percentage
        self.add_log(f"🔊 Âm lượng đã đặt: {volume}%", "info")
        return f"✅ Âm lượng: {volume}%"


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

        with gr.Tab("🤖 Cấu Hình AI & Âm Thanh"):
            gr.HTML(
                """
            <div class="info-box">
                <h3>🤖 Quản Lý Mô Hình AI</h3>
                <p>Chọn phương thức phát hiện té ngã và quản lý mô hình VideoLLaMA3 local</p>
            </div>
            """
            )

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🧠 Phương Thức Phát Hiện")

                    detection_method = gr.Radio(
                        choices=[("OpenAI GPT-4V (Online)", "openai"), ("VideoLLaMA3 (Local)", "videollama3")],
                        value="openai",
                        label="Chọn phương thức phát hiện",
                        info="OpenAI cần kết nối internet, VideoLLaMA3 chạy offline",
                    )

                    method_output = gr.Textbox(label="📢 Trạng Thái Phương Thức", interactive=False)

                    gr.Markdown("### 🎯 VideoLLaMA3 Model")

                    with gr.Row():
                        load_model_btn = gr.Button("📥 Tải Model", variant="primary")
                        unload_model_btn = gr.Button("🗑️ Gỡ Model", variant="secondary")

                    model_output = gr.Textbox(label="📢 Trạng Thái Model", interactive=False)

                with gr.Column(scale=1):
                    gr.Markdown("### 🔊 Cảnh Báo Âm Thanh")

                    audio_enabled = gr.Checkbox(label="🔊 Bật cảnh báo âm thanh", value=True, info="Tự động phát cảnh báo khi phát hiện té ngã")

                    audio_volume = gr.Slider(minimum=0, maximum=100, value=80, step=5, label="🔉 Âm lượng (%)", info="Điều chỉnh âm lượng cảnh báo")

                    with gr.Row():
                        test_audio_btn = gr.Button("🔊 Test Âm Thanh", variant="primary")
                        audio_output = gr.Textbox(label="📢 Trạng Thái Audio", interactive=False)

            gr.HTML(
                """
            <div class="alert-box">
                <h4>⚠️ Lưu Ý Quan Trọng</h4>
                <ul>
                    <li><strong>OpenAI:</strong> Cần API key và kết nối internet, tốc độ phân tích nhanh</li>
                    <li><strong>VideoLLaMA3:</strong> Chạy offline, cần GPU mạnh, tốc độ chậm hơn nhưng riêng tư</li>
                    <li><strong>Audio:</strong> Cần cài đặt espeak-ng: <code>sudo apt-get install espeak-ng</code></li>
                    <li><strong>RAM:</strong> VideoLLaMA3 cần ~4-8GB VRAM để chạy mượt</li>
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

        # AI & Audio Control Event Handlers
        def on_detection_method_change(method):
            return fall_system.set_detection_method(method)

        def on_load_model():
            return fall_system.load_videollama3_model()

        def on_unload_model():
            return fall_system.unload_videollama3_model()

        def on_test_audio():
            return fall_system.test_audio_warning()

        def on_audio_enabled_change(enabled):
            return fall_system.set_audio_enabled(enabled)

        def on_audio_volume_change(volume):
            return fall_system.set_audio_volume(volume)

        # Bind AI & Audio events
        detection_method.change(on_detection_method_change, inputs=[detection_method], outputs=[method_output])

        load_model_btn.click(on_load_model, outputs=[model_output])

        unload_model_btn.click(on_unload_model, outputs=[model_output])

        test_audio_btn.click(on_test_audio, outputs=[audio_output])

        audio_enabled.change(on_audio_enabled_change, inputs=[audio_enabled], outputs=[audio_output])

        audio_volume.change(on_audio_volume_change, inputs=[audio_volume], outputs=[audio_output])

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

        # Enhanced status update with model status checking
        def update_status_and_logs_enhanced():
            # Check for UI updates from queue
            model_status_msg = ""
            try:
                while not fall_system.ui_update_queue.empty():
                    update_type, message = fall_system.ui_update_queue.get_nowait()
                    if update_type in ["model_loaded", "model_error", "model_unloaded"]:
                        model_status_msg = message
            except:
                pass

            if fall_system.is_running:
                evidence_text, evidence_gifs = fall_system.get_evidence_gifs_display()
                if model_status_msg:
                    return (
                        fall_system.get_status_info(),
                        fall_system.get_logs_display(),
                        fall_system.get_alert_history_display(),
                        evidence_text,
                        evidence_gifs,
                        model_status_msg,
                    )
                else:
                    return (
                        fall_system.get_status_info(),
                        fall_system.get_logs_display(),
                        fall_system.get_alert_history_display(),
                        evidence_text,
                        evidence_gifs,
                        fall_system.get_model_status_message(),
                    )
            else:
                evidence_text, evidence_gifs = fall_system.get_evidence_gifs_display()
                if model_status_msg:
                    return (fall_system.get_status_info(), gr.update(), gr.update(), evidence_text, evidence_gifs, model_status_msg)
                else:
                    return (fall_system.get_status_info(), gr.update(), gr.update(), evidence_text, evidence_gifs, fall_system.get_model_status_message())

        # Set up dual auto-refresh timers using gr.Timer (Gradio 5.x)
        try:
            # Fast timer for camera feed (0.1s = 10 FPS)
            camera_timer = gr.Timer(0.1)
            camera_timer.tick(update_camera, outputs=[camera_feed])

            # Slower timer for status and logs (2s) with model status
            status_timer = gr.Timer(2.0)
            status_timer.tick(update_status_and_logs_enhanced, outputs=[status_display, logs_display, alert_display, evidence_list, evidence_gallery, model_output])

            print("✅ Enhanced dual refresh timers set up: Camera 0.1s, Status/Logs 2s with model status")

        except Exception as e:
            print(f"⚠️ Enhanced auto-refresh timers not available: {e}")
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
                            fall_system.get_model_status_message(),
                        )
                    else:
                        evidence_text, evidence_gifs = fall_system.get_evidence_gifs_display()
                        return (
                            fall_system.get_current_frame(),
                            fall_system.get_status_info(),
                            gr.update(),
                            gr.update(),
                            evidence_text,
                            evidence_gifs,
                            fall_system.get_model_status_message(),
                        )

                fallback_timer.tick(update_all, outputs=[camera_feed, status_display, logs_display, alert_display, evidence_list, evidence_gallery, model_output])
                print("⚠️ Using enhanced fallback timer: All components 1s with model status")
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
