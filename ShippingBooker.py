from pydantic import BaseModel
from typing import Dict
from requests import Session, Response
from constants import headers_post, post_application_query


class ShippingBooker(BaseModel):
    post_header: Dict[str, str]
    session: Session

    def __init__(self, session: Session, api_key: str):
        self.post_header = headers_post
        headers_post['Authorization'] = f"Bearer {api_key}"
        self.session = session
        super().__init__()

    def book_shipping(self, shipping_id: int) -> Response:
        booking_response = self.session.post(
            f"{post_application_query}{shipping_id}/reserve",
            headers=headers_post)
        return booking_response

    def update_headers(self, api_key: str) -> bool:
        try:
            self.post_header['Authorization'] = f"Bearer {api_key}"
            return True
        except KeyError as e:
            return False
