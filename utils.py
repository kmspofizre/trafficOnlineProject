import subprocess
import csv
import json


def check_process():
    command = 'ps aux | grep "[p]ython3 main.py"'
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout.strip()

    if output:
        print("Найденные процессы:")
        print(output)
        print(len(output.split("\n")))
        return True, len(output.split("\n"))
    else:
        print("Процесс main.py не найден.")
        return False, 0


def get_ids(filename):
    ids = []
    with open(filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ids.append(row['id'])
    return ids


def save_ids(ids, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        writer.writerow(['id'])

        for id_value in ids:
            writer.writerow([id_value])


def save_json(json_filename, data):
    with open(json_filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def get_directions_from_json(json_filename):
    with open(json_filename, 'r', encoding='utf-8') as file:
        return json.load(file)


def get_shipping_info_from_json(json_string):
    data = json.loads(json_string)

    route_points = data.get("route_points", [])

    if len(route_points) >= 2:
        from_point = route_points[0].get("location", {}).get("city", "Неизвестно")
        to_point = route_points[-1].get("location", {}).get("city", "Неизвестно")
    else:
        from_point, to_point = "Неизвестно", "Неизвестно"

    dates = []
    for point in route_points:
        supply_range = point.get("car_supply_range", [])
        for period in supply_range:
            dates.append(period.get("from"))

    return f"Пункт отправления: {from_point}\nПункт назначения: {to_point}\nДаты перевозки: {dates}"