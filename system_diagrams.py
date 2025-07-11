import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

# Thiết lập font tiếng Việt
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

def create_system_overview():
    """Tạo sơ đồ tổng quan hệ thống"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Màu sắc
    colors = {
        'camera': '#FF6B6B',
        'processing': '#4ECDC4', 
        'ai': '#45B7D1',
        'alert': '#96CEB4',
        'storage': '#FFEAA7',
        'ui': '#DDA0DD'
    }
    
    # Camera
    camera_box = FancyBboxPatch((1, 9), 3, 2, boxstyle="round,pad=0.1", 
                               facecolor=colors['camera'], edgecolor='black', linewidth=2)
    ax.add_patch(camera_box)
    ax.text(2.5, 10, '📹 Camera\nBệnh viện', ha='center', va='center', fontsize=12, weight='bold')
    
    # Frame Buffer
    buffer_box = FancyBboxPatch((6, 9), 3, 2, boxstyle="round,pad=0.1",
                               facecolor=colors['processing'], edgecolor='black', linewidth=2)
    ax.add_patch(buffer_box)
    ax.text(7.5, 10, '🔄 Frame Buffer\n(10 giây)', ha='center', va='center', fontsize=12, weight='bold')
    
    # SmolVLM Analysis
    ai_box = FancyBboxPatch((11, 9), 3, 2, boxstyle="round,pad=0.1",
                            facecolor=colors['ai'], edgecolor='black', linewidth=2)
    ax.add_patch(ai_box)
    ax.text(12.5, 10, '🤖 SmolVLM\nPhân tích', ha='center', va='center', fontsize=12, weight='bold')
    
    # Fall Detection Logic
    logic_box = FancyBboxPatch((6, 6), 4, 2, boxstyle="round,pad=0.1",
                               facecolor=colors['processing'], edgecolor='black', linewidth=2)
    ax.add_patch(logic_box)
    ax.text(8, 7, '🧠 Logic Phát hiện\nTé ngã', ha='center', va='center', fontsize=12, weight='bold')
    
    # Alert System
    alert_box = FancyBboxPatch((1, 6), 3, 2, boxstyle="round,pad=0.1",
                               facecolor=colors['alert'], edgecolor='black', linewidth=2)
    ax.add_patch(alert_box)
    ax.text(2.5, 7, '🚨 Hệ thống\nCảnh báo', ha='center', va='center', fontsize=12, weight='bold')
    
    # Storage
    storage_box = FancyBboxPatch((11, 6), 3, 2, boxstyle="round,pad=0.1",
                                 facecolor=colors['storage'], edgecolor='black', linewidth=2)
    ax.add_patch(storage_box)
    ax.text(12.5, 7, '💾 Lưu trữ\nBằng chứng', ha='center', va='center', fontsize=12, weight='bold')
    
    # Web UI
    ui_box = FancyBboxPatch((6, 3), 4, 2, boxstyle="round,pad=0.1",
                            facecolor=colors['ui'], edgecolor='black', linewidth=2)
    ax.add_patch(ui_box)
    ax.text(8, 4, '🌐 Web UI\nGiao diện', ha='center', va='center', fontsize=12, weight='bold')
    
    # Console UI
    console_box = FancyBboxPatch((1, 3), 3, 2, boxstyle="round,pad=0.1",
                                 facecolor=colors['ui'], edgecolor='black', linewidth=2)
    ax.add_patch(console_box)
    ax.text(2.5, 4, '🖥️ Console\nTerminal', ha='center', va='center', fontsize=12, weight='bold')
    
    # Telegram
    telegram_box = FancyBboxPatch((11, 3), 3, 2, boxstyle="round,pad=0.1",
                                  facecolor=colors['alert'], edgecolor='black', linewidth=2)
    ax.add_patch(telegram_box)
    ax.text(12.5, 4, '📱 Telegram\nThông báo', ha='center', va='center', fontsize=12, weight='bold')
    
    # Vẽ các mũi tên kết nối
    arrows = [
        ((2.5, 9), (6, 9.5)),  # Camera -> Buffer
        ((7.5, 9), (8, 8)),    # Buffer -> Logic
        ((12.5, 9), (8, 8)),   # AI -> Logic
        ((8, 6), (2.5, 6.5)),  # Logic -> Alert
        ((8, 6), (12.5, 6.5)), # Logic -> Storage
        ((2.5, 4), (8, 4)),    # Console -> Web UI
        ((8, 4), (12.5, 4)),   # Web UI -> Telegram
    ]
    
    for start, end in arrows:
        arrow = ConnectionPatch(start, end, "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=20, fc="black", ec="black", linewidth=2)
        ax.add_patch(arrow)
    
    # Tiêu đề
    ax.text(8, 11.5, '🏥 HỆ THỐNG PHÁT HIỆN TÉ NGÃ BỆNH VIỆN', 
            ha='center', va='center', fontsize=16, weight='bold')
    
    plt.tight_layout()
    plt.savefig('system_overview.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_directory_structure():
    """Tạo sơ đồ cấu trúc thư mục"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Màu sắc
    colors = {
        'root': '#FF6B6B',
        'src': '#4ECDC4',
        'file': '#45B7D1',
        'config': '#96CEB4',
        'docs': '#FFEAA7'
    }
    
    # Root directory
    root_box = FancyBboxPatch((0.5, 8.5), 3, 1, boxstyle="round,pad=0.1",
                              facecolor=colors['root'], edgecolor='black', linewidth=2)
    ax.add_patch(root_box)
    ax.text(2, 9, '📁 video_understanding/', ha='center', va='center', fontsize=12, weight='bold')
    
    # Main files
    main_files = [
        (0.5, 7.5, 'main.py', 'Hệ thống chính'),
        (2.5, 7.5, 'main_ui.py', 'Web UI'),
        (4.5, 7.5, 'start_web_ui.py', 'Khởi động Web UI'),
        (6.5, 7.5, 'demo.py', 'Demo'),
        (8.5, 7.5, 'requirements.txt', 'Dependencies'),
        (10.5, 7.5, '.env', 'Cấu hình'),
        (12.5, 7.5, 'README.md', 'Tài liệu')
    ]
    
    for x, y, name, desc in main_files:
        file_box = FancyBboxPatch((x, y), 1.5, 0.8, boxstyle="round,pad=0.05",
                                 facecolor=colors['file'], edgecolor='black', linewidth=1)
        ax.add_patch(file_box)
        ax.text(x + 0.75, y + 0.4, f'{name}\n{desc}', ha='center', va='center', fontsize=8)
    
    # src directory
    src_box = FancyBboxPatch((0.5, 6), 3, 1, boxstyle="round,pad=0.1",
                             facecolor=colors['src'], edgecolor='black', linewidth=2)
    ax.add_patch(src_box)
    ax.text(2, 6.5, '📁 src/', ha='center', va='center', fontsize=12, weight='bold')
    
    # src files
    src_files = [
        (0.5, 5, '__init__.py', 'Cấu hình'),
        (2.5, 5, 'utils.py', 'Tiện ích'),
        (4.5, 5, 'alert_services.py', 'Thông báo'),
        (6.5, 5, 'audio_warning.py', 'Cảnh báo âm thanh'),
        (8.5, 5, 'videollama_detector.py', 'SmolVLM'),
        (10.5, 5, 'setup.py', 'Thiết lập'),
        (12.5, 5, 'test_system.py', 'Kiểm tra')
    ]
    
    for x, y, name, desc in src_files:
        file_box = FancyBboxPatch((x, y), 1.5, 0.8, boxstyle="round,pad=0.05",
                                 facecolor=colors['file'], edgecolor='black', linewidth=1)
        ax.add_patch(file_box)
        ax.text(x + 0.75, y + 0.4, f'{name}\n{desc}', ha='center', va='center', fontsize=8)
    
    # Directories
    dirs = [
        (0.5, 3.5, '📁 test/', 'Kiểm thử'),
        (2.5, 3.5, '📁 media/', 'Phương tiện'),
        (4.5, 3.5, '📁 temp/', 'Tạm thời'),
        (6.5, 3.5, '📁 evidence_gifs/', 'Bằng chứng'),
        (8.5, 3.5, '📁 .gradio/', 'Gradio cache'),
        (10.5, 3.5, '📁 .git/', 'Git'),
    ]
    
    for x, y, name, desc in dirs:
        dir_box = FancyBboxPatch((x, y), 1.5, 0.8, boxstyle="round,pad=0.05",
                                facecolor=colors['config'], edgecolor='black', linewidth=1)
        ax.add_patch(dir_box)
        ax.text(x + 0.75, y + 0.4, f'{name}\n{desc}', ha='center', va='center', fontsize=8)
    
    # Vẽ các mũi tên kết nối
    arrows = [
        ((2, 8.5), (2, 7.5)),  # Root -> main files
        ((2, 6), (2, 5)),       # src -> src files
        ((2, 8.5), (2, 6)),     # Root -> src
    ]
    
    for start, end in arrows:
        arrow = ConnectionPatch(start, end, "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=15, fc="black", ec="black", linewidth=1.5)
        ax.add_patch(arrow)
    
    # Tiêu đề
    ax.text(7, 9.5, '📂 CẤU TRÚC THƯ MỤC HỆ THỐNG', 
            ha='center', va='center', fontsize=16, weight='bold')
    
    plt.tight_layout()
    plt.savefig('directory_structure.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_module_diagrams():
    """Tạo sơ đồ cho từng module chính"""
    
    # 1. Main System Module
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # Main System
    main_box = FancyBboxPatch((4, 6), 4, 1.5, boxstyle="round,pad=0.1",
                              facecolor='#FF6B6B', edgecolor='black', linewidth=2)
    ax.add_patch(main_box)
    ax.text(6, 6.75, 'main.py\nHệ thống chính', ha='center', va='center', fontsize=12, weight='bold')
    
    # Methods
    methods = [
        (1, 4.5, '__init__()', 'Khởi tạo'),
        (3, 4.5, 'initialize_camera()', 'Camera'),
        (5, 4.5, 'capture_frames()', 'Chụp khung hình'),
        (7, 4.5, 'analyze_frames()', 'Phân tích'),
        (9, 4.5, 'handle_fall_detection()', 'Xử lý té ngã'),
        (1, 3, 'start()', 'Khởi động'),
        (3, 3, 'stop()', 'Dừng'),
        (5, 3, 'create_status_table()', 'Bảng trạng thái'),
    ]
    
    for x, y, name, desc in methods:
        method_box = FancyBboxPatch((x, y), 1.8, 0.8, boxstyle="round,pad=0.05",
                                   facecolor='#4ECDC4', edgecolor='black', linewidth=1)
        ax.add_patch(method_box)
        ax.text(x + 0.9, y + 0.4, f'{name}\n{desc}', ha='center', va='center', fontsize=8)
    
    # Properties
    props = [
        (1, 1.5, 'camera', 'Camera object'),
        (3, 1.5, 'is_running', 'Trạng thái'),
        (5, 1.5, 'frame_buffer', 'Buffer khung hình'),
        (7, 1.5, 'analysis_interval', 'Chu kỳ phân tích'),
        (9, 1.5, 'fall_detected_cooldown', 'Thời gian chờ'),
    ]
    
    for x, y, name, desc in props:
        prop_box = FancyBboxPatch((x, y), 1.8, 0.8, boxstyle="round,pad=0.05",
                                 facecolor='#45B7D1', edgecolor='black', linewidth=1)
        ax.add_patch(prop_box)
        ax.text(x + 0.9, y + 0.4, f'{name}\n{desc}', ha='center', va='center', fontsize=8)
    
    # Tiêu đề
    ax.text(6, 7.5, '🔧 MODULE MAIN.PY', ha='center', va='center', fontsize=14, weight='bold')
    
    plt.tight_layout()
    plt.savefig('main_module.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. SmolVLM Detector Module
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # SmolVLM Detector
    detector_box = FancyBboxPatch((4, 6), 4, 1.5, boxstyle="round,pad=0.1",
                                  facecolor='#96CEB4', edgecolor='black', linewidth=2)
    ax.add_patch(detector_box)
    ax.text(6, 6.75, 'videollama_detector.py\nSmolVLM Detector', ha='center', va='center', fontsize=12, weight='bold')
    
    # Methods
    methods = [
        (1, 4.5, '__init__()', 'Khởi tạo'),
        (3, 4.5, 'load_model()', 'Tải model'),
        (5, 4.5, 'unload_model()', 'Dỡ model'),
        (7, 4.5, 'get_video_description()', 'Mô tả video'),
        (9, 4.5, 'analyze_frames()', 'Phân tích'),
        (1, 3, 'create_video_file_from_frames()', 'Tạo video'),
        (3, 3, 'translate_to_vietnamese_analysis()', 'Phân tích tiếng Việt'),
        (5, 3, 'get_model_status()', 'Trạng thái model'),
    ]
    
    for x, y, name, desc in methods:
        method_box = FancyBboxPatch((x, y), 1.8, 0.8, boxstyle="round,pad=0.05",
                                   facecolor='#4ECDC4', edgecolor='black', linewidth=1)
        ax.add_patch(method_box)
        ax.text(x + 0.9, y + 0.4, f'{name}\n{desc}', ha='center', va='center', fontsize=8)
    
    # Properties
    props = [
        (1, 1.5, 'model', 'SmolVLM model'),
        (3, 1.5, 'processor', 'Video processor'),
        (5, 1.5, 'is_loaded', 'Trạng thái tải'),
        (7, 1.5, 'device', 'Thiết bị (CPU/GPU)'),
        (9, 1.5, 'openai_client', 'OpenAI client'),
    ]
    
    for x, y, name, desc in props:
        prop_box = FancyBboxPatch((x, y), 1.8, 0.8, boxstyle="round,pad=0.05",
                                 facecolor='#45B7D1', edgecolor='black', linewidth=1)
        ax.add_patch(prop_box)
        ax.text(x + 0.9, y + 0.4, f'{name}\n{desc}', ha='center', va='center', fontsize=8)
    
    # Tiêu đề
    ax.text(6, 7.5, '🤖 MODULE SMOLVLM DETECTOR', ha='center', va='center', fontsize=14, weight='bold')
    
    plt.tight_layout()
    plt.savefig('smolvlm_module.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Alert Services Module
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # Alert Services
    alert_box = FancyBboxPatch((4, 6), 4, 1.5, boxstyle="round,pad=0.1",
                               facecolor='#FFEAA7', edgecolor='black', linewidth=2)
    ax.add_patch(alert_box)
    ax.text(6, 6.75, 'alert_services.py\nDịch vụ cảnh báo', ha='center', va='center', fontsize=12, weight='bold')
    
    # Methods
    methods = [
        (1, 4.5, 'send_telegram_alert()', 'Gửi Telegram'),
        (3, 4.5, 'send_email_alert()', 'Gửi Email'),
        (5, 4.5, 'send_sms_alert()', 'Gửi SMS'),
        (7, 4.5, 'log_alert()', 'Ghi log'),
        (9, 4.5, 'save_evidence()', 'Lưu bằng chứng'),
    ]
    
    for x, y, name, desc in methods:
        method_box = FancyBboxPatch((x, y), 1.8, 0.8, boxstyle="round,pad=0.05",
                                   facecolor='#4ECDC4', edgecolor='black', linewidth=1)
        ax.add_patch(method_box)
        ax.text(x + 0.9, y + 0.4, f'{name}\n{desc}', ha='center', va='center', fontsize=8)
    
    # External Services
    services = [
        (1, 3, '📱 Telegram Bot', 'Thông báo tức thì'),
        (3, 3, '📧 Email Server', 'Thông báo email'),
        (5, 3, '📞 SMS Gateway', 'Thông báo SMS'),
        (7, 3, '💾 File System', 'Lưu trữ bằng chứng'),
        (9, 3, '📝 Log System', 'Ghi log hệ thống'),
    ]
    
    for x, y, name, desc in services:
        service_box = FancyBboxPatch((x, y), 1.8, 0.8, boxstyle="round,pad=0.05",
                                    facecolor='#DDA0DD', edgecolor='black', linewidth=1)
        ax.add_patch(service_box)
        ax.text(x + 0.9, y + 0.4, f'{name}\n{desc}', ha='center', va='center', fontsize=8)
    
    # Tiêu đề
    ax.text(6, 7.5, '🚨 MODULE ALERT SERVICES', ha='center', va='center', fontsize=14, weight='bold')
    
    plt.tight_layout()
    plt.savefig('alert_module.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_data_flow():
    """Tạo sơ đồ luồng dữ liệu"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Màu sắc
    colors = {
        'input': '#FF6B6B',
        'process': '#4ECDC4',
        'ai': '#45B7D1',
        'output': '#96CEB4',
        'storage': '#FFEAA7'
    }
    
    # Input
    input_box = FancyBboxPatch((1, 8), 2, 1, boxstyle="round,pad=0.1",
                               facecolor=colors['input'], edgecolor='black', linewidth=2)
    ax.add_patch(input_box)
    ax.text(2, 8.5, '📹 Camera\nInput', ha='center', va='center', fontsize=10, weight='bold')
    
    # Frame Processing
    process1_box = FancyBboxPatch((4, 8), 2, 1, boxstyle="round,pad=0.1",
                                  facecolor=colors['process'], edgecolor='black', linewidth=2)
    ax.add_patch(process1_box)
    ax.text(5, 8.5, '🔄 Frame\nProcessing', ha='center', va='center', fontsize=10, weight='bold')
    
    # Buffer
    buffer_box = FancyBboxPatch((7, 8), 2, 1, boxstyle="round,pad=0.1",
                                facecolor=colors['storage'], edgecolor='black', linewidth=2)
    ax.add_patch(buffer_box)
    ax.text(8, 8.5, '📦 Frame\nBuffer', ha='center', va='center', fontsize=10, weight='bold')
    
    # SmolVLM Analysis
    ai_box = FancyBboxPatch((10, 8), 2, 1, boxstyle="round,pad=0.1",
                            facecolor=colors['ai'], edgecolor='black', linewidth=2)
    ax.add_patch(ai_box)
    ax.text(11, 8.5, '🤖 SmolVLM\nAnalysis', ha='center', va='center', fontsize=10, weight='bold')
    
    # Decision
    decision_box = FancyBboxPatch((13, 8), 2, 1, boxstyle="round,pad=0.1",
                                 facecolor=colors['process'], edgecolor='black', linewidth=2)
    ax.add_patch(decision_box)
    ax.text(14, 8.5, '🧠 Fall\nDecision', ha='center', va='center', fontsize=10, weight='bold')
    
    # Outputs
    outputs = [
        (2, 6, '🚨 Alert\nSystem', colors['output']),
        (5, 6, '💾 Evidence\nStorage', colors['storage']),
        (8, 6, '📱 Telegram\nNotification', colors['output']),
        (11, 6, '🖥️ Console\nLog', colors['output']),
        (14, 6, '🌐 Web UI\nUpdate', colors['output'])
    ]
    
    for x, y, name, color in outputs:
        output_box = FancyBboxPatch((x-1, y), 2, 1, boxstyle="round,pad=0.1",
                                   facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(output_box)
        ax.text(x, y + 0.5, name, ha='center', va='center', fontsize=10, weight='bold')
    
    # Data flow arrows
    arrows = [
        ((2, 8), (4, 8.5)),    # Camera -> Processing
        ((5, 8), (7, 8.5)),    # Processing -> Buffer
        ((8, 8), (10, 8.5)),   # Buffer -> AI
        ((11, 8), (13, 8.5)),  # AI -> Decision
        ((14, 8), (2, 6.5)),   # Decision -> Alert
        ((14, 8), (5, 6.5)),   # Decision -> Storage
        ((14, 8), (8, 6.5)),   # Decision -> Telegram
        ((14, 8), (11, 6.5)),  # Decision -> Console
        ((14, 8), (14, 6.5)),  # Decision -> Web UI
    ]
    
    for start, end in arrows:
        arrow = ConnectionPatch(start, end, "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=15, fc="black", ec="black", linewidth=1.5)
        ax.add_patch(arrow)
    
    # Data types
    data_types = [
        (1, 4, 'Raw Video\nFrames', colors['input']),
        (4, 4, 'Processed\nFrames', colors['process']),
        (7, 4, 'Frame Buffer\n(10s)', colors['storage']),
        (10, 4, 'Video\nDescription', colors['ai']),
        (13, 4, 'Fall\nDetection', colors['process']),
    ]
    
    for x, y, name, color in data_types:
        data_box = FancyBboxPatch((x-0.5, y), 1.5, 0.8, boxstyle="round,pad=0.05",
                                 facecolor=color, edgecolor='black', linewidth=1)
        ax.add_patch(data_box)
        ax.text(x, y + 0.4, name, ha='center', va='center', fontsize=8)
    
    # Tiêu đề
    ax.text(8, 9.5, '📊 LUỒNG DỮ LIỆU HỆ THỐNG', ha='center', va='center', fontsize=16, weight='bold')
    
    plt.tight_layout()
    plt.savefig('data_flow.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    # Tạo tất cả các sơ đồ
    create_system_overview()
    create_directory_structure()
    create_module_diagrams()
    create_data_flow()
    print("✅ Đã tạo xong tất cả các sơ đồ hệ thống!")