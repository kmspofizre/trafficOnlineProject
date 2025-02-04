import logging


class NoErrorFilter(logging.Filter):
    def filter(self, record):
        return record.levelno < logging.ERROR


def setup_logger():
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    error_handler = logging.FileHandler('logs/bot_errors.log', mode='a', encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    info_handler = logging.FileHandler('logs/bot_info.log', mode='a', encoding='utf-8')
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    info_handler.addFilter(NoErrorFilter())
    logger.addHandler(error_handler)
    logger.addHandler(info_handler)
    return logger
