import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 설정 부분 ---
# Railway 환경 변수에서 토큰을 가져옵니다.
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
# -----------------

# 로깅 설정
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# /start 명령어에만 응답하는 간단한 함수
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start 명령어에 간단한 응답을 보냅니다."""
    logger.info("'/start' 명령어를 받았습니다.")
    await update.message.reply_text("챗봇이 응답했습니다!")

def main() -> None:
    """챗봇을 시작하고 실행합니다."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # /start 명령어만 처리하도록 핸들러를 등록합니다.
    application.add_handler(CommandHandler("start", start))

    print("진단용 챗봇이 시작되었습니다...")
    application.run_polling()

if __name__ == "__main__":
    main()
