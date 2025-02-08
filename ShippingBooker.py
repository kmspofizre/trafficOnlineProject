from pydantic import BaseModel
from typing import Dict
from requests import Session
from constants import headers_post


class ShippingBooker(BaseModel):
    post_header: Dict[str, str]
    session: Session

    def __init__(self, session: Session, api_key:str):
        self.post_header = headers_post
        headers_post['Authorization'] = f"Bearer {api_key}"
        self.session = session
        super().__init__()
