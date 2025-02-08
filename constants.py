import dotenv
import os


dotenv.load_dotenv()
login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")
API_refresh = os.getenv("API_REFRESH")
API_key = os.getenv("API_KEY")
tg_token = os.getenv("BOT_TOKEN")

get_shipping_query = "https://api.traffic.online/api/v1/request_view"
post_application_query = "https://api.traffic.online/api/v1/shipping_requests/"

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


login_password = {
    "grant_type": "password",
    "username": login,
    "password": password
}
