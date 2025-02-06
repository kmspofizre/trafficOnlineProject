import dotenv
import os


"""
piter_id = 04f59a69-3bc9-11da-8059-00112fdd6583
mytishy = 652db5a5-55b5-11da-81e1-00112fdd6583
"""


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
    "Authorization": f"Bearer {API_key}"
}


headers_get = {
    "User-Agent": "Mozilla/5.0",
    "Authorization": f"Bearer {API_key}"
}


# из Питера в Москву (МСК id - Мытищи)
spb_to_msc = {
    "max_tonnage": 10,
    "from_location_id": "04f59a69-3bc9-11da-8059-00112fdd6583",
    "from_radius": 300,
    "type": "shipping_request",
    "direction_location_id": "652db5a5-55b5-11da-81e1-00112fdd6583",
    "direction_radius": 300
}


# из Москвы в Питер (МСК id - Мытищи)
msc_to_spb = {
    "max_tonnage": 10,
    "from_location_id": "652db5a5-55b5-11da-81e1-00112fdd6583",
    "from_radius": 300,
    "type": "shipping_request",
    "direction_location_id": "04f59a69-3bc9-11da-8059-00112fdd6583",
    "direction_radius": 300
}

login_password = {
    "grant_type": "password",
    "username": login,
    "password": password
}
