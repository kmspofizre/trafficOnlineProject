from pydantic import BaseModel
from typing import List, Dict
from ShippingBooker import ShippingBooker
from ShippingRequestsHandler import ShippingGetter
from requests import Session
from utils import get_ids
from logging import Logger
from loggersetup import setup_logger
from exceptions import ShippingGetterException
import json
import threading


class TrafficBot(BaseModel):

    shipping_getter: ShippingGetter
    shipping_booker: ShippingBooker
    session: Session
    shipping_ids: List[str]
    data_filename: str
    logger: Logger
    directions: List
    thread_lock: threading.Lock

    def __init__(self, api_key: str, data_filename: str):
        self.session = Session()
        self.shipping_getter = ShippingGetter(self.session, api_key)
        self.shipping_booker = ShippingBooker(self.session, api_key)
        self.data_filename = data_filename
        self.shipping_ids = get_ids(data_filename)
        self.logger = setup_logger()
        with open('jsons/directions.json', 'r', encoding='utf-8') as file:
            self.directions = json.load(file)
        self.thread_lock = threading.Lock()
        super().__init__()

    def refresh_api_key(self, api_key: str):
        self.shipping_getter.update_headers(api_key)
        self.shipping_booker.update_headers(api_key)

    def refresh_directions(self, api_key: str):
        pass

    def polling(self):
        self.logger.info(f"Previous ids: {self.shipping_ids}")
        j = 0
        while True:
            try:
                # здесь нужно перебирать направления, два запроса плохо для масшатбируемости
                with self.thread_lock:
                    direction_responses = self.shipping_getter.get_shipping_responses(self.directions)

                if direction_responses[0].status_code:
                    # process для каждого
                    raise ShippingGetterException
            except ShippingGetterException as shipping_getter_exception:
                self.logger.error(f"an error during handling get request")
            except Exception as e:
                pass

    def update_directions(self):
        pass