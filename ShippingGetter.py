from pydantic import BaseModel
from typing import Dict, List
import json
from requests import Session, Response
from constants import get_shipping_query, headers_get


class ShippingGetter(BaseModel):

    shipping_request_data_spb_to_msc: Dict[str, str]
    shipping_request_data_msc_to_spb: Dict[str, str]
    session: Session
    get_header: Dict[str, str]

    def __init__(self, session: Session, api_key:str):
        with open('jsons/spb_to_msc.json', 'r', encoding='utf-8') as file:
            self.shipping_request_data_spb_to_msc = json.load(file)
        with open('jsons/msc_to_spb.json', 'r', encoding='utf-8') as file:
            self.shipping_request_data_msc_to_spb = json.load(file)
        self.session = session
        self.get_header = headers_get
        headers_get['Authorization'] = f"Bearer {api_key}"
        super().__init__()

    def get_shipping_requests(self) -> List[Response]:
        spb_msc_request = self.session.get(get_shipping_query, headers=headers_get,
                                           params=self.shipping_request_data_spb_to_msc)
        msc_spb_request = self.session.get(get_shipping_query, headers=headers_get,
                                           params=self.shipping_request_data_msc_to_spb)
        return [spb_msc_request, msc_spb_request]

    @staticmethod
    def process_shipping_response(spb_msc_response, msc_spb_response) -> List[str]:
        spb_msc_data = spb_msc_response.json()
        msc_spb_data = msc_spb_response.json()

        spb_msc_items = spb_msc_data.get("items", [])
        msc_spb_items = msc_spb_data.get("items", [])
        new_ids = [item["id"] for item in spb_msc_items if "id" in item]
        new_ids.extend([item["id"] for item in msc_spb_items if "id" in item])
        return new_ids

    def update_headers(self, api_key: str) -> bool:
        try:
            self.get_header['Authorization'] = f"Bearer {api_key}"
            return True
        except KeyError as e:
            return False
