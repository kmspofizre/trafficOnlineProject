import requests
import time
import csv
from loggersetup import setup_logger
from headers import headers_post, headers_get, spb_to_msc, msc_to_spb, get_shipping_query, post_application_query
from utils import check_process
logger = setup_logger()

session = requests.Session()

# TODO: добавить проверку, есть ли инстанс


def get_ids():
    ids = []
    with open('data.csv', mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ids.append(row['id'])
    return ids


SHIPPING_IDS = get_ids()


def save_ids(ids):
    with open('data.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        writer.writerow(['id'])

        for id_value in ids:
            writer.writerow([id_value])


def trafficbot():
    logger.info(f"Previous ids: {SHIPPING_IDS}")
    j = 0
    while True:
        try:
            spb_msc_request = session.get(get_shipping_query, headers=headers_get, params=spb_to_msc)
            msc_spb_request = session.get(get_shipping_query, headers=headers_get, params=msc_to_spb)

            spb_msc_data = spb_msc_request.json()
            msc_spb_data = msc_spb_request.json()

            spb_msc_items = spb_msc_data.get("items", [])
            msc_spb_items = msc_spb_data.get("items", [])
            new_ids = [item["id"] for item in spb_msc_items if "id" in item]
            new_ids.extend([item["id"] for item in msc_spb_items if "id" in item])
            logger.info(f"С Питера: {spb_msc_request.status_code}")
            logger.info(f"С Москвы: {msc_spb_request.status_code}")
            logger.info(f"Список id: {new_ids}")
            i = 2
            j += 1
            for new_item in new_ids:
                if new_item not in SHIPPING_IDS:
                    i += 1
                    application_request = session.post(
                        f"{post_application_query}{new_item}/reserve",
                        headers=headers_post)
                    logger.info(f"Запрос для груза {new_item}: {application_request.status_code}")
                    if application_request.status_code == 200:
                        logger.info("Gotcha!")
                    else:
                        logger.error(f"Couldn't book this shipping with error code: {application_request.status_code}")
                        logger.error(application_request.json())
                    SHIPPING_IDS.append(new_item)
                    if i == 3:
                        time.sleep(1)
                        i = 0
            time.sleep(1)
        except Exception as e:
            logger.error(e)
            logger.error(e.args)
            time.sleep(2)
        if j == 70:
            try:
                j = 0
                save_ids(SHIPPING_IDS)
                logger.info("Ids saved successfully")
            except Exception as e:
                logger.error(f"Something went wrong during id saving: {e}")


if __name__ == '__main__':
    process_exists, number_of_processes = check_process()
    if not process_exists:
        trafficbot()
        logger.info(f"Количество процессов: {number_of_processes}")
    else:
        logger.info(f"Количество процессов: {number_of_processes}")
        logger.info("Уже есть работающий инстанс, нельзя запустить еще один")
        print("Уже есть работающий инстанс, нельзя запустить еще один")