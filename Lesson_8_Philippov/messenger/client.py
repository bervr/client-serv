"""Программа-клиент"""
import logging
import sys
import json
import socket
import time
import argparse
import logs.conf.client_log_config
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, MESSAGE_TEXT, MESSAGE
from common.utils import get_message, send_message, create_arg_parser
import common.errors as errors
from decor import func_log
from threading import Thread

LOGGER = logging.getLogger('client')  # забрали логгер из конфига


class MsgClient:
    @func_log
    def create_presence(self, account_name='Guest'):
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }
        LOGGER.debug(f'Сформирован presence: {out}')
        return out

    def create_message(self, account_name='Guest'):
        message = input('Введите сообщения для отправки или !!! для выхода: ')
        if message == '!!!':
            self.transport.close()
            LOGGER.info('Пользователь завершил работу приложения')
            sys.exit(0)
        out = {
            ACTION: MESSAGE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name,
                MESSAGE_TEXT: message
            }
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {out}')
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
        # client.py -a localhost -p 8079 -m send/listen
        LOGGER.debug("Запуск клиента")
        parser = create_arg_parser()
        namespace = parser.parse_args(sys.argv[1:])
        server_address = namespace.a
        server_port = namespace.p
        client_mode = namespace.m
        LOGGER.debug(f'Адрес и порт сервера {server_address}:{server_port}')
        try:
            self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.transport.connect((server_address, server_port))
            # print(self.transport)
            print(self.transport.getsockname()[1])
            LOGGER.debug(
                f'Подключение к серверу с адресом {server_address if server_address else "localhost"} '
                f'по {server_port} порту')
        except ConnectionRefusedError:
            LOGGER.error(f'Не удалось подключится к серверу {server_address}:{server_port}, '
                         f'возможн он не запущен или что-то с сетью')
        except json.JSONDecodeError:
            LOGGER.error('Не удалось декодировать полученную Json строку.')
            sys.exit(1)
        except errors.ServerError as error:
            LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
            sys.exit(1)
        except errors.ReqFieldMissingError as missing_error:
            LOGGER.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
            sys.exit(1)

        message_to_server = self.create_presence()
        LOGGER.info(f'Отправка сообщения на сервер - {message_to_server}')
        send_message(self.transport, message_to_server)
        try:
            answer = self.process_ans(get_message(self.transport))
            # print(answer)
            LOGGER.info(f'Получен ответ от сервера {answer}')
        except (ValueError, json.JSONDecodeError):
            # print('Не удалось декодировать сообщение сервера.')
            LOGGER.critical(f'Не удалось декодировать сообщение от сервера')

        if client_mode == 'send':
            LOGGER.info('Режим работы - отправка сообщений')
        else:
            LOGGER.info('Режим работы - прием сообщений')
        while True:
            if client_mode == 'send':
                try:
                    send_message(self.transport, self.create_message())
                except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                    LOGGER.error(f'Соединение с сервером {server_address} было утеряно')
                    sys.exit(1)

            if client_mode == 'listen':
                try:
                    answer = get_message(self.transport)
                    LOGGER.info(f'Сообщение из чята от {answer["sender"]}: {answer["message_text"]}')
                    print(f'Сообщение из чята от {answer["sender"]}: {answer["message_text"]}')
                except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                    LOGGER.error(f'Соединение с сервером {server_address} было утеряно')
                    sys.exit(1)


if __name__ == '__main__':
    client = MsgClient()
    client.start()
