import asyncio
import threading
import time
from datetime import datetime

import cv2
from rich.panel import Panel
from rich.table import Table

from src import (
    EVIDENT_DIR,
    OPENAI_CLIENT,
    SAVE_ANALYSIS_FRAMES,
    SAVE_FORMAT,
    TELEGRAM_BOT,
    USE_TELE_ALERT,
    alert_services,
    console,
    logger,
)
from src.utils import frames_to_base64, prepare_messages, save_analysis_frames_to_temp


class FallDetectionSystem:
    def __init__(self):
        # Camera and detection settings
        self.camera = None
        self.is_running = False
        self.analysis_interval = 5  # seconds
        self.frame_buffer = []
        self.last_analysis_time = 0
        self.fall_detected_cooldown = 30  # seconds between fall alerts
        self.last_fall_alert = 0
        self.frame_count = 0
        self.analysis_count = 0

    def create_status_table(self):
        """Create a status table for real-time monitoring"""
        table = Table(title="[bold blue]Trạng thái hệ thống[/bold blue]")
        table.add_column("Thông số", style="cyan", no_wrap=True)
        table.add_column("Giá trị", style="green")

        # Calculate uptime
        uptime = time.strftime("%H:%M:%S", time.gmtime(time.time() - getattr(self, "start_time", time.time())))

        table.add_row("🎥 Khung hình đã xử lý", str(self.frame_count))
        table.add_row("🔍 Lần phân tích", str(self.analysis_count))
        table.add_row("📱 Telegram", "Bật" if USE_TELE_ALERT else "Tắt")
        save_status = f"Bật ({SAVE_FORMAT})" if SAVE_ANALYSIS_FRAMES else "Tắt"
        table.add_row("💾 Lưu frames", save_status)
        table.add_row("⏰ Thời gian hoạt động", uptime)
        table.add_row("🔄 Chu kỳ phân tích", f"{self.analysis_interval}s")
        table.add_row("📊 Buffer frames", str(len(self.frame_buffer)))

        return table

    def initialize_camera(self, camera_index=0):
        """Initialize camera capture"""
        try:
            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                raise Exception(f"Failed to open camera {camera_index}")

            # Set camera properties for better performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)

            logger.info("[green]✓[/green] Camera đã được khởi tạo thành công", extra={"markup": True})
            return True
        except Exception as e:
            logger.error(f"[red]✗[/red] Không thể khởi tạo camera: {e}", extra={"markup": True})
            return False

    def capture_frames(self):
        """Continuously capture frames from camera"""
        while self.is_running and self.camera:
            ret, frame = self.camera.read()
            if not ret:
                logger.warning("Không thể chụp khung hình")
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

            # Display frame
            cv2.imshow("Fall Detection System", frame)

            # Check for analysis trigger
            if current_time - self.last_analysis_time >= self.analysis_interval:
                threading.Thread(target=self.analyze_frames, daemon=True).start()
                self.last_analysis_time = current_time

            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.stop()
                break

    def analyze_frames(self):
        """Analyze recent frames for fall detection using OpenAI"""
        if not self.frame_buffer:
            return

        try:
            self.analysis_count += 1
            logger.info(f"[blue]🔍[/blue] Bắt đầu phân tích lần {self.analysis_count}...", extra={"markup": True})

            # Get recent frames
            recent_frames = self.frame_buffer.copy()

            # Save analysis frames if enabled
            if SAVE_ANALYSIS_FRAMES:
                threading.Thread(target=save_analysis_frames_to_temp, args=([recent_frames], "analysis")).start()

            base64_frames = frames_to_base64(recent_frames)

            if not base64_frames:
                return

            # Call OpenAI API
            response = OPENAI_CLIENT.chat.completions.create(model="gpt-4o-mini", messages=prepare_messages(base64_frames), max_tokens=150)

            analysis_result = response.choices[0].message.content.strip()
            logger.info(f"[green]📊[/green] Kết quả phân tích: [white]{analysis_result}[/white]", extra={"markup": True})

            # Check for fall detection (Vietnamese)
            if analysis_result.startswith("PHÁT_HIỆN_TÉ_NGÃ"):
                self.handle_fall_detection(analysis_result)

        except Exception as e:
            logger.error(f"Error during frame analysis: {e}")

    def handle_fall_detection(self, analysis_result):
        """Handle detected fall - send alerts"""
        current_time = time.time()

        # Check cooldown to prevent spam
        if current_time - self.last_fall_alert < self.fall_detected_cooldown:
            logger.info("[yellow]⏳[/yellow] Phát hiện té ngã nhưng vẫn trong thời gian chờ", extra={"markup": True})
            return

        self.last_fall_alert = current_time
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Always log to terminal with Rich formatting
        alert_panel = Panel(
            f"[bold red]🚨 PHÁT HIỆN TÉ NGÃ 🚨[/bold red]\n\n"
            f"[bold]Thời gian:[/bold] [cyan]{timestamp}[/cyan]\n"
            f"[bold]Vị trí:[/bold] [yellow]Camera Bệnh viện[/yellow]\n"
            f"[bold]Chi tiết:[/bold] [white]{analysis_result}[/white]",
            title="[bold red]CẢNH BÁO KHẨN CẤP[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
        console.print(alert_panel)
        logger.warning(f"PHÁT HIỆN TÉ NGÃ tại {timestamp}: {analysis_result}")

        # Send Telegram notification only if enabled
        if TELEGRAM_BOT and USE_TELE_ALERT:
            asyncio.create_task(alert_services.send_telegram_alert(analysis_result, timestamp, self.frame_buffer))
        else:
            logger.info("[blue]ℹ[/blue] Bỏ qua thông báo Telegram (đã tắt hoặc chưa cấu hình)", extra={"markup": True})

        # Save current frame as evidence
        if self.frame_buffer:
            threading.Thread(target=save_analysis_frames_to_temp, args=([self.frame_buffer], EVIDENT_DIR)).start()

    def start(self):
        """Start the fall detection system"""
        if not self.initialize_camera():
            return False

        self.is_running = True
        self.start_time = time.time()
        logger.info("[green]🚀[/green] Hệ thống phát hiện té ngã đã khởi động", extra={"markup": True})

        try:
            self.capture_frames()
        except KeyboardInterrupt:
            logger.info("[yellow]⚠[/yellow] Hệ thống bị ngắt bởi người dùng", extra={"markup": True})
        finally:
            self.stop()

        return True

    def stop(self):
        """Stop the fall detection system"""
        self.is_running = False

        if self.camera:
            self.camera.release()

        cv2.destroyAllWindows()
        logger.info("[red]🛑[/red] Hệ thống phát hiện té ngã đã dừng", extra={"markup": True})


def main():
    """Main function to run the fall detection system"""

    # Create startup panel
    startup_content = (
        "[bold blue]🏥 HỆ THỐNG PHÁT HIỆN TÉ NGÃ BỆNH VIỆN[/bold blue]\n\n"
        "[yellow]📋 Hướng dẫn sử dụng:[/yellow]\n"
        "• Nhấn '[bold red]q[/bold red]' trong cửa sổ camera để thoát\n"
        "• Hệ thống sẽ phân tích video mỗi 5 giây\n\n"
        "[green]⚙️ Cấu hình cần thiết trong file .env:[/green]\n"
        "• [bold]OPENAI_API_KEY[/bold] (bắt buộc)\n"
        "• [bold]USE_TELE_ALERT[/bold]=true/false (tùy chọn, mặc định: false)\n"
        "• [bold]SAVE_ANALYSIS_FRAMES[/bold]=true/false (tùy chọn, mặc định: false)\n"
        "• [bold]SAVE_FORMAT[/bold]=images/gif/video/all (tùy chọn, mặc định: images)\n"
        "• [bold]TELEGRAM_BOT_TOKEN[/bold] (bắt buộc nếu USE_TELE_ALERT=true)\n"
        "• [bold]TELEGRAM_CHAT_ID[/bold] (bắt buộc nếu USE_TELE_ALERT=true)"
    )

    startup_panel = Panel(startup_content, title="[bold green]KHỞI ĐỘNG HỆ THỐNG[/bold green]", border_style="blue", padding=(1, 2))

    console.print(startup_panel)

    system = FallDetectionSystem()
    system.start()


if __name__ == "__main__":
    main()
