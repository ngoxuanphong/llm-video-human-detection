#!/usr/bin/env python3
"""
Quick test script to demonstrate GIF and video saving features
"""

import os
import dotenv
from rich.console import Console
from rich.panel import Panel

# Load environment variables
dotenv.load_dotenv()
console = Console()

def test_gif_video_features():
    """Test the new GIF and video saving features"""
    
    console.print(Panel(
        "[bold blue]🎬 Test GIF và Video Saving Features[/bold blue]\n\n"
        "[yellow]Script này sẽ test các tính năng mới:[/yellow]\n"
        "• 🖼️ Lưu ảnh riêng lẻ\n"
        "• 🎞️ Tạo GIF animation\n"
        "• 🎬 Tạo video MP4\n"
        "• 📦 Lưu tất cả định dạng",
        title="[bold green]DEMO TEST[/bold green]",
        border_style="blue"
    ))
    
    # Test different save formats
    formats_to_test = ["images", "gif", "video", "all"]
    
    for save_format in formats_to_test:
        console.print(f"\n[cyan]🔍 Testing SAVE_FORMAT={save_format}[/cyan]")
        
        # Set environment variable
        os.environ["SAVE_ANALYSIS_FRAMES"] = "true"
        os.environ["SAVE_FORMAT"] = save_format
        
        # Import and run demo
        try:
            from src.demo_video_analysis import analyze_video_for_falls
            
            console.print(f"[green]✓[/green] Chạy demo với format: [bold]{save_format}[/bold]")
            
            # Check if video file exists
            video_files = ['src/media/bison.mp4', 'bison.mp4', 'src/media/output.mp4', 'output.mp4']
            video_to_test = None
            
            for video_file in video_files:
                if os.path.exists(video_file):
                    video_to_test = video_file
                    break
            
            if video_to_test:
                console.print(f"[blue]📹[/blue] Sử dụng video: [cyan]{video_to_test}[/cyan]")
                analyze_video_for_falls(video_to_test)
            else:
                console.print("[yellow]⚠ Không tìm thấy video test file[/yellow]")
                
        except Exception as e:
            console.print(f"[red]❌ Lỗi khi test {save_format}: {e}[/red]")
    
    # Show results
    console.print(Panel(
        "[green]✅ Test hoàn thành![/green]\n\n"
        "[yellow]Kiểm tra thư mục temp/ để xem kết quả:[/yellow]\n"
        "• Mỗi format sẽ tạo thư mục riêng\n"
        "• GIF files có thể xem trực tiếp\n"
        "• MP4 files tương thích với media players\n"
        "• Images có thể xem từng frame chi tiết",
        title="[bold green]KẾT QUẢ[/bold green]",
        border_style="green"
    ))

if __name__ == "__main__":
    test_gif_video_features() 