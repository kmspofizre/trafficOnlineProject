from pydantic import BaseModel
from typing import List
from ShippingBooker import ShippingBooker
from ShippingRequestsHandler import ShippingGetter
from requests import Session
from utils import get_ids, save_ids
from logging import Logger
from loggersetup import setup_logger
import json
import threading
import time
from utils import check_process


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

    def polling(self):
        instance_allowed = self.check_instances()
        if not instance_allowed:
            self.logger.info("Уже есть работающий инстанс, нельзя запустить еще один")
            return
        self.logger.info("Запустились")
        self.logger.info(f"Previous ids: {self.shipping_ids}")
        j = 0
        while True:
            try:
                # здесь нужно перебирать направления, два запроса плохо для масшатбируемости
                with self.thread_lock:
                    direction_responses = self.shipping_getter.get_shipping_responses(self.directions)
                filtered_direction_responses = self.shipping_getter.filter_shipping_responses_by_status_code(
                    direction_responses, self.logger)
                shipping_ids = self.shipping_getter.process_shipping_response(filtered_direction_responses)
                j += 1
                i = len(direction_responses) % 3
                for shipping_id in shipping_ids:
                    i += 1
                    shipping_booking_response = self.shipping_booker.book_shipping(shipping_id)
                    shipping_booked = self.shipping_booker.process_booking_response(shipping_booking_response,
                                                                                    self.logger)
                    if shipping_booked:
                        self.shipping_ids.append(shipping_id)
                    if i == 3:
                        time.sleep(1)
                        i = 0
            except Exception as e:
                self.logger.error(e, exc_info=True)
                self.logger.error(e.args)
                time.sleep(2)
            if j == 70:
                try:
                    j = 0
                    save_ids(self.shipping_ids, self.data_filename)
                    self.logger.info("Ids saved successfully")
                except Exception as e:
                    self.logger.error(f"Something went wrong during id saving: {e}")

    def check_instances(self) -> bool:
        number_of_processes = check_process()[1]
        if number_of_processes <= 1:
            self.logger.info(f"Количество процессов: {number_of_processes}")
            return True
        else:
            self.logger.info(f"Количество процессов: {number_of_processes}")
            return False

    def update_directions(self):
        pass

    def refresh_directions(self, api_key: str):
        pass
