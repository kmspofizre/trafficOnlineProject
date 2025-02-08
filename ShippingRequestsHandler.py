from pydantic import BaseModel
from typing import Dict, List
from requests import Session, Response
from constants import get_shipping_query, headers_get
from logging import Logger
import time


class ShippingGetter(BaseModel):

    shipping_request_data_spb_to_msc: Dict[str, str]
    shipping_request_data_msc_to_spb: Dict[str, str]
    session: Session
    get_header: Dict[str, str]

    def __init__(self, session: Session, api_key:str):

        self.session = session
        self.get_header = headers_get
        headers_get['Authorization'] = f"Bearer {api_key}"
        super().__init__()

    def get_shipping_responses(self, directions: List) -> List[Response]:
        direction_responses = []
        i = 0
        for direction in directions:
            direction_responses.append(self.session.get(get_shipping_query, headers=headers_get, params=direction))
            i += 1
            if i % 3 == 0:
                time.sleep(1)
                i = 0
        return direction_responses

    @staticmethod
    def filter_shipping_responses_by_status_code(shipping_responses: List[Response],
                                                 logger: Logger) -> List[Response]:
        filtered_responses = []
        for shipping_response in shipping_responses:
            if shipping_response.status_code != 200:
                logger.error(f"Error with shipping: {shipping_response.status_code} {shipping_response.text}")
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

    def update_headers(self, api_key: str) -> bool:
        try:
            self.get_header['Authorization'] = f"Bearer {api_key}"
            return True
        except KeyError as e:
            return False
