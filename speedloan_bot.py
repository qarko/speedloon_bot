# 필요한 라이브러리를 설치해야 합니다.
# pip install python-telegram-bot==20.8

import logging
import re  # 데이터 검증을 위한 정규식 라이브러리
import os # 환경 변수 사용을 위한 라이브러리 추가

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# --- 설정 부분 ---
# Railway 환경 변수에서 토큰과 ID를 가져옵니다.
TELEGRAM_BOT_TOKEN = os.environ.get('7627967287:AAFkVYBWwNzBX_blu1B2W8k5hHy01xZiUQQ')
ADMIN_CHAT_ID = os.environ.get('5669071201')
# -----------------

# 로깅 설정
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 대화 상태 정의
(NAME, PHONE, REGION, OCCUPATION, INCOME, LOAN_AMOUNT, 
 DOB, REPAYMENT_PERIOD, PRIVATE_LOAN, DELINQUENCY_HISTORY) = range(10)

# --- '이전' 및 '취소' 커맨드 핸들러 ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """대화를 취소하고 종료합니다."""
    await update.message.reply_text(
        "접수가 취소되었습니다. 처음부터 다시 시작하시려면 /start 를 눌러주세요.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END

# --- 대화 시작 ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """대화의 시작점. 사용자에게 이름 입력을 요청합니다."""
    await update.message.reply_text(
        "안녕하세요! 대출 접수를 시작하겠습니다.\n\n"
        "언제든 '이전'을 입력하면 이전 질문으로 돌아가고, '/cancel'을 입력하면 접수를 취소합니다.\n\n"
        "먼저 성함을 알려주시겠어요?"
    )
    return NAME

# --- 각 항목별 정보 수집, 검증, 이전 단계 이동 함수 ---
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("연락 가능한 전화번호를 알려주세요. ('-' 없이 10~11자리 숫자만 입력)")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전':
        await update.message.reply_text("성함을 다시 알려주세요.")
        return NAME

    if re.match(r'^\d{10,11}$', text):
        context.user_data['phone'] = text
        await update.message.reply_text("거주하고 계신 지역을 알려주세요. (예: 서울시 강남구)")
        return REGION
    else:
        await update.message.reply_text("올바른 형식이 아닙니다. '-' 없이 10~11자리 숫자만 입력해주세요.")
        return PHONE

async def get_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전':
        await update.message.reply_text("연락 가능한 전화번호를 다시 알려주세요.")
        return PHONE

    context.user_data['region'] = text
    await update.message.reply_text("직업을 알려주세요. (예: 직장인, 사업자, 프리랜서)")
    return OCCUPATION

async def get_occupation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전':
        await update.message.reply_text("거주하고 계신 지역을 다시 알려주세요.")
        return REGION

    context.user_data['occupation'] = text
    await update.message.reply_text("월 평균 수입을 숫자로만 알려주세요. (단위: 만 원, 예: 300)")
    return INCOME

async def get_income(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전':
        await update.message.reply_text("직업을 다시 알려주세요.")
        return OCCUPATION

    if text.isdigit():
        context.user_data['income'] = text
        await update.message.reply_text("필요하신 금액을 숫자로만 알려주세요. (단위: 만 원, 예: 1000)")
        return LOAN_AMOUNT
    else:
        await update.message.reply_text("올바른 형식이 아닙니다. 숫자만 입력해주세요.")
        return INCOME

async def get_loan_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전':
        await update.message.reply_text("월 평균 수입을 다시 알려주세요.")
        return INCOME

    if text.isdigit():
        context.user_data['loan_amount'] = text
        await update.message.reply_text("생년월일 8자리를 알려주세요. (예: 19900101)")
        return DOB
    else:
        await update.message.reply_text("올바른 형식이 아닙니다. 숫자만 입력해주세요.")
        return LOAN_AMOUNT

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전':
        await update.message.reply_text("필요하신 금액을 다시 알려주세요.")
        return LOAN_AMOUNT

    if re.match(r'^\d{8}$', text):
        context.user_data['dob'] = text
        await update.message.reply_text("예상 상환 기간을 알려주세요. (예: 36개월)")
        return REPAYMENT_PERIOD
    else:
        await update.message.reply_text("올바른 형식이 아닙니다. 8자리 숫자(YYYYMMDD)로 입력해주세요.")
        return DOB

async def get_repayment_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전':
        await update.message.reply_text("생년월일 8자리를 다시 알려주세요.")
        return DOB

    context.user_data['repayment_period'] = text
    reply_keyboard = [["예", "아니오"]]
    await update.message.reply_text(
        "현재 사용 중인 개인대부가 있으신가요?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, input_field_placeholder="버튼 선택 또는 '이전' 입력"),
    )
    return PRIVATE_LOAN

async def get_private_loan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전':
        await update.message.reply_text("예상 상환 기간을 다시 알려주세요.", reply_markup=ReplyKeyboardRemove())
        return REPAYMENT_PERIOD

    if text in ["예", "아니오"]:
        context.user_data['private_loan'] = text
        reply_keyboard = [["예", "아니오"]]
        await update.message.reply_text(
            "최근 5년 내 연체 또는 사고자 이력이 있으신가요?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, input_field_placeholder="버튼 선택 또는 '이전' 입력"),
        )
        return DELINQUENCY_HISTORY
    else:
        await update.message.reply_text("버튼을 선택하거나 '이전'을 입력해주세요.")
        return PRIVATE_LOAN

async def get_delinquency_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전':
        reply_keyboard = [["예", "아니오"]]
        await update.message.reply_text(
            "현재 사용 중인 개인대부가 있으신가요?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, input_field_placeholder="버튼 선택 또는 '이전' 입력"),
        )
        return PRIVATE_LOAN

    if text in ["예", "아니오"]:
        context.user_data['delinquency_history'] = text
        await update.message.reply_text(
            "감사합니다! 모든 정보가 성공적으로 접수되었습니다.\n"
            "담당자가 확인 후 신속하게 연락드리겠습니다.",
            reply_markup=ReplyKeyboardRemove(),
        )

        ud = context.user_data
        admin_message = (
            f"🔔 **신규 대출 접수 알림** 🔔\n\n"
            f"─────── 기본 정보 ───────\n"
            f"👤 **이름:** {ud.get('name', 'N/A')}\n"
            f"📞 **번호:** {ud.get('phone', 'N/A')}\n"
            f"🎂 **생년월일:** {ud.get('dob', 'N/A')}\n"
            f"📍 **지역:** {ud.get('region', 'N/A')}\n\n"
            f"─── 소득 및 대출 정보 ───\n"
            f"👨‍💼 **직업:** {ud.get('occupation', 'N/A')}\n"
            f"💰 **월 수입:** {ud.get('income', 'N/A')}만 원\n"
            f"💵 **필요 금액:** {ud.get('loan_amount', 'N/A')}만 원\n"
            f"🗓️ **상환 기간:** {ud.get('repayment_period', 'N/A')}\n\n"
            f"───── 기타 확인 사항 ─────\n"
            f"• 개인대부 사용: {ud.get('private_loan', 'N/A')}\n"
            f"• 연체/사고 이력: {ud.get('delinquency_history', 'N/A')}\n"
        )

        if ADMIN_CHAT_ID:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode='Markdown')
            logger.info("관리자에게 상세 접수 내용을 성공적으로 전달했습니다.")
        else:
            logger.error("ADMIN_CHAT_ID가 설정되지 않았습니다.")
            
        return ConversationHandler.END
    else:
        await update.message.reply_text("버튼을 선택하거나 '이전'을 입력해주세요.")
        return DELINQUENCY_HISTORY


def main() -> None:
    """챗봇을 시작하고 실행합니다."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다. 봇을 시작할 수 없습니다.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_region)],
            OCCUPATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_occupation)],
            INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_income)],
            LOAN_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_loan_amount)],
            DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
            REPAYMENT_PERIOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_repayment_period)],
            PRIVATE_LOAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_private_loan)],
            DELINQUENCY_HISTORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_delinquency_history)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    print("환경 변수 설정이 적용된 챗봇이 시작되었습니다...")
    application.run_polling()

if __name__ == "__main__":
    main()