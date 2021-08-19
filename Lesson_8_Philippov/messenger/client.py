"""Программа-клиент"""
import logging
import sys
import json
import socket
import time
import argparse
import logs.conf.client_log_config
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, MESSAGE_TEXT, MESSAGE, EXIT, SENDER, DESTINATION
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

    def create_message(self, account_name='Guest', destination='ALL'):
        message = input('Введите сообщения для отправки или !!! для выхода: ')
        if message == '!!!':
            self.create_exit_message(self.client_name)
            self.transport.close()
            LOGGER.info('Пользователь завершил работу приложения')
            sys.exit(0)
        out = {
            DESTINATION: destination,
            SENDER: account_name,
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

    # def __init__(self):
    #     LOGGER.debug("Инициализация клиента")
    def client_sending(self):
        LOGGER.info('Режим работы - отправка сообщений')
        while True:
            try:
                send_message(self.transport, self.create_message(self.client_name))
            except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                LOGGER.error(f'Соединение с сервером {self.server_address} было утеряно')
                sys.exit(1)

    def client_receiving(self):
        LOGGER.info('Режим работы - прием сообщений')
        while True:
            try:
                answer = get_message(self.transport)
                # print(answer)
                print(f'User{answer[SENDER]}: {answer["message_text"]}')
                LOGGER.info(f'Сообщение из чята от {answer[SENDER]}: {answer["message_text"]}')
                # print(f'Сообщение из чята от {answer["sender"]}: {answer["message_text"]}')
            except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                LOGGER.error(f'Соединение с сервером {self.server_address} было утеряно')
                sys.exit(1)

    @func_log
    def create_exit_message(account_name):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: account_name
        }

    def __init__(self):
        # получаем параметры из командной строки
        # client.py -a localhost -p 8079 -m send/listen
        LOGGER.debug("Попытка получить параметры запуска клиента")
        parser = create_arg_parser()
        namespace = parser.parse_args(sys.argv[1:])
        self.server_address = namespace.a
        self.server_port = namespace.p
        client_mode = namespace.m
        LOGGER.debug(f'Адрес и порт сервера {self.server_address}:{self.server_port}')

        try:
            self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.transport.connect((self.server_address, self.server_port))
            print(f'User{self.transport.getsockname()[1]}')
            self.client_name = self.transport.getsockname()[1]
            LOGGER.debug(
                f'Подключение к серверу с адресом {self.server_address if self.server_address else "localhost"} '
                f'по {self.server_port} порту')
        except ConnectionRefusedError:
            LOGGER.error(f'Не удалось подключится к серверу {self.server_address}:{self.server_port}, '
                         f'возможно он не запущен или что-то с сетью')
        except json.JSONDecodeError:
            LOGGER.error('Не удалось декодировать полученную Json строку.')
            sys.exit(1)
        except errors.ServerError as error:
            LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
            sys.exit(1)
        except errors.ReqFieldMissingError as missing_error:
            LOGGER.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
            sys.exit(1)

        message_to_server = self.create_presence(self.client_name)
        LOGGER.info(f'Отправка сообщения на сервер - {message_to_server}')
        send_message(self.transport, message_to_server)
        try:
            answer = self.process_ans(get_message(self.transport))
            LOGGER.info(f'Получен ответ от сервера {answer}')
        except (ValueError, json.JSONDecodeError):
            # print('Не удалось декодировать сообщение сервера.')
            LOGGER.critical(f'Не удалось декодировать сообщение от сервера')

    def start(self):
        send_thread = Thread(target=self.client_sending, daemon=True)
        receive_thread = Thread(target=self.client_receiving, daemon=True)
        send_thread.start()
        receive_thread.start()
        send_thread.join()
        receive_thread.join()


if __name__ == '__main__':
    client = MsgClient()
    client.start()
