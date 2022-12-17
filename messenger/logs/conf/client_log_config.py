"""Настройки логирования клиента"""
import logging
import os
import sys

sys.path.append(os.path.join(os.getcwd(), '../..'))
from common.variables import LOGGING_LEVEL



PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
PATH = os.path.join(PATH, 'client.log')

# создали логгер
CLIENT_LOGGER = logging.getLogger('client')

# задаем уровень важности
CLIENT_LOGGER.setLevel(logging.DEBUG)

# создали хендлер, указали куда писать лог
FILE_HANDLER = logging.FileHandler(PATH, encoding="UTF-8")

# уровень логгирования для данного хендлера
FILE_HANDLER.setLevel(logging.DEBUG)

# задаем формант логгирования
FORMATTER = logging.Formatter("%(asctime)-25s %(levelname)-9s %(filename)-10s %(message)s")

# привязали формалирование к хендлеру
FILE_HANDLER.setFormatter(FORMATTER)

# привязали хендлер к логгеру
CLIENT_LOGGER.addHandler(FILE_HANDLER)

# еще один хедлер для вывода ошибок в консоль:
# создали хендлер
STREAM_HANDLER = logging.StreamHandler(sys.stdout)

# уровень логгирования для данного хендлера
STREAM_HANDLER.setLevel(logging.CRITICAL)

# привязали формалирование к хендлеру
STREAM_HANDLER.setFormatter(FORMATTER)

# привязали хендлер к логгеру
CLIENT_LOGGER.addHandler(STREAM_HANDLER)

if __name__ == '__main__':
    CLIENT_LOGGER.debug('test debug message')
    CLIENT_LOGGER.info('test info message')
    CLIENT_LOGGER.warning('test warning message')
    CLIENT_LOGGER.critical('test critical message')
    CLIENT_LOGGER.error('test error message')
