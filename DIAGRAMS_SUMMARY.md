# 📊 Tóm tắt Sơ đồ Hệ thống

## 🎯 Mục đích

Tài liệu này mô tả các sơ đồ hệ thống đã được tạo để minh họa kiến trúc và luồng hoạt động của hệ thống phát hiện té ngã bệnh viện với SmolVLM.

## 📁 Files Sơ đồ

### 1. `system_overview.png` - Sơ đồ Tổng quan Hệ thống
- **Mô tả**: Tổng quan toàn bộ hệ thống với các thành phần chính
- **Thành phần**:
  - 📹 Camera Bệnh viện
  - 🔄 Frame Buffer (10 giây)
  - 🤖 SmolVLM Phân tích
  - 🧠 Logic Phát hiện Té ngã
  - 🚨 Hệ thống Cảnh báo
  - 💾 Lưu trữ Bằng chứng
  - 🌐 Web UI Giao diện
  - 🖥️ Console Terminal
  - 📱 Telegram Thông báo

### 2. `directory_structure.png` - Cấu trúc Thư mục
- **Mô tả**: Sơ đồ cấu trúc thư mục và files của dự án
- **Thành phần**:
  - 📁 Root directory (video_understanding/)
  - 📁 src/ với các modules
  - 📁 test/, media/, temp/, evidence_gifs/
  - Files chính: main.py, main_ui.py, requirements.txt, .env

### 3. `main_module.png` - Module Main.py
- **Mô tả**: Chi tiết class FallDetectionSystem và các methods
- **Thành phần**:
  - 🔧 Main System (main.py)
  - Methods: __init__(), initialize_camera(), capture_frames(), analyze_frames()
  - Properties: camera, is_running, frame_buffer, analysis_interval

### 4. `smolvlm_module.png` - Module SmolVLM Detector
- **Mô tả**: Chi tiết class SmolVLMFallDetector
- **Thành phần**:
  - 🤖 SmolVLM Detector (smolvlm_detector.py)
  - Methods: load_model(), unload_model(), get_video_description()
  - Properties: model, processor, is_loaded, device

### 5. `alert_module.png` - Module Alert Services
- **Mô tả**: Hệ thống cảnh báo và thông báo
- **Thành phần**:
  - 🚨 Alert Services (alert_services.py)
  - Methods: send_telegram_alert(), send_email_alert(), log_alert()
  - External Services: Telegram Bot, Email Server, SMS Gateway

### 6. `data_flow.png` - Luồng Dữ liệu
- **Mô tả**: Luồng xử lý dữ liệu từ camera đến cảnh báo
- **Thành phần**:
  - 📹 Camera Input
  - 🔄 Frame Processing
  - 📦 Frame Buffer
  - 🤖 SmolVLM Analysis
  - 🧠 Fall Decision
  - Outputs: Alert System, Evidence Storage, Telegram, Console, Web UI

## 🎨 Đặc điểm Thiết kế

### Màu sắc
- **Camera/Input**: #FF6B6B (Đỏ)
- **Processing**: #4ECDC4 (Xanh lá)
- **AI/SmolVLM**: #45B7D1 (Xanh dương)
- **Alert/Output**: #96CEB4 (Xanh nhạt)
- **Storage**: #FFEAA7 (Vàng)
- **UI**: #DDA0DD (Tím)

### Ký hiệu
- 📹 Camera
- 🔄 Buffer/Processing
- 🤖 AI/SmolVLM
- 🧠 Logic/Decision
- 🚨 Alert
- 💾 Storage
- 🌐 Web UI
- 🖥️ Console
- 📱 Telegram

## 🔄 Luồng Hoạt động

### 1. Thu thập Dữ liệu
```
Camera → Frame Buffer (10s) → Video Creation
```

### 2. Phân tích AI
```
Video → SmolVLM → English Description → OpenAI Text Analysis → Vietnamese Result
```

### 3. Cảnh báo
```
Fall Detection → Alert System → Telegram/Console/Web UI
```

### 4. Lưu trữ
```
Evidence → File System → GIF/Video/Images
```

## 📊 Metrics và Monitoring

### Performance Metrics
- **FPS**: Frames per second
- **Analysis Time**: Thời gian phân tích SmolVLM
- **Memory Usage**: GPU/CPU memory
- **Detection Accuracy**: Độ chính xác phát hiện

### System Status
- **Camera Status**: Connected/Disconnected
- **Model Status**: Loaded/Unloaded
- **Alert Status**: Enabled/Disabled
- **Storage Status**: Available/Full

## 🛠️ Công cụ Tạo Sơ đồ

### File: `system_diagrams.py`
- **Thư viện**: matplotlib, numpy, pillow
- **Functions**:
  - `create_system_overview()`: Sơ đồ tổng quan
  - `create_directory_structure()`: Cấu trúc thư mục
  - `create_module_diagrams()`: Sơ đồ modules
  - `create_data_flow()`: Luồng dữ liệu

### Cách sử dụng:
```bash
python3 system_diagrams.py
```

## 📈 Cải tiến Tương lai

### Sơ đồ Động
- [ ] Real-time system status
- [ ] Live performance metrics
- [ ] Interactive diagrams

### Sơ đồ Chi tiết
- [ ] Network architecture
- [ ] Database schema
- [ ] API endpoints
- [ ] Security layers

### Visualization
- [ ] 3D system diagrams
- [ ] Animated flow charts
- [ ] Interactive web diagrams

## 📞 Hỗ trợ

### Tạo sơ đồ mới:
1. Thêm function vào `system_diagrams.py`
2. Gọi function trong `if __name__ == "__main__"`
3. Chạy script để tạo PNG

### Chỉnh sửa sơ đồ:
1. Sửa đổi function tương ứng
2. Chạy lại script
3. Kiểm tra output PNG

---

**Lưu ý**: Tất cả sơ đồ được tạo bằng Python matplotlib và được lưu dưới định dạng PNG với độ phân giải cao (300 DPI).