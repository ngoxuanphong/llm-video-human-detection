#!/usr/bin/env python3
"""
Demo script to test fall detection on existing video
This analyzes the bison.mp4 file to demonstrate the system
"""

import cv2
import base64
from openai import OpenAI
import os
import dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

dotenv.load_dotenv()
console = Console()

def save_demo_frames(video_path, base64_frames):
    """Save demo frames to temp directory in various formats"""
    try:
        from datetime import datetime
        import imageio
        
        save_format = os.environ.get("SAVE_FORMAT", "images").lower()
        
        # Create temp directory
        temp_dir = "temp"
        demo_dir = os.path.join(temp_dir, f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(demo_dir, exist_ok=True)
        
        # Decode all frames first
        frame_arrays = []
        saved_files = []
        
        for i, base64_frame in enumerate(base64_frames):
            try:
                # Decode base64 to image
                import base64
                import numpy as np
                img_data = base64.b64decode(base64_frame)
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                frame_arrays.append(frame)
                
                # Save individual images if needed
                if save_format in ["images", "all"]:
                    filename = f"frame_{i+1:03d}.jpg"
                    filepath = os.path.join(demo_dir, filename)
                    cv2.imwrite(filepath, frame)
                    saved_files.append(filepath)
                    
            except Exception as e:
                console.print(f"[yellow]⚠ Không thể xử lý frame {i+1}: {e}[/yellow]")
        
        # Save as GIF if requested
        if save_format in ["gif", "all"] and len(frame_arrays) > 1:
            gif_path = os.path.join(demo_dir, "demo_analysis.gif")
            # Convert BGR to RGB for imageio
            rgb_frames = [cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) for frame in frame_arrays]
            imageio.mimsave(gif_path, rgb_frames, duration=0.1, loop=0)  # 5x faster (10 FPS)
            saved_files.append(gif_path)
            console.print(f"[green]🎞️ Đã tạo GIF: [cyan]{gif_path}[/cyan][/green]")
        
        # Save as MP4 video if requested
        if save_format in ["video", "all"] and len(frame_arrays) > 1:
            video_path_output = os.path.join(demo_dir, "demo_analysis.mp4")
            save_demo_video(frame_arrays, video_path_output, fps=10.0)  # 5x faster (10 FPS)
            saved_files.append(video_path_output)
            console.print(f"[green]🎬 Đã tạo video: [cyan]{video_path_output}[/cyan][/green]")
        
        # Save video info
        video_name = os.path.basename(video_path)
        info_file = os.path.join(demo_dir, "analysis_info.txt")
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"Demo Analysis Information\n")
            f.write(f"========================\n")
            f.write(f"Original video: {video_name}\n")
            f.write(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total frames analyzed: {len(frame_arrays)}\n")
            f.write(f"Save format: {save_format}\n")
            if save_format in ["gif", "all"]:
                f.write(f"GIF duration: {len(frame_arrays) * 0.1:.1f}s (10 FPS)\n")
            if save_format in ["video", "all"]:
                f.write(f"Video duration: {len(frame_arrays) / 10.0:.1f}s (10 FPS)\n")
            f.write(f"\nFiles saved:\n")
            for file_path in saved_files:
                f.write(f"- {os.path.basename(file_path)}\n")
        
        format_icons = {"images": "🖼️", "gif": "🎞️", "video": "🎬", "all": "📦"}
        icon = format_icons.get(save_format, "💾")
        
        console.print(f"[green]{icon} Đã lưu {len(saved_files)} file demo ({save_format}) tại: [cyan]{demo_dir}[/cyan][/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Lỗi khi lưu frames demo: {e}[/red]")

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

def analyze_video_for_falls(video_path="bison.mp4"):
    """Analyze video file for potential falls"""
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    save_frames = os.environ.get("SAVE_ANALYSIS_FRAMES", "false").lower() == "true"
    
    if not os.path.exists(video_path):
        console.print(f"[red]❌ Không tìm thấy file video {video_path}[/red]")
        return
    
    console.print(f"[blue]📹 Đang phân tích video:[/blue] [cyan]{video_path}[/cyan]")
    
    # Extract frames from video
    video = cv2.VideoCapture(video_path)
    base64_frames = []
    frame_count = 0
    
    while video.isOpened() and frame_count < 100:  # Limit frames for demo
        success, frame = video.read()
        if not success:
            break
        
        frame_count += 1
        
        # Take every 10th frame to reduce processing
        if frame_count % 10 == 0:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            base64_frame = base64.b64encode(buffer).decode("utf-8")
            base64_frames.append(base64_frame)
    
    video.release()
    console.print(f"[green]📊 Đã trích xuất {len(base64_frames)} khung hình để phân tích[/green]")
    
    if not base64_frames:
        console.print("[red]❌ Không trích xuất được khung hình từ video[/red]")
        return
    
    # Save frames if enabled
    if save_frames:
        save_demo_frames(video_path, base64_frames)
    
    # Analyze frames with OpenAI
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]🤖 Đang phân tích với AI...", total=None)
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Bạn là trợ lý AI chuyên về phân tích phát hiện té ngã. 
                        Hãy phân tích các khung hình video này và xác định xem có xảy ra té ngã của con người hay không.
                        
                        Tìm kiếm các dấu hiệu sau:
                        - Người bất ngờ thay đổi từ tư thế đứng/ngồi sang tư thế nằm ngang
                        - Chuyển động nhanh xuống dưới
                        - Người nằm trên sàn trong tình trạng khó khăn
                        - Đột ngột ngã hoặc mất thăng bằng
                        - Tình huống khẩn cấp cần sự chú ý ngay lập tức
                        
                        Cũng cung cấp mô tả tổng quát về những gì bạn thấy trong video.
                        
                        Trả lời theo định dạng này:
                        TÌNH_TRẠNG_TÉ_NGÃ: [PHÁT_HIỆN/KHÔNG_PHÁT_HIỆN]
                        MÔ_TẢ: [Những gì bạn thấy trong video]
                        PHÂN_TÍCH: [Phân tích chi tiết về các chuyển động hoặc hoạt động]"""
                    }
                ] + [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{frame}"
                        }
                    }
                    for frame in base64_frames[:8]  # Analyze first 8 frames
                ]
            }
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=400
        )
        
        analysis_result = response.choices[0].message.content.strip()
        
        # Display results in a beautiful panel
        result_panel = Panel(
            analysis_result,
            title="[bold green]🎯 KẾT QUẢ PHÂN TÍCH[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        console.print(result_panel)
        
        # Check if fall was detected
        if "TÌNH_TRẠNG_TÉ_NGÃ: PHÁT_HIỆN" in analysis_result:
            console.print("\n[red]🚨 PHÁT HIỆN TÉ NGÃ trong video![/red]")
        else:
            console.print("\n[green]✅ Không phát hiện té ngã trong video[/green]")
            
    except Exception as e:
        console.print(f"[red]❌ Lỗi trong quá trình phân tích: {e}[/red]")

def main():
    """Main demo function"""
    startup_panel = Panel(
        "[bold blue]🎬 Demo Phân Tích Video Phát Hiện Té Ngã[/bold blue]\n\n"
        "[yellow]Chương trình này sẽ phân tích video để tìm kiếm dấu hiệu té ngã[/yellow]",
        title="[bold green]DEMO SYSTEM[/bold green]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(startup_panel)
    
    # Check if OpenAI API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        console.print("[red]❌ Không tìm thấy OPENAI_API_KEY trong biến môi trường[/red]")
        console.print("[yellow]Vui lòng thiết lập file .env trước[/yellow]")
        return
    
    # Check if video file exists
    video_files = ['src/media/fall-01-cam0.mp4', 'src/media/fall-01-cam1.mp4']
    video_to_analyze = None
    
    for video_file in video_files:
        if os.path.exists(video_file):
            video_to_analyze = video_file
            break
    
    if not video_to_analyze:
        console.print("[red]❌ Không tìm thấy file video để phân tích[/red]")
        console.print("[yellow]Các tùy chọn có sẵn: bison.mp4, output.mp4[/yellow]")
        return
    
    # Run analysis
    analyze_video_for_falls(video_to_analyze)
    
    info_panel = Panel(
        "[blue]💡 Demo này cho thấy cách AI phân tích nội dung video.[/blue]\n"
        "[green]Hệ thống thời gian thực hoạt động tương tự nhưng với camera trực tiếp.[/green]",
        title="[bold cyan]THÔNG TIN[/bold cyan]",
        border_style="cyan"
    )
    console.print(info_panel)

if __name__ == "__main__":
    main() 