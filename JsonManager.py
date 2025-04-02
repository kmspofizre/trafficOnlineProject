import json
from constants import JsonManagerException
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

class JsonManager:
    def __init__(self, file_path: str = None):
        """
        Если передана строка с JSON, загружаем данные из неё, иначе инициализируем пустой список.
        """
        if file_path:
            self.data = []
            self.load_from_file(file_path)
        else:
            raise JsonManagerException("Не передан или не найден файл с данными")

    def load_from_file(self, file_path: str) -> None:
        with open(file_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def save_to_file(self, file_path: str) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get_group_by_id(self, group_id: str) -> dict:
        for group in self.data:
            if group.get("group_id") == group_id:
                return group
        return None

    def get_group_by_name(self, group_name: str) -> dict:
        for group in self.data:
            if group.get("group_name") == group_name:
                return group
        return None

    def get_direction_by_id(self, group_id: str, direction_id: str) -> dict:
        """
        Возвращает словарь направления по его идентификатору внутри заданной группы.
        Если группа или направление не найдены, возвращается None.
        """
        group = self.get_group_by_id(group_id)
        if group:
            for direction in group.get("group_directions", []):
                if direction.get("direction_id") == direction_id:
                    return direction
        return None

    def update_direction_active(self, group_id: str, direction_id: str, active: bool) -> bool:
        """
        Изменяет значение поля 'active' для направления в заданной группе.
        Возвращает True, если обновление прошло успешно, иначе False.
        """
        direction = self.get_direction_by_id(group_id, direction_id)
        if direction is not None:
            direction["active"] = active
            return True
        return False

    def get_direction_active(self, group_id: str, direction_id: str) -> bool:
        direction = self.get_direction_by_id(group_id, direction_id)
        return direction["active"]

    def update_direction_param(self, group_id: str, direction_id: str, param_name: str, param_value) -> bool:
        """
        Изменяет произвольный параметр в 'direction_params' для указанного направления.
        Возвращает True, если параметр найден и обновлён, иначе False.
        """
        direction = self.get_direction_by_id(group_id, direction_id)
        if direction:
            direction_params = direction.get("direction_params", {})
            direction_params[param_name] = param_value
            direction["direction_params"] = direction_params
            return True
        return False

    def get_directions_for_group(self, group_id: str) -> list:
        """
        Возвращает список всех направлений для заданной группы.
        Если группа не найдена, возвращает пустой список.
        """
        group = self.get_group_by_id(group_id)
        if group:
            return group.get("group_directions", [])
        return []

    def get_direction_params(self, group_id: str, direction_id: str) -> dict:
        direction = self.get_direction_by_id(group_id, direction_id)
        if direction:
            return direction.get("direction_params")
        return {}

    @staticmethod
    def make_directions_keyboard(group: dict) -> InlineKeyboardMarkup:
        directions = group.get("group_directions", [])
        directions_items = []
        for direction in directions:
            if direction.get("active"):
                directions_items.append([InlineKeyboardButton(direction.get("direction_name") + " ✅",
                                                             callback_data=f'{group.get("group_id")}'
                                                                           f'_{direction.get("direction_id")}')])
            else:
                directions_items.append([InlineKeyboardButton(direction.get("direction_name") + " ❌",
                                                             callback_data=f'{group.get("group_id")}'
                                                                           f'_{direction.get("direction_id")}')])


        directions_items.append([InlineKeyboardButton("Назад", callback_data='back')])

        return InlineKeyboardMarkup(directions_items)