import logging
from constants import tg_token, main_menu_markup, directions_menu_markup
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters, CallbackQueryHandler
)
from collections import deque
import functools
import inspect
from TrafficBot import TrafficBot
from constants import API_key
from JsonManager import JsonManager
from telegram.error import BadRequest

#TODO: сохранение json
#TODO: refresh изменений в боте


MAIN_MENU, DIRECTIONS_MENU, CITY_MENU = range(3)

class TGTraffic:
    def __init__(self, data_path, directions_path):
        self.traffic_bot = TrafficBot(API_key, data_path, directions_path)
        self.jm = JsonManager(directions_path)
        self.application = Application.builder().token(tg_token).build()
        self.application.add_handler(CommandHandler("activate_script", self.activate_script))
        self.application.add_handler(CommandHandler("stop_script", self.stop_script))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("update_tokens", self.update_tokens))
        self.application.add_handler(CommandHandler("show_logs", self.show_logs))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("show_directions", self.show_directions))
        self.application.add_handler(CallbackQueryHandler(self.direction_callback))
        self.last_inline_message = None
        self.last_group_id = None
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
            #filename='logs/tg.log',
            #filemode='a'
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
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        self.logger.info(update.message.from_user)
        self.logger.info(update.message.from_user.id)
        await update.message.reply_text(
            "Привет! Traffic Mafia бот на связи, выбери одну из опций",
            reply_markup=main_menu_markup
        )
        return MAIN_MENU

    def get_help(self) -> str:
        return (
            "Справка:\n"
            "1. Статус — показывает текущее состояние бота.\n"
            "2. Справка — выводит это сообщение.\n"
            "3. Посмотреть логи — показывает логи.\n"
            "4. Запустить скрипт — запускает скрипт.\n"
            "5. Остановить скрипт — останавливает скрипт.\n"
            "6. Направления — позволяет выбрать направления."
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
        await update.message.reply_text(self.traffic_bot.get_operating_status())

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
        text = update.message.text
        print("here")
        if text == "Статус 📈":
            print("here2")
            await update.message.reply_text(self.traffic_bot.get_operating_status(), reply_markup=main_menu_markup)
            return MAIN_MENU

        elif text == "Справка ℹ️":
            await update.message.reply_text(self.get_help(), reply_markup=main_menu_markup)
            return MAIN_MENU

        elif text == "Посмотреть логи 🔍":
            with open("logs/bot_info.log", 'r', encoding='utf-8') as f:
                last_lines = deque(f, maxlen=10)
                await update.message.reply_text(f"Последние 10 записей из логов:\n{''.join(last_lines)}")
            return MAIN_MENU

        elif text == "Запустить скрипт ▶":
            response_text = self.traffic_bot.start()
            await update.message.reply_text(response_text)
            return MAIN_MENU

        elif text == "Остановить скрипт ⛔":
            self.traffic_bot.set_exit_message(f"Остановлен пользователем {update.message.from_user.username}")
            response_text = self.traffic_bot.stop()
            await update.message.reply_text(response_text)
            return MAIN_MENU

        elif text == "Направления 🚘":
            await update.message.reply_text("Выберите город:", reply_markup=directions_menu_markup)
            return DIRECTIONS_MENU

        else:
            await update.message.reply_text(
                "Неизвестная команда. Пожалуйста, выберите действие из меню.",
                reply_markup=main_menu_markup
            )
            return MAIN_MENU

    @trusted_user(check_user)
    async def directions_menu_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text
        if text in ("Из Москвы 🏙", "Из Питера 🌉", "Из Казани 🕌", "Из Ростова-на-Дону 🌊", "Из Краснодара 🌳"):
            direction_group = self.jm.get_group_by_name(text)
            await self.delete_last_inline()
            if direction_group:
                keyboard = self.jm.make_directions_keyboard(direction_group)
                self.last_inline_message = await update.message.reply_text(f"Направления {text}", reply_markup=keyboard)
                return DIRECTIONS_MENU

        elif text == "Посмотреть активные 🧭":
            await self.delete_last_inline()
            active_keyboard = self.jm.make_active_directions_keyboard()
            self.last_inline_message = await update.message.reply_text("Активные направления:",
                                                                       reply_markup=active_keyboard)
            return DIRECTIONS_MENU
        elif text == "Назад":
            await self.delete_last_inline()
            await update.message.reply_text("Возвращаемся:", reply_markup=main_menu_markup)
            return MAIN_MENU
        else:
            await self.delete_last_inline()
            await update.message.reply_text(
                "Неизвестная команда. Пожалуйста, выберите действие из меню.",
                reply_markup=main_menu_markup
            )
            return DIRECTIONS_MENU

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

    async def direction_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        if query.data == 'back':
            await query.message.delete()
            return

        direction_info = query.data.split('_')
        if len(direction_info) == 3:
            if direction_info[0] == "sd":
                self.jm.invert_direction_active(direction_info[1], direction_info[2])
                self.jm.save()
                updated_keyboard = self.jm.make_directions_keyboard(direction_info[1])
                await query.edit_message_reply_markup(reply_markup=updated_keyboard)
            elif direction_info[0] == "ac":
                self.jm.invert_direction_active(direction_info[1], direction_info[2])
                self.jm.save()
                updated_keyboard = self.jm.make_active_directions_keyboard()
                await query.edit_message_reply_markup(reply_markup=updated_keyboard)

    async def delete_last_inline(self):
        if self.last_inline_message is not None:
            try:
                await self.last_inline_message.delete()
            except BadRequest:
                pass







