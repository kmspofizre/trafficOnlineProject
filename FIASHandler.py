from requests import Session
from dadata import Dadata
from constants import dadata_token, dadata_secret, fias_query


class FIASHandler:
    def __init__(self):
        self.session = Session()
        self.dadata = Dadata(dadata_token, dadata_secret)

    def get_fias_by_name(self, object_name):
        object_data = self.dadata.clean("address", object_name)
        object_fias = object_data["fias_id"]
        return object_fias

    def compare_fias_with_traffic(self, object_fias):
        get_object_from_traffic = self.session.get(f"{fias_query}{object_fias}")
        if get_object_from_traffic.status_code == 200:
            return True
        else:
            return False
