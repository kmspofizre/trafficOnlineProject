import requests
import dotenv
from headers import headers_auth, login_password


def refresh_tokens():
    dotenv_path = ".env"

    r = requests.post("https://api.traffic.online/api/v1/auth/token", json=login_password, headers=headers_auth)

    d_refresh = {
        "grant_type": "refresh_token",
        "refresh_token": r.json().get("refresh_token")
    }
    r1 = requests.post("https://api.traffic.online/api/v1/auth/token", json=d_refresh, headers=headers_auth)
    data = r1.json()
    dotenv.set_key(dotenv_path, 'API_KEY', data.get("access_token"))
    dotenv.set_key(dotenv_path, 'API_REFRESH', data.get("refresh_token"))
    return r1.status_code
