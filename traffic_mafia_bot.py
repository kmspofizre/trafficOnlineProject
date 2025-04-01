import logging
from constants import tg_token, main_menu_markup
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)
from collections import deque
import functools
import inspect
from TrafficBot import TrafficBot
from constants import API_key

MAIN_MENU, DIRECTIONS_MENU, CITY_MENU = range(3)

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
        self.application.add_handler(CommandHandler("show_directions", self.show_directions))
        self.application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", self.start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.main_menu_handler)],
            DIRECTIONS_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.directions_menu_handler)],
            CITY_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.city_menu_handler)],
        },
        fallbacks=[CommandHandler("cancel", self.cancel)],
    ))
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
        # self.application.job_queue.run_repeating(self.check_booked_shipping, interval=120, first=0)
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
        if update.message.from_user.id in (988468804, 2017350326, 273012006):
            return True
        else:
            return False

    @trusted_user(check_user)
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.logger.info(update.message.from_user)
        self.logger.info(update.message.from_user.id)
        await update.message.reply_text(
            "Привет! Traffic Mafia бот на связи, выбери одну из опций",
            reply_markup=main_menu_markup
        )

    @trusted_user(check_user)
    async def activate_script(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        response_text = self.traffic_bot.start()
        await update.message.reply_text(response_text)

    @trusted_user(check_user)
    async def stop_script(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.traffic_bot.set_exit_message(f"Остановлен пользователем {update.message.from_user.username}")
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

            await update.message.reply_text(
                f"Бот в данный момент не работает 😴\nСтатус: {self.traffic_bot.get_exit_message()}\nВремя остановки:"
                f" {self.traffic_bot.get_exit_time().strftime('%d.%m.%Y %H:%M')}")

    @trusted_user(check_user)
    async def update_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        getter_updated, booker_updated = self.traffic_bot.refresh_and_restart()
        await context.bot.send_message(chat_id=update.message.from_user.id,
                                       text=f"Обновление токенов, статус: {getter_updated}, {booker_updated}")

    async def token_refresh(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        getter_updated, booker_updated = self.traffic_bot.refresh_and_restart()
        await context.bot.send_message(chat_id=988468804,
                                       text=f"Обновление токенов, статус: {getter_updated}, {booker_updated}")

    async def check_booked_shipping(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        shipping_string = self.traffic_bot.get_last_booked_string()
        self.traffic_bot.clear_last_booked()
        if shipping_string != "":
            for user in (988468804, 2017350326, 273012006):
                await context.bot.send_message(chat_id=user, text=shipping_string)

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

    @trusted_user(check_user)
    async def show_directions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        directions = self.traffic_bot.get_current_directions_names()
        await update.message.reply_text(directions)

    @trusted_user(check_user)
    async def main_menu_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        pass

    @trusted_user(check_user)
    async def directions_menu_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        pass

    @trusted_user(check_user)
    async def city_menu_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        pass

    @trusted_user(check_user)
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text(
            "Мафия уходит на покой...\nНо только на время",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END