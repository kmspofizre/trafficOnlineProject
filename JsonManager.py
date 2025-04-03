import json
from typing import List

from constants import JsonManagerException
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

class JsonManager:
    def __init__(self, file_path: str = None):
        if file_path:
            self.data = []
            self.file_path = file_path
            self.load_from_file(file_path)
        else:
            raise JsonManagerException("Не передан или не найден файл с данными")

    def load_from_file(self, file_path: str) -> None:
        with open(file_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def save(self) -> None:
        print("saving data")
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get_group_by_id(self, group_id: str) -> dict:
        for group in self.data:
            if group.get("group_id") == group_id:
                return group
        return None

    def get_group_by_name(self, group_name: str) -> str:
        for group in self.data:
            if group.get("group_name") == group_name:
                return group.get("group_id")
        return None

    def get_direction_by_id(self, group_id: str, direction_id: str) -> dict:
        group = self.get_group_by_id(group_id)
        if group:
            for direction in group.get("group_directions", []):
                if direction.get("direction_id") == direction_id:
                    return direction
        return None

    def update_direction_active(self, group_id: str, direction_id: str, active: bool) -> bool:
        direction = self.get_direction_by_id(group_id, direction_id)
        if direction is not None:
            direction["active"] = active
            return True
        return False

    def invert_direction_active(self, group_id: str, direction_id: str) -> bool:
        direction = self.get_direction_by_id(group_id, direction_id)
        if direction is not None:
            direction["active"] = not direction["active"]
            return True
        return False

    def get_direction_active(self, group_id: str, direction_id: str) -> bool:
        direction = self.get_direction_by_id(group_id, direction_id)
        return direction["active"]

    def update_direction_param(self, group_id: str, direction_id: str, param_name: str, param_value) -> bool:
        direction = self.get_direction_by_id(group_id, direction_id)
        if direction:
            direction_params = direction.get("direction_params", {})
            direction_params[param_name] = param_value
            direction["direction_params"] = direction_params
            return True
        return False

    def get_directions_for_group(self, group_id: str) -> list:
        group = self.get_group_by_id(group_id)
        if group:
            return group.get("group_directions", [])
        return []

    def get_direction_params(self, group_id: str, direction_id: str) -> dict:
        direction = self.get_direction_by_id(group_id, direction_id)
        if direction:
            return direction.get("direction_params")
        return {}


    def make_directions_keyboard(self, group: str) -> InlineKeyboardMarkup:
        gr = self.get_group_by_id(group)
        directions = gr.get("group_directions", [])
        directions_items = []
        for direction in directions:
            if direction.get("active"):
                directions_items.append([InlineKeyboardButton(direction.get("direction_name") + " ✅",
                                                             callback_data=f'sd_{group}'
                                                                           f'_{direction.get("direction_id")}')])
            else:
                directions_items.append([InlineKeyboardButton(direction.get("direction_name") + " ❌",
                                                             callback_data=f'sd_{group}'
                                                                           f'_{direction.get("direction_id")}')])


        directions_items.append([InlineKeyboardButton("Назад", callback_data='back')])

        return InlineKeyboardMarkup(directions_items)

    def get_active_directions(self):
        pass

    def get_active_directions_params(self) -> List:
        active_directions = []
        for group in self.data:
            for direction in group.get("group_directions", []):
                if direction.get("active"):
                    active_directions.append(direction.get("direction_params"))
        return active_directions

    def make_active_directions_keyboard(self) -> InlineKeyboardMarkup:
        keyboard = []
        for group in self.data:
            group_id = group.get("group_id")
            group_name = group.get("group_name")
            for direction in group.get("group_directions", []):
                if direction.get("active"):
                    direction_id = direction.get("direction_id")
                    direction_name = direction.get("direction_name")
                    button_text = f"{group_name} - {direction_name} ✅"
                    callback_data = f"ac_{group_id}_{direction_id}"
                    keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
        keyboard.append([InlineKeyboardButton(text="Назад", callback_data="back")])
        return InlineKeyboardMarkup(keyboard)