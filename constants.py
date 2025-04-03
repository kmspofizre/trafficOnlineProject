import dotenv
import os
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove


dotenv.load_dotenv()
login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")
API_refresh = os.getenv("API_REFRESH")
API_key = os.getenv("API_KEY")
tg_token = os.getenv("BOT_TOKEN")
dadata_secret = os.getenv("DADATA_TOKEN")
dadata_token = os.getenv("DADATA_API")


class JsonManagerException(Exception):
    pass


get_shipping_query = "https://api.traffic.online/api/v1/request_view"
post_application_query = "https://api.traffic.online/api/v1/shipping_requests/"
auth_query = "https://api.traffic.online/api/v1/auth/token"
fias_query = "https://api.traffic.online/api/v1/catalog/address/"
shipping_info_query = "https://api.traffic.online/api/{version}/request_view/"
get_all_shippings_query = "https://api.traffic.online/api/v1/shippings/"

headers_auth = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0",
}

headers_post = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Authorization": ""
}


headers_get = {
    "User-Agent": "Mozilla/5.0",
    "Authorization": ""
}

hg = {
"User-Agent": "Mozilla/5.0",
    "Authorization": f"Bearer {API_key}"
}


login_password = {
    "grant_type": "password",
    "username": login,
    "password": password
}


main_menu_keyboard = [
    ["Статус 📈", "Справка ℹ️"],
    ["Посмотреть логи 🔍", "Запустить скрипт"],
    ["Остановить скрипт", "Направления 🚘"]
]
main_menu_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)

directions_menu_keyboard = [
    ["Из Москвы 🏙", "Из Питера 🌉"],
    ["Из Казани 🕌", "Из Ростова-на-Дону 🌊"],
    ["Из Краснодара 🌳", "Посмотреть активные 🧭"],
    ["Назад"]
]
directions_menu_markup = ReplyKeyboardMarkup(directions_menu_keyboard, resize_keyboard=True)
