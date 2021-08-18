import argparse
import logging
import select
import socket
import sys
import json
import time

import logs.conf.server_log_config
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, MESSAGE_TEXT, \
    MESSAGE, SENDER, MESSAGE_KEY, ACCOUNT_KEY
from common.utils import get_message, send_message, create_arg_parser

LOGGER = logging.getLogger('server')  # забрали  логгер из конфига


class MsgServer:
    def __init__(self):
        self.clients = []
        self.messages = []

    def process_client_message(self, message, client):
        LOGGER.debug(f'Попытка разобрать клиентское сообщение: {message}')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message \
                and message[USER][ACCOUNT_NAME] == 'Guest':
            send_message(client, {RESPONSE: 200})
            return
        elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and MESSAGE_TEXT in message[USER]:
            LOGGER.debug(f"От клиета {message[USER][ACCOUNT_NAME]} получено сообщение {message[USER][MESSAGE_TEXT]}")
            self.messages.append(
                (message[USER][ACCOUNT_NAME], message[USER][MESSAGE_TEXT]))  # кортеж для уменьшения объема памяти
            return
        else:
            LOGGER.debug(f"Некорректный запрос, вернуть 400")
            send_message(client, {
                RESPONSE: 400,
                ERROR: 'Bad Request'
            })
            return

    def start(self):
        LOGGER.info('Попытка запуска сервера')
        parser = create_arg_parser()
        namespace = parser.parse_args(sys.argv[1:])
        listen_address = namespace.a
        listen_port = namespace.p

        if not 1023 < listen_port < 65535:
            LOGGER.critical(f'Невозможно запустить сервер на порту {listen_port}, порт занят или недопустим')
            sys.exit(1)
        try:
            transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            transport.bind((listen_address, listen_port))
            transport.listen(MAX_CONNECTIONS)
            transport.settimeout(0.1)
        except OSError as err:
            LOGGER.error(f'Адрес {listen_address} и порт {listen_port} не  могут быть использованы для запуска,'
                         f' потому что уже используются другой программой', err)
            sys.exit(1)
        else:
            print(f'Запущен сервер прослушивающий на {listen_address if listen_address else "любом"} ip-адресе и '
                  f'{listen_port} порту')
            LOGGER.info(f'Запущен сервер прослушивающий на {listen_address if listen_address else "любом"} ip-адресе'
                        f' и {listen_port} порту')

        while True:
            try:
                client, client_address = transport.accept()
            except OSError:
                pass
            else:
                LOGGER.info(f'Установлено соединение с адресом {client_address}')
                self.clients.append(client)
            incoming_data_list = []
            to_send_data_list = []
            errors_list = []

            # проверяем есть ли новые клиенты или данные от уже подключеных
            try:
                if self.clients:
                    incoming_data_list, to_send_data_list, errors_list = select.select(self.clients, self.clients, [],
                                                                                       0)
                    # print(incoming_data_list, to_send_data_list, self.clients)
            except OSError:
                pass

            # парсим сообщения слиентов и есть есть сообщения кладем их в словарь сообщений,
            # если ошибка - исключаем клиента
            if incoming_data_list:
                for sended_from_client in incoming_data_list:
                    try:
                        self.process_client_message(get_message(sended_from_client), sended_from_client)
                    except:
                        LOGGER.info(f'{sended_from_client.getpeername()} отключился от сервера')
                        self.clients.remove(sended_from_client)

            # print(self.messages)

            # проверяем есть ли ожидающие сообщений клиенты и сообщения для отправки и  отправляем их клиентам
            if to_send_data_list and self.messages:
                message = {
                    ACTION: MESSAGE,
                    TIME: time.time(),
                    SENDER: self.messages[0][ACCOUNT_KEY],
                    MESSAGE_TEXT: self.messages[0][MESSAGE_KEY],
                }
                del self.messages[0]
                for one_client in to_send_data_list:
                    try:
                        LOGGER.info(f'Отправляем сообщение {message} клиенту {one_client}')
                        send_message(one_client, message)
                    except:
                        LOGGER.info(f'{one_client.getpeername()} отключился от сервера')
                        self.clients.remove(one_client)


if __name__ == '__main__':
    server = MsgServer()
    server.start()
