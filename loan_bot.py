# 필요한 라이브러리
import logging
import re
import os
from datetime import datetime
from telegram.error import Forbidden

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
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')
# -----------------

# 로깅 설정
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 대화 상태 정의
(NAME, PHONE, REGION, OCCUPATION, INCOME, LOAN_AMOUNT, 
 DOB, REPAYMENT_PERIOD, PRIVATE_LOAN, DELINQUENCY_HISTORY) = range(10)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"사용자 {update.message.from_user.first_name}가 대화를 취소했습니다.")
    await update.message.reply_text(
        "접수가 취소되었습니다. 처음부터 다시 시작하시려면 /start 를 눌러주세요.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"사용자 {update.message.from_user.first_name}가 /start 명령어를 사용했습니다.")
    try:
        await update.message.reply_text(
            "안녕하세요! 대출 접수를 시작하겠습니다.\n\n"
            "언제든 '이전' 또는 '취소'를 입력하면 이전 질문으로 돌아가거나 접수를 취소합니다.\n\n"
            "먼저 성함을 알려주시겠어요?"
        )
        logger.info("STATE: NAME - 이름을 질문했습니다.")
        return NAME
    except Forbidden:
        user = update.message.from_user
        logger.warning(f"사용자 '{user.first_name}' (ID: {user.id})님이 봇을 차단한 상태입니다.")
        return ConversationHandler.END


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    logger.info(f"STATE: NAME - 사용자로부터 '{user_input}' 입력을 받았습니다.")
    context.user_data['name'] = user_input
    await update.message.reply_text("연락 가능한 전화번호를 알려주세요. ('-' 없이 10~11자리 숫자만 입력)")
    logger.info("STATE: PHONE - 다음 상태로 이동합니다.")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    logger.info(f"STATE: PHONE - 사용자로부터 '{text}' 입력을 받았습니다.")
    if text == '이전':
        logger.info("이전 단계(NAME)로 돌아갑니다.")
        await update.message.reply_text("성함을 다시 알려주세요.")
        return NAME

    if re.match(r'^\d{10,11}$', text):
        context.user_data['phone'] = text
        await update.message.reply_text("거주하고 계신 지역을 알려주세요. (예: 서울시 강남구)")
        logger.info("STATE: REGION - 다음 상태로 이동합니다.")
        return REGION
    else:
        logger.warning("잘못된 형식의 전화번호가 입력되었습니다.")
        await update.message.reply_text("올바른 형식이 아닙니다. '-' 없이 10~11자리 숫자만 입력해주세요.")
        return PHONE

# ... (이후 다른 모든 get_... 함수들에도 비슷한 방식으로 logger.info()를 추가할 수 있습니다)
# ... 하지만 우선 이 상태로 테스트하여 ConversationHandler의 진입 자체에 문제가 있는지 확인합니다.

# 여기부터는 원래의 최종 코드를 그대로 사용합니다.
async def get_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전': return await get_phone(update, context) # 이전 함수 호출로 간결화 가능 (옵션)
    context.user_data['region'] = text
    await update.message.reply_text("직업을 알려주세요. (예: 직장인, 사업자, 프리랜서)")
    return OCCUPATION

async def get_occupation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전': return await get_region(update, context)
    context.user_data['occupation'] = text
    await update.message.reply_text("월 평균 수입을 숫자로만 알려주세요. (단위: 만 원, 예: 300)")
    return INCOME

async def get_income(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전': return await get_occupation(update, context)
    if text.isdigit():
        context.user_data['income'] = text
        await update.message.reply_text("필요하신 금액을 숫자로만 알려주세요. (단위: 만 원, 예: 1000)")
        return LOAN_AMOUNT
    else:
        await update.message.reply_text("올바른 형식이 아닙니다. 숫자만 입력해주세요.")
        return INCOME

async def get_loan_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전': return await get_income(update, context)
    if text.isdigit():
        context.user_data['loan_amount'] = text
        await update.message.reply_text("생년월일 8자리를 알려주세요. (예: 19900101)")
        return DOB
    else:
        await update.message.reply_text("올바른 형식이 아닙니다. 숫자만 입력해주세요.")
        return LOAN_AMOUNT

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전': return await get_loan_amount(update, context)
    try:
        datetime.strptime(text, '%Y%m%d')
        context.user_data['dob'] = text
        await update.message.reply_text("예상 상환 기간을 알려주세요. (예: 36개월)")
        return REPAYMENT_PERIOD
    except ValueError:
        await update.message.reply_text("존재하지 않는 날짜입니다. 8자리(YYYYMMDD) 형식의 유효한 날짜를 입력해주세요.")
        return DOB

async def get_repayment_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전': return await get_dob(update, context)
    context.user_data['repayment_period'] = text
    reply_keyboard = [["예", "아니오"]]
    await update.message.reply_text(
        "현재 사용 중인 개인대부가 있으신가요?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return PRIVATE_LOAN

async def get_private_loan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전': return await get_repayment_period(update, context)
    if text in ["예", "아니오"]:
        context.user_data['private_loan'] = text
        reply_keyboard = [["예", "아니오"]]
        await update.message.reply_text(
            "최근 5년 내 연체 또는 사고자 이력이 있으신가요?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return DELINQUENCY_HISTORY
    else:
        await update.message.reply_text("버튼을 선택해주세요.")
        return PRIVATE_LOAN

async def get_delinquency_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == '이전': return await get_private_loan(update, context)
    if text in ["예", "아니오"]:
        context.user_data['delinquency_history'] = text
        await update.message.reply_text(
            "감사합니다! 모든 정보가 성공적으로 접수되었습니다.\n"
            "담당자가 확인 후 신속하게 연락드리겠습니다.",
            reply_markup=ReplyKeyboardRemove(),
        )
        ud = context.user_data
        admin_message = (
            f"🔔 신규 접수: {ud.get('name', 'N/A')}\n"
            f"📞 번호: {ud.get('phone', 'N/A')}\n"
            f"🎂 생년월일: {ud.get('dob', 'N/A')}\n"
            f"📍 지역: {ud.get('region', 'N/A')}\n"
            f"👨‍💼 직업: {ud.get('occupation', 'N/A')}\n"
            f"💰 수입: {ud.get('income', 'N/A')}만\n"
            f"💵 필요금액: {ud.get('loan_amount', 'N/A')}만\n"
            f"🗓️ 상환기간: {ud.get('repayment_period', 'N/A')}\n"
            f"• 개인대부: {ud.get('private_loan', 'N/A')}\n"
            f"• 연체이력: {ud.get('delinquency_history', 'N/A')}"
        )
        if ADMIN_CHAT_ID: await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
        return ConversationHandler.END
    else:
        await update.message.reply_text("버튼을 선택해주세요.")
        return DELINQUENCY_HISTORY


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
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
            PRIVATE_LOAN: [MessageHandler(filters.Regex('^(예|아니오)$'), get_private_loan)],
            DELINQUENCY_HISTORY: [MessageHandler(filters.Regex('^(예|아니오)$'), get_delinquency_history)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex('^취소$'), cancel)
        ],
    )
    application.add_handler(conv_handler)
    print("상세 로그 추적 기능이 포함된 챗봇이 시작되었습니다...")
    application.run_polling()

if __name__ == "__main__":
    main()
