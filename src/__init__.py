import logging
import os

import dotenv
from openai import OpenAI
from rich.console import Console
from rich.logging import RichHandler
from telegram import Bot

# Load environment variables
dotenv.load_dotenv(override=True)

# Configure Rich console and logging
console = Console()
logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler(console=console, rich_tracebacks=True)])
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
TEMP_DIR = "temp"
EVIDENT_DIR = "evidence"
OPENAI_CLIENT = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
USE_TELE_ALERT = os.environ.get("USE_TELE_ALERT", "false").lower() == "true"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SAVE_ANALYSIS_FRAMES = os.environ.get("SAVE_ANALYSIS_FRAMES", "false").lower() == "true"
SAVE_FORMAT = os.environ.get("SAVE_FORMAT", "all").lower()
MAX_FRAMES = int(os.environ.get("MAX_FRAMES", 5))

os.makedirs(EVIDENT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


# ------------------------------------------------------------

# Log frame saving status
if SAVE_ANALYSIS_FRAMES:
    format_icon = {"images": "🖼️", "gif": "🎞️", "video": "🎬", "all": "📦"}.get(SAVE_FORMAT, "💾")
    logger.info(f"[green]{format_icon}[/green] Lưu khung hình phân tích đã được bật - Format: [cyan]{SAVE_FORMAT}[/cyan]", extra={"markup": True})
else:
    logger.info("[blue]ℹ[/blue] Lưu khung hình phân tích đã tắt theo cấu hình", extra={"markup": True})

# Initialize Telegram bot only if enabled and credentials available
if USE_TELE_ALERT and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    TELEGRAM_BOT = Bot(token=TELEGRAM_BOT_TOKEN)
    logger.info("[green]✓[/green] Thông báo Telegram đã được bật", extra={"markup": True})
else:
    TELEGRAM_BOT = None
    if not USE_TELE_ALERT:
        logger.info("[yellow]ℹ[/yellow] Thông báo Telegram đã tắt theo cấu hình", extra={"markup": True})
    else:
        logger.warning("[red]⚠[/red] Không tìm thấy thông tin đăng nhập Telegram. Thông báo Telegram đã tắt.", extra={"markup": True})
