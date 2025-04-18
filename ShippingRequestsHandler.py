from typing import List
from requests import Session, Response
from constants import get_shipping_query, headers_get
from logging import Logger
import time
from exceptions import TokenExpiredException, ServerTroubleException


class ShippingGetter:
    def __init__(self, session: Session, api_key:str):

        self.session = session
        self.get_header = headers_get
        headers_get['Authorization'] = f"Bearer {api_key}"
        self.request_counter = 0
        super().__init__()

    def get_shipping_responses(self, directions: List) -> List[Response]:
        direction_responses = []
        for direction in directions:
            direction_data = direction
            direction_responses.append(self.session.get(get_shipping_query, headers=headers_get, params=direction_data))
            self.request_counter += 1
            if self.request_counter % 2 == 0:
                self.request_counter = 0
                time.sleep(1)
        return direction_responses

    @staticmethod
    def filter_shipping_responses_by_status_code(shipping_responses: List[Response],
                                                 logger: Logger) -> List[Response]:
        filtered_responses = []
        for shipping_response in shipping_responses:
            if shipping_response.status_code != 200:
                if shipping_response.status_code == 401:
                    raise TokenExpiredException
                if shipping_response.status_code == 503:
                    raise ServerTroubleException
                logger.error(f"Error with shipping: {shipping_response.status_code}"
                             f"shipping response: {shipping_response.text}")
            else:
                filtered_responses.append(shipping_response)
        return filtered_responses

    @staticmethod
    def process_shipping_response(shipping_responses: List[Response]) -> List[str]:
        new_ids = []
        for shipping_response in shipping_responses:
            shipping_response_data = shipping_response.json()
            shipping_response_items = shipping_response_data.get("items", [])
            new_ids.extend([item["id"] for item in shipping_response_items if "id" in item])
        return new_ids

    def update_headers(self, api_key: str):
        self.get_header['Authorization'] = f"Bearer {api_key}"
