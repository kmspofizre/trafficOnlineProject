import requests
import dotenv
from constants import headers_auth, login_password


def refresh_tokens():
    dotenv_path = ".env"

    r = requests.post("https://api.traffic.online/api/v1/auth/token", json=login_password, headers=headers_auth)
    data = r.json()
    dotenv.set_key(dotenv_path, 'API_KEY', data.get("access_token"))
    dotenv.set_key(dotenv_path, 'API_REFRESH', data.get("refresh_token"))
    return r.status_code
