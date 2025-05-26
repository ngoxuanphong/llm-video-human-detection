import cv2
import base64
import threading
import time
import asyncio
import logging
from datetime import datetime
from openai import OpenAI
import os
import dotenv
import numpy as np
from telegram import Bot
from telegram.ext import Application
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich import print as rprint

# Load environment variables
dotenv.load_dotenv()

# Configure Rich console and logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

class FallDetectionSystem:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Check if Telegram alerts are enabled
        self.use_tele_alert = os.environ.get("USE_TELE_ALERT", "false").lower() == "true"
        self.telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        # Check if frame saving is enabled
        self.save_analysis_frames = os.environ.get("SAVE_ANALYSIS_FRAMES", "false").lower() == "true"
        self.save_format = os.environ.get("SAVE_FORMAT", "images").lower()
        
        # Initialize Telegram bot only if enabled and credentials available
        if self.use_tele_alert and self.telegram_token and self.telegram_chat_id:
            self.telegram_bot = Bot(token=self.telegram_token)
            logger.info("[green]✓[/green] Thông báo Telegram đã được bật", extra={"markup": True})
        else:
            self.telegram_bot = None
            if not self.use_tele_alert:
                logger.info("[yellow]ℹ[/yellow] Thông báo Telegram đã tắt theo cấu hình", extra={"markup": True})
            else:
                logger.warning("[red]⚠[/red] Không tìm thấy thông tin đăng nhập Telegram. Thông báo Telegram đã tắt.", extra={"markup": True})
        
        # Log frame saving status
        if self.save_analysis_frames:
            format_icon = {"images": "🖼️", "gif": "🎞️", "video": "🎬", "all": "📦"}.get(self.save_format, "💾")
            logger.info(f"[green]{format_icon}[/green] Lưu khung hình phân tích đã được bật - Format: [cyan]{self.save_format}[/cyan]", extra={"markup": True})
        else:
            logger.info("[blue]ℹ[/blue] Lưu khung hình phân tích đã tắt theo cấu hình", extra={"markup": True})
        
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
        uptime = time.strftime("%H:%M:%S", time.gmtime(time.time() - getattr(self, 'start_time', time.time())))
        
        table.add_row("🎥 Khung hình đã xử lý", str(self.frame_count))
        table.add_row("🔍 Lần phân tích", str(self.analysis_count))
        table.add_row("📱 Telegram", "Bật" if self.use_tele_alert else "Tắt")
        save_status = f"Bật ({self.save_format})" if self.save_analysis_frames else "Tắt"
        table.add_row("💾 Lưu frames", save_status)
        table.add_row("⏰ Thời gian hoạt động", uptime)
        table.add_row("🔄 Chu kỳ phân tích", f"{self.analysis_interval}s")
        table.add_row("📊 Buffer frames", str(len(self.frame_buffer)))
        
        return table
    
    def save_analysis_frames_to_temp(self, frames, analysis_count):
        """Save frames that were sent to LLM for analysis in various formats"""
        if not self.save_analysis_frames or not frames:
            return
        
        try:
            import imageio
            
            # Create temp directory structure
            temp_dir = "temp"
            analysis_dir = os.path.join(temp_dir, f"analysis_{analysis_count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(analysis_dir, exist_ok=True)
            
            # Extract frames as numpy arrays
            frame_arrays = []
            saved_files = []
            step = max(1, len(frames) // 20)
            
            for i, frame_data in enumerate(frames[::step]):
                frame = frame_data['frame']
                timestamp = frame_data['timestamp']
                frame_arrays.append(frame)
                
                # Save individual images if needed
                if self.save_format in ["images", "all"]:
                    filename = f"frame_{i+1:03d}_{datetime.fromtimestamp(timestamp).strftime('%H%M%S_%f')[:-3]}.jpg"
                    filepath = os.path.join(analysis_dir, filename)
                    cv2.imwrite(filepath, frame)
                    saved_files.append(filepath)
            
            # Save as GIF if requested
            if self.save_format in ["gif", "all"] and len(frame_arrays) > 1:
                gif_path = os.path.join(analysis_dir, f"analysis_{analysis_count}.gif")
                # Convert BGR to RGB for imageio
                rgb_frames = [cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) for frame in frame_arrays]
                imageio.mimsave(gif_path, rgb_frames, duration=0.1, loop=0)  # 5x faster (0.1s per frame = 10 FPS)
                saved_files.append(gif_path)
                logger.info(f"[green]🎞️[/green] Đã tạo GIF: [cyan]{gif_path}[/cyan]", extra={"markup": True})
            
            # Save as MP4 video if requested
            if self.save_format in ["video", "all"] and len(frame_arrays) > 1:
                video_path = os.path.join(analysis_dir, f"analysis_{analysis_count}.mp4")
                self.save_frames_as_video(frame_arrays, video_path, fps=10.0)  # 5x faster (10 FPS)
                saved_files.append(video_path)
                logger.info(f"[green]🎬[/green] Đã tạo video: [cyan]{video_path}[/cyan]", extra={"markup": True})
            
            # Create info file with analysis details
            info_path = os.path.join(analysis_dir, "analysis_info.txt")
            with open(info_path, 'w', encoding='utf-8') as f:
                f.write(f"Fall Detection Analysis #{analysis_count}\n")
                f.write(f"{'='*40}\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total frames: {len(frame_arrays)}\n")
                f.write(f"Save format: {self.save_format}\n")
                f.write(f"Frame rate: {1/self.analysis_interval:.2f} FPS\n")
                f.write(f"Analysis interval: {self.analysis_interval}s\n")
                if self.save_format in ["gif", "all"]:
                    f.write(f"GIF duration: {len(frame_arrays) * 0.1:.1f}s (10 FPS)\n")
                if self.save_format in ["video", "all"]:
                    f.write(f"Video duration: {len(frame_arrays) / 10.0:.1f}s (10 FPS)\n")
                f.write(f"\nFiles saved:\n")
                for file_path in saved_files:
                    f.write(f"- {os.path.basename(file_path)}\n")
            
            format_icons = {"images": "🖼️", "gif": "🎞️", "video": "🎬", "all": "📦"}
            icon = format_icons.get(self.save_format, "💾")
            
            if self.save_format == "images":
                logger.info(f"[green]{icon}[/green] Đã lưu {len(frame_arrays)} khung hình tại: [cyan]{analysis_dir}[/cyan]", extra={"markup": True})
            else:
                logger.info(f"[green]{icon}[/green] Đã lưu {len(saved_files)} file ({self.save_format}) tại: [cyan]{analysis_dir}[/cyan]", extra={"markup": True})
            
        except Exception as e:
            logger.error(f"[red]✗[/red] Không thể lưu khung hình phân tích: {e}", extra={"markup": True})
    
    def save_frames_as_video(self, frames, output_path, fps=10.0):
        """Save frames as MP4 video using OpenCV"""
        try:
            if not frames:
                return
            
            height, width, layers = frames[0].shape
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            for frame in frames:
                video_writer.write(frame)
            
            video_writer.release()
            
        except Exception as e:
            logger.error(f"[red]✗[/red] Không thể tạo video: {e}", extra={"markup": True})
    
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
            self.frame_buffer.append({
                'frame': frame,
                'timestamp': current_time
            })
            
            # Keep only recent frames (last 10 seconds)
            self.frame_buffer = [f for f in self.frame_buffer if current_time - f['timestamp'] < 10]
            
            # Display frame
            cv2.imshow('Fall Detection System', frame)
            
            # Check for analysis trigger
            if current_time - self.last_analysis_time >= self.analysis_interval:
                threading.Thread(target=self.analyze_frames, daemon=True).start()
                self.last_analysis_time = current_time
            
            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop()
                break
    
    def frames_to_base64(self, frames, max_frames=5):
        """Convert frames to base64 for OpenAI API"""
        base64_frames = []
        step = max(1, len(frames) // max_frames)
        
        for i in range(0, len(frames), step):
            if len(base64_frames) >= max_frames:
                break
            
            frame = frames[i]['frame']
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            base64_frame = base64.b64encode(buffer).decode("utf-8")
            base64_frames.append(base64_frame)
        
        return base64_frames
    
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
            # self.save_analysis_frames_to_temp(recent_frames, self.analysis_count)
            threading.Thread(target=self.save_analysis_frames_to_temp, args=(recent_frames, self.analysis_count)).start()
            
            base64_frames = self.frames_to_base64(recent_frames)
            
            print('--------------------------------', len(base64_frames))
            
            if not base64_frames:
                return
            
            # Prepare messages for OpenAI API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Bạn là trợ lý AI chuyên về phát hiện té ngã trong môi trường bệnh viện. 
                            Hãy phân tích các khung hình video này và xác định xem có xảy ra té ngã của con người hay không.
                            
                            Tìm kiếm các dấu hiệu sau:
                            - Người bất ngờ thay đổi từ tư thế đứng/ngồi sang tư thế nằm ngang
                            - Chuyển động nhanh xuống dưới
                            - Người nằm trên sàn trong tình trạng khó khăn
                            - Đột ngột ngã hoặc mất thăng bằng
                            - Tình huống khẩn cấp cần sự chú ý ngay lập tức
                            
                            Chỉ trả lời theo một trong hai định dạng sau:
                            "PHÁT_HIỆN_TÉ_NGÃ: [mô tả ngắn gọn về những gì bạn thấy]"
                            "KHÔNG_TÉ_NGÃ: [mô tả ngắn gọn về hoạt động bình thường]"
                            
                            Hãy rất cẩn thận để tránh báo động giả - chỉ báo cáo PHÁT_HIỆN_TÉ_NGÃ khi bạn chắc chắn rằng đã xảy ra té ngã."""
                        }
                    ] + [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{frame}"
                            }
                        }
                        for frame in base64_frames
                    ]
                }
            ]
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=150
            )
            
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
            padding=(1, 2)
        )
        console.print(alert_panel)
        logger.warning(f"PHÁT HIỆN TÉ NGÃ tại {timestamp}: {analysis_result}")
        
        # Send Telegram notification only if enabled
        if self.telegram_bot and self.use_tele_alert:
            asyncio.create_task(self.send_telegram_alert(analysis_result, timestamp))
        else:
            logger.info("[blue]ℹ[/blue] Bỏ qua thông báo Telegram (đã tắt hoặc chưa cấu hình)", extra={"markup": True})
        
        # Save current frame as evidence
        if self.frame_buffer:
            self.save_evidence_frame(timestamp)
    
    async def send_telegram_alert(self, analysis_result, timestamp):
        """Send Telegram notification about fall detection"""
        if not self.telegram_bot or not self.use_tele_alert:
            logger.info("Telegram notification skipped")
            return
        
        try:
            message = f"🚨 PHÁT HIỆN TÉ NGÃ 🚨\n\n"
            message += f"Thời gian: {timestamp}\n"
            message += f"Vị trí: Camera Bệnh viện\n"
            message += f"Chi tiết: {analysis_result}\n\n"
            message += "Vui lòng kiểm tra ngay lập tức!"
            
            await self.telegram_bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message
            )
            
            # Send evidence image if available
            if self.frame_buffer:
                latest_frame = self.frame_buffer[-1]['frame']
                _, buffer = cv2.imencode('.jpg', latest_frame)
                
                await self.telegram_bot.send_photo(
                    chat_id=self.telegram_chat_id,
                    photo=buffer.tobytes(),
                    caption=f"Hình ảnh bằng chứng - {timestamp}"
                )
            
            logger.info("[green]✓[/green] Thông báo Telegram đã gửi thành công", extra={"markup": True})
            
        except Exception as e:
            logger.error(f"Không thể gửi thông báo Telegram: {e}")
    
    def save_evidence_frame(self, timestamp):
        """Save frame as evidence when fall is detected"""
        try:
            if not self.frame_buffer:
                return
            
            # Create evidence directory
            os.makedirs("evidence", exist_ok=True)
            
            # Save latest frame
            latest_frame = self.frame_buffer[-1]['frame']
            filename = f"evidence/fall_detected_{timestamp.replace(':', '-').replace(' ', '_')}.jpg"
            cv2.imwrite(filename, latest_frame)
            
            logger.info(f"[green]💾[/green] Khung hình bằng chứng đã lưu: [cyan]{filename}[/cyan]", extra={"markup": True})
            
        except Exception as e:
            logger.error(f"Không thể lưu khung hình bằng chứng: {e}")
    
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
    
    startup_panel = Panel(
        startup_content,
        title="[bold green]KHỞI ĐỘNG HỆ THỐNG[/bold green]",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(startup_panel)
    
    system = FallDetectionSystem()
    system.start()

if __name__ == "__main__":
    main() 