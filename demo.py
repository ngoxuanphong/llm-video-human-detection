import base64
import os
import threading

import cv2
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src import OPENAI_CLIENT, console
from src.utils import prepare_messages, save_analysis_frames_to_temp


def analyze_video_for_falls(video_path="src/media/fall-01-cam1.mp4"):
    """Analyze video file for potential falls"""

    if not os.path.exists(video_path):
        console.print(f"[red]❌ Không tìm thấy file video {video_path}[/red]")
        return

    console.print(f"[blue]📹 Đang phân tích video:[/blue] [cyan]{video_path}[/cyan]")

    # Extract frames from video
    video = cv2.VideoCapture(video_path)
    base64_frames = []
    recent_frames = []
    frame_count = 0

    while video.isOpened():  # Limit frames for demo
        success, frame = video.read()
        if not success:
            break

        frame_count += 1

        # Take every 10th frame to reduce processing
        recent_frames.append(frame)
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        base64_frame = base64.b64encode(buffer).decode("utf-8")
        base64_frames.append(base64_frame)

    base64_frames = base64_frames[::10]
    video.release()
    console.print(f"[green]📊 Đã trích xuất {len(base64_frames)} khung hình để phân tích[/green]")

    if not base64_frames:
        console.print("[red]❌ Không trích xuất được khung hình từ video[/red]")
        return

    # Analyze frames with OpenAI
    # try:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("[cyan]🤖 Đang phân tích với AI...", total=None)

    response = OPENAI_CLIENT.chat.completions.create(model="gpt-4o-mini", messages=prepare_messages(base64_frames), max_tokens=400)

    analysis_result = response.choices[0].message.content.strip()

    # Display results in a beautiful panel
    result_panel = Panel(analysis_result, title="[bold green]🎯 KẾT QUẢ PHÂN TÍCH[/bold green]", border_style="green", padding=(1, 2))
    console.print(result_panel)

    # Check if fall was detected
    if "PHÁT_HIỆN_TÉ_NGÃ" in analysis_result:
        console.print("\n[red]🚨 PHÁT HIỆN TÉ NGÃ trong video![/red]")
        # save_analysis_frames_to_temp(recent_frames)
        threading.Thread(target=save_analysis_frames_to_temp, args=([recent_frames])).start()
    else:
        console.print("\n[green]✅ Không phát hiện té ngã trong video[/green]")

    # except Exception as e:
    #     console.print(f"[red]❌ Lỗi trong quá trình phân tích: {e}[/red]")


def main():
    """Main demo function"""
    startup_panel = Panel(
        "[bold blue]🎬 Demo Phân Tích Video Phát Hiện Té Ngã[/bold blue]", title="[bold green]DEMO SYSTEM[/bold green]", border_style="blue", padding=(1, 2)
    )
    console.print(startup_panel)

    # Check if OpenAI API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        console.print("[red]❌ Không tìm thấy OPENAI_API_KEY trong biến môi trường[/red]")
        console.print("[yellow]Vui lòng thiết lập file .env trước[/yellow]")
        return

    # Check if video file exists
    video_files = ["media/fall-01-cam0.mp4"]
    video_to_analyze = None

    for video_file in video_files:
        if os.path.exists(video_file):
            video_to_analyze = video_file
            break

    if not video_to_analyze:
        console.print("[red]❌ Không tìm thấy file video để phân tích[/red]")
        console.print("[yellow]Các tùy chọn có sẵn: media/fall-01-cam0.mp4[/yellow]")
        return

    # Run analysis
    analyze_video_for_falls(video_to_analyze)


if __name__ == "__main__":
    main()
