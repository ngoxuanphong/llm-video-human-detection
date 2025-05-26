import cv2
import logging
from src import TELEGRAM_BOT, USE_TELE_ALERT, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

async def send_telegram_alert(analysis_result, timestamp, frame_buffer):
    """Send Telegram notification about fall detection"""
    if not TELEGRAM_BOT or not USE_TELE_ALERT:
        logger.info("Telegram notification skipped")
        return
    
    try:
        message = f"🚨 PHÁT HIỆN TÉ NGÃ 🚨\n\n"
        message += f"Thời gian: {timestamp}\n"
        message += f"Vị trí: Camera Bệnh viện\n"
        message += f"Chi tiết: {analysis_result}\n\n"
        message += "Vui lòng kiểm tra ngay lập tức!"
        
        await TELEGRAM_BOT.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        
        # Send evidence image if available
        if frame_buffer:
            latest_frame = frame_buffer[-1]['frame']
            _, buffer = cv2.imencode('.jpg', latest_frame)
            
            await TELEGRAM_BOT.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=buffer.tobytes(),
                caption=f"Hình ảnh bằng chứng - {timestamp}"
            )
        
        logger.info("[green]✓[/green] Thông báo Telegram đã gửi thành công", extra={"markup": True})
        
    except Exception as e:
        logger.error(f"Không thể gửi thông báo Telegram: {e}")