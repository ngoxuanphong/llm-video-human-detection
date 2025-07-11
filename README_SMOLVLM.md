# Hệ thống Phát hiện Té ngã Bệnh viện với SmolVLM

## 🆕 Cập nhật: Chuyển từ OpenAI sang SmolVLM

Hệ thống đã được cập nhật để sử dụng **SmolVLM** thay vì OpenAI GPT-4 Vision cho việc phân tích video. Điều này mang lại những lợi ích sau:

### ✅ Lợi ích của SmolVLM

1. **Hiệu suất cao hơn**: SmolVLM được tối ưu hóa cho việc phân tích video
2. **Chi phí thấp hơn**: Không cần gọi API OpenAI cho mỗi lần phân tích
3. **Bảo mật tốt hơn**: Dữ liệu video không được gửi ra ngoài
4. **Độ trễ thấp**: Phân tích local nhanh hơn so với API call
5. **Khả năng tùy chỉnh**: Có thể fine-tune model cho mục đích cụ thể

### 🔄 Thay đổi Kiến trúc

```
Trước (OpenAI):
Camera → Frame Buffer → OpenAI API → Vietnamese Analysis → Alert

Sau (SmolVLM):
Camera → Frame Buffer → SmolVLM Local → OpenAI Text Analysis → Alert
```

### 📦 Yêu cầu Hệ thống

- **GPU**: NVIDIA GPU với CUDA support (khuyến nghị)
- **RAM**: Tối thiểu 8GB, khuyến nghị 16GB+
- **VRAM**: Tối thiểu 4GB cho SmolVLM-2.5B
- **Python**: 3.8+

### 🚀 Cài đặt

1. **Cài đặt dependencies**:
```bash
pip install -r requirements.txt
```

2. **Cấu hình môi trường**:
```bash
cp env_template.txt .env
```

Chỉnh sửa file `.env`:
```env
# OpenAI API (chỉ cần cho phân tích text)
OPENAI_API_KEY=your_openai_api_key_here

# Telegram (tùy chọn)
USE_TELE_ALERT=true
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Lưu trữ bằng chứng
SAVE_ANALYSIS_FRAMES=true
SAVE_FORMAT=all
```

### 🔧 Sử dụng

#### Console Version
```bash
python main.py
```

#### Web UI Version
```bash
python start_web_ui.py
```

### 📊 So sánh Hiệu suất

| Tiêu chí | OpenAI GPT-4V | SmolVLM |
|----------|----------------|---------|
| Thời gian phân tích | 2-5 giây | 1-3 giây |
| Chi phí | $0.01-0.03/lần | Miễn phí |
| Bảo mật | Dữ liệu gửi ra ngoài | Local processing |
| Độ chính xác | Cao | Cao |
| Khả năng tùy chỉnh | Hạn chế | Cao |

### 🧠 Model SmolVLM

- **Model**: `microsoft/SmolVLM-2.5B`
- **Kích thước**: ~2.5B parameters
- **Định dạng hỗ trợ**: Video, Image
- **Ngôn ngữ**: Multilingual (English + Vietnamese analysis)

### 🔄 Quy trình Phân tích

1. **Thu thập frames**: Camera liên tục thu thập frames
2. **Tạo video**: Frames được ghép thành video ngắn
3. **SmolVLM phân tích**: Model phân tích video và mô tả bằng tiếng Anh
4. **OpenAI text analysis**: Mô tả được phân tích để phát hiện té ngã bằng tiếng Việt
5. **Cảnh báo**: Nếu phát hiện té ngã, hệ thống gửi cảnh báo

### 📁 Cấu trúc File

```
src/
├── smolvlm_detector.py    # SmolVLM detector (mới)
├── utils.py               # Utility functions
├── alert_services.py      # Telegram alerts
├── audio_warning.py       # Audio warnings
└── __init__.py           # Configuration
```

### 🛠️ Troubleshooting

#### Lỗi GPU Memory
```bash
# Giảm batch size hoặc sử dụng CPU
export CUDA_VISIBLE_DEVICES=""
python main.py
```

#### Lỗi Model Loading
```bash
# Xóa cache và tải lại
rm -rf ~/.cache/huggingface/
python main.py
```

#### Lỗi CUDA
```bash
# Cài đặt CUDA toolkit
sudo apt-get install nvidia-cuda-toolkit
```

### 📈 Monitoring

Hệ thống cung cấp các metrics sau:
- **FPS**: Frames per second
- **Analysis time**: Thời gian phân tích
- **Memory usage**: Sử dụng GPU/CPU memory
- **Detection accuracy**: Độ chính xác phát hiện

### 🔮 Tính năng Tương lai

- [ ] Fine-tuning SmolVLM cho fall detection
- [ ] Multi-camera support
- [ ] Real-time streaming
- [ ] Edge deployment
- [ ] Mobile app integration

### 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra logs trong console
2. Xác nhận GPU drivers đã cài đặt
3. Kiểm tra CUDA compatibility
4. Tạo issue trên GitHub

---

**Lưu ý**: SmolVLM yêu cầu GPU để hoạt động tối ưu. Nếu không có GPU, hệ thống sẽ chạy trên CPU nhưng sẽ chậm hơn đáng kể.