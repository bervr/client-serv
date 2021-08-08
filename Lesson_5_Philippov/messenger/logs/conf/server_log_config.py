import logging
import logging.handlers
import os
import sys
sys.path.append(os.path.join(os.getcwd(), '../..'))
from common.variables import LOGGING_LEVEL


PATH =os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
PATH = os.path.join(PATH, 'server.log')  # куда будем писать

SERVER_LOGGER = logging.getLogger('server')  # создали логгер
SERVER_LOGGER.setLevel(logging.INFO)  # уровень важности
FILE_ROTATE_HANDLER = logging.handlers.TimedRotatingFileHandler(PATH, encoding='utf-8', interval=1, when='D')
# FILE_ROTATE_HANDLER.setLevel(logging.DEBUG)  # уровень логгирования для данного хендлера
FORMATTER = logging.Formatter("%(asctime)-25s %(levelname)-9s %(filename)-10s %(message)s")  # формант логгирования
FILE_ROTATE_HANDLER.setFormatter(FORMATTER)  # привязали формалирование к хендлеру
SERVER_LOGGER.addHandler(FILE_ROTATE_HANDLER)  # привязали хендлер к логгеру
SERVER_LOGGER.setLevel(LOGGING_LEVEL)
# еще один хедлер для вывода ошибок в консоль:
STREAM_HANDLER = logging.StreamHandler(sys.stdout)  # создали хендлер
STREAM_HANDLER.setLevel(logging.INFO)  # уровень логгирования для данного хендлера
STREAM_HANDLER.setFormatter(FORMATTER)  # привязали формалирование к хендлеру
SERVER_LOGGER.addHandler(STREAM_HANDLER)  # привязали хендлер к логгеру

if __name__ == '__main__':
    SERVER_LOGGER.debug('test debug message')
    SERVER_LOGGER.info('test info message')
    SERVER_LOGGER.warning('test warning message')
    SERVER_LOGGER.critical('test critical message')
    SERVER_LOGGER.error('test error message')
