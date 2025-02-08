import logging
from constants import tg_token
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)
import subprocess
import signal
import sys
from utils import check_process
from refresh import refresh_tokens
from collections import deque
import functools
import inspect
import time


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='logs/tg.log',
    filemode='a'
)

logger = logging.getLogger(__name__)


def graceful_shutdown(signum, frame):
    logger.info(f"Получен сигнал {signum}. Выполняем завершающие действия...")
    subprocess.Popen(
        ["sh", "./stop_bot.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True
    )
    sys.exit(0)


signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)


def trusted_user(condition):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = condition(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result

            if result:
                return await func(*args, **kwargs)
            else:
                return None
        return wrapper
    return decorator


async def check_user(update, context):
    if update.message.from_user.id in (988468804, 2017350326):
        return True
    else:
        return False


@trusted_user(check_user)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(update.message.from_user)
    logger.info(update.message.from_user.id)
    await update.message.reply_text(
            "Привет! Проверка связи, теперь мне могут писать только два человека"
    )


@trusted_user(check_user)
async def activate_script(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    start_bot = subprocess.Popen(
        ["sh", "./start_bot.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True
    )

    logger.info(f"Скрипт запущен в фоне, PID: {start_bot.pid}")
    await update.message.reply_text("Скрипт активирован!")


@trusted_user(check_user)
async def stop_script(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    stop_bot = subprocess.Popen(
        ["sh", "./stop_bot.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True
    )

    logger.info(f"Скрипт остановки запущен в фоне, PID: {stop_bot.pid}")
    await update.message.reply_text("Скрипт остановлен!")


@trusted_user(check_user)
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    process_running, number_pf_processes = check_process()
    if process_running:
        await update.message.reply_text("Бот на охоте за грузами 😈")
    else:
        await update.message.reply_text("Бот в данный момент не работает 😴")


@trusted_user(check_user)
async def update_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Обновляю токены")
    process_running = check_process()[0]
    if process_running:
        subprocess.run(["sh", "./stop_bot.sh"], capture_output=True, text=True)
        refresh_status = refresh_tokens()
        time.sleep(5)
        start_bot = subprocess.Popen(
            ["sh", "./start_bot.sh"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        logger.info(f"Скрипт запущен в фоне, PID: {start_bot.pid}")
    else:
        refresh_status = refresh_tokens()
    if refresh_status == 200:
        await context.bot.send_message(chat_id=update.message.from_user.id, text="Токены обновлены успешно")
    else:
        await context.bot.send_message(chat_id=update.message.from_user.id,
                                       text="Что-то пошло не так при обновлении токенов")


async def token_refresh(context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Обновляю токены")
    process_running = check_process()[0]
    if process_running:
        subprocess.run(["sh", "./stop_bot.sh"], capture_output=True, text=True)
        refresh_status = refresh_tokens()
        time.sleep(5)
        start_bot = subprocess.Popen(
            ["sh", "./start_bot.sh"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        logger.info(f"Скрипт запущен в фоне, PID: {start_bot.pid}")
    else:
        refresh_status = refresh_tokens()
    if refresh_status == 200:
        await context.bot.send_message(chat_id=988468804, text="Токены обновлены успешно")
    else:
        await context.bot.send_message(chat_id=988468804, text="Что-то пошло не так при обновлении токенов")


@trusted_user(check_user)
async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    with open("logs/bot_info.log", 'r', encoding='utf-8') as f:
        last_lines = deque(f, maxlen=10)
        await update.message.reply_text(f"Последние 10 записей из логов:\n{''.join(last_lines)}")


@trusted_user(check_user)
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = """
    /activate_script - запустить бота и начать отслеживание грузов\n\n
/stop_script - остановить бота и отслеживание грузов\n\n
/status - узнать, работает ли бот в данный момент\n\n
/show_logs - посмотреть последние 10 записей из логов, если коды ответа равны 200, значит все хорошо, если код ответа 401 - имеет смысл обновить токены командой /update_tokens. Если код ответа другой, значит нужно разбираться\n\n
/update_tokens - обновление токенов, рекомендуется запустить эту команду, если бот был неактивен больше 10 часов
    """
    await update.message.reply_text(text)


def main() -> None:
    application = Application.builder().token(tg_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("activate_script", activate_script))
    application.add_handler(CommandHandler("stop_script", stop_script))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("update_tokens", update_tokens))
    application.add_handler(CommandHandler("show_logs", show_logs))
    application.add_handler(CommandHandler("help", help))
    interval = 12 * 3600
    application.job_queue.run_repeating(token_refresh, interval=interval, first=0)
    application.run_polling()
    graceful_shutdown("Ctrl+C", "mainFrame")


main()
