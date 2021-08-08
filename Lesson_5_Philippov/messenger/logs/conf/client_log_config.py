import logging
import os
import sys

PATH =os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
PATH = os.path.join(PATH, 'client.log')  # куда будем писать

CLIENT_LOGGER = logging.getLogger('client')  # создали логгер
CLIENT_LOGGER.setLevel(logging.INFO)  # уровень важности
FILE_HANDLER = logging.FileHandler(PATH)  # создали хендлер, указали куда писать лог
FILE_HANDLER.setLevel(logging.DEBUG)  # уровень логгирования для данного хендлера
FORMATTER = logging.Formatter("%(asctime)-25s %(levelname)-9s %(filename)-10s %(message)s")  # формант логгирования
FILE_HANDLER.setFormatter(FORMATTER)  # привязали формалирование к хендлеру
CLIENT_LOGGER.addHandler(FILE_HANDLER)  # привязали хендлер к логгеру

# еще один хедлер для вывода ошибок в консоль:
STREAM_HANDLER = logging.StreamHandler(sys.stdout)  # создали хендлер
STREAM_HANDLER.setLevel(logging.CRITICAL)  # уровень логгирования для данного хендлера
STREAM_HANDLER.setFormatter(FORMATTER)  # привязали формалирование к хендлеру
CLIENT_LOGGER.addHandler(STREAM_HANDLER)  # привязали хендлер к логгеру

if __name__ == '__main__':
    CLIENT_LOGGER.debug('test debug message')
    CLIENT_LOGGER.info('test info message')
    CLIENT_LOGGER.warning('test warning message')
    CLIENT_LOGGER.critical('test critical message')
    CLIENT_LOGGER.error('test error message')
