# Hiểu và mô tả dự án chi tiết
_Exported on 6/30/2025 at 11:16:40 GMT+7 from Cursor (1.1.6)_

---

**User**

@main_ui.py @/src hiểu toàn bộ project, mô tả lại cho tôi từng mô đun chi tiết và vẽ sơ đồ khối 

---

**Cursor**

Tôi sẽ đọc tất cả các file trong thư mục src để hiểu toàn bộ project và mô tả chi tiết từng mô đun.

Dựa trên việc phân tích toàn bộ source code, tôi sẽ mô tả chi tiết từng mô đun và vẽ sơ đồ khối của hệ thống phát hiện té ngã này.

## **📋 MÔ TẢ TỔNG QUAN PROJECT**

Đây là **Hệ Thống Phát Hiện Té Ngã Bệnh Viện** sử dụng AI với các tính năng:
- **Phát hiện té ngã thời gian thực** từ camera
- **Phân tích video upload** để tìm té ngã  
- **2 phương thức AI**: VLM SmolVLM và VideoLLaMA3 + OpenAI hybrid
- **Cảnh báo đa kênh**: âm thanh, Telegram, lưu bằng chứng GIF
- **Giao diện web** thân thiện với Gradio

---

## **🔧 CHI TIẾT TỪNG MÔ ĐUN**

### **1. 🎯 `main_ui.py` - Giao Diện Web Chính (1289 lines)**
**Chức năng**: Giao diện web chính sử dụng Gradio
- **Class `FallDetectionWebUI`**: Core system controller
- **Camera Management**: Khởi tạo, điều khiển camera real-time
- **Frame Processing**: Buffer frames, phân tích theo chu kỳ
- **Detection Methods**: Chuyển đổi giữa OpenAI và VideoLLaMA3
- **UI Components**: 6 tabs - Camera, Logs, Alerts, Upload, Evidence, Config
- **Auto-refresh**: Dual timers (0.1s camera, 2s status)
- **Evidence Management**: Lưu và hiển thị GIF bằng chứng

### **2. ⚙️ `src/__init__.py` - Cấu Hình Hệ Thống (52 lines)**
**Chức năng**: Cấu hình toàn bộ hệ thống và khởi tạo services
```python
# Các biến cấu hình chính:
OPENAI_CLIENT: OpenAI client
TELEGRAM_BOT: Bot instance (nếu enabled)
SAVE_ANALYSIS_FRAMES: Có lưu frames không
SAVE_FORMAT: images/gif/video/all
MAX_FRAMES: Số frames tối đa gửi AI (default: 5)
```

### **3. 🛠️ `src/utils.py` - Hàm Tiện Ích (142 lines)**
**Chức năng**: Xử lý frames và tương tác với AI
- **`prepare_messages()`**: Tạo prompts tiếng Việt cho OpenAI
- **`frames_to_base64()`**: Chuyển frames sang base64 để gửi API
- **`save_analysis_frames_to_temp()`**: Lưu frames phân tích (GIF/video)
- **`save_demo_video()`**: Tạo MP4 từ frames

### **4. 🤖 `src/videollama_detector.py` - VideoLLaMA3 Detector (269 lines)**
**Chức năng**: Mô đun phát hiện hybrid VideoLLaMA3 + OpenAI
- **Class `VideoLLamaFallDetector`**: 
  - Model: DAMO-NLP-SG/VideoLLaMA3-2B
  - **2-step analysis**: VideoLLaMA3 mô tả → OpenAI phân tích tiếng Việt
- **`load_model()`/`unload_model()`**: Quản lý model memory
- **`get_video_description()`**: VideoLLaMA3 mô tả video (English)
- **`translate_to_vietnamese_analysis()`**: OpenAI phân tích tiếng Việt
- **`analyze_frames()`**: Pipeline hoàn chỉnh 2 bước

### **5. 🔊 `src/audio_warning.py` - Hệ Thống Cảnh Báo Âm Thanh (331 lines)**
**Chức năng**: Text-to-Speech cảnh báo âm thanh
- **Class `AudioWarningSystem`**:
  - **Đa nền tảng**: Google TTS, espeak-ng, Windows SAPI, macOS say
  - **Ưu tiên Google TTS** cho tiếng Việt chất lượng cao
  - **Contextual warnings**: Tạo nội dung cảnh báo dựa trên phân tích
- **`_detect_tts_system()`**: Tự động phát hiện TTS khả dụng
- **`play_warning_async()`**: Phát âm thanh không đồng bộ

### **6. 📱 `src/alert_services.py` - Dịch Vụ Thông Báo (36 lines)**
**Chức năng**: Gửi thông báo Telegram
- **`send_telegram_alert()`**: Async function gửi tin nhắn + ảnh bằng chứng
- Tự động skip nếu Telegram disabled
- Format tin nhắn chuẩn với timestamp, vị trí, chi tiết

### **7. 🚀 `src/setup.py` - Script Thiết Lập (113 lines)**
**Chức năng**: Hướng dẫn setup ban đầu
- **`install_dependencies()`**: Cài requirements.txt
- **`create_env_file()`**: Tạo .env từ template
- **`check_camera()`**: Kiểm tra camera khả dụng
- **`print_next_steps()`**: Hướng dẫn bước tiếp theo

### **8. 🧪 `src/test_system.py` - Script Kiểm Tra (130 lines)**
**Chức năng**: Test tất cả components trước khi chạy
- **`test_camera()`**: Test camera connection
- **`test_openai_connection()`**: Test OpenAI API
- **`test_telegram_connection()`**: Test Telegram bot
- **`main()`**: Chạy tất cả tests và báo cáo kết quả

---

## **🏗️ SƠ ĐỒ KHỐI HỆ THỐNG**

```python
# Các biến cấu hình chính:
OPENAI_CLIENT: OpenAI client
TELEGRAM_BOT: Bot instance (nếu enabled)
SAVE_ANALYSIS_FRAMES: Có lưu frames không
SAVE_FORMAT: images/gif/video/all
MAX_FRAMES: Số frames tối đa gửi AI (default: 5)
```

## **🔄 LUỒNG XỬ LÝ CHI TIẾT**

### **1. 📹 Luồng Camera Real-time**
```
Camera → Frame Buffer (10s) → Analysis Trigger (5s) → AI Detection → Alert Pipeline
```

### **2. 📁 Luồng Video Upload**  
```
Upload File → Read All Frames → Sample Frames → AI Analysis → Evidence Generation
```

### **3. 🤖 Luồng AI Detection (2 chế độ)**

**Mode 1: OpenAI Direct**
```
Frames → Base64 → VLM SmolVLM → Vietnamese Result
```

**Mode 2: VideoLLaMA3 Hybrid**  
```
Frames → Video File → VideoLLaMA3 → English Description → OpenAI → Vietnamese Result
```

### **4. 🚨 Luồng Alert Multi-channel**
```
Fall Detected → [Audio TTS + Telegram Message + GIF Evidence + System Logs] (Parallel)
```

---

## **⚡ TÍNH NĂNG NỔI BẬT**

### **🎯 AI Detection Capabilities**
- **Dual AI Methods**: OpenAI fast vs VideoLLaMA3 accurate
- **Vietnamese Processing**: Intelligent prompt engineering 
- **False Positive Reduction**: Careful prompt design
- **Real-time Analysis**: 5-second intervals

### **🔊 Multi-platform Audio**
- **Google TTS**: Best Vietnamese quality (online)
- **espeak-ng**: Cross-platform offline TTS
- **System TTS**: Windows SAPI, macOS say
- **Contextual Messages**: Smart warning generation

### **📱 Evidence & Alerts**
- **GIF Evidence**: 5x speed for quick review
- **Telegram Integration**: Instant notifications with photos
- **Comprehensive Logging**: Detailed system logs
- **Evidence Gallery**: Browse and review all detections

### **🌐 Web Interface**
- **Real-time UI**: Auto-refresh components
- **Multi-tab Design**: Organized functionality
- **Progress Tracking**: Video upload progress
- **Model Management**: Load/unload VideoLLaMA3

---

## **🔧 KIẾN TRÚC KỸ THUẬT**

### **📊 Technology Stack**
- **Frontend**: Gradio (Python web framework)
- **Computer Vision**: OpenCV, PIL
- **AI Models**: VLM SmolVLM, VideoLLaMA3-2B
- **Audio**: gTTS, pygame, system TTS
- **Messaging**: Telegram Bot API
- **Threading**: Async/threading for non-blocking operations

### **💾 Data Flow**
- **Frame Buffer**: Rolling 10-second window
- **Evidence Storage**: Organized timestamp folders
- **Configuration**: Environment-based settings
- **Model Memory**: Dynamic VideoLLaMA3 loading

### **🚀 Performance Optimizations**
- **Frame Sampling**: Reduce processing load
- **Parallel Processing**: Multiple simultaneous alerts
- **Memory Management**: Model loading/unloading
- **Async Operations**: Non-blocking audio and alerts

Hệ thống này được thiết kế để **production-ready** với khả năng mở rộng cao, đặc biệt phù hợp cho môi trường bệnh viện cần giám sát té ngã 24/7.

```plaintext
Camera → Frame Buffer (10s) → Analysis Trigger (5s) → AI Detection → Alert Pipeline
```

```plaintext
Camera → Frame Buffer (10s) → Analysis Trigger (5s) → AI Detection → Alert Pipeline
```

```plaintext
Upload File → Read All Frames → Sample Frames → AI Analysis → Evidence Generation
```

```plaintext
Frames → Base64 → VLM SmolVLM → Vietnamese Result
```

```plaintext
Frames → Video File → VideoLLaMA3 → English Description → OpenAI → Vietnamese Result
```

```plaintext
Fall Detected → [Audio TTS + Telegram Message + GIF Evidence + System Logs] (Parallel)
```

---

**User**

chi tiết về cấu trúc file, 
hướng dẫn chạy project,
các yêu cầu về thư viện, phần cứng...

---

**Cursor**

Tôi sẽ đọc thêm các file cấu hình và hướng dẫn để cung cấp thông tin chi tiết về cấu trúc, yêu cầu và cách chạy project.

# 📚 CHI TIẾT TOÀN DIỆN VỀ PROJECT FALL DETECTION SYSTEM

## 🗂️ **CẤU TRÚC FILE CHI TIẾT**

```
llm-video-human-detection/
├── 🎯 **ENTRY POINTS**
│   ├── main.py                     # Console version - Terminal interface
│   ├── main_ui.py                  # Web UI version - Gradio interface  
│   ├── start_web_ui.py             # Quick start script với pre-checks
│   └── demo.py                     # Demo analysis script
│
├── 🔧 **CONFIGURATION FILES**
│   ├── requirements.txt            # Python dependencies
│   ├── env_template.txt           # Environment variables template
│   ├── .env                       # Environment configuration (tạo từ template)
│   ├── Makefile                   # Utility commands
│   └── README.md                  # Main documentation
│
├── 🧠 **SOURCE CODE MODULES**
│   └── src/
│       ├── __init__.py            # System configuration & initialization
│       ├── utils.py               # Frame processing & AI utilities  
│       ├── videollama_detector.py # VideoLLaMA3 hybrid detector
│       ├── audio_warning.py       # Text-to-speech alert system
│       ├── alert_services.py      # Telegram notification service
│       ├── setup.py               # System setup script
│       └── test_system.py         # Component testing script
│
├── 🎬 **ALTERNATE IMPLEMENTATIONS**
│   └── vid_llama.py               # Standalone VideoLLaMA3 script
│
├── 📁 **DATA DIRECTORIES** (auto-created)
│   ├── temp/                      # Temporary analysis files
│   ├── evidence/                  # Evidence images/videos
│   ├── evidence_gifs/             # GIF evidence with timestamps
│   ├── analysis/                  # Analysis results by timestamp
│   └── media/                     # Sample videos for testing
│       ├── fall-01-cam0.mp4
│       ├── fall-01-cam1.mp4
│       ├── image1.jpg
│       └── image2.jpg
│
└── 📝 **DOCUMENTATION**
    └── WEB_UI_SUMMARY.md          # Web UI detailed documentation
```

---

## 📋 **YÊU CẦU HỆ THỐNG**

### **🔧 Yêu Cầu Phần Cứng**

#### **Minimum Requirements:**
```
CPU: Intel i3/AMD Ryzen 3 (4 cores, 2.4GHz+)
RAM: 8GB DDR4
Webcam: USB 2.0 camera (720p+)
Network: Ethernet/WiFi cho API calls
OS: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
```

#### **Recommended for VideoLLaMA3:**
```
CPU: Intel i7/AMD Ryzen 7 (8 cores, 3.0GHz+)
RAM: 16GB+ DDR4 
GPU: NVIDIA GTX 1660/RTX 3060 (6GB+ VRAM)
CUDA: 11.8+ hoặc 12.1+
Storage: 10GB+ free space
```

#### **Production Hospital Environment:**
```
CPU: Intel Xeon/AMD EPYC (16+ cores)
RAM: 32GB+ ECC
GPU: NVIDIA RTX 4090/A4000 (16GB+ VRAM)
Network: Gigabit Ethernet 
UPS: Backup power cho continuous operation
```

### **📱 Yêu Cầu Phần Mềm**

#### **Core Requirements:**
- **Python**: 3.8+ (recommend 3.9-3.11)
- **OpenAI API Key**: Bắt buộc ($5+ credit)
- **Camera Drivers**: USB/IP camera support
- **Network**: Internet cho API calls

#### **Optional but Recommended:**
- **Telegram Bot**: Instant notifications
- **Audio Drivers**: TTS support 
- **Docker**: Container deployment
- **GPU Drivers**: CUDA for VideoLLaMA3

---

## 📦 **THƯ VIỆN VÀ DEPENDENCIES**

### **🎯 Core Dependencies (requirements.txt)**
```python
# Computer Vision & Image Processing
opencv-python==4.8.1.78          # Camera capture, video processing
numpy==1.24.3                    # Numerical operations
Pillow==10.0.1                   # Image manipulation
imageio==2.34.0                  # GIF creation
imageio-ffmpeg==0.4.9            # Video format support

# AI & Language Models  
openai==1.12.0                   # VLM SmolVLM API
transformers==4.46.3             # VideoLLaMA3 model loading

# Web Interface
gradio>=5.31.0                   # Web UI framework

# Communication & Notifications
python-telegram-bot==20.7        # Telegram alerts

# System & Configuration
python-dotenv==1.0.0             # Environment variables
rich==13.7.0                     # Terminal formatting
pre-commit==4.2.0                # Code quality
```

### **🤖 VideoLLaMA3 Additional Requirements**
```python
torch>=2.0.0                     # PyTorch for model inference
torch-audio                      # Audio processing
transformers[torch]               # Transformer models
accelerate                       # Model optimization
bitsandbytes                     # Memory optimization
flash-attn                       # Attention optimization
```

### **🔊 Audio TTS Dependencies**
```python
# Google TTS (Recommended)
gtts==2.4.0                      # Google Text-to-Speech
pygame==2.5.2                    # Audio playback

# Platform TTS Alternatives
pyttsx3                          # Cross-platform TTS
espeak-ng                        # Linux TTS engine
```

### **⚡ Performance Optimization**
```python
# GPU Acceleration
torch[cuda]                      # CUDA support
tensorrt                         # NVIDIA optimization

# Async Processing  
asyncio                          # Built-in async
threading                       # Built-in threading
multiprocessing                 # Built-in multiprocessing
```

---

## 🚀 **HƯỚNG DẪN CHẠY PROJECT**

### **📥 BƯỚC 1: INSTALLATION**

#### **Clone Project:**
```bash
git clone <repository-url>
cd llm-video-human-detection
```

#### **Setup Python Environment:**
```bash
# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### **Quick Setup với Script:**
```bash
# Automatic setup
python src/setup.py

# Hoặc dùng Makefile
make setup
```

### **⚙️ BƯỚC 2: CONFIGURATION**

#### **Tạo Environment File:**
```bash
# Copy template
cp env_template.txt .env

# Edit với editor
nano .env  # hoặc vim, code, notepad++
```

#### **Cấu hình .env File:**
```env
# 🔑 REQUIRED: OpenAI API Key
OPENAI_API_KEY=sk-proj-your-actual-api-key-here

# 📱 OPTIONAL: Telegram Notifications  
USE_TELE_ALERT=true
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_id

# 💾 OPTIONAL: Frame Saving
SAVE_ANALYSIS_FRAMES=true
SAVE_FORMAT=gif                  # images, gif, video, all

# 🎥 OPTIONAL: Camera Settings
CAMERA_INDEX=0                   # Default camera
MAX_FRAMES=5                     # Frames sent to AI
```

### **🧪 BƯỚC 3: TESTING**

#### **Test System Components:**
```bash
# Comprehensive system test
python src/test_system.py

# Individual tests
make test                        # Using Makefile
```

#### **Test Output Example:**
```
=== Fall Detection System Tests ===
📋 Camera:
✅ Camera working - Frame size: (480, 640, 3)

📋 OpenAI API:
✅ OpenAI connection successful

📋 Telegram Bot:
✅ Telegram connection successful

=== Test Results ===
Camera: ✅ PASS
OpenAI API: ✅ PASS  
Telegram Bot: ✅ PASS

🎉 All tests passed! System ready to run.
```

### **🎯 BƯỚC 4: CHẠY HỆ THỐNG**

#### **🌐 Option 1: Web UI (Recommended)**
```bash
# Quick start với pre-checks
python start_web_ui.py

# Hoặc chạy trực tiếp
python main_ui.py
```

**Sau đó truy cập:** http://localhost:7860

#### **🖥️ Option 2: Console Version**
```bash
# Terminal interface
python main.py

# Sử dụng Makefile
make main
```

#### **🎬 Option 3: Demo Analysis**
```bash
# Analyze sample videos
python demo.py

# Using Makefile
make demo
```

### **🔧 BƯỚC 5: ADVANCED SETUP**

#### **VideoLLaMA3 Model Setup:**
```bash
# Trong Web UI: vào tab "🤖 Cấu Hình AI"
# Click "📥 Tải Model" 
# Hoặc set detection method = "videollama3"

# Kiểm tra GPU memory:
nvidia-smi

# Free memory if needed:
python -c "import torch; torch.cuda.empty_cache()"
```

#### **Audio TTS Setup:**

**Linux:**
```bash
sudo apt-get install espeak-ng
# Hoặc
sudo apt-get install festival
```

**Windows:** (Windows SAPI có sẵn)
```powershell
# Install Google TTS
pip install gtts pygame
```

**macOS:** (say command có sẵn)  
```bash
# Install Google TTS
pip install gtts pygame
```

---

## 🎮 **HƯỚNG DẪN SỬ DỤNG**

### **🌐 Web UI Interface**

#### **Tab 1: 🎥 Camera & Điều Khiển**
```
1. Chọn Camera Index (thường là 0)
2. Click "🚀 Khởi Động" 
3. Xem live feed và status dashboard
4. Click "🛑 Dừng" để stop
```

#### **Tab 2: 📁 Upload Video**
```
1. Click "📹 Chọn File Video" 
2. Upload MP4/AVI/MOV file
3. Click "🔍 Phân Tích Video"
4. Xem kết quả trong "ℹ️ Thông Tin Video"
```

#### **Tab 3: 🎬 Bằng Chứng GIF**
```
1. Browse saved evidence GIFs
2. Select từ dropdown để xem chi tiết
3. Review 5x speed GIF evidence
```

#### **Tab 4: 🤖 Cấu Hình AI**
```
1. Chọn detection method:
   - VLM SmolVLM (fast, online)
   - VideoLLaMA3 + OpenAI (accurate, hybrid)
2. Load/Unload VideoLLaMA3 model
3. Test audio warning system
```

### **🖥️ Console Interface**

#### **Keyboard Controls:**
```
q       = Quit system
Ctrl+C  = Emergency stop
Space   = Manual analysis trigger
```

#### **Terminal Output:**
```
🔍 Analysis logs every 5 seconds
🚨 Fall alerts with Rich formatting  
📊 Real-time status table
💾 Evidence saving confirmations
```

### **🎬 Demo Mode**

#### **Analyze Sample Videos:**
```bash
python demo.py

# Available sample videos:
media/fall-01-cam0.mp4
media/fall-01-cam1.mp4
```

---

## ⚡ **PERFORMANCE OPTIMIZATION**

### **🚀 Speed Optimizations**

#### **OpenAI Mode (Fast):**
```python
analysis_interval = 3       # 3s intervals instead of 5s
max_frames = 3             # Fewer frames to AI
jpeg_quality = 60          # Lower quality for speed
```

#### **VideoLLaMA3 Mode (Accurate):**
```python
model_precision = "fp16"    # Half precision
max_frames = 64            # More frames for accuracy  
batch_processing = True    # Process multiple videos
```

### **💾 Memory Management**

#### **RAM Optimization:**
```python
# Trong main_ui.py
frame_buffer_size = 5      # Reduce from 10 seconds
unload_model_when_idle = True
clear_cache_interval = 300 # 5 minutes
```

#### **VRAM Optimization:**
```python
# Trong videollama_detector.py
torch_dtype = torch.bfloat16  # Memory efficient
device_map = "auto"           # Auto GPU distribution
load_in_8bit = True          # Quantization
```

### **🌐 Network Optimization**

#### **API Call Reduction:**
```python
max_frames = 3               # Reduce API payload
frame_compression = 0.7      # Higher compression
cooldown_period = 45         # Longer cooldown
```

#### **Offline Processing:**
```python
detection_method = "videollama3"  # Local processing
save_frames_locally = True        # Reduce uploads
batch_analysis = True             # Group API calls
```

---

## 🔧 **TROUBLESHOOTING**

### **❌ Common Issues & Solutions**

#### **Camera Issues:**
```bash
# Problem: Camera not detected
# Solution:
lsusb                       # Linux: List USB devices
Device Manager              # Windows: Check camera status
brew install ffmpeg         # macOS: Install video drivers

# Problem: Permission denied
sudo chmod 666 /dev/video0  # Linux: Camera permissions
```

#### **API Issues:**
```bash
# Problem: OpenAI API timeout  
# Solution:
export OPENAI_TIMEOUT=60    # Increase timeout
export MAX_RETRIES=3        # Retry failed calls

# Problem: Rate limiting
# Add delay between calls or upgrade API plan
```

#### **Memory Issues:**
```bash
# Problem: GPU out of memory
# Solution:
torch.cuda.empty_cache()     # Clear GPU memory
reduce max_frames            # Fewer frames to model
use model quantization       # 8-bit/4-bit precision
```

#### **Audio Issues:**
```bash
# Problem: TTS not working
# Linux:
sudo apt-get install espeak-ng alsa-utils

# Windows: 
# Check Windows Speech Platform in Control Panel

# macOS:
say "test"                   # Verify say command works
```

### **🐛 Debug Mode**

#### **Enable Detailed Logging:**
```python
# Trong main_ui.py
logging.basicConfig(level=logging.DEBUG)

# Environment variable
export DEBUG=1
```

#### **Performance Monitoring:**
```python
# Monitor GPU usage
nvidia-smi -l 1             # Continuous monitoring

# Monitor memory usage  
python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'CPU: {psutil.cpu_percent()}%')
"
```

---

## 🔒 **PRODUCTION DEPLOYMENT**

### **🏥 Hospital Environment Setup**

#### **Network Configuration:**
```bash
# Private network deployment
SERVER_HOST=192.168.1.100
SERVER_PORT=7860
ALLOWED_IPS=192.168.1.0/24

# Firewall rules
sudo ufw allow from 192.168.1.0/24 to any port 7860
```

#### **Service Configuration:**
```bash
# Systemd service (Linux)
sudo nano /etc/systemd/system/falldetection.service

[Unit]
Description=Fall Detection System
After=network.target

[Service]
Type=simple
User=falldetection
WorkingDirectory=/opt/falldetection
ExecStart=/opt/falldetection/venv/bin/python main_ui.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### **Container Deployment:**
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 7860

CMD ["python", "main_ui.py"]
```

### **📊 Monitoring & Alerts**

#### **System Health Checks:**
```python
# Health endpoint in main_ui.py
@app.route("/health")
def health_check():
    return {
        "status": "healthy",
        "camera": camera_status,
        "ai_model": model_status,
        "uptime": system_uptime
    }
```

#### **Log Aggregation:**
```bash
# Centralized logging
tail -f /var/log/falldetection/system.log
journalctl -u falldetection -f
```

Hệ thống này được thiết kế để **production-ready** với khả năng mở rộng cao, đặc biệt phù hợp cho môi trường bệnh viện cần giám sát té ngã 24/7 với độ tin cậy và chính xác cao.

```plaintext
llm-video-human-detection/
├── 🎯 **ENTRY POINTS**
│   ├── main.py                     # Console version - Terminal interface
│   ├── main_ui.py                  # Web UI version - Gradio interface  
│   ├── start_web_ui.py             # Quick start script với pre-checks
│   └── demo.py                     # Demo analysis script
│
├── 🔧 **CONFIGURATION FILES**
│   ├── requirements.txt            # Python dependencies
│   ├── env_template.txt           # Environment variables template
│   ├── .env                       # Environment configuration (tạo từ template)
│   ├── Makefile                   # Utility commands
│   └── README.md                  # Main documentation
│
├── 🧠 **SOURCE CODE MODULES**
│   └── src/
│       ├── __init__.py            # System configuration & initialization
│       ├── utils.py               # Frame processing & AI utilities  
│       ├── videollama_detector.py # VideoLLaMA3 hybrid detector
│       ├── audio_warning.py       # Text-to-speech alert system
│       ├── alert_services.py      # Telegram notification service
│       ├── setup.py               # System setup script
│       └── test_system.py         # Component testing script
│
├── 🎬 **ALTERNATE IMPLEMENTATIONS**
│   └── vid_llama.py               # Standalone VideoLLaMA3 script
│
├── 📁 **DATA DIRECTORIES** (auto-created)
│   ├── temp/                      # Temporary analysis files
│   ├── evidence/                  # Evidence images/videos
│   ├── evidence_gifs/             # GIF evidence with timestamps
│   ├── analysis/                  # Analysis results by timestamp
│   └── media/                     # Sample videos for testing
│       ├── fall-01-cam0.mp4
│       ├── fall-01-cam1.mp4
│       ├── image1.jpg
│       └── image2.jpg
│
└── 📝 **DOCUMENTATION**
    └── WEB_UI_SUMMARY.md          # Web UI detailed documentation
```

```plaintext
CPU: Intel i3/AMD Ryzen 3 (4 cores, 2.4GHz+)
RAM: 8GB DDR4
Webcam: USB 2.0 camera (720p+)
Network: Ethernet/WiFi cho API calls
OS: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
```

```plaintext
CPU: Intel i7/AMD Ryzen 7 (8 cores, 3.0GHz+)
RAM: 16GB+ DDR4 
GPU: NVIDIA GTX 1660/RTX 3060 (6GB+ VRAM)
CUDA: 11.8+ hoặc 12.1+
Storage: 10GB+ free space
```

```plaintext
CPU: Intel Xeon/AMD EPYC (16+ cores)
RAM: 32GB+ ECC
GPU: NVIDIA RTX 4090/A4000 (16GB+ VRAM)
Network: Gigabit Ethernet 
UPS: Backup power cho continuous operation
```

```python
# Computer Vision & Image Processing
opencv-python==4.8.1.78          # Camera capture, video processing
numpy==1.24.3                    # Numerical operations
Pillow==10.0.1                   # Image manipulation
imageio==2.34.0                  # GIF creation
imageio-ffmpeg==0.4.9            # Video format support

# AI & Language Models  
openai==1.12.0                   # VLM SmolVLM API
transformers==4.46.3             # VideoLLaMA3 model loading

# Web Interface
gradio>=5.31.0                   # Web UI framework

# Communication & Notifications
python-telegram-bot==20.7        # Telegram alerts

# System & Configuration
python-dotenv==1.0.0             # Environment variables
rich==13.7.0                     # Terminal formatting
pre-commit==4.2.0                # Code quality
```

```python
torch>=2.0.0                     # PyTorch for model inference
torch-audio                      # Audio processing
transformers[torch]               # Transformer models
accelerate                       # Model optimization
bitsandbytes                     # Memory optimization
flash-attn                       # Attention optimization
```

```python
# Google TTS (Recommended)
gtts==2.4.0                      # Google Text-to-Speech
pygame==2.5.2                    # Audio playback

# Platform TTS Alternatives
pyttsx3                          # Cross-platform TTS
espeak-ng                        # Linux TTS engine
```

```python
# GPU Acceleration
torch[cuda]                      # CUDA support
tensorrt                         # NVIDIA optimization

# Async Processing  
asyncio                          # Built-in async
threading                       # Built-in threading
multiprocessing                 # Built-in multiprocessing
```

```shellscript
git clone <repository-url>
cd llm-video-human-detection
```

```shellscript
# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

```shellscript
# Automatic setup
python src/setup.py

# Hoặc dùng Makefile
make setup
```

```shellscript
# Copy template
cp env_template.txt .env

# Edit với editor
nano .env  # hoặc vim, code, notepad++
```

```plaintext
# 🔑 REQUIRED: OpenAI API Key
OPENAI_API_KEY=sk-proj-your-actual-api-key-here

# 📱 OPTIONAL: Telegram Notifications  
USE_TELE_ALERT=true
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_id

# 💾 OPTIONAL: Frame Saving
SAVE_ANALYSIS_FRAMES=true
SAVE_FORMAT=gif                  # images, gif, video, all

# 🎥 OPTIONAL: Camera Settings
CAMERA_INDEX=0                   # Default camera
MAX_FRAMES=5                     # Frames sent to AI
```

```shellscript
# Comprehensive system test
python src/test_system.py

# Individual tests
make test                        # Using Makefile
```

```plaintext
=== Fall Detection System Tests ===
📋 Camera:
✅ Camera working - Frame size: (480, 640, 3)

📋 OpenAI API:
✅ OpenAI connection successful

📋 Telegram Bot:
✅ Telegram connection successful

=== Test Results ===
Camera: ✅ PASS
OpenAI API: ✅ PASS  
Telegram Bot: ✅ PASS

🎉 All tests passed! System ready to run.
```

```shellscript
# Quick start với pre-checks
python start_web_ui.py

# Hoặc chạy trực tiếp
python main_ui.py
```

```shellscript
# Terminal interface
python main.py

# Sử dụng Makefile
make main
```

```shellscript
# Analyze sample videos
python demo.py

# Using Makefile
make demo
```

```shellscript
# Trong Web UI: vào tab "🤖 Cấu Hình AI"
# Click "📥 Tải Model" 
# Hoặc set detection method = "videollama3"

# Kiểm tra GPU memory:
nvidia-smi

# Free memory if needed:
python -c "import torch; torch.cuda.empty_cache()"
```

```shellscript
sudo apt-get install espeak-ng
# Hoặc
sudo apt-get install festival
```

```powershell
# Install Google TTS
pip install gtts pygame
```

```shellscript
# Install Google TTS
pip install gtts pygame
```

```plaintext
1. Chọn Camera Index (thường là 0)
2. Click "🚀 Khởi Động" 
3. Xem live feed và status dashboard
4. Click "🛑 Dừng" để stop
```

```plaintext
1. Click "📹 Chọn File Video" 
2. Upload MP4/AVI/MOV file
3. Click "🔍 Phân Tích Video"
4. Xem kết quả trong "ℹ️ Thông Tin Video"
```

```plaintext
1. Browse saved evidence GIFs
2. Select từ dropdown để xem chi tiết
3. Review 5x speed GIF evidence
```

```plaintext
1. Chọn detection method:
   - VLM SmolVLM (fast, online)
   - VideoLLaMA3 + OpenAI (accurate, hybrid)
2. Load/Unload VideoLLaMA3 model
3. Test audio warning system
```

```plaintext
q       = Quit system
Ctrl+C  = Emergency stop
Space   = Manual analysis trigger
```

```plaintext
🔍 Analysis logs every 5 seconds
🚨 Fall alerts with Rich formatting  
📊 Real-time status table
💾 Evidence saving confirmations
```

```shellscript
python demo.py

# Available sample videos:
media/fall-01-cam0.mp4
media/fall-01-cam1.mp4
```

```python
analysis_interval = 3       # 3s intervals instead of 5s
max_frames = 3             # Fewer frames to AI
jpeg_quality = 60          # Lower quality for speed
```

```python
model_precision = "fp16"    # Half precision
max_frames = 64            # More frames for accuracy  
batch_processing = True    # Process multiple videos
```

```python
# Trong main_ui.py
frame_buffer_size = 5      # Reduce from 10 seconds
unload_model_when_idle = True
clear_cache_interval = 300 # 5 minutes
```

```python
# Trong videollama_detector.py
torch_dtype = torch.bfloat16  # Memory efficient
device_map = "auto"           # Auto GPU distribution
load_in_8bit = True          # Quantization
```

```python
max_frames = 3               # Reduce API payload
frame_compression = 0.7      # Higher compression
cooldown_period = 45         # Longer cooldown
```

```python
detection_method = "videollama3"  # Local processing
save_frames_locally = True        # Reduce uploads
batch_analysis = True             # Group API calls
```

```shellscript
# Problem: Camera not detected
# Solution:
lsusb                       # Linux: List USB devices
Device Manager              # Windows: Check camera status
brew install ffmpeg         # macOS: Install video drivers

# Problem: Permission denied
sudo chmod 666 /dev/video0  # Linux: Camera permissions
```

```shellscript
# Problem: OpenAI API timeout  
# Solution:
export OPENAI_TIMEOUT=60    # Increase timeout
export MAX_RETRIES=3        # Retry failed calls

# Problem: Rate limiting
# Add delay between calls or upgrade API plan
```

```shellscript
# Problem: GPU out of memory
# Solution:
torch.cuda.empty_cache()     # Clear GPU memory
reduce max_frames            # Fewer frames to model
use model quantization       # 8-bit/4-bit precision
```

```shellscript
# Problem: TTS not working
# Linux:
sudo apt-get install espeak-ng alsa-utils

# Windows: 
# Check Windows Speech Platform in Control Panel

# macOS:
say "test"                   # Verify say command works
```

```python
# Trong main_ui.py
logging.basicConfig(level=logging.DEBUG)

# Environment variable
export DEBUG=1
```

```python
# Monitor GPU usage
nvidia-smi -l 1             # Continuous monitoring

# Monitor memory usage  
python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'CPU: {psutil.cpu_percent()}%')
"
```

```shellscript
# Private network deployment
SERVER_HOST=192.168.1.100
SERVER_PORT=7860
ALLOWED_IPS=192.168.1.0/24

# Firewall rules
sudo ufw allow from 192.168.1.0/24 to any port 7860
```

```shellscript
# Systemd service (Linux)
sudo nano /etc/systemd/system/falldetection.service

[Unit]
Description=Fall Detection System
After=network.target

[Service]
Type=simple
User=falldetection
WorkingDirectory=/opt/falldetection
ExecStart=/opt/falldetection/venv/bin/python main_ui.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 7860

CMD ["python", "main_ui.py"]
```

```python
# Health endpoint in main_ui.py
@app.route("/health")
def health_check():
    return {
        "status": "healthy",
        "camera": camera_status,
        "ai_model": model_status,
        "uptime": system_uptime
    }
```

```shellscript
# Centralized logging
tail -f /var/log/falldetection/system.log
journalctl -u falldetection -f
```

