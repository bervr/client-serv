"""Программа-клиент"""
import logging
import sys
import json
import socket
import time
import argparse
import logs.conf.client_log_config
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT
from common.utils import get_message, send_message, create_arg_parser
import common.errors as errors
from decor import func_log

CLIENT_LOGGER = logging.getLogger('client')  # забрали логгер из конфига


class MsgClient():
    @func_log
    def create_presence(self, account_name='Guest'):
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }
        CLIENT_LOGGER.debug(f'Сформирован presence: {out}')
        return out


    def process_ans(self, message):
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            return f'400 : {message[ERROR]}'
        raise errors.ReqFieldMissingError(RESPONSE)



    def start(self):
    # def __init__(self):
        # получаем параметры из командной строки
        # client.py -a localhost -p 8079
        CLIENT_LOGGER.debug("Запуск клиента")
        # try:
            # server_address = sys.argv[1]
            # server_port = int(sys.argv[2])
        parser = create_arg_parser()
        namespace = parser.parse_args(sys.argv[1:])
        server_address = namespace.a
        server_port = namespace.p
        CLIENT_LOGGER.debug(f'Адрес и порт сервера {server_address}:{server_port}')

        #     if server_port < 1024 or server_port > 65535:
        #         LOGGER.critical(f'Недопустимый порт сервера {server_port}')
        #         raise ValueError
        # except IndexError:
        #     server_address = DEFAULT_IP_ADDRESS
        #     server_port = DEFAULT_PORT
        #     LOGGER.error(f'Установлены дефолтовые значения - '
        #                         f'{DEFAULT_IP_ADDRESS if DEFAULT_IP_ADDRESS else "любой"} '
        #                         f'ip-адрес  и {DEFAULT_PORT} порт')
        # except ValueError:
        #     LOGGER.critical('В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
        #     # print('В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
        #     sys.exit(1)

        # Инициализация сокета и обмен

        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        CLIENT_LOGGER.debug(f'Подключение к серверу с адресом {server_address if server_address else "localhost"} по {server_port} порту')
        message_to_server = self.create_presence()
        CLIENT_LOGGER.info(f'Отправка сообщения на сервер - {message_to_server}')
        send_message(transport, message_to_server)
        try:
            answer = self.process_ans(get_message(transport))
            # print(answer)
            CLIENT_LOGGER.info(f'Получен ответ от сервера {answer}')
        except (ValueError, json.JSONDecodeError):
            # print('Не удалось декодировать сообщение сервера.')
            CLIENT_LOGGER.critical(f'Не удалось декодировать сообщение от сервера')


if __name__ == '__main__':
    client = MsgClient()
    client.start()