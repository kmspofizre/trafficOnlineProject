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
from utils import check_process, get_directions_from_json
from exceptions import InstanceIsRunningException, ServerTroubleException, TokenExpiredException
from refresh import refresh_tokens
from utils import get_shipping_info_from_json
from constants import shipping_info_query


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
        self.directions = get_directions_from_json(directions_file_path)
        self.thread_lock = threading.Lock()
        self.exit_message = ""
        self.exit_time = datetime.now() + timedelta(hours=3)
        self.last_booked = []
        self.activated_directions = []
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
        self.exit_message = ""
        self.directions = get_directions_from_json(self.directions_file_path)
        self.shipping_ids = get_ids(self.data_filename)
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.polling, daemon=True)
            self.thread.start()
            return "Скрипт запущен!"
        return "Скрипт уже работает"

    def stop(self) -> str:
        save_ids(self.shipping_ids, self.data_filename)
        self.exit_time = datetime.now() + timedelta(hours=3)
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
                    direction_responses = self.shipping_getter.get_shipping_responses(self.activated_directions)
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
                            self.last_booked.append(shipping_id)
                        if i % 3 == 0:
                            time.sleep(1)
                            i = 0
                    else:
                        self.logger.info(f"This id was processed before ({shipping_id})")
            except ServerTroubleException:
                self.exit_message = "Проблемы на внешнем сервере"
                self.stop()
            except TokenExpiredException:
                self.refresh_and_restart()
            except ConnectionError:
                self.exit_message = "ConnectionError при попытке запроса"
                self.stop()
            except Exception as e:
                self.logger.error(e, exc_info=True)
                self.logger.error(e.args)
                time.sleep(2)
            if j % 30 == 0:
                self.last_statuses = list(map(lambda x: x.status_code, direction_responses))
                self.last_status_update = datetime.now() + timedelta(hours=3)
                self.logger.info(f"Последние статусы ответов: {self.last_statuses}")
            if j == 60:
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

    def get_exit_message(self):
        return self.exit_message

    def refresh_and_restart(self):
        self.logger.info("Обновляю токены")
        refresh_status, data = refresh_tokens()
        time.sleep(2)
        if refresh_status == 200:
            getter_updated, booker_updated = self.refresh_api_key(data.get("access_token"))
            self.logger.info(f"Обновление токенов, статус: {getter_updated}, {booker_updated}")
            if self.running:
                self.start()
            return getter_updated, booker_updated
        else:
            self.logger.info(f"Что-то пошло не так при обновлении токенов")
            self.exit_message = "Не удалось обновить токены"
            return False, False

    def get_exit_time(self):
        return self.exit_time

    def set_exit_message(self, exit_message):
        self.exit_message = exit_message

    def get_current_directions_names(self):
        i = 1
        directions = ""
        for direction in self.directions:
            directions += f"{i}. {direction['direction_name']}: " \
                          f"радиус пункта отправления - {direction['direction_params']['from_radius']} км; " \
                          f"радиус пункта назначения - {direction['direction_params']['direction_radius']}\n"
            i += 1
        return directions

    def get_shipping_info_by_id(self, shipping_id) -> str:
        ship_info = self.session.get(f"{shipping_info_query}{shipping_id}")
        shipping_json = ship_info.json()
        shipping_info_string = get_shipping_info_from_json(shipping_json)
        return shipping_info_string

    def get_last_booked_string(self):
        shipping_string = list(map(lambda x: self.get_shipping_info_by_id(x), self.last_booked))
        return "\n".join(shipping_string)

    def clear_last_booked(self):
        self.last_booked = []
