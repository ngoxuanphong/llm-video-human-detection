# Hướng Dẫn Lưu Khung Hình Phân Tích

## 📸 Tính Năng Lưu Khung Hình

Hệ thống phát hiện té ngã giờ đây có thể lưu tất cả các khung hình được gửi đến AI để phân tích vào thư mục tạm thời. Tính năng này hữu ích để:

- **Kiểm tra chất lượng** các khung hình được phân tích
- **Debug** khi có kết quả phân tích không mong muốn  
- **Xem lại** những gì AI đã phân tích
- **Đánh giá hiệu suất** của hệ thống

## ⚙️ Cấu Hình

### Bật/Tắt Tính Năng

Thêm vào file `.env`:

```env
# Bật lưu khung hình
SAVE_ANALYSIS_FRAMES=true

# Tắt lưu khung hình (mặc định)
SAVE_ANALYSIS_FRAMES=false
```

## 📁 Cấu Trúc Thư Mục

### Hệ Thống Thời Gian Thực

```
temp/
├── analysis_1_20250526_113529/
│   ├── frame_1_113529_488.jpg
│   ├── frame_2_113529_520.jpg
│   └── ...
├── analysis_2_20250526_113534/
│   ├── frame_1_113534_123.jpg
│   ├── frame_2_113534_155.jpg
│   └── ...
```

### Demo Script

```
temp/
├── demo_20250526_114523/
│   ├── analysis_info.txt
│   ├── frame_001.jpg
│   ├── frame_002.jpg
│   └── ...
```

## 📋 Thông Tin Khung Hình

### Tên File Hệ Thống Thời Gian Thực

- **Format**: `frame_{số_thứ_tự}_{giờ_phút_giây}_{mili_giây}.jpg`
- **Ví dụ**: `frame_3_113529_750.jpg`
  - Frame số 3
  - Thời gian: 11:35:29.750

### Tên File Demo

- **Format**: `frame_{số_thứ_tự:03d}.jpg`
- **Ví dụ**: `frame_005.jpg`
- **Info file**: `analysis_info.txt` chứa thông tin phân tích

## 🔍 Nội Dung File Info (Demo)

```
Demo Analysis Information
========================
Video file: bison.mp4
Analysis time: 2025-05-26 11:45:23
Total frames analyzed: 8
```

## 💡 Sử Dụng

### Khi Chạy Hệ Thống

```bash
# Với frame saving bật
python fall_detection_system.py
```

Bạn sẽ thấy log:
```
[11:35:28] INFO     💾 Lưu khung hình phân tích đã được bật
[11:35:29] INFO     💾 Đã lưu 152 khung hình phân tích tại: temp/analysis_1_20250526_113529
```

### Khi Chạy Demo

```bash
# Với frame saving bật
python src/demo_video_analysis.py
```

Bạn sẽ thấy:
```
💾 Đã lưu 8 khung hình demo tại: temp/demo_20250526_114523
```

## ⚠️ Lưu Ý

### Dung Lượng

- Mỗi khung hình khoảng **50-100KB**
- Mỗi lần phân tích có thể lưu **5-200+ khung hình**
- **Tự động dọn dẹp** thư mục temp định kỳ

### Hiệu Suất

- Lưu khung hình **không ảnh hưởng** đến tốc độ phân tích
- Chạy **song song** với quá trình AI analysis
- **Tắt tính năng** để tiết kiệm dung lượng đĩa

### Bảo Mật

- Khung hình chứa **thông tin nhạy cảm** từ camera
- **Chỉ bật** khi cần thiết để debug
- **Xóa thường xuyên** sau khi sử dụng

## 🧹 Dọn Dẹp Thư Mục

### Manual

```bash
# Xóa tất cả
rm -rf temp/

# Xóa các file cũ (hơn 7 ngày)
find temp/ -type f -mtime +7 -delete
```

### Script Tự Động

```bash
# Tạo script dọn dẹp
cat > cleanup_temp.sh << 'EOF'
#!/bin/bash
echo "Dọn dẹp thư mục temp..."
find temp/ -type d -mtime +7 -exec rm -rf {} +
echo "Hoàn thành!"
EOF

chmod +x cleanup_temp.sh
./cleanup_temp.sh
```

## 🔧 Tùy Chỉnh

### Thay Đổi Đường Dẫn Lưu

Sửa trong `fall_detection_system.py`:

```python
# Thay đổi từ
temp_dir = "temp"

# Thành
temp_dir = "/path/to/your/storage"
```

### Thay Đổi Format Tên File

Sửa trong hàm `save_analysis_frames_to_temp()`:

```python
# Thay đổi format tên file
filename = f"custom_frame_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
```

## 📊 Thống Kê Sử Dụng

### Kiểm Tra Dung Lượng

```bash
# Dung lượng thư mục temp
du -sh temp/

# Số file trong temp
find temp/ -type f | wc -l

# File lớn nhất
find temp/ -type f -exec ls -lh {} + | sort -k5 -hr | head -5
```

### Monitor Real-time

```bash
# Theo dõi thư mục temp
watch -n 2 'ls -la temp/ | tail -10'
```

## ❓ Troubleshooting

### Không Lưu Được Khung Hình

1. **Kiểm tra quyền ghi**: `ls -la temp/`
2. **Kiểm tra dung lượng đĩa**: `df -h`
3. **Kiểm tra cấu hình**: `grep SAVE_ANALYSIS_FRAMES .env`

### Lỗi Memory

- **Giảm số khung hình**: Sửa `max_frames=5` thành `max_frames=3`
- **Tăng chu kỳ phân tích**: Sửa `analysis_interval = 5` thành `analysis_interval = 10`

### File Bị Corrupt

- **Kiểm tra OpenCV**: `python -c "import cv2; print(cv2.__version__)"`
- **Kiểm tra định dạng**: Thử mở file với image viewer 