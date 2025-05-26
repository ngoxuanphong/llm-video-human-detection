# 🏥 Hệ Thống Phát Hiện Té Ngã - Web UI

## 📖 Tổng Quan

Phiên bản Web UI của hệ thống phát hiện té ngã bằng AI, sử dụng Gradio để tạo giao diện web thân thiện và dễ sử dụng. Hệ thống cho phép giám sát và điều khiển qua trình duyệt web mà không cần kiến thức kỹ thuật.

## ✨ Tính Năng Web UI

### 🎥 Camera & Điều Khiển
- **Live Camera Feed**: Hiển thị video trực tiếp từ camera
- **Start/Stop Controls**: Điều khiển hệ thống bằng nút bấm
- **Camera Selection**: Chọn camera index (0, 1, 2...)
- **Real-time Status**: Theo dõi trạng thái hệ thống thời gian thực

### 📊 Monitoring Dashboard
- **System Status**: Thống kê hoạt động hệ thống
- **Analysis Counter**: Số lần phân tích đã thực hiện
- **Frame Processing**: Số khung hình đã xử lý
- **Uptime Tracking**: Thời gian hoạt động liên tục

### 📋 System Logs
- **Real-time Logs**: Nhật ký hệ thống cập nhật tự động
- **Color-coded Messages**: Phân loại theo mức độ (info, warning, error, alert)
- **Timestamp Display**: Hiển thị thời gian chính xác
- **Log History**: Lưu trữ 100 log gần nhất

### 🚨 Alert Management
- **Fall Detection History**: Lịch sử phát hiện té ngã
- **Alert Details**: Thông tin chi tiết từng cảnh báo
- **Evidence Tracking**: Theo dõi bằng chứng đã lưu
- **Export Reports**: Xuất báo cáo JSON

### ⚙️ Configuration View
- **Current Settings**: Hiển thị cấu hình hiện tại
- **Environment Variables**: Hướng dẫn cấu hình .env
- **Feature Status**: Trạng thái các tính năng (Telegram, Frame Saving)

## 🚀 Cài Đặt & Chạy

### 1. Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### 2. Cấu Hình Environment
Tạo file `.env` từ template:
```bash
cp env_template.txt .env
```

Chỉnh sửa `.env`:
```env
# OpenAI API (bắt buộc)
OPENAI_API_KEY=your_openai_api_key_here

# Telegram Notifications (tùy chọn)
USE_TELE_ALERT=false
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Frame Saving (tùy chọn)
SAVE_ANALYSIS_FRAMES=false
SAVE_FORMAT=images
MAX_FRAMES=5
```

### 3. Khởi Động Web UI
```bash
python main_ui.py
```

### 4. Truy Cập Giao Diện
- **Local Access**: http://localhost:7860
- **Network Access**: http://[your-ip]:7860

## 🖥️ Hướng Dẫn Sử Dụng

### Khởi Động Hệ Thống
1. Mở trình duyệt và truy cập Web UI
2. Vào tab "🎥 Camera & Điều Khiển"
3. Chọn Camera Index (thường là 0)
4. Nhấn "🚀 Khởi Động"
5. Camera feed sẽ hiển thị và hệ thống bắt đầu phân tích

### Theo Dõi Hoạt Động
1. **Status Panel**: Theo dõi trạng thái hệ thống bên phải
2. **System Logs**: Chuyển đến tab "📋 Nhật Ký Hệ Thống"
3. **Alert History**: Kiểm tra tab "🚨 Lịch Sử Cảnh Báo"

### Dừng Hệ Thống
1. Nhấn "🛑 Dừng" trong tab Camera
2. Camera feed sẽ dừng và tài nguyên được giải phóng

## 📱 Tính Năng Nâng Cao

### Auto-Refresh
- Giao diện tự động cập nhật mỗi 2 giây
- Camera feed, status, logs được làm mới real-time
- Không cần refresh trang thủ công

### Alert Management
- **View History**: Xem 10 cảnh báo gần nhất
- **Clear History**: Xóa toàn bộ lịch sử cảnh báo
- **Export Report**: Xuất báo cáo JSON với timestamp

### System Monitoring
- **Frame Counter**: Tổng số khung hình đã xử lý
- **Analysis Counter**: Số lần gửi AI phân tích
- **Uptime Display**: Thời gian hoạt động liên tục
- **Buffer Status**: Số frames trong buffer

## 🔧 Cấu Hình Nâng Cao

### Camera Settings
```python
# Trong main_ui.py, có thể điều chỉnh:
self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # Độ rộng
self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Độ cao
self.camera.set(cv2.CAP_PROP_FPS, 30)            # FPS
```

### Analysis Interval
```python
# Thay đổi tần suất phân tích (mặc định 5 giây):
self.analysis_interval = 5  # seconds
```

### UI Refresh Rate
```python
# Trong create_interface(), thay đổi every parameter:
demo.load(
    update_interface,
    outputs=[...],
    every=2  # seconds
)
```

## 🌐 Network Access

### Local Network
Để truy cập từ thiết bị khác trong mạng LAN:
```python
demo.launch(
    server_name="0.0.0.0",  # Listen trên tất cả interfaces
    server_port=7860,
    share=False
)
```

### Public Access (Gradio Share)
Để tạo public link (cẩn thận với bảo mật):
```python
demo.launch(
    share=True  # Tạo public tunnel
)
```

## 🔒 Bảo Mật

### Recommendations
1. **Local Use**: Chỉ sử dụng trong mạng nội bộ
2. **Environment Variables**: Không commit .env file
3. **API Keys**: Bảo vệ OpenAI API key
4. **Network**: Không expose ra internet công cộng

### Production Deployment
Cho môi trường production, nên sử dụng:
- Reverse proxy (nginx)
- SSL/TLS encryption
- Authentication middleware
- Firewall rules

## 📊 Monitoring & Debugging

### Log Levels
- **✅ Success**: Hoạt động thành công
- **ℹ️ Info**: Thông tin hệ thống
- **⚠️ Warning**: Cảnh báo không nghiêm trọng
- **❌ Error**: Lỗi cần xử lý
- **🚨 Alert**: Phát hiện té ngã

### Common Issues
1. **Camera không hoạt động**: Kiểm tra camera index
2. **OpenAI API lỗi**: Kiểm tra API key và credits
3. **Telegram không gửi**: Kiểm tra bot token và chat ID
4. **Frame saving lỗi**: Kiểm tra quyền ghi file

## 🔄 So Sánh với Console Version

| Tính Năng | Console (main.py) | Web UI (main_ui.py) |
|-----------|-------------------|---------------------|
| Interface | Terminal/Console | Web Browser |
| Monitoring | Rich console panels | Gradio dashboard |
| Camera Feed | OpenCV window | Web image display |
| Controls | Keyboard (q to quit) | Button clicks |
| Logs | Terminal output | Web text display |
| Accessibility | Cần kiến thức CLI | User-friendly GUI |
| Remote Access | Không | Network/Internet |
| Multi-user | Không | Có thể chia sẻ |

## 🆕 Tính Năng Mới Web UI

1. **Browser-based**: Chạy hoàn toàn trên trình duyệt
2. **Remote Control**: Điều khiển từ xa qua mạng
3. **Multi-tab Interface**: Giao diện nhiều tab organized
4. **Export Functions**: Xuất báo cáo và dữ liệu
5. **Auto-refresh**: Cập nhật tự động không cần reload
6. **Responsive Design**: Tương thích nhiều thiết bị
7. **Status Dashboard**: Bảng điều khiển trạng thái chi tiết

## 🤝 Support

Nếu gặp vấn đề:
1. Kiểm tra logs trong tab "📋 Nhật Ký Hệ Thống"
2. Xem cấu hình trong tab "⚙️ Cấu Hình"
3. Đảm bảo .env file được cấu hình đúng
4. Kiểm tra camera permissions và connections

---

**📧 Contact**: Liên hệ để được hỗ trợ kỹ thuật
**🔗 GitHub**: Link repository để updates và bug reports 