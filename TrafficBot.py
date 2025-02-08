from pydantic import BaseModel
from typing import List
from ShippingBooker import ShippingBooker
from ShippingGetter import ShippingGetter
from requests import Session
from utils import get_ids


class TrafficBot(BaseModel):

    shipping_getter: ShippingGetter
    shipping_booker: ShippingBooker
    session: Session
    shipping_ids: List[str]
    data_filename: str

    def __init__(self, api_key: str, data_filename: str):
        self.session = Session()
        self.shipping_getter = ShippingGetter(self.session, api_key)
        self.shipping_booker = ShippingBooker(self.session, api_key)
        self.data_filename = data_filename
        self.shipping_ids = get_ids(data_filename)
        super().__init__()

    def refresh_api_key(self, api_key: str):
        self.shipping_getter.update_headers(api_key)
        self.shipping_booker.update_headers(api_key)

    def poll(self):
        pass


