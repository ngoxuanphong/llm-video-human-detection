from src import console
import cv2
from src import logger, TEMP_DIR, SAVE_FORMAT, MAX_FRAMES
import os
from datetime import datetime

def prepare_messages(base64_frames: list[str]) -> list[dict]:
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
    return messages

def save_demo_video(frames, output_path, fps=10.0):
    """Save demo frames as MP4 video"""
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
        console.print(f"[red]❌ Không thể tạo demo video: {e}[/red]")
        
        
def save_analysis_frames_to_temp(frames):
    # """Save frames that were sent to LLM for analysis in various formats"""
    # if not frames:
    #     return
    
    # try:
        import imageio
        
        analysis_dir = os.path.join(TEMP_DIR, f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(analysis_dir, exist_ok=True)
        
        # Extract frames as numpy arrays
        frame_arrays = []
        saved_files = []
        step = max(1, len(frames) // 20)
        
        for i, frame_data in enumerate(frames[::step]):
            if isinstance(frame_data, dict):
                frame = frame_data['frame']
            else:
                frame = frame_data
            frame_arrays.append(frame)
        
        # Save as GIF if requested
        if SAVE_FORMAT in ["gif", "all"] and len(frame_arrays) > 1:
            gif_path = os.path.join(analysis_dir, f"analysis.gif")
            # Convert BGR to RGB for imageio
            rgb_frames = [cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) for frame in frame_arrays]
            imageio.mimsave(gif_path, rgb_frames, duration=0.1, loop=0)  # 5x faster (0.1s per frame = 10 FPS)
            saved_files.append(gif_path)
            logger.info(f"[green]🎞️[/green] Đã tạo GIF: [cyan]{gif_path}[/cyan]", extra={"markup": True})
        
        # Save as MP4 video if requested
        if SAVE_FORMAT in ["video", "all"] and len(frame_arrays) > 1:
            video_path = os.path.join(analysis_dir, f"analysis.mp4")
            save_demo_video(frame_arrays, video_path, fps=10.0)  # 5x faster (10 FPS)
            saved_files.append(video_path)
            logger.info(f"[green]🎬[/green] Đã tạo video: [cyan]{video_path}[/cyan]", extra={"markup": True})
        
        # Create info file with analysis details
        info_path = os.path.join(analysis_dir, "analysis_info.txt")
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(f"Fall Detection Analysis \n")
            f.write(f"{'='*40}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total frames: {len(frame_arrays)}\n")
            f.write(f"Save format: {SAVE_FORMAT}\n")
            if SAVE_FORMAT in ["gif", "all"]:
                f.write(f"GIF duration: {len(frame_arrays) * 0.1:.1f}s (10 FPS)\n")
            if SAVE_FORMAT in ["video", "all"]:
                f.write(f"Video duration: {len(frame_arrays) / 10.0:.1f}s (10 FPS)\n")
            f.write(f"\nFiles saved:\n")
            for file_path in saved_files:
                f.write(f"- {os.path.basename(file_path)}\n")
        
        format_icons = {"images": "🖼️", "gif": "🎞️", "video": "🎬", "all": "📦"}
        icon = format_icons.get(SAVE_FORMAT, "💾")
        
        if SAVE_FORMAT == "images":
            logger.info(f"[green]{icon}[/green] Đã lưu {len(frame_arrays)} khung hình tại: [cyan]{analysis_dir}[/cyan]", extra={"markup": True})
        else:
            logger.info(f"[green]{icon}[/green] Đã lưu {len(saved_files)} file ({SAVE_FORMAT}) tại: [cyan]{analysis_dir}[/cyan]", extra={"markup": True})
        
    # except Exception as e:
    #     logger.error(f"[red]✗[/red] Không thể lưu khung hình phân tích: {e}", extra={"markup": True})

import base64

def frames_to_base64(frames, max_frames=MAX_FRAMES):
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