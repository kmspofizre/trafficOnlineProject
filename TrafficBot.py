from typing import Tuple
from ShippingBooker import ShippingBooker
from ShippingRequestsHandler import ShippingGetter
from requests import Session, ConnectionError
from utils import get_ids, save_ids
from loggersetup import setup_logger
import json
import threading
import time
from datetime import datetime, timedelta
from utils import check_process, get_json_data
from exceptions import InstanceIsRunningException, ServerTroubleException, TokenExpiredException


class TrafficBot:
    def __init__(self, api_key: str, data_filename: str, directions_file_path: str):
        self.session = Session()
        self.shipping_getter = ShippingGetter(self.session, api_key)
        self.shipping_booker = ShippingBooker(self.session, api_key)
        self.data_filename = data_filename
        self.shipping_ids = get_ids(data_filename)
        self.logger = setup_logger()
        self.directions_file_path = directions_file_path
        self.running = False
        self.thread = None
        self.last_statuses = []
        self.current_statuses = []
        self.last_status_update = datetime.now() + timedelta(hours=3)
        self.directions = get_json_data(directions_file_path)
        self.thread_lock = threading.Lock()
        super().__init__()

    def refresh_api_key(self, api_key: str) -> Tuple[bool, bool]:
        try:
            self.shipping_getter.update_headers(api_key)
            getter_updated = True
        except KeyError:
            getter_updated = False
        try:
            self.shipping_booker.update_headers(api_key)
            booker_updated = True
        except KeyError:
            booker_updated = False
        return getter_updated, booker_updated

    def start(self) -> str:
        self.directions = get_json_data(self.directions_file_path)
        self.shipping_ids = get_ids(self.data_filename)
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.polling, daemon=True)
            self.thread.start()
            return "Скрипт запущен!"
        return "Скрипт уже работает"

    def stop(self) -> str:
        save_ids(self.shipping_ids, self.data_filename)
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            return "TrafficBot остановлен"
        return "Скрипт не был запущен"

    def polling(self):
        instance_allowed = self.check_instances()
        if not instance_allowed:
            self.logger.error("Уже есть работающий инстанс, нельзя запустить еще один")
            raise InstanceIsRunningException("Уже есть работающий инстанс, нельзя запустить еще один")
        self.logger.info("Запустились")
        self.logger.info(f"Previous ids: {self.shipping_ids}")
        j = 0
        while self.running:
            try:
                with self.thread_lock:
                    direction_responses = self.shipping_getter.get_shipping_responses(self.directions)
                filtered_direction_responses = self.shipping_getter.filter_shipping_responses_by_status_code(
                    direction_responses, self.logger)
                shipping_ids = self.shipping_getter.process_shipping_response(filtered_direction_responses)
                j += 1
                i = len(direction_responses) % 3
                for shipping_id in shipping_ids:
                    self.logger.info(f"Processing: {shipping_id}")
                    if shipping_id not in self.shipping_ids:
                        i += 1
                        with self.thread_lock:
                            shipping_booking_response = self.shipping_booker.book_shipping(shipping_id)
                        shipping_booked = self.shipping_booker.process_booking_response(shipping_booking_response,
                                                                                        self.logger)
                        if shipping_booked:
                            self.shipping_ids.append(shipping_id)
                        if i % 3:
                            time.sleep(2)
                            i = 0
                    else:
                        self.logger.info(f"This id was processed before ({shipping_id})")
            except ServerTroubleException as e:
                pass
            except TokenExpiredException as e:
                pass
            except ConnectionError as e:
                # self.stop с сообщением
                pass
            except Exception as e:
                self.logger.error(e, exc_info=True)
                self.logger.error(e.args)
                time.sleep(2)
            if j % 60 == 0:
                self.last_statuses = list(map(lambda x: x.status_code, direction_responses))
                self.last_status_update = datetime.now() + timedelta(hours=3)
                self.logger.info(f"Последние статусы ответов: {self.last_statuses}")
            if j == 120:
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

    def refresh_directions(self):
        with open(self.directions_file_path, 'r', encoding='utf-8') as file:
            self.directions = json.load(file)

    def is_running(self):
        return self.running

    def get_last_statuses(self):
        return self.last_statuses

    def get_last_status_update(self):
        return self.last_status_update
