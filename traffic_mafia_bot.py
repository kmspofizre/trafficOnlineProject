import logging
from constants import tg_token
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)
from refresh import refresh_tokens
from collections import deque
import functools
import inspect
import time
from TrafficBot import TrafficBot
from constants import API_key


class TGTraffic:
    def __init__(self, data_path, directions_path):
        self.traffic_bot = TrafficBot(API_key, data_path, directions_path)
        self.application = Application.builder().token(tg_token).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("activate_script", self.activate_script))
        self.application.add_handler(CommandHandler("stop_script", self.stop_script))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("update_tokens", self.update_tokens))
        self.application.add_handler(CommandHandler("show_logs", self.show_logs))
        self.application.add_handler(CommandHandler("help", self.help))
        self.interval = 12 * 3600
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO,
            filename='logs/tg.log',
            filemode='a'
        )
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.application.job_queue.run_repeating(self.token_refresh, interval=self.interval, first=0)
        self.application.run_polling()

    @staticmethod
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

    async def check_user(self, update, context):
        if update.message.from_user.id in (988468804, 2017350326):
            return True
        else:
            return False

    @trusted_user(check_user)
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.logger.info(update.message.from_user)
        self.logger.info(update.message.from_user.id)
        await update.message.reply_text(
            "Привет! Проверка связи, теперь мне могут писать только два человека"
        )

    @trusted_user(check_user)
    async def activate_script(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        response_text = self.traffic_bot.start()
        await update.message.reply_text(response_text)

    @trusted_user(check_user)
    async def stop_script(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        response_text = self.traffic_bot.stop()
        await update.message.reply_text(response_text)

    @trusted_user(check_user)
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        process_running = self.traffic_bot.is_running()
        if process_running:
            await update.message.reply_text("Бот на охоте за грузами 😈"
                                            f"\nПоследние статусы ответов: {self.traffic_bot.get_last_statuses()}"
                                            f"\nВремя обновления: "
                                            f"{self.traffic_bot.get_last_status_update().strftime('%d.%m.%Y %H:%M')}")
        else:
            await update.message.reply_text("Бот в данный момент не работает 😴")

    @trusted_user(check_user)
    async def update_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.logger.info("Обновляю токены")
        refresh_status, data = refresh_tokens()
        time.sleep(2)
        if refresh_status == 200:
            getter_updated, booker_updated = self.traffic_bot.refresh_api_key(data.get("access_token"))
            await context.bot.send_message(chat_id=update.message.from_user.id,
                                           text=f"Обновление токенов, статус: {getter_updated}, {booker_updated}")
        else:
            await context.bot.send_message(chat_id=update.message.from_user.id,
                                           text="Что-то пошло не так при обновлении токенов")

    async def token_refresh(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.logger.info("Обновляю токены")
        refresh_status, data = refresh_tokens()
        time.sleep(2)
        if refresh_status == 200:
            getter_updated, booker_updated = self.traffic_bot.refresh_api_key(data.get("access_token"))
            await context.bot.send_message(chat_id=988468804,
                                           text=f"Обновление токенов, статус: {getter_updated}, {booker_updated}")
        else:
            await context.bot.send_message(chat_id=988468804,
                                           text="Что-то пошло не так при обновлении токенов")

    @trusted_user(check_user)
    async def show_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        with open("logs/bot_info.log", 'r', encoding='utf-8') as f:
            last_lines = deque(f, maxlen=10)
            await update.message.reply_text(f"Последние 10 записей из логов:\n{''.join(last_lines)}")

    @trusted_user(check_user)
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        text = """
        /activate_script - запустить бота и начать отслеживание грузов\n\n
    /stop_script - остановить бота и отслеживание грузов\n\n
    /status - узнать, работает ли бот в данный момент\n\n
    /show_logs - посмотреть последние 10 записей из логов, если коды ответа равны 200, значит все хорошо, если код ответа 401 - имеет смысл обновить токены командой /update_tokens. Если код ответа другой, значит нужно разбираться\n\n
    /update_tokens - обновление токенов, рекомендуется запустить эту команду, если бот был неактивен больше 10 часов
        """
        await update.message.reply_text(text)








