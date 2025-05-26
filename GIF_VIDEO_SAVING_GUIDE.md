# 🎬 Hướng dẫn lưu GIF và Video - Fall Detection System

## 📋 Tổng quan

Hệ thống Fall Detection System hiện đã hỗ trợ lưu khung hình phân tích dưới nhiều định dạng khác nhau để dễ dàng xem xét và kiểm tra:

- **🖼️ Images**: Lưu các khung hình riêng lẻ (JPG)
- **🎞️ GIF**: Tạo animation GIF từ chuỗi khung hình
- **🎬 Video**: Tạo video MP4 từ chuỗi khung hình
- **📦 All**: Lưu tất cả các định dạng trên

## ⚙️ Cấu hình

### 1. Thiết lập trong file `.env`

```bash
# Bật tính năng lưu khung hình
SAVE_ANALYSIS_FRAMES=true

# Chọn định dạng lưu (images/gif/video/all)
SAVE_FORMAT=gif
```

### 2. Các tùy chọn SAVE_FORMAT

| Giá trị | Mô tả | Files được tạo |
|---------|-------|----------------|
| `images` | Chỉ lưu ảnh riêng lẻ | `frame_001.jpg`, `frame_002.jpg`, ... |
| `gif` | Chỉ tạo GIF animation | `analysis_X.gif` |
| `video` | Chỉ tạo video MP4 | `analysis_X.mp4` |
| `all` | Tạo tất cả định dạng | Tất cả files trên |

## 📁 Cấu trúc thư mục được tạo

```
temp/
├── analysis_1_20241214_143052/
│   ├── analysis_info.txt          # Thông tin chi tiết
│   ├── analysis_1.gif             # GIF animation (nếu enabled)
│   ├── analysis_1.mp4             # Video MP4 (nếu enabled)
│   ├── frame_001_143052_123.jpg   # Khung hình riêng lẻ (nếu enabled)
│   ├── frame_002_143052_456.jpg
│   └── frame_003_143052_789.jpg
└── analysis_2_20241214_143117/
    ├── analysis_info.txt
    └── ...
```

## 🎯 Đặc điểm kỹ thuật

### GIF Animation
- **Frame rate**: 10 FPS (0.1 giây/frame) - 5x faster!
- **Loop**: Vô hạn
- **Format**: RGB color space
- **Compression**: Tự động tối ưu

### Video MP4
- **Codec**: MP4V
- **Frame rate**: 10 FPS - 5x faster!
- **Quality**: Chất lượng gốc từ camera
- **Format**: Tương thích với tất cả trình phát

### Individual Images
- **Format**: JPEG
- **Quality**: 80% (tối ưu cho kích thước file)
- **Naming**: `frame_XXX_HHMMSS_mmm.jpg`

## 📊 File thông tin (`analysis_info.txt`)

Mỗi thư mục phân tích chứa file thông tin chi tiết:

```
Fall Detection Analysis #1
========================================
Timestamp: 2024-12-14 14:30:52
Total frames: 5
Save format: gif
Frame rate: 0.20 FPS
Analysis interval: 5s
GIF duration: 0.5s (10 FPS)

Files saved:
- analysis_1.gif
- frame_001_143052_123.jpg
- frame_002_143052_456.jpg
```

## 🔧 Sử dụng trong code

### 1. Hệ thống real-time

```python
# Tự động lưu khi phân tích khung hình
system = FallDetectionSystem()
system.start()  # Sẽ tự động lưu theo cấu hình
```

### 2. Demo script

```python
# Chạy demo với video test
python src/demo_video_analysis.py
# Sẽ tạo thư mục demo_YYYYMMDD_HHMMSS/
```

## 💡 Lợi ích của từng định dạng

### 🖼️ Images
- **Ưu điểm**: Xem từng frame chi tiết, dễ debug
- **Sử dụng**: Phân tích từng moment cụ thể

### 🎞️ GIF
- **Ưu điểm**: Xem animation liền mạch, dễ chia sẻ
- **Sử dụng**: Preview nhanh sequence của té ngã

### 🎬 Video
- **Ưu điểm**: Chất lượng cao, compatible với media players
- **Sử dụng**: Báo cáo chính thức, archiving

### 📦 All
- **Ưu điểm**: Có tất cả tùy chọn
- **Sử dụng**: Môi trường production, cần backup đầy đủ

## 🎨 Demo và Testing

### Test với video có sẵn
```bash
# Thiết lập môi trường
export SAVE_ANALYSIS_FRAMES=true
export SAVE_FORMAT=all

# Chạy demo
python src/demo_video_analysis.py
```

### Test với camera real-time
```bash
# Thiết lập GIF chỉ
export SAVE_FORMAT=gif

# Chạy hệ thống
python fall_detection_system.py
```

## 📈 Performance và Storage

### Kích thước file ước tính (5 frames)
- **Images**: ~50KB per frame = ~250KB total
- **GIF**: ~200-500KB (tùy nội dung)
- **Video**: ~300-800KB (tùy chất lượng)
- **All**: ~1-1.5MB total

### Khuyến nghị
- **Development**: Sử dụng `gif` hoặc `video`
- **Production**: Sử dụng `images` hoặc `video`
- **Demo**: Sử dụng `all` để có đầy đủ tùy chọn

## 🔍 Troubleshooting

### Lỗi thiếu dependencies
```bash
pip install imageio imageio-ffmpeg
```

### Lỗi không tạo được video
- Kiểm tra codec MP4V support
- Thử thay đổi FPS settings
- Kiểm tra disk space

### Lỗi không tạo được GIF
- Kiểm tra imageio installation
- Verify RGB conversion
- Kiểm tra frame dimensions consistency

## 🎯 Tips và Best Practices

1. **Storage Management**: Thường xuyên dọn dẹp thư mục `temp/`
2. **Performance**: Sử dụng `gif` cho testing nhanh
3. **Quality**: Sử dụng `video` cho chất lượng tốt nhất
4. **Debugging**: Sử dụng `images` để debug từng frame
5. **Sharing**: GIF dễ chia sẻ qua chat/email nhất

---
📝 **Lưu ý**: Tính năng này giúp bạn dễ dàng review và analyze các sequence dẫn đến fall detection, cải thiện độ chính xác và debugging system. 