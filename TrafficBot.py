from pydantic import BaseModel
from typing import Dict
from ShippingBooker import ShippingBooker
from ShippingGetter import ShippingGetter
from requests import Session


class TrafficBot(BaseModel):

    post_header: Dict[str, str]
    shipping_getter: ShippingGetter
    shipping_booker: ShippingBooker
    session: Session

    def __init__(self, api_key: str):
        self.session = Session()
        self.shipping_getter = ShippingGetter(self.session, api_key)
        self.shipping_booker = ShippingBooker(self.session, api_key)
        super().__init__()

    def refresh_api_key(self, api_key: str):
        self.get_header['Authorization'] = f"Bearer {api_key}"
        self.post_header['Authorization'] = f"Bearer {api_key}"

    def poll(self):
        pass


