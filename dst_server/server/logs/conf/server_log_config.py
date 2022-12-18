"""Параметры логирования сервера"""

import logging
import logging.handlers
import os
import sys
# дабавим путь для импорта переменной
sys.path.append(os.path.join(os.getcwd(), '../../../../messenger/server'))
from common.variables import LOGGING_LEVEL

# задаем путь куда будем писать
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
PATH = os.path.join(PATH, 'server.log')

# создали логгер
SERVER_LOGGER = logging.getLogger('server')

#
# LOGGER.setLevel(logging.INFO)

# уровень логгирования для данного хендлера
FILE_ROTATE_HANDLER = logging.handlers.TimedRotatingFileHandler(PATH, encoding='utf-8', interval=1, when='D')
# FILE_ROTATE_HANDLER.setLevel(logging.DEBUG)

# формат логгирования
FORMATTER = logging.Formatter("%(asctime)-25s %(levelname)-9s %(filename)-10s %(message)s")

# привязали форматирование к хендлеру
FILE_ROTATE_HANDLER.setFormatter(FORMATTER)

# привязали хендлер к логгеру
SERVER_LOGGER.addHandler(FILE_ROTATE_HANDLER)

# facility
SERVER_LOGGER.setLevel(LOGGING_LEVEL)

# еще один хедлер для вывода ошибок в консоль:
# создали хендлер
STREAM_HANDLER = logging.StreamHandler(sys.stdout)

# уровень логгирования для данного хендлера
STREAM_HANDLER.setLevel(logging.CRITICAL)

# привязали формалирование к хендлеру
STREAM_HANDLER.setFormatter(FORMATTER)

# привязали хендлер к логгеру
SERVER_LOGGER.addHandler(STREAM_HANDLER)

if __name__ == '__main__':
    SERVER_LOGGER.debug('test debug message')
    SERVER_LOGGER.info('test info message')
    SERVER_LOGGER.warning('test warning message')
    SERVER_LOGGER.critical('test critical message')
    SERVER_LOGGER.error('test error message')
